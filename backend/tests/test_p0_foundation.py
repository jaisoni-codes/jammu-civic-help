import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import SessionLocal
from backend.app.models import Ward, Department, Officer, Ticket, POI
from backend.app import clock

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["project"] == "Bharosa Jammu"
    assert "clock_now" in data

def test_seed_data_counts():
    db = SessionLocal()
    try:
        assert db.query(Ward).count() == 10
        assert db.query(Department).count() == 8
        assert db.query(Officer).count() == 12
        assert db.query(POI).count() >= 15
        assert db.query(Ticket).count() == 300
    finally:
        db.close()

def test_clock_offset():
    initial = clock.get_demo_offset()
    clock.advance_demo_offset(5.0)
    assert clock.get_demo_offset() == initial + 5.0
    clock.reset_clock()
    assert clock.get_demo_offset() == 0.0
