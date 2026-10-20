from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from backend.app.db import get_db
from backend.app.models import Ward, Ticket, Report, TicketEvent, Project, Vote, TrustSnapshot, Officer, Department, Citizen, TicketStatus
from backend.app.services.audit import verify_ticket_chain, append_ticket_event
from backend.app.services.priority import get_ward_rank, compute_priority_score
from backend.app.services.routing import find_nearest_ward, route_ticket
from backend.app.services.clustering import find_duplicate_ticket
from backend.app.services.ai import ai_service
from backend.app import clock
from datetime import timedelta

router = APIRouter(prefix="/api/public", tags=["Public"])

@router.get("/city")
def get_city_overview(db: Session = Depends(get_db)):
    wards = db.query(Ward).all()
    total_tickets = db.query(Ticket).count()
    open_tickets = db.query(Ticket).filter(Ticket.status.in_(["open", "assigned", "in_progress", "reopened"])).count()
    verified_closed = db.query(Ticket).filter(Ticket.status == "verified_closed").count()

    # Calculate average trust index from latest snapshots
    ward_summaries = []
    total_trust = 0.0
    for w in wards:
        latest_snap = (
            db.query(TrustSnapshot)
            .filter(TrustSnapshot.ward_id == w.id)
            .order_by(TrustSnapshot.date.desc())
            .first()
        )
        t_index = latest_snap.trust_index if latest_snap else 65.0
        total_trust += t_index
        ward_summaries.append({
            "id": w.id,
            "name": w.name,
            "centroid_lat": w.centroid_lat,
            "centroid_lng": w.centroid_lng,
            "population": w.population_est,
            "trust_index": t_index,
            "open_tickets": db.query(Ticket).filter(Ticket.ward_id == w.id, Ticket.status.in_(["open", "assigned", "in_progress", "reopened"])).count()
        })

    avg_city_trust = round(total_trust / max(1, len(wards)), 1)
    
    # Sort leaderboard
    leaderboard = sorted(ward_summaries, key=lambda x: x["trust_index"], reverse=True)
    if leaderboard:
        leaderboard[0]["is_champion"] = True

    return {
        "city": "Jammu Smart City",
        "city_trust_index": avg_city_trust,
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "verified_closed": verified_closed,
        "wards": leaderboard
    }

@router.get("/wards")
def list_wards(db: Session = Depends(get_db)):
    return db.query(Ward).all()

