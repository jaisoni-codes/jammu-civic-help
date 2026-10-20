from typing import Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.models import Ward, Department, Officer, OfficerRole
from backend.app.db import haversine_distance_m
from backend.app.business_rules import CATEGORIES_CONFIG

def find_nearest_ward(db: Session, lat: float, lng: float) -> Ward:
    """Finds ward with closest centroid to given coordinates."""
    wards = db.query(Ward).all()
    if not wards:
        raise ValueError("No wards configured in database")

    closest = None
    min_dist = float("inf")
    for w in wards:
        dist = haversine_distance_m(lat, lng, w.centroid_lat, w.centroid_lng)
        if dist < min_dist:
            min_dist = dist
            closest = w
    return closest

def route_ticket(db: Session, category: str, ward_id: int) -> Tuple[Department, Optional[Officer]]:
    """
    Finds department responsible for category and assigns appropriate officer
    in that ward and department.
    """
    cat_cfg = CATEGORIES_CONFIG.get(category, CATEGORIES_CONFIG["other"])
    dept_code = cat_cfg["department_code"]

    dept = db.query(Department).filter(Department.code == dept_code).first()
    if not dept:
        dept = db.query(Department).filter(Department.code == "JMC_GENERAL").first()

    # Find Junior Engineer or officer assigned to this department and ward
    officers = db.query(Officer).filter(Officer.department_id == dept.id).all()
    assigned_officer = None
    
    # Priority: JE whose ward_ids contains this ward
    for off in officers:
        if off.ward_ids and ward_id in off.ward_ids and off.role == OfficerRole.JE:
            assigned_officer = off
            break

    # Fallback to any officer in this department
    if not assigned_officer and officers:
        assigned_officer = officers[0]

    return dept, assigned_officer
