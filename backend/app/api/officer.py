from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.models import Ticket, Officer, TicketStatus, Resolution, TicketEvent
from backend.app.api.auth import get_current_officer
from backend.app.services.closure import process_resolution
from backend.app.services.audit import append_ticket_event
from backend.app.channels import get_channel_adapter
from backend.app import clock

router = APIRouter(prefix="/api/officer", tags=["Officer"])

class BlockRequest(BaseModel):
    reason_code: str  # budget | jurisdiction | material | safety
    notes: Optional[str] = None

@router.get("/tickets")
def list_officer_tickets(
    status_filter: Optional[str] = None,
    officer: Officer = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    """
    Officer inbox sorted by explainable priority score.
    Includes SLA countdown and status indicators.
    """
    query = db.query(Ticket)

    # If JE, filter by officer assigned or department + ward
    if officer.role.value == "je":
        query = query.filter(
            (Ticket.assigned_officer_id == officer.id) |
            (Ticket.department_id == officer.department_id)
        )
    elif officer.role.value == "ee":
        query = query.filter(Ticket.department_id == officer.department_id)
    # Commissioner and admin see all

    if status_filter:
        query = query.filter(Ticket.status == status_filter)

    tickets = query.order_by(Ticket.priority_score.desc()).all()
    now_dt = clock.now()

    result = []
    for t in tickets:
        sla_hours_left = None
        sla_status = "green"  # green, amber, red
        if t.sla_due_at and t.created_at:
            total_sla = (t.sla_due_at - t.created_at).total_seconds()
            left_seconds = (t.sla_due_at - now_dt).total_seconds()
            sla_hours_left = round(left_seconds / 3600.0, 1)

            if left_seconds < 0:
                sla_status = "red"  # breached
            elif total_sla > 0 and (left_seconds / total_sla) < 0.30:
                sla_status = "amber"  # approaching breach

        result.append({
            "id": t.id,
            "code": t.code,
            "category": t.category,
            "department": t.department.name,
            "ward": t.ward.name,
            "ward_id": t.ward_id,
            "lat": t.lat,
            "lng": t.lng,
            "address": t.address_text,
            "status": t.status.value,
            "severity": t.severity,
            "affected_count": t.affected_count,
            "priority_score": t.priority_score,
            "priority_reason": t.priority_reason,
            "sla_due_at": t.sla_due_at.isoformat() if t.sla_due_at else None,
            "sla_hours_left": sla_hours_left,
            "sla_status": sla_status,
            "escalation_level": t.escalation_level,
            "created_at": t.created_at.isoformat() if t.created_at else None
        })

    return result

@router.get("/tickets/{ticket_id}")
def get_officer_ticket_detail(
    ticket_id: int,
    officer: Officer = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    events = db.query(TicketEvent).filter(TicketEvent.ticket_id == ticket.id).order_by(TicketEvent.created_at.asc()).all()
    reports = ticket.reports
    latest_res = ticket.resolutions[-1] if ticket.resolutions else None

    return {
        "id": ticket.id,
        "code": ticket.code,
        "category": ticket.category,
        "department": ticket.department.name,
        "ward": ticket.ward.name,
        "ward_id": ticket.ward_id,
        "lat": ticket.lat,
        "lng": ticket.lng,
        "address": ticket.address_text,
        "status": ticket.status.value,
        "severity": ticket.severity,
        "affected_count": ticket.affected_count,
        "priority_score": ticket.priority_score,
        "priority_reason": ticket.priority_reason,
        "sla_due_at": ticket.sla_due_at.isoformat() if ticket.sla_due_at else None,
        "escalation_level": ticket.escalation_level,
        "reopen_count": ticket.reopen_count,
        "reports": [
            {
                "id": r.id,
                "text": r.text,
                "media_url": r.media_url,
                "audio_url": r.audio_url,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in reports
        ],
        "resolution": {
            "after_photo_url": latest_res.after_photo_url,
            "distance_m": latest_res.distance_m,
            "needs_review": latest_res.needs_review,
            "ai_check": latest_res.ai_check,
            "created_at": latest_res.created_at.isoformat()
        } if latest_res else None,
        "events": [
            {
                "type": e.type,
                "actor_type": e.actor_type,
                "actor_id": e.actor_id,
                "payload": e.payload,
                "created_at": e.created_at.isoformat()
            }
            for e in events
        ]
    }

@router.post("/tickets/{ticket_id}/accept")
def accept_ticket(
    ticket_id: int,
    officer: Officer = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = TicketStatus.IN_PROGRESS
    ticket.assigned_officer_id = officer.id
    if not ticket.first_response_at:
        ticket.first_response_at = clock.now()

    append_ticket_event(
        db,
        ticket_id=ticket.id,
        event_type="in_progress",
        actor_type="officer",
        actor_id=str(officer.id),
        payload={"officer_name": officer.name},
        timestamp=clock.now()
    )
    db.commit()

    # Notify reporting citizens
    for r in ticket.reports:
        if r.citizen:
            get_channel_adapter(r.citizen.channel).send_text(
                r.citizen.channel_user_id,
                f"👷 *Work Started:* Officer {officer.name} has accepted and started work on Ticket {ticket.code}."
            )

    return {"status": "ok", "ticket_status": "in_progress"}

@router.post("/tickets/{ticket_id}/block")
def block_ticket(
    ticket_id: int,
    block_req: BlockRequest,
    officer: Officer = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    append_ticket_event(
        db,
        ticket_id=ticket.id,
        event_type="blocked",
        actor_type="officer",
        actor_id=str(officer.id),
        payload={"reason_code": block_req.reason_code, "notes": block_req.notes},
        timestamp=clock.now()
    )
    db.commit()

    # Transparent communication to citizens
    reason_human = {
        "budget": "pending budget sanction",
        "jurisdiction": "coordination with NHAI / Railways",
        "material": "procurement of specialized asphalt / materials",
        "safety": "heavy rain / site safety clearance"
    }.get(block_req.reason_code, block_req.reason_code)

    for r in ticket.reports:
        if r.citizen:
            get_channel_adapter(r.citizen.channel).send_text(
                r.citizen.channel_user_id,
                f"📢 *Notice for Ticket {ticket.code}:* Action temporarily delayed due to: *{reason_human}*.\nTransparent tracking remains active."
            )

    return {"status": "ok", "message": f"Block reason recorded: {block_req.reason_code}"}

@router.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: int,
    lat: float = Form(...),
    lng: float = Form(...),
    note: Optional[str] = Form(None),
    mismatch_reason: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    officer: Officer = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    photo_bytes = await photo.read()
    
    # Store or simulate photo URL
    after_photo_url = f"https://images.unsplash.com/photo-1584467735871-8e85353a8413?w=600&ticket={ticket.code}"

    success, message, resolution = process_resolution(
        db=db,
        ticket=ticket,
        officer_id=officer.id,
        after_photo_bytes=photo_bytes,
        after_photo_url=after_photo_url,
        officer_lat=lat,
        officer_lng=lng,
        mismatch_reason=mismatch_reason
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "status": "ok",
        "message": message,
        "needs_review": resolution.needs_review,
        "distance_m": resolution.distance_m
    }