@router.get("/wards/{ward_id}")
def get_ward_details(ward_id: int, db: Session = Depends(get_db)):
    ward = db.query(Ward).get(ward_id)
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")

    snapshots = (
        db.query(TrustSnapshot)
        .filter(TrustSnapshot.ward_id == ward_id)
        .order_by(TrustSnapshot.date.asc())
        .limit(30)
        .all()
    )

    open_count = db.query(Ticket).filter(Ticket.ward_id == ward_id, Ticket.status.in_(["open", "assigned", "in_progress"])).count()
    verified_count = db.query(Ticket).filter(Ticket.ward_id == ward_id, Ticket.status == "verified_closed").count()
    reopened_count = db.query(Ticket).filter(Ticket.ward_id == ward_id, Ticket.status == "reopened").count()

    latest_snap = snapshots[-1] if snapshots else None
    trust_index = latest_snap.trust_index if latest_snap else 65.0
    components = latest_snap.components if latest_snap else {}

    # Recent verified wins
    wins = (
        db.query(Ticket)
        .filter(Ticket.ward_id == ward_id, Ticket.status == "verified_closed")
        .order_by(Ticket.closed_at.desc())
        .limit(3)
        .all()
    )

    # Top 10 open tickets by priority
    open_tickets_list = (
        db.query(Ticket)
        .filter(Ticket.ward_id == ward_id, Ticket.status.in_(["open", "assigned", "in_progress", "reopened"]))
        .order_by(Ticket.priority_score.desc())
        .limit(10)
        .all()
    )

    # Mohalla Budget projects
    projects_list = (
        db.query(Project)
        .filter(Project.ward_id == ward_id)
        .order_by(Project.id.desc())
        .all()
    )
    project_votes = {}
    for p in projects_list:
        cnt = db.query(Vote).filter(Vote.project_id == p.id).count()
        project_votes[p.id] = cnt

    return {
        "id": ward.id,
        "name": ward.name,
        "population_est": ward.population_est,
        "centroid_lat": ward.centroid_lat,
        "centroid_lng": ward.centroid_lng,
        "trust_index": trust_index,
        "components": components,
        "open_count": open_count,
        "open_tickets_count": open_count,
        "verified_count": verified_count,
        "reopened_count": reopened_count,
        "history": [{"date": s.date, "score": s.trust_index} for s in snapshots],
        "open_tickets": [
            {
                "id": t.id,
                "code": t.code,
                "category": t.category,
                "status": t.status.value if hasattr(t.status, "value") else t.status,
                "priority_score": round(t.priority_score or 0, 1),
                "affected_count": t.affected_count,
                "escalation_level": t.escalation_level,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in open_tickets_list
        ],
        "projects": [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "est_cost": p.est_cost,
                "status": p.status.value if hasattr(p.status, "value") else p.status,
                "cycle": p.cycle,
                "vote_count": project_votes.get(p.id, 0),
            }
            for p in projects_list
        ],
        "recent_wins": [
            {
                "code": w.code,
                "category": w.category,
                "resolved_at": w.resolved_at.isoformat() if w.resolved_at else None,
                "affected_count": w.affected_count
            }
            for w in wins
        ]
    }

@router.get("/tickets/{code}")
def get_ticket_public(code: str, db: Session = Depends(get_db)):
    """
    Public ticket view with privacy preservation:
    Exact citizen phone numbers and exact house coordinates are omitted.
    Location is fuzzed to ward centroid + general landmark.
    """
    ticket = db.query(Ticket).filter(Ticket.code == code).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    rank, total_open = get_ward_rank(db, ticket)
    is_valid_chain, _, chain_msg = verify_ticket_chain(db, ticket.id)

    # Timeline from ticket_events
    events = (
        db.query(TicketEvent)
        .filter(TicketEvent.ticket_id == ticket.id)
        .order_by(TicketEvent.created_at.asc())
        .all()
    )

    first_report = ticket.reports[0] if ticket.reports else None
    latest_resolution = ticket.resolutions[-1] if ticket.resolutions else None

    return {
        "code": ticket.code,
        "category": ticket.category,
        "department": ticket.department.name,
        "ward": {
            "id": ticket.ward.id,
            "name": ticket.ward.name,
            "centroid_lat": ticket.ward.centroid_lat,
            "centroid_lng": ticket.ward.centroid_lng,
        },
        "address_landmark": ticket.address_text or f"Ward {ticket.ward_id}, Jammu",
        "status": ticket.status.value,
        "affected_count": ticket.affected_count,
        "priority_score": ticket.priority_score,
        "priority_reason": ticket.priority_reason,
        "ward_rank": rank,
        "total_ward_open_tickets": total_open,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "sla_due_at": ticket.sla_due_at.isoformat() if ticket.sla_due_at else None,
        "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
        "reopen_count": ticket.reopen_count,
        "before_photo_url": first_report.media_url if first_report else None,
        "after_photo_url": latest_resolution.after_photo_url if latest_resolution else None,
        "audit_chain": {
            "is_valid": is_valid_chain,
            "message": chain_msg,
            "event_count": len(events)
        },
        "timeline": [
            {
                "id": ev.id,
                "type": ev.type,
                "actor_type": ev.actor_type,
                "created_at": ev.created_at.isoformat() if ev.created_at else None,
                "payload": ev.payload
            }
            for ev in events
        ]
    }

@router.get("/tickets/{code}/verify-chain")
def verify_ticket_chain_endpoint(code: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.code == code).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    is_valid, count, message = verify_ticket_chain(db, ticket.id)
    return {
        "ticket_code": code,
        "valid": is_valid,
        "events_verified": count,
        "message": message
    }

