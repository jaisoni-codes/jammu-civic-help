import enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, 
    Text, Enum, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from backend.app.db import Base
from backend.app import clock

class OfficerRole(str, enum.Enum):
    JE = "je"
    EE = "ee"
    COMMISSIONER = "commissioner"
    ADMIN = "admin"

class TicketStatus(str, enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED_PENDING_VERIFICATION = "resolved_pending_verification"
    VERIFIED_CLOSED = "verified_closed"
    UNVERIFIED_CLOSED = "unverified_closed"
    REOPENED = "reopened"

class VerificationResult(str, enum.Enum):
    SOLVED = "solved"
    NOT_SOLVED = "not_solved"
    NO_RESPONSE = "no_response"

class BroadcastKind(str, enum.Enum):
    WATER = "water"
    POWER = "power"
    ROAD = "road"
    DRIVE = "drive"
    GENERAL = "general"

class ProjectStatus(str, enum.Enum):
    VOTING = "voting"
    FUNDED = "funded"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"

class POIType(str, enum.Enum):
    HOSPITAL = "hospital"
    SCHOOL = "school"
    ELDERLY_HOME = "elderly_home"

# --- Models ---

class Ward(Base):
    __tablename__ = "wards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    centroid_lat = Column(Float, nullable=False)
    centroid_lng = Column(Float, nullable=False)
    population_est = Column(Integer, default=20000)

    tickets = relationship("Ticket", back_populates="ward")
    projects = relationship("Project", back_populates="ward")
    trust_snapshots = relationship("TrustSnapshot", back_populates="ward")

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)

    officers = relationship("Officer", back_populates="department")
    tickets = relationship("Ticket", back_populates="department")

class Officer(Base):
    __tablename__ = "officers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    role = Column(Enum(OfficerRole), default=OfficerRole.JE, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    ward_ids = Column(JSON, default=list)  # list of int ward ids
    pin_hash = Column(String(255), nullable=False)

    department = relationship("Department", back_populates="officers")
    assigned_tickets = relationship("Ticket", back_populates="assigned_officer")

class Citizen(Base):
    __tablename__ = "citizens"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String(20), default="console")  # console, telegram, whatsapp
    channel_user_id = Column(String(100), unique=True, nullable=False, index=True)
    lang = Column(String(10), default="en")  # hi, en
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)
    subscribed = Column(Boolean, default=True)
    senior_opt_in = Column(Boolean, default=False)
    created_at = Column(DateTime, default=clock.now)

    reports = relationship("Report", back_populates="citizen")
    verifications = relationship("Verification", back_populates="citizen")
    pulse_responses = relationship("PulseResponse", back_populates="citizen")
    votes = relationship("Vote", back_populates="citizen")

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)  # e.g. "BH-0001"
    category = Column(String(50), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False, index=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    address_text = Column(String(255), nullable=True)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN, nullable=False, index=True)
    severity = Column(Integer, default=3)  # 1-5
    safety_flag = Column(Float, default=0.0)  # 0, 0.5, 1.0
    affected_count = Column(Integer, default=1)
    priority_score = Column(Float, default=0.0, index=True)
    priority_reason = Column(JSON, default=list)  # list of str reasons
    sla_due_at = Column(DateTime, nullable=True)
    escalation_level = Column(Integer, default=0)  # 0, 1, 2
    assigned_officer_id = Column(Integer, ForeignKey("officers.id"), nullable=True)
    embedding = Column(JSON, nullable=True)  # list of float
    reopen_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=clock.now)
    first_response_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    is_synthetic = Column(Boolean, default=False)

    department = relationship("Department", back_populates="tickets")
    ward = relationship("Ward", back_populates="tickets")
    assigned_officer = relationship("Officer", back_populates="assigned_tickets")
    reports = relationship("Report", back_populates="ticket", cascade="all, delete-orphan")
    events = relationship("TicketEvent", back_populates="ticket", cascade="all, delete-orphan")
    resolutions = relationship("Resolution", back_populates="ticket", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="ticket", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tickets_ward_status", "ward_id", "status"),
    )

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    citizen_id = Column(Integer, ForeignKey("citizens.id"), nullable=False)
    text = Column(Text, nullable=True)
    media_url = Column(String(255), nullable=True)
    audio_url = Column(String(255), nullable=True)
    transcript = Column(Text, nullable=True)
    lang = Column(String(10), default="en")
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    created_at = Column(DateTime, default=clock.now)

    ticket = relationship("Ticket", back_populates="reports")
    citizen = relationship("Citizen", back_populates="reports")

