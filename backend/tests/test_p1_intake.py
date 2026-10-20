import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import SessionLocal
from backend.app.models import Ticket, Report, Citizen
from backend.app.services.intake import process_citizen_intake

client = TestClient(app)

def test_clustering_three_nearby_reports():
    """
    Acceptance check for P1:
    Tests prove 3 nearby reports -> 1 ticket with affected_count = 3.
    """
    db = SessionLocal()
    try:
        # Pothole at coordinates isolated from seed
        lat = 32.7885
        lng = 74.8931

        # Citizen 1 reports pothole
        res1 = process_citizen_intake(
            db=db,
            channel="console",
            channel_user_id="citizen_p1_01",
            text="Big pothole on the main market road, please repair.",
            lat=lat,
            lng=lng
        )
        # Citizen 1 confirms
        res1_confirm = process_citizen_intake(
            db=db,
            channel="console",
            channel_user_id="citizen_p1_01",
            button_reply_id="confirm_yes"
        )
        assert res1_confirm["action"] == "confirmed"
        assert res1_confirm["is_new"] is True
        ticket_code = res1_confirm["ticket_code"]

        ticket = db.query(Ticket).filter(Ticket.code == ticket_code).first()
        assert ticket is not None
        assert ticket.affected_count == 1
        assert ticket.category == "road_pothole"

        # Citizen 2 reports same pothole 20 meters away (approx 0.00018 deg lat)
        lat2 = lat + 0.00015
        lng2 = lng + 0.00010
        process_citizen_intake(
            db=db,
            channel="console",
            channel_user_id="citizen_p1_02",
            text="Deep pothole right here on road, danger to scooters.",
            lat=lat2,
            lng=lng2
        )
        res2_confirm = process_citizen_intake(
            db=db,
            channel="console",
            channel_user_id="citizen_p1_02",
            button_reply_id="confirm_yes"
        )
        assert res2_confirm["action"] == "confirmed"
        assert res2_confirm["is_new"] is False
        assert res2_confirm["ticket_code"] == ticket_code

        # Citizen 3 reports same pothole 35 meters away
        lat3 = lat - 0.00020
        lng3 = lng + 0.00005
        process_citizen_intake(
            db=db,
            channel="console",
            channel_user_id="citizen_p1_03",
            text="Gaddhe se accident ho sakta hai road par.",
            lat=lat3,
            lng=lng3
        )
        res3_confirm = process_citizen_intake(
            db=db,
            channel="console",
            channel_user_id="citizen_p1_03",
            button_reply_id="confirm_yes"
        )
        assert res3_confirm["action"] == "confirmed"
        assert res3_confirm["is_new"] is False
        assert res3_confirm["ticket_code"] == ticket_code

        # Re-query ticket from db
        db.refresh(ticket)
        assert ticket.affected_count == 3
        # Check attached reports
        reports = db.query(Report).filter(Report.ticket_id == ticket.id).all()
        assert len(reports) == 3

    finally:
        db.close()

def test_different_category_does_not_merge():
    """
    Acceptance check for P1:
    Reports at same location but different category create separate tickets.
    """
    db = SessionLocal()
    try:
        lat = 32.7410
        lng = 74.8390

        # Streetlight report
        process_citizen_intake(
            db=db,
            channel="console",
            channel_user_id="cit_cat_test_1",
            text="Streetlight broken and dark on the pole.",
            lat=lat,
            lng=lng
        )
        res1 = process_citizen_intake(
            db=db,
            channel="console",
            channel_user_id="cit_cat_test_1",
            button_reply_id="confirm_yes"
        )
        t1_code = res1["ticket_code"]

        # Garbage report at exact same spot
        process_citizen_intake(
            db=db,
            channel="console",
            channel_user_id="cit_cat_test_2",
            text="Garbage dump overflowing with flies.",
            lat=lat,
            lng=lng
        )
        res2 = process_citizen_intake(
            db=db,
            channel="console",
            channel_user_id="cit_cat_test_2",
            button_reply_id="confirm_yes"
        )
        t2_code = res2["ticket_code"]

        assert t1_code != t2_code
        t1 = db.query(Ticket).filter(Ticket.code == t1_code).first()
        t2 = db.query(Ticket).filter(Ticket.code == t2_code).first()
        assert t1.category == "streetlight"
        assert t2.category == "garbage"
        assert t1.id != t2.id

    finally:
        db.close()

def test_public_ticket_api():
    """Verify public ticket endpoint returns timeline and transparent priority rank."""
    db = SessionLocal()
    try:
        t = db.query(Ticket).first()
        res = client.get(f"/api/public/tickets/{t.code}")
        assert res.status_code == 200
        data = res.json()
        assert data["code"] == t.code
        assert "ward_rank" in data
        assert "priority_reason" in data
        assert "audit_chain" in data
        assert data["audit_chain"]["is_valid"] is True
    finally:
        db.close()
