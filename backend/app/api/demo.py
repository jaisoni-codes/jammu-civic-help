from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.db import get_db, SessionLocal
from backend.app.models import Ticket, Citizen, TicketStatus, Ward
from backend.app.services.intake import process_citizen_intake
from backend.app.services.sla import check_sla_and_escalations, check_auto_close_72h
from backend.app.services.trust_index import snapshot_all_wards, compute_ward_trust_index
from backend.app.channels.console import get_outbox, clear_outbox, drain_outbox
from backend.app import clock

router = APIRouter(prefix="/api/demo", tags=["Demo Control Panel"])

class AdvanceTimeRequest(BaseModel):
    hours: float

class CitizenReplyRequest(BaseModel):
    code: str
    result: str  # "yes" (solved) | "no" (not solved) | "rating_5"

class SimulateComplaintRequest(BaseModel):
    ward_id: int = 1
    category: str = "road_pothole"
    text: str = "Pothole in Purani Mandi main market road causing scooter skids."
    citizen_count: int = 3

@router.post("/advance-time")
def advance_time(req: AdvanceTimeRequest, db: Session = Depends(get_db)):
    """Advances simulated demo clock by specified hours and triggers SLA/auto-close jobs."""
    new_offset = clock.advance_demo_offset(req.hours)
    
    # Run SLA escalation checks and 72h auto-close
    check_sla_and_escalations(db)
    check_auto_close_72h(db)
    
    # Refresh trust snapshots
    snapshot_all_wards(db)

    return {
        "status": "ok",
        "advanced_hours": req.hours,
        "total_offset_hours": new_offset,
        "simulated_time": clock.now().isoformat()
    }

@router.post("/simulate-complaint")
def simulate_complaint(req: SimulateComplaintRequest, db: Session = Depends(get_db)):
    """Simulates N citizens reporting the same issue to demo Collective Voice clustering."""
    ward = db.query(Ward).get(req.ward_id)
    if not ward:
        ward = db.query(Ward).first()

    lat = ward.centroid_lat + 0.0005
    lng = ward.centroid_lng + 0.0005

    results = []
    ticket_code = None

    for i in range(1, req.citizen_count + 1):
        user_id = f"sim_demo_cit_{i}"
        
        # 1. Citizen sends report
        process_citizen_intake(
            db=db,
            channel="console",
            channel_user_id=user_id,
            text=f"{req.text} (Report from citizen #{i})",
            lat=lat + (i * 0.0001), # Within ~15m
            lng=lng + (i * 0.0001)
        )
        
        # 2. Citizen confirms report
        conf = process_citizen_intake(
            db=db,
            channel="console",
            channel_user_id=user_id,
            button_reply_id="confirm_yes"
        )
        results.append(conf)
        ticket_code = conf.get("ticket_code")

    ticket = db.query(Ticket).filter(Ticket.code == ticket_code).first()
    return {
        "status": "ok",
        "ticket_code": ticket_code,
        "affected_count": ticket.affected_count if ticket else req.citizen_count,
        "priority_score": ticket.priority_score if ticket else None,
        "priority_reason": ticket.priority_reason if ticket else None,
        "is_clustered": req.citizen_count > 1
    }

@router.post("/citizen-reply")
def citizen_reply(req: CitizenReplyRequest, db: Session = Depends(get_db)):
    """Simulates citizen tapping Yes (Solved) or No (Not Solved) or Rating."""
    button_id = f"verify_{req.result}_{req.code}"
    res = process_citizen_intake(
        db=db,
        channel="console",
        channel_user_id="demo_citizen_verifier",
        button_reply_id=button_id
    )
    # Recompute trust index for ticket's ward
    t = db.query(Ticket).filter(Ticket.code == req.code).first()
    new_score = None
    if t:
        new_score, _ = compute_ward_trust_index(db, t.ward_id)
        snapshot_all_wards(db)

    return {
        "status": "ok",
        "result": res,
        "ward_trust_index": new_score
    }

@router.get("/outbox")
def read_console_outbox():
    """Returns AND clears messages sent to the console channel (drain-on-read)."""
    return {"messages": drain_outbox()}

@router.post("/outbox/clear")
def clear_console_outbox():
    """Explicit clear if needed."""
    clear_outbox()
    return {"status": "cleared"}

@router.post("/reset")
def reset_demo_state(db: Session = Depends(get_db)):
    """Resets clock offset and clears console outbox."""
    clock.reset_clock()
    clear_outbox()
    return {
        "status": "ok",
        "demo_offset_hours": 0.0,
        "clock_now": clock.now().isoformat()
    }
