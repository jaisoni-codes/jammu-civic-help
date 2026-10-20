import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models import TicketEvent
from backend.app import clock

def canonical_json(data: Any) -> str:
    """Produces a deterministic JSON string with sorted keys and no whitespace."""
    return json.dumps(data, sort_keys=True, separators=(',', ':'))

def calculate_event_hash(prev_hash: str, ticket_id: int, event_type: str, payload: Dict[str, Any], created_at_iso: str) -> str:
    payload_str = canonical_json(payload)
    to_hash = f"{prev_hash}{ticket_id}{event_type}{payload_str}{created_at_iso}"
    return hashlib.sha256(to_hash.encode("utf-8")).hexdigest()

def append_ticket_event(
    db: Session,
    ticket_id: int,
    event_type: str,
    actor_type: str,
    actor_id: str,
    payload: Dict[str, Any],
    timestamp: datetime = None
) -> TicketEvent:
    """
    Appends an immutable event to the ticket's hash chain.
    First event uses prev_hash = 'GENESIS'.
    """
    if timestamp is None:
        timestamp = clock.now()

    # Find the latest event for this ticket
    last_event = (
        db.query(TicketEvent)
        .filter(TicketEvent.ticket_id == ticket_id)
        .order_by(TicketEvent.id.desc())
        .first()
    )

    prev_hash = last_event.hash if last_event else "GENESIS"
    created_at_iso = timestamp.isoformat()
    current_hash = calculate_event_hash(prev_hash, ticket_id, event_type, payload, created_at_iso)

    event = TicketEvent(
        ticket_id=ticket_id,
        type=event_type,
        actor_type=actor_type,
        actor_id=str(actor_id),
        payload=payload,
        prev_hash=prev_hash,
        hash=current_hash,
        created_at=timestamp
    )
    db.add(event)
    db.flush()
    return event

def verify_ticket_chain(db: Session, ticket_id: int) -> Tuple[bool, int, str]:
    """
    Verifies the cryptographic SHA-256 chain for a given ticket.
    Returns (is_valid, events_count, reason).
    """
    events = (
        db.query(TicketEvent)
        .filter(TicketEvent.ticket_id == ticket_id)
        .order_by(TicketEvent.id.asc())
        .all()
    )

    if not events:
        return True, 0, "No events logged"

    expected_prev = "GENESIS"
    for idx, ev in enumerate(events):
        if ev.prev_hash != expected_prev:
            return False, idx, f"Broken chain link at event #{ev.id}: prev_hash mismatch"

        created_at_dt = ev.created_at
        created_at_iso = created_at_dt.isoformat() if isinstance(created_at_dt, datetime) else str(created_at_dt)
        computed_hash = calculate_event_hash(ev.prev_hash, ev.ticket_id, ev.type, ev.payload or {}, created_at_iso)
        
        if ev.hash != computed_hash:
            return False, idx, f"Tampered hash detected at event #{ev.id}"

        expected_prev = ev.hash

    return True, len(events), "Audit chain cryptographically intact"
