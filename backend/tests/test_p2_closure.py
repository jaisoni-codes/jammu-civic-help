import io
from PIL import Image
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import SessionLocal
from backend.app.models import Ticket, Officer, TicketStatus, TicketEvent
from backend.app.services.closure import process_resolution
from backend.app.services.intake import process_citizen_intake
from backend.app.services.audit import verify_ticket_chain
from backend.app.services.sla import check_sla_and_escalations
from backend.app import clock

client = TestClient(app)

def create_dummy_image_bytes(pattern_id: int = 1) -> bytes:
    from PIL import ImageDraw
    img = Image.new("RGB", (200, 200), color="white")
    d = ImageDraw.Draw(img)
    # Draw geometric patterns dependent on pattern_id
    d.rectangle([10 * pattern_id, 20, 80 + pattern_id * 5, 90], fill="blue")
    d.ellipse([50, 40 + pattern_id * 10, 150, 140], fill="red")
    d.line([(0, 0), (200, 200)], fill="black", width=pattern_id * 2)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_officer_login_and_auth():
    """Verify PIN login and JWT generation for seeded officers."""
    res = client.post("/api/auth/login", json={"officer_id": 1, "pin": "1234"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["officer"]["id"] == 1
    assert data["officer"]["name"] == "Rajesh Sharma"

def test_verified_closure_flow_and_reopen_escalation():
    """
    Acceptance check for P2:
    Resolve with photo & GPS -> Citizen taps NOT SOLVED -> Reopen and escalation +1.
    """
    db = SessionLocal()
    try:
        import uuid
        test_code = f"BH-P2-{uuid.uuid4().hex[:6].upper()}"
        t = Ticket(
            code=test_code,
            category="road_pothole",
            department_id=1,
            ward_id=1,
            lat=32.7285,
            lng=74.8631,
            status=TicketStatus.IN_PROGRESS,
            severity=4,
            priority_score=60.0,
            escalation_level=0,
            reopen_count=0,
            created_at=clock.now()
        )
        db.add(t)
        db.commit()
        db.refresh(t)

        officer = db.query(Officer).first()
        photo_bytes = create_dummy_image_bytes(pattern_id=1)

        # 1. Resolve ticket within 15 meters
        success, msg, res_obj = process_resolution(
            db=db,
            ticket=t,
            officer_id=officer.id,
            after_photo_bytes=photo_bytes,
            after_photo_url="https://images.unsplash.com/photo-test-blue.jpg",
            officer_lat=32.7286,  # ~11 meters away
            officer_lng=74.8631
        )
        assert success is True
        assert t.status == TicketStatus.RESOLVED_PENDING_VERIFICATION

        # 2. Citizen taps NOT SOLVED
        intake_res = process_citizen_intake(
            db=db,
            channel="console",
            channel_user_id="cit_verify_test",
            button_reply_id=f"verify_no_{t.code}"
        )
        assert intake_res["action"] == "reopened"
        assert intake_res["escalation_level"] == 1

        db.refresh(t)
        assert t.status == TicketStatus.REOPENED
        assert t.reopen_count == 1
        assert t.escalation_level == 1

    finally:
        db.close()

def test_reused_photo_perceptual_hash_rejected():
    """
    Acceptance check for P2:
    Reject exact or near-identical reuse of photos (perceptual hash distance < 6).
    """
    db = SessionLocal()
    try:
        t = db.query(Ticket).filter(Ticket.status == TicketStatus.IN_PROGRESS).first()
        officer = db.query(Officer).first()

        # Use exactly identical dummy image bytes with distinct pattern
        photo_bytes = create_dummy_image_bytes(pattern_id=5)

        # First resolution succeeds
        success1, msg1, res1 = process_resolution(
            db=db,
            ticket=t,
            officer_id=officer.id,
            after_photo_bytes=photo_bytes,
            after_photo_url="https://images.unsplash.com/photo-green-1.jpg",
            officer_lat=t.lat,
            officer_lng=t.lng
        )
        assert success1 is True

        # Second attempt with same identical photo on another ticket must fail
        t2 = db.query(Ticket).filter(Ticket.id != t.id).first()
        success2, msg2, res2 = process_resolution(
            db=db,
            ticket=t2,
            officer_id=officer.id,
            after_photo_bytes=photo_bytes,
            after_photo_url="https://images.unsplash.com/photo-green-2.jpg",
            officer_lat=t2.lat,
            officer_lng=t2.lng
        )
        assert success2 is False
        assert "Duplicate photo rejected" in msg2

    finally:
        db.close()

def test_audit_chain_tamper_detection():
    """
    Acceptance check for P2:
    Altering an event payload or hash invalidates the chain.
    """
    db = SessionLocal()
    try:
        t = db.query(Ticket).first()
        valid_before, _, _ = verify_ticket_chain(db, t.id)
        assert valid_before is True

        # Tamper an event in db
        ev = db.query(TicketEvent).filter(TicketEvent.ticket_id == t.id).first()
        ev.hash = "0000000000000000000000000000000000000000000000000000000000000000"
        db.commit()

        # Check verification fails
        valid_after, idx, reason = verify_ticket_chain(db, t.id)
        assert valid_after is False
        assert "Tampered hash detected" in reason

    finally:
        db.close()
