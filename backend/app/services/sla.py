from datetime import timedelta
from sqlalchemy.orm import Session
from backend.app.models import Ticket, TicketEvent, TicketStatus, Officer, OfficerRole
from backend.app.services.audit import append_ticket_event
from backend.app.channels import get_channel_adapter
from backend.app import clock

def check_sla_and_escalations(db: Session):
    """
    SLA and Escalation Specification:
    - 100% of SLA with no resolution -> escalation_level 1 (notify EE).
    - 150% of SLA -> level 2 (notify Commissioner).
    - Every change writes a ticket_event and notifies reporting citizens.
    """
    now_dt = clock.now()
    active_tickets = (
        db.query(Ticket)
        .filter(Ticket.status.in_([TicketStatus.OPEN, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS, TicketStatus.REOPENED]))
        .all()
    )

    for t in active_tickets:
        if not t.sla_due_at or not t.created_at:
            continue

        total_sla_seconds = (t.sla_due_at - t.created_at).total_seconds()
        elapsed_seconds = (now_dt - t.created_at).total_seconds()

        if total_sla_seconds <= 0:
            continue

        ratio = elapsed_seconds / total_sla_seconds

        # Escalation level 2 check (150% of SLA)
        if ratio >= 1.50 and t.escalation_level < 2:
            t.escalation_level = 2
            append_ticket_event(
                db,
                ticket_id=t.id,
                event_type="escalated_level_2",
                actor_type="system",
                actor_id="sla_engine",
                payload={"ratio": round(ratio, 2), "notified": "commissioner"},
                timestamp=now_dt
            )
            # Notify citizens
            for r in t.reports:
                if r.citizen:
                    get_channel_adapter(r.citizen.channel).send_text(
                        r.citizen.channel_user_id,
                        f"🚨 *Update for Ticket {t.code}:* Resolution exceeded 150% of SLA. Escalated directly to Municipal Commissioner for expedited action."
                    )

        # Escalation level 1 check (100% of SLA)
        elif ratio >= 1.0 and t.escalation_level < 1:
            t.escalation_level = 1
            append_ticket_event(
                db,
                ticket_id=t.id,
                event_type="escalated_level_1",
                actor_type="system",
                actor_id="sla_engine",
                payload={"ratio": round(ratio, 2), "notified": "executive_engineer"},
                timestamp=now_dt
            )
            # Notify citizens
            for r in t.reports:
                if r.citizen:
                    get_channel_adapter(r.citizen.channel).send_text(
                        r.citizen.channel_user_id,
                        f"⚠️ *Update for Ticket {t.code}:* SLA deadline reached without resolution. Escalated to Executive Engineer."
                    )

    db.commit()

def check_auto_close_72h(db: Session):
    """
    72h Auto-Close Specification:
    If a ticket is in resolved_pending_verification for >= 72h without citizen response,
    mark as unverified_closed (counts at 0.5 weight in Trust Index).
    """
    now_dt = clock.now()
    threshold = now_dt - timedelta(hours=72)

    pending_tickets = (
        db.query(Ticket)
        .filter(
            Ticket.status == TicketStatus.RESOLVED_PENDING_VERIFICATION,
            Ticket.resolved_at <= threshold
        )
        .all()
    )

    for t in pending_tickets:
        t.status = TicketStatus.UNVERIFIED_CLOSED
        t.closed_at = now_dt
        append_ticket_event(
            db,
            ticket_id=t.id,
            event_type="unverified_closed",
            actor_type="system",
            actor_id="auto_close_job",
            payload={"reason": "72h silence without citizen confirmation"},
            timestamp=now_dt
        )
        # Notify citizens
        for r in t.reports:
            if r.citizen:
                get_channel_adapter(r.citizen.channel).send_text(
                    r.citizen.channel_user_id,
                    f"Ticket {t.code} automatically closed (unverified) after 72 hours of inactivity."
                )

    db.commit()
