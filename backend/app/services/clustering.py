import math
from typing import List, Optional
from datetime import timedelta
from sqlalchemy.orm import Session
from backend.app.models import Ticket, TicketStatus
from backend.app.db import haversine_distance_m
from backend.app import clock

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)

def find_duplicate_ticket(
    db: Session,
    category: str,
    lat: float,
    lng: float,
    embedding: Optional[List[float]] = None
) -> Optional[Ticket]:
    """
    Duplicate Clustering Specification:
    A new report joins an existing OPEN ticket if:
      1. Same category
      2. Within 60 m (Haversine/PostGIS ST_DWithin)
      3. Created within 14 days
      4. (embedding cosine similarity >= 0.80 OR text/embedding is missing)
    """
    now_dt = clock.now()
    fourteen_days_ago = now_dt - timedelta(days=14)

    # Candidates: same category, created in last 14 days, still open/in-progress
    open_statuses = [
        TicketStatus.OPEN,
        TicketStatus.ASSIGNED,
        TicketStatus.IN_PROGRESS,
        TicketStatus.REOPENED
    ]

    candidates = (
        db.query(Ticket)
        .filter(
            Ticket.category == category,
            Ticket.status.in_(open_statuses),
            Ticket.created_at >= fourteen_days_ago
        )
        .all()
    )

    for cand in candidates:
        dist_m = haversine_distance_m(lat, lng, cand.lat, cand.lng)
        if dist_m <= 60.0:
            if not embedding or not cand.embedding:
                # Text or embedding missing: cluster on geo + category
                return cand
            sim = cosine_similarity(embedding, cand.embedding)
            if sim >= 0.80:
                return cand

    return None
