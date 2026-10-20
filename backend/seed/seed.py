import random
from datetime import datetime, timedelta, timezone
from backend.app.security import hash_pin
from backend.app.db import engine, SessionLocal, Base
from backend.app.models import (
    Ward, Department, Officer, Citizen, Ticket, Report, TicketEvent,
    Resolution, Verification, Broadcast, PulseResponse,
    Project, Vote, TrustSnapshot, POI, OfficerRole, TicketStatus,
    VerificationResult, BroadcastKind, ProjectStatus, POIType
)
from backend.app.business_rules import CATEGORIES_CONFIG
from backend.app.services.audit import append_ticket_event
from backend.app.services.priority import compute_priority_score
from backend.app import clock

# Jammu Center ~ 32.7266° N, 74.8570° E
JAMMU_WARDS = [
    {"name": "Ward 1 - Old Heritage City / Purani Mandi", "lat": 32.7285, "lng": 74.8631, "pop": 24000},
    {"name": "Ward 7 - Raghunath Bazaar", "lat": 32.7252, "lng": 74.8605, "pop": 22000},
    {"name": "Ward 12 - Gandhi Nagar South", "lat": 32.7056, "lng": 74.8622, "pop": 28000},
    {"name": "Ward 18 - Shastri Nagar", "lat": 32.7001, "lng": 74.8580, "pop": 26000},
    {"name": "Ward 21 - Talab Tillo Central", "lat": 32.7230, "lng": 74.8250, "pop": 31000},
    {"name": "Ward 24 - Bakshi Nagar", "lat": 32.7410, "lng": 74.8390, "pop": 29000},
    {"name": "Ward 30 - Janipur Main", "lat": 32.7560, "lng": 74.8460, "pop": 35000},
    {"name": "Ward 38 - Trikuta Nagar", "lat": 32.6950, "lng": 74.8780, "pop": 32000},
    {"name": "Ward 43 - Channi Himmat", "lat": 32.6840, "lng": 74.8920, "pop": 34000},
    {"name": "Ward 50 - Bahu Fort & Gujjar Nagar", "lat": 32.7180, "lng": 74.8750, "pop": 27000},
]

DEPARTMENTS = [
    {"code": "JMC_ROADS", "name": "JMC Roads & Infrastructure"},
    {"code": "JMC_ELECTRICAL", "name": "JMC Electrical & Lighting"},
    {"code": "JMC_SANITATION", "name": "JMC Sanitation & Waste Management"},
    {"code": "JMC_DRAINAGE", "name": "JMC Drainage & Stormwater"},
    {"code": "JAL_SHAKTI", "name": "Jal Shakti PHE Jammu"},
    {"code": "POWER_DEPT", "name": "Power Dept (JPDCL)"},
    {"code": "JMC_VET", "name": "JMC Veterinary & Animal Care"},
    {"code": "JMC_GENERAL", "name": "JMC General Civic Services"},
]

POIS = [
    (POIType.HOSPITAL, "Government Medical College (GMC) Jammu", 32.7420, 74.8400),
    (POIType.HOSPITAL, "SMGS Hospital Shalamar", 32.7290, 74.8640),
    (POIType.HOSPITAL, "Gandhi Nagar Govt Hospital", 32.7040, 74.8630),
    (POIType.HOSPITAL, "ASCOMS Hospital Sidhra", 32.7520, 74.9010),
    (POIType.SCHOOL, "Govt SPMR College of Commerce", 32.7220, 74.8550),
    (POIType.SCHOOL, "MAM College Jammu", 32.7120, 74.8590),
    (POIType.SCHOOL, "St. Mary's Convent School", 32.7010, 74.8610),
    (POIType.SCHOOL, "Presentation Convent Senior Secondary", 32.6980, 74.8670),
    (POIType.SCHOOL, "Delhi Public School Jammu", 32.7100, 74.8320),
    (POIType.SCHOOL, "Govt Girls High School Bazar Qasaban", 32.7270, 74.8610),
    (POIType.ELDERLY_HOME, "Jammu Senior Citizens Old Age Home Amphalla", 32.7450, 74.8550),
    (POIType.ELDERLY_HOME, "Red Cross Old Age Shelter Gandhi Nagar", 32.7030, 74.8650),
    (POIType.HOSPITAL, "Rotary Eye Hospital Udhampur Link", 32.7300, 74.8600),
    (POIType.SCHOOL, "KC Public School Paloura", 32.7480, 74.8290),
    (POIType.SCHOOL, "Kendriya Vidyalaya No. 1 Gandhi Nagar", 32.7090, 74.8680),
]

