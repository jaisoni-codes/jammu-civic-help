from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.models import (
    Ward, Department, Officer, Ticket, Citizen, Broadcast,
    Project, Vote, TrustSnapshot, ProjectStatus, BroadcastKind
)
from backend.app.api.auth import get_current_officer
from backend.app.channels import get_channel_adapter
from backend.app.services.trust_index import compute_ward_trust_index, snapshot_all_wards
from backend.app import clock

router = APIRouter(prefix="/api/admin", tags=["Admin"])

class CreateBroadcastRequest(BaseModel):
    ward_id: Optional[int] = None  # None = city-wide
    kind: str = "general"          # water | power | road | drive | general
    title: str
    body: str

class CreateProjectRequest(BaseModel):
    ward_id: int
    title: str
    description: str
    est_cost: float = 100000.0
    cycle: str = "2026-Q4"

@router.get("/overview")
def get_admin_overview(
    officer: Officer = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    total_tickets = db.query(Ticket).count()
    open_tickets = db.query(Ticket).filter(Ticket.status.in_(["open", "assigned", "in_progress", "reopened"])).count()
    escalated_l1 = db.query(Ticket).filter(Ticket.escalation_level == 1).count()
    escalated_l2 = db.query(Ticket).filter(Ticket.escalation_level == 2).count()
    verified_closed = db.query(Ticket).filter(Ticket.status == "verified_closed").count()
    unverified_closed = db.query(Ticket).filter(Ticket.status == "unverified_closed").count()
    total_citizens = db.query(Citizen).count()

    return {
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "escalated_level_1": escalated_l1,
        "escalated_level_2": escalated_l2,
        "verified_closed": verified_closed,
        "unverified_closed": unverified_closed,
        "total_citizens": total_citizens,
        "clock_now": clock.now().isoformat(),
        "demo_offset_hours": clock.get_demo_offset()
    }

@router.get("/heatmap")
def get_complaint_heatmap(
    officer: Officer = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    """Returns coordinates and severity intensity of open/active complaints for map visualization."""
    open_tickets = (
        db.query(Ticket)
        .filter(Ticket.status.in_(["open", "assigned", "in_progress", "reopened"]))
        .all()
    )
    points = []
    for t in open_tickets:
        points.append({
            "lat": t.lat,
            "lng": t.lng,
            "intensity": round(t.severity / 5.0, 2),
            "category": t.category,
            "code": t.code,
            "ward_id": t.ward_id,
            "priority_score": t.priority_score
        })
    return points

@router.get("/workload")
def get_officer_workload(
    officer: Officer = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    officers = db.query(Officer).all()
    workload = []
    for o in officers:
        assigned = db.query(Ticket).filter(Ticket.assigned_officer_id == o.id).all()
        open_count = sum(1 for t in assigned if t.status.value in ["assigned", "in_progress", "reopened"])
        resolved_count = sum(1 for t in assigned if t.status.value in ["resolved_pending_verification", "verified_closed", "unverified_closed"])
        workload.append({
            "officer_id": o.id,
            "name": o.name,
            "role": o.role.value,
            "department": o.department.name,
            "assigned_open": open_count,
            "resolved": resolved_count
        })
    return workload

@router.post("/broadcasts")
def send_ward_broadcast(
    req: CreateBroadcastRequest,
    officer: Officer = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    """
    Sends proactive advisory to citizens of a ward (e.g. water supply disruption, road repair drive).
    Records sent & delivered statistics.
    """
    citizens_query = db.query(Citizen).filter(Citizen.subscribed == True)
    if req.ward_id:
        citizens_query = citizens_query.filter(Citizen.ward_id == req.ward_id)
    citizens = citizens_query.all()

    delivered = 0
    broadcast_text = f"📢 *{req.title}*\n\n{req.body}\n\n— Jammu Municipal Corporation (JMC)"
    for c in citizens:
        adapter = get_channel_adapter(c.channel)
        if adapter.send_text(c.channel_user_id, broadcast_text):
            delivered += 1

    bc = Broadcast(
        ward_id=req.ward_id,
        kind=req.kind,
        title=req.title,
        body=req.body,
        created_by=officer.name,
        sent_at=clock.now(),
        recipients=len(citizens),
        delivered=delivered
    )
    db.add(bc)
    db.commit()
    db.refresh(bc)

    return {
        "status": "ok",
        "broadcast_id": bc.id,
        "recipients": len(citizens),
        "delivered": delivered
    }

@router.post("/projects")
def create_mohalla_project(
    req: CreateProjectRequest,
    officer: Officer = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    project = Project(
        ward_id=req.ward_id,
        title=req.title,
        description=req.description,
        est_cost=req.est_cost,
        status=ProjectStatus.VOTING,
        cycle=req.cycle
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"status": "ok", "project_id": project.id, "title": project.title}

@router.post("/digest/run")
def trigger_monthly_digest(
    ward_id: Optional[int] = None,
    officer: Officer = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    """
    Runs the honest 'You Said, We Did' monthly digest generator:
    Computes complaints received, verified-resolved, reopened, top 3 wins, top 3 pending.
    """
    target_wards = [db.query(Ward).get(ward_id)] if ward_id else db.query(Ward).all()
    digest_reports = []

    for w in target_wards:
        total_rec = db.query(Ticket).filter(Ticket.ward_id == w.id).count()
        verified = db.query(Ticket).filter(Ticket.ward_id == w.id, Ticket.status == "verified_closed").count()
        reopened = db.query(Ticket).filter(Ticket.ward_id == w.id, Ticket.status == "reopened").count()

        top_wins = (
            db.query(Ticket)
            .filter(Ticket.ward_id == w.id, Ticket.status == "verified_closed")
            .order_by(Ticket.closed_at.desc())
            .limit(3)
            .all()
        )
        top_pending = (
            db.query(Ticket)
            .filter(Ticket.ward_id == w.id, Ticket.status.in_(["open", "in_progress", "reopened"]))
            .order_by(Ticket.priority_score.desc())
            .limit(3)
            .all()
        )

        digest_reports.append({
            "ward_id": w.id,
            "ward_name": w.name,
            "complaints_received": total_rec,
            "verified_resolved": verified,
            "reopened": reopened,
            "top_wins": [t.code for t in top_wins],
            "top_pending": [t.code for t in top_pending]
        })

    return {"status": "ok", "digest": digest_reports}