@router.post("/quick-report")
async def submit_quick_report(
    text: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    photo: Optional[UploadFile] = File(None),
    citizen_name: Optional[str] = Form("Jammu Citizen"),
    db: Session = Depends(get_db)
):
    """
    Zero-friction, zero-login, QR-friendly citizen reporting endpoint.
    Performs AI authenticity checks to block spam, memes, greetings, and fake reports.
    Clusters duplicates automatically if within 60m.
    """
    photo_bytes = await photo.read() if photo else None

    # Step 1: AI Authenticity & Credibility Filter
    auth_check = ai_service.check_authenticity(text=text, photo_bytes=photo_bytes)
    if not auth_check.is_valid_civic_issue:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "AUTHENTICITY_REJECTED",
                "message": auth_check.rejection_reason or "Only genuine municipal issues (potholes, garbage, water, streetlights) can be reported.",
                "detected": auth_check.detected_issue
            }
        )

    # Step 2: Auto-route to Ward by exact GPS coordinates
    ward = find_nearest_ward(db, lat, lng)
    if not ward:
        raise HTTPException(status_code=400, detail="Location outside Jammu municipal coverage.")

    # Step 3: Classify complaint
    classification = ai_service.classify_complaint(text)
    dept, officer = route_ticket(db, classification.category, ward.id)

    # Step 4: Ensure an anonymous citizen record exists
    citizen = db.query(Citizen).filter(Citizen.channel == "web_qr", Citizen.channel_user_id == "web_qr_citizen").first()
    if not citizen:
        citizen = Citizen(
            channel="web_qr",
            channel_user_id="web_qr_citizen",
            lang="en",
            ward_id=ward.id,
            subscribed=True
        )
        db.add(citizen)
        db.commit()
        db.refresh(citizen)

    # Step 5: Duplicate Clustering Check (Collective Voice within 60m)
    embedding = ai_service.get_embedding(text)
    existing_ticket = find_duplicate_ticket(
        db,
        category=classification.category,
        lat=lat,
        lng=lng,
        embedding=embedding
    )

    now_dt = clock.now()
    photo_url = f"https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?w=600&q=80" if photo_bytes else None

    if existing_ticket:
        # Clustered to existing ticket
        existing_ticket.affected_count += 1
        report = Report(
            ticket_id=existing_ticket.id,
            citizen_id=citizen.id,
            text=text,
            media_url=photo_url,
            lat=lat,
            lng=lng,
            created_at=now_dt
        )
        db.add(report)
        db.flush()

        # Recalculate priority
        p_score, p_reasons = compute_priority_score(
            db,
            affected_count=existing_ticket.affected_count,
            severity=existing_ticket.severity,
            created_at=existing_ticket.created_at,
            safety_flag=existing_ticket.safety_flag,
            lat=existing_ticket.lat,
            lng=existing_ticket.lng
        )
        existing_ticket.priority_score = p_score
        existing_ticket.priority_reason = p_reasons

        append_ticket_event(
            db,
            ticket_id=existing_ticket.id,
            event_type="cluster_joined",
            actor_type="citizen",
            actor_id=str(citizen.id),
            payload={"affected_count": existing_ticket.affected_count, "channel": "web_qr"},
            timestamp=now_dt
        )
        db.commit()

        return {
            "status": "clustered",
            "is_new": False,
            "ticket_code": existing_ticket.code,
            "ward_name": ward.name,
            "category": existing_ticket.category,
            "affected_count": existing_ticket.affected_count,
            "priority_score": existing_ticket.priority_score,
            "message": f"Your report joined existing Ticket {existing_ticket.code}! {existing_ticket.affected_count} citizens have now reported this problem."
        }

    # Step 6: Create New Ticket
    count = db.query(Ticket).count() + 1
    code = f"BH-{count:04d}"

    p_score, p_reasons = compute_priority_score(
        db,
        affected_count=1,
        severity=classification.severity,
        created_at=now_dt,
        safety_flag=classification.safety_flag,
        lat=lat,
        lng=lng
    )

    from backend.app.business_rules import CATEGORIES_CONFIG
    cat_cfg = CATEGORIES_CONFIG.get(classification.category, CATEGORIES_CONFIG["other"])
    sla_due = now_dt + timedelta(hours=cat_cfg["sla_hours"])

    new_ticket = Ticket(
        code=code,
        category=classification.category,
        department_id=dept.id,
        ward_id=ward.id,
        lat=lat,
        lng=lng,
        address_text=f"Near {ward.name}, Jammu",
        status=TicketStatus.ASSIGNED if officer else TicketStatus.OPEN,
        severity=classification.severity,
        safety_flag=classification.safety_flag,
        affected_count=1,
        priority_score=p_score,
        priority_reason=p_reasons,
        sla_due_at=sla_due,
        assigned_officer_id=officer.id if officer else None,
        created_at=now_dt
    )
    db.add(new_ticket)
    db.flush()

    report = Report(
        ticket_id=new_ticket.id,
        citizen_id=citizen.id,
        text=text,
        media_url=photo_url,
        lat=lat,
        lng=lng,
        created_at=now_dt
    )
    db.add(report)

    append_ticket_event(
        db,
        ticket_id=new_ticket.id,
        event_type="created",
        actor_type="citizen",
        actor_id=str(citizen.id),
        payload={"category": new_ticket.category, "channel": "web_qr", "text_summary": classification.summary},
        timestamp=now_dt
    )
    db.commit()

    return {
        "status": "created",
        "is_new": True,
        "ticket_code": new_ticket.code,
        "ward_name": ward.name,
        "category": new_ticket.category,
        "assigned_to": officer.name if officer else "Municipal Dispatch",
        "priority_score": new_ticket.priority_score,
        "message": f"Grievance successfully recorded as Ticket {new_ticket.code} in {ward.name}!"
    }