OFFICERS = [
    # JEs
    ("Rajesh Sharma", OfficerRole.JE, "JMC_ROADS", [1, 2, 3], "1234"),
    ("Sunil Verma", OfficerRole.JE, "JMC_ELECTRICAL", [1, 2, 3], "1234"),
    ("Pooja Rajput", OfficerRole.JE, "JMC_SANITATION", [1, 2, 3, 4], "1234"),
    ("Amit Choudhary", OfficerRole.JE, "JMC_DRAINAGE", [1, 2, 3, 4], "1234"),
    ("Vikas Gupta", OfficerRole.JE, "JAL_SHAKTI", [1, 2, 5, 6], "1234"),
    ("Rohit Manhas", OfficerRole.JE, "POWER_DEPT", [1, 2, 7, 8], "1234"),
    ("Neeraj Dogra", OfficerRole.JE, "JMC_VET", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "1234"),
    ("Sanjay Jamwal", OfficerRole.JE, "JMC_ROADS", [4, 5, 6, 7, 8, 9, 10], "1234"),
    # EEs
    ("Er. Kuldeep Kotwal", OfficerRole.EE, "JMC_ROADS", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "1234"),
    ("Er. Renu Sharma", OfficerRole.EE, "JMC_ELECTRICAL", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "1234"),
    # Commissioner & Admin
    ("Sh. Devinder Singh (IAS)", OfficerRole.COMMISSIONER, "JMC_GENERAL", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "1234"),
    ("Admin Control Room", OfficerRole.ADMIN, "JMC_GENERAL", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "1234"),
]

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    random.seed(42)

    try:
        print("[SEED] Checking existing records...")
        if db.query(Ward).count() > 0:
            print("[SEED] Database already contains wards. Clearing synthetic historical data for clean idempotency...")
            db.query(Vote).delete()
            db.query(Project).delete()
            db.query(TrustSnapshot).delete()
            db.query(PulseResponse).delete()
            db.query(Broadcast).delete()
            db.query(Verification).delete()
            db.query(Resolution).delete()
            db.query(TicketEvent).delete()
            db.query(Report).delete()
            db.query(Ticket).delete()
            db.query(Citizen).delete()
            db.query(Officer).delete()
            db.query(Department).delete()
            db.query(POI).delete()
            db.query(Ward).delete()
            db.commit()

        # 1. Wards
        print("[SEED] Creating 10 Jammu demo wards...")
        ward_objs = []
        for w in JAMMU_WARDS:
            ward = Ward(
                name=w["name"],
                centroid_lat=w["lat"],
                centroid_lng=w["lng"],
                population_est=w["pop"]
            )
            db.add(ward)
            ward_objs.append(ward)
        db.flush()

        # 2. Departments
        print("[SEED] Creating 8 civic departments...")
        dept_map = {}
        for d in DEPARTMENTS:
            dept = Department(code=d["code"], name=d["name"])
            db.add(dept)
            db.flush()
            dept_map[d["code"]] = dept

        # 3. POIs
        print("[SEED] Creating 15 vulnerability POIs (hospitals, schools, senior homes)...")
        for poi_type, name, lat, lng in POIS:
            poi = POI(type=poi_type, name=name, lat=lat, lng=lng)
            db.add(poi)
        db.flush()

        # 4. Officers
        print("[SEED] Creating 12 officers with role-based routing...")
        officer_objs = []
        for name, role, dept_code, w_ids, pin in OFFICERS:
            officer = Officer(
                name=name,
                role=role,
                department_id=dept_map[dept_code].id,
                ward_ids=w_ids,
                pin_hash=hash_pin(pin)
            )
            db.add(officer)
            officer_objs.append(officer)
        db.flush()

        # 5. Citizens
        print("[SEED] Creating 400 synthetic registered citizens...")
        citizen_objs = []
        for i in range(1, 401):
            w_idx = (i % 10) + 1
            citizen = Citizen(
                channel="console" if i <= 50 else ("whatsapp" if i % 2 == 0 else "telegram"),
                channel_user_id=f"cit_demo_{i:04d}",
                lang="hi" if i % 3 == 0 else "en",
                ward_id=w_idx,
                subscribed=True,
                senior_opt_in=(i % 15 == 0),
                created_at=clock.now() - timedelta(days=random.randint(20, 60))
            )
            db.add(citizen)
            citizen_objs.append(citizen)
        db.flush()

        # 6. Historical Synthetic Tickets (over 60 days)
        print("[SEED] Generating 300 realistic historical tickets with full audit chains...")
        categories = list(CATEGORIES_CONFIG.keys())
        ticket_counter = 1
        now_dt = clock.now()

        for i in range(1, 301):
            days_ago = random.uniform(0.5, 60.0)
            created_at = now_dt - timedelta(days=days_ago)
            cat = random.choice(categories)
            cfg = CATEGORIES_CONFIG[cat]
            dept = dept_map[cfg["department_code"]]
            ward = ward_objs[random.randint(0, 9)]

            # Jitter around ward centroid
            lat = ward.centroid_lat + random.uniform(-0.005, 0.005)
            lng = ward.centroid_lng + random.uniform(-0.005, 0.005)

            # Assign suitable officer
            suitable_officers = [o for o in officer_objs if o.department_id == dept.id and (not o.ward_ids or ward.id in o.ward_ids)]
            assigned_off = random.choice(suitable_officers) if suitable_officers else officer_objs[0]

            severity = random.randint(1, 5)
            safety_flag = random.choice([0.0, 0.0, 0.0, 0.5, 1.0])
            affected_count = 1 if random.random() > 0.25 else random.randint(2, 6)

            # Status distribution: older tickets mostly verified_closed, newer are open/assigned/in_progress
            if days_ago > 10:
                roll = random.random()
                if roll < 0.65:
                    status = TicketStatus.VERIFIED_CLOSED
                elif roll < 0.80:
                    status = TicketStatus.UNVERIFIED_CLOSED
                elif roll < 0.90:
                    status = TicketStatus.REOPENED
                else:
                    status = TicketStatus.IN_PROGRESS
            else:
                roll = random.random()
                if roll < 0.35:
                    status = TicketStatus.RESOLVED_PENDING_VERIFICATION
                elif roll < 0.65:
                    status = TicketStatus.IN_PROGRESS
                elif roll < 0.85:
                    status = TicketStatus.ASSIGNED
                else:
                    status = TicketStatus.OPEN

            sla_hours = cfg["sla_hours"]
            sla_due_at = created_at + timedelta(hours=sla_hours)
            first_response_at = created_at + timedelta(hours=random.uniform(1.0, 18.0))
            resolved_at = None
            closed_at = None
            reopen_count = 1 if status == TicketStatus.REOPENED else 0

            if status in [TicketStatus.RESOLVED_PENDING_VERIFICATION, TicketStatus.VERIFIED_CLOSED, TicketStatus.UNVERIFIED_CLOSED]:
                resolved_at = created_at + timedelta(hours=random.uniform(6.0, min(sla_hours * 1.2, days_ago * 24)))
                if status in [TicketStatus.VERIFIED_CLOSED, TicketStatus.UNVERIFIED_CLOSED]:
                    closed_at = resolved_at + timedelta(hours=random.uniform(2.0, 48.0))

            score, reasons = compute_priority_score(db, affected_count, severity, created_at, safety_flag, lat, lng)
            ticket_code = f"BH-{ticket_counter:04d}"
            ticket_counter += 1

            t = Ticket(
                code=ticket_code,
                category=cat,
                department_id=dept.id,
                ward_id=ward.id,
                lat=lat,
                lng=lng,
                address_text=f"Near Landmark, {ward.name}",
                status=status,
                severity=severity,
                safety_flag=safety_flag,
                affected_count=affected_count,
                priority_score=score,
                priority_reason=reasons,
                sla_due_at=sla_due_at,
                escalation_level=1 if (days_ago > 5 and status in [TicketStatus.OPEN, TicketStatus.REOPENED]) else 0,
                assigned_officer_id=assigned_off.id,
                reopen_count=reopen_count,
                created_at=created_at,
                first_response_at=first_response_at,
                resolved_at=resolved_at,
                closed_at=closed_at,
                is_synthetic=True
            )
            db.add(t)
            db.flush()

            # Reports
            cit = random.choice(citizen_objs)
            rep = Report(
                ticket_id=t.id,
                citizen_id=cit.id,
                text=f"Issue regarding {cfg['label']} spotted here.",
                media_url="https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?w=600",
                lat=lat,
                lng=lng,
                created_at=created_at
            )
            db.add(rep)

            # Audit Genesis
            append_ticket_event(db, t.id, "created", "citizen", str(cit.id), {"category": cat, "severity": severity}, created_at)
            append_ticket_event(db, t.id, "assigned", "system", "auto_router", {"officer_id": assigned_off.id}, created_at + timedelta(minutes=5))

            if resolved_at:
                res = Resolution(
                    ticket_id=t.id,
                    officer_id=assigned_off.id,
                    after_photo_url="https://images.unsplash.com/photo-1584467735871-8e85353a8413?w=600",
                    officer_lat=lat + random.uniform(-0.0001, 0.0001),
                    officer_lng=lng + random.uniform(-0.0001, 0.0001),
                    distance_m=round(random.uniform(10.0, 35.0), 1),
                    phash_distance=18.0,
                    ai_check={"same_place_likely": True, "issue_resolved_after": True, "confidence": 0.92},
                    needs_review=False,
                    created_at=resolved_at
                )
                db.add(res)
                append_ticket_event(db, t.id, "resolved", "officer", str(assigned_off.id), {"distance_m": res.distance_m}, resolved_at)

            if status == TicketStatus.VERIFIED_CLOSED:
                ver = Verification(
                    ticket_id=t.id,
                    citizen_id=cit.id,
                    result=VerificationResult.SOLVED,
                    rating=random.randint(4, 5),
                    created_at=closed_at
                )
                db.add(ver)
                append_ticket_event(db, t.id, "verified_closed", "citizen", str(cit.id), {"rating": ver.rating}, closed_at)
            elif status == TicketStatus.REOPENED:
                ver = Verification(
                    ticket_id=t.id,
                    citizen_id=cit.id,
                    result=VerificationResult.NOT_SOLVED,
                    rating=1,
                    created_at=created_at + timedelta(hours=30)
                )
                db.add(ver)
                append_ticket_event(db, t.id, "reopened", "citizen", str(cit.id), {"reason": "Still broken"}, created_at + timedelta(hours=30))

        db.flush()

        # 7. Mohalla Budget Projects
        print("[SEED] Creating Mohalla Budget participatory projects in Ward 1 & Ward 12...")
        projects_data = [
            (1, "Purani Mandi Heritage Solar Street Lighting", "Install 40 solar LED poles with battery backup in narrow heritage gallis.", 350000.0, ProjectStatus.VOTING),
            (1, "Old City Storm Drain Modernization & Grates", "Deep desilting and installation of iron safety grates on open storm drains.", 500000.0, ProjectStatus.VOTING),
            (1, "Community Organic Composting Station", "Decentralized bio-waste compost facility for vegetable market waste.", 220000.0, ProjectStatus.FUNDED),
            (3, "Gandhi Nagar Walkability & Tactile Pavers", "Repair continuous walking paths with tactile paving for elderly & vision impaired.", 450000.0, ProjectStatus.VOTING),
            (3, "Smart Water Pipeline Pressure Sensors", "Install 12 telemetry sensors to rapidly detect low pressure & pipeline leaks.", 300000.0, ProjectStatus.IN_PROGRESS),
            (3, "Green Verge Native Tree Plantation Drive", "Plant 200 Chinar & Neem saplings along Apsara Road median.", 150000.0, ProjectStatus.COMPLETED),
        ]
        for w_id, title, desc, cost, stat in projects_data:
            proj = Project(ward_id=w_id, title=title, description=desc, est_cost=cost, status=stat, cycle="2026-Q4")
            db.add(proj)
        db.flush()

        # 8. Monthly Pulse Responses
        print("[SEED] Adding monthly citizen pulse survey data...")
        for i in range(150):
            cit = random.choice(citizen_objs)
            pr = PulseResponse(
                citizen_id=cit.id,
                ward_id=cit.ward_id or 1,
                score=random.choice([3, 4, 4, 5, 5, 4, 2]),
                month="2026-10"
            )
            db.add(pr)

        # 9. Initial Trust Snapshots
        print("[SEED] Generating 30-day Trust Snapshots for all 10 wards...")
        for w in ward_objs:
            base_score = 62.0 + (w.id % 5) * 3.5
            for day_offset in range(30, 0, -1):
                snap_date = (now_dt - timedelta(days=day_offset)).strftime("%Y-%m-%d")
                score_variation = base_score + random.uniform(-2.5, 3.5)
                snap = TrustSnapshot(
                    ward_id=w.id,
                    date=snap_date,
                    trust_index=round(min(98.0, max(20.0, score_variation)), 1),
                    components={
                        "response": 0.85,
                        "closure": 0.78,
                        "reopen": 0.88,
                        "satisfaction": 0.82,
                        "proactive": 0.75,
                        "participation": 0.65
                    }
                )
                db.add(snap)

        db.commit()
        print("[SEED] Successfully seeded database with all idempotent fixtures!")
    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
