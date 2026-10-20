import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models import Ticket, POI
from backend.app.db import haversine_distance_m
from backend.app.business_rules import PRIORITY_WEIGHTS
from backend.app import clock

def compute_priority_score(
    db: Session,
    affected_count: int,
    severity: int,
    created_at: datetime,
    safety_flag: float,
    lat: float,
    lng: float
) -> Tuple[float, List[str]]:
    """
    Computes explainable priority score:
    aff = min(1, ln(1+affected_count)/ln(51))
    sev = severity/5
    age = min(1, age_days/14)
    safety = safety_flag (0, 0.5, 1)
    vuln = 1 if hospital/school/elderly_home POI <= 300 m else 0
    priority_score = 100*(0.30*aff + 0.25*sev + 0.20*age + 0.15*safety + 0.10*vuln)
    """
    reasons: List[str] = []

    # 1. Affected Citizens (Collective Voice)
    aff_norm = min(1.0, math.log(1.0 + max(1, affected_count)) / math.log(51.0))
    if affected_count > 1:
        reasons.append(f"{affected_count} citizens reported this (Collective Voice)")
    else:
        reasons.append("1 citizen reported")

    # 2. Severity (1-5)
    sev_norm = min(1.0, max(1, severity) / 5.0)
    reasons.append(f"Severity level {severity}/5")

    # 3. Age
    now_dt = clock.now()
    if now_dt.tzinfo is not None:
        now_dt = now_dt.replace(tzinfo=None)
    created_at_naive = created_at.replace(tzinfo=None) if created_at.tzinfo else created_at
    
    age_days = max(0.0, (now_dt - created_at_naive).total_seconds() / 86400.0)
    age_norm = min(1.0, age_days / 14.0)
    if age_days >= 1.0:
        reasons.append(f"{int(age_days)} days pending")
    else:
        hours = max(1, int(age_days * 24))
        reasons.append(f"{hours} hours pending")

    # 4. Safety Flag (0, 0.5, 1.0)
    safety_norm = float(safety_flag)
    if safety_norm >= 1.0:
        reasons.append("High public safety hazard (open live wire / sinkhole)")
    elif safety_norm >= 0.5:
        reasons.append("Moderate safety risk")

    # 5. Vulnerability: POI within 300m
    vuln_norm = 0.0
    pois = db.query(POI).all()
    for poi in pois:
        dist = haversine_distance_m(lat, lng, poi.lat, poi.lng)
        if dist <= 300.0:
            vuln_norm = 1.0
            reasons.append(f"Near vulnerable facility: {poi.name} ({int(dist)}m away)")
            break

    score = 100.0 * (
        PRIORITY_WEIGHTS["affected"] * aff_norm +
        PRIORITY_WEIGHTS["severity"] * sev_norm +
        PRIORITY_WEIGHTS["age"] * age_norm +
        PRIORITY_WEIGHTS["safety"] * safety_norm +
        PRIORITY_WEIGHTS["vulnerability"] * vuln_norm
    )

    return round(score, 1), reasons

def get_ward_rank(db: Session, ticket: Ticket) -> Tuple[int, int]:
    """
    Returns (rank, total_open_tickets) for this ticket among OPEN/IN_PROGRESS/ASSIGNED/REOPENED tickets in the same ward.
    """
    open_statuses = ["open", "assigned", "in_progress", "reopened"]
    open_tickets = (
        db.query(Ticket)
        .filter(Ticket.ward_id == ticket.ward_id, Ticket.status.in_(open_statuses))
        .order_by(Ticket.priority_score.desc())
        .all()
    )
    total = len(open_tickets)
    rank = 1
    for idx, t in enumerate(open_tickets):
        if t.id == ticket.id:
            rank = idx + 1
            break
    return rank, max(1, total)