class FeedbackRequest(BaseModel):
    reason: Optional[str] = None

@router.post("/tickets/{code}/verify")
def citizen_verify_resolved(code: str, db: Session = Depends(get_db)):
    """Citizen confirms the repair is complete and satisfactory — closes the ticket."""
    ticket = db.query(Ticket).filter(Ticket.code == code).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.status.value not in ("resolved_pending_verification", "in_progress", "assigned", "open"):
        raise HTTPException(status_code=400, detail=f"Ticket is already {ticket.status.value}")

    ticket.status = TicketStatus.VERIFIED_CLOSED
    from backend.app import clock as _clock
    ticket.closed_at = _clock.now()

    append_ticket_event(
        db,
        ticket_id=ticket.id,
        event_type="verified_closed",
        actor_type="citizen",
        actor_id="web_citizen",
        payload={"feedback": "satisfied", "channel": "web_portal"},
        timestamp=_clock.now()
    )
    db.commit()
    return {"status": "ok", "message": "Thank you! Ticket has been verified and closed."}


@router.post("/tickets/{code}/reopen")
def citizen_reopen_ticket(code: str, req: FeedbackRequest, db: Session = Depends(get_db)):
    """Citizen reports that the issue is NOT resolved — reopens the ticket."""
    ticket = db.query(Ticket).filter(Ticket.code == code).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.status.value == "verified_closed":
        raise HTTPException(status_code=400, detail="Ticket is already verified closed")

    ticket.status = TicketStatus.REOPENED
    ticket.reopen_count = (ticket.reopen_count or 0) + 1

    from backend.app import clock as _clock
    append_ticket_event(
        db,
        ticket_id=ticket.id,
        event_type="reopened",
        actor_type="citizen",
        actor_id="web_citizen",
        payload={"reason": req.reason or "Not satisfied with resolution", "channel": "web_portal"},
        timestamp=_clock.now()
    )
    db.commit()
    return {"status": "ok", "message": "Ticket has been reopened. The officer has been notified."}