class TicketEvent(Base):
    """
    Append-only audit chain.
    hash = sha256(prev_hash + ticket_id + type + canonical_json(payload) + created_at_iso)
    First event prev_hash = 'GENESIS'
    """
    __tablename__ = "ticket_events"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # created, assigned, status_changed, escalated, verified, reopened
    actor_type = Column(String(20), nullable=False)  # system, citizen, officer, admin
    actor_id = Column(String(50), nullable=True)
    payload = Column(JSON, default=dict)
    prev_hash = Column(String(64), nullable=False)
    hash = Column(String(64), nullable=False, unique=True)
    created_at = Column(DateTime, default=clock.now)

    ticket = relationship("Ticket", back_populates="events")

class Resolution(Base):
    __tablename__ = "resolutions"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    officer_id = Column(Integer, ForeignKey("officers.id"), nullable=False)
    after_photo_url = Column(String(255), nullable=False)
    officer_lat = Column(Float, nullable=False)
    officer_lng = Column(Float, nullable=False)
    distance_m = Column(Float, nullable=False)
    phash_distance = Column(Float, nullable=True)
    ai_check = Column(JSON, default=dict)
    needs_review = Column(Boolean, default=False)
    created_at = Column(DateTime, default=clock.now)

    ticket = relationship("Ticket", back_populates="resolutions")

class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    citizen_id = Column(Integer, ForeignKey("citizens.id"), nullable=False)
    result = Column(Enum(VerificationResult), nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5
    created_at = Column(DateTime, default=clock.now)

    ticket = relationship("Ticket", back_populates="verifications")
    citizen = relationship("Citizen", back_populates="verifications")

class Broadcast(Base):
    __tablename__ = "broadcasts"

    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)  # null = city-wide
    kind = Column(Enum(BroadcastKind), default=BroadcastKind.GENERAL, nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    created_by = Column(String(100), default="admin")
    sent_at = Column(DateTime, default=clock.now)
    recipients = Column(Integer, default=0)
    delivered = Column(Integer, default=0)

class PulseResponse(Base):
    __tablename__ = "pulse_responses"

    id = Column(Integer, primary_key=True, index=True)
    citizen_id = Column(Integer, ForeignKey("citizens.id"), nullable=False)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False)
    score = Column(Integer, nullable=False)  # 1-5
    month = Column(String(7), nullable=False)  # "2026-10"

    citizen = relationship("Citizen", back_populates="pulse_responses")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    est_cost = Column(Float, default=100000.0)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.VOTING, nullable=False)
    cycle = Column(String(20), default="2026-Q4", nullable=False)

    ward = relationship("Ward", back_populates="projects")
    votes = relationship("Vote", back_populates="project")

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    citizen_id = Column(Integer, ForeignKey("citizens.id"), nullable=False)
    cycle = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=clock.now)

    project = relationship("Project", back_populates="votes")
    citizen = relationship("Citizen", back_populates="votes")

    __table_args__ = (
        UniqueConstraint("citizen_id", "cycle", name="uq_citizen_cycle_vote"),
    )

class TrustSnapshot(Base):
    __tablename__ = "trust_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    trust_index = Column(Float, nullable=False)
    components = Column(JSON, default=dict)

    ward = relationship("Ward", back_populates="trust_snapshots")

class POI(Base):
    __tablename__ = "pois"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(POIType), nullable=False)
    name = Column(String(150), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
