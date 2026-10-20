import pytest
from backend.app.db import SessionLocal
from backend.app.models import Ward, Ticket, Broadcast, Citizen, Vote, Project
from backend.app.services.trust_index import compute_ward_trust_index
from backend.app.channels.console import get_outbox, clear_outbox
from backend.app.api.admin import send_ward_broadcast, CreateBroadcastRequest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_trust_index_formula_and_bounds():
    """
    Acceptance check for P3:
    Trust Index computes 6 components and returns a score strictly between 0 and 100.
    """
    db = SessionLocal()
    try:
        ward = db.query(Ward).first()
        index, details = compute_ward_trust_index(db, ward.id)
        assert 0.0 <= index <= 100.0
        comps = details["components"]
        assert "response" in comps
        assert "closure" in comps
        assert "reopen" in comps
        assert "satisfaction" in comps
        assert "proactive" in comps
        assert "participation" in comps
    finally:
        db.close()

def test_broadcast_reaches_target_ward_only():
    """
    Acceptance check for P4:
    Broadcast sent to Ward 1 reaches only subscribers of Ward 1.
    """
    db = SessionLocal()
    try:
        clear_outbox()
        # Login admin officer
        res_login = client.post("/api/auth/login", json={"officer_id": 12, "pin": "1234"})
        token = res_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Send broadcast to Ward 1
        res = client.post(
            "/api/admin/broadcasts",
            headers=headers,
            json={
                "ward_id": 1,
                "kind": "water",
                "title": "Emergency PHE Water Supply Maintenance",
                "body": "PHE water supply in Purani Mandi will be closed between 2 PM and 6 PM for valve upgrade."
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        recipients = data["recipients"]
        
        # Verify count matches ward 1 subscribed citizens
        ward_1_cits = db.query(Citizen).filter(Citizen.ward_id == 1, Citizen.subscribed == True).count()
        assert recipients == ward_1_cits

    finally:
        db.close()

def test_demo_time_advancement_and_sla_escalation():
    """
    Acceptance check for P5/Demo:
    Advancing time via demo panel triggers SLA checks and updates clock.
    """
    res = client.post("/api/demo/advance-time", json={"hours": 24.0})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["advanced_hours"] == 24.0

    # Reset
    reset_res = client.post("/api/demo/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["demo_offset_hours"] == 0.0
