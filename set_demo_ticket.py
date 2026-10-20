"""
Set BH-0001 to resolved_pending_verification for demo.
Uses the proper append_ticket_event so audit chain stays valid.
"""
import sys
sys.path.insert(0, ".")

from backend.app.db import SessionLocal
from backend.app.models import Ticket, TicketStatus
from backend.app.services.audit import append_ticket_event
from backend.app import clock

db = SessionLocal()

ticket = db.query(Ticket).filter(Ticket.code == "BH-0001").first()
if not ticket:
    print("Not found!")
    db.close()
    sys.exit(1)

ticket.status = TicketStatus.RESOLVED_PENDING_VERIFICATION
ticket.after_photo_url = "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80"
db.flush()

append_ticket_event(
    db,
    ticket_id=ticket.id,
    event_type="resolved_pending_verification",
    actor_type="officer",
    actor_id="1",
    payload={"message": "Repair completed, after-photo submitted", "channel": "officer_portal"},
    timestamp=clock.now()
)

db.commit()
print(f"Done! BH-0001 -> {ticket.status.value}")
print("Visit: http://localhost:3000/t/BH-0001")
db.close()
