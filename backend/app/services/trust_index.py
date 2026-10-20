import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models import (
    Ward, Ticket, Verification, VerificationResult, Broadcast,
    PulseResponse, Citizen, Vote, TrustSnapshot, TicketStatus
)
from backend.app.business_rules import TRUST_WEIGHTS
from backend.app import clock

def compute_ward_trust_index(db: Session, ward_id: int) -> Tuple[float, Dict[str, Any]]:
    """
    Ward Trust Index (0-100, trailing 30 days):
    - r = response score = clamp(1 - median_hours_to_first_response/24, 0, 1)
    - c = closure score = share of due tickets closed within SLA; unverified_closed counts 0.5
    - o = reopen score = clamp(1 - 2*reopen_rate, 0, 1)
    - s = satisfaction = mean((rating-1)/4) over ratings
    - p = proactive score = clamp(broadcasts_30d/4, 0, 1) * delivery_rate
    - q = participation = clamp(active_citizens / (subscribed * 0.20), 0, 1)
    
    Index = 100 * (0.15*r + 0.25*c + 0.15*o + 0.20*s + 0.10*p + 0.15*q)
    If a component has no data, redistribute weights. Show 'insufficient data' badge when fewer than 10 tickets.
    """
    now_dt = clock.now()
    thirty_days_ago = now_dt - timedelta(days=30)

    # 1. Trailing 30-day tickets for ward
    tickets = (
        db.query(Ticket)
        .filter(Ticket.ward_id == ward_id, Ticket.created_at >= thirty_days_ago)
        .all()
    )

    total_tickets = len(tickets)
    insufficient_data = total_tickets < 10

    # Component r: Response score
    response_hours = []
    for t in tickets:
        if t.first_response_at and t.created_at:
            h = (t.first_response_at - t.created_at).total_seconds() / 3600.0
            if h >= 0:
                response_hours.append(h)
    
    r_score = None
    if response_hours:
        median_h = float(np.median(response_hours))
        r_score = max(0.0, min(1.0, 1.0 - (median_h / 24.0)))

    # Component c: Closure score
    # Due tickets closed within SLA; unverified closed counts at 0.5 weight
    due_tickets = [t for t in tickets if t.sla_due_at and t.sla_due_at <= now_dt]
    c_score = None
    if due_tickets:
        weighted_closed = 0.0
        for t in due_tickets:
            if t.status == TicketStatus.VERIFIED_CLOSED:
                if t.closed_at and t.sla_due_at and t.closed_at <= t.sla_due_at:
                    weighted_closed += 1.0
                elif t.resolved_at and t.sla_due_at and t.resolved_at <= t.sla_due_at:
                    weighted_closed += 1.0
                else:
                    weighted_closed += 0.7  # Closed but late
            elif t.status == TicketStatus.UNVERIFIED_CLOSED:
                weighted_closed += 0.5  # Half weight
        c_score = max(0.0, min(1.0, weighted_closed / len(due_tickets)))
    elif tickets:
        c_score = 0.75  # Default baseline if tickets not yet due

    # Component o: Reopen score
    reopened_count = sum(1 for t in tickets if t.reopen_count > 0 or t.status == TicketStatus.REOPENED)
    o_score = None
    if tickets:
        reopen_rate = reopened_count / max(1, total_tickets)
        o_score = max(0.0, min(1.0, 1.0 - 2.0 * reopen_rate))

    # Component s: Satisfaction rating
    ratings = (
        db.query(Verification.rating)
        .join(Ticket, Verification.ticket_id == Ticket.id)
        .filter(Ticket.ward_id == ward_id, Verification.rating.isnot(None), Verification.created_at >= thirty_days_ago)
        .all()
    )
    s_score = None
    if ratings:
        vals = [(r[0] - 1.0) / 4.0 for r in ratings if r[0] is not None]
        if vals:
            s_score = float(np.mean(vals))

    # Component p: Proactive Broadcast score
    broadcasts = (
        db.query(Broadcast)
        .filter((Broadcast.ward_id == ward_id) | (Broadcast.ward_id.is_(None)))
        .filter(Broadcast.sent_at >= thirty_days_ago)
        .all()
    )
    p_score = None
    if broadcasts:
        b_count = len(broadcasts)
        total_recipients = sum(b.recipients for b in broadcasts) or 1
        total_delivered = sum(b.delivered for b in broadcasts) or 1
        delivery_rate = min(1.0, total_delivered / total_recipients)
        p_score = min(1.0, b_count / 4.0) * delivery_rate
    else:
        p_score = 0.5  # neutral baseline

    # Component q: Participation score
    active_citizens_count = (
        db.query(Citizen.id)
        .filter(Citizen.ward_id == ward_id)
        .count()
    )
    # Target 20% active participation
    subscribed_count = max(1, db.query(Citizen).filter(Citizen.ward_id == ward_id, Citizen.subscribed == True).count())
    q_score = min(1.0, (active_citizens_count / subscribed_count) / 0.20)

    components = {
        "response": round(r_score, 2) if r_score is not None else None,
        "closure": round(c_score, 2) if c_score is not None else None,
        "reopen": round(o_score, 2) if o_score is not None else None,
        "satisfaction": round(s_score, 2) if s_score is not None else None,
        "proactive": round(p_score, 2) if p_score is not None else None,
        "participation": round(q_score, 2) if q_score is not None else None,
    }

    # Dynamic Weight Redistribution for missing components
    active_weights = {}
    for comp, val in components.items():
        if val is not None:
            active_weights[comp] = TRUST_WEIGHTS[comp]

    sum_weights = sum(active_weights.values())
    if sum_weights > 0:
        index_val = 100.0 * sum((active_weights[k] / sum_weights) * components[k] for k in active_weights)
    else:
        index_val = 65.0  # safe city average baseline

    final_index = round(min(100.0, max(0.0, index_val)), 1)
    
    details = {
        "ward_id": ward_id,
        "trust_index": final_index,
        "components": components,
        "insufficient_data": insufficient_data,
        "total_tickets_30d": total_tickets
    }

    return final_index, details

def snapshot_all_wards(db: Session) -> Dict[int, float]:
    """Snapshots current Trust Index for all 10 wards."""
    wards = db.query(Ward).all()
    today_str = clock.now().strftime("%Y-%m-%d")
    results = {}

    for w in wards:
        score, details = compute_ward_trust_index(db, w.id)
        results[w.id] = score

        # Upsert or save snapshot
        existing = (
            db.query(TrustSnapshot)
            .filter(TrustSnapshot.ward_id == w.id, TrustSnapshot.date == today_str)
            .first()
        )
        if existing:
            existing.trust_index = score
            existing.components = details["components"]
        else:
            snap = TrustSnapshot(
                ward_id=w.id,
                date=today_str,
                trust_index=score,
                components=details["components"]
            )
            db.add(snap)

    db.commit()
    return results
