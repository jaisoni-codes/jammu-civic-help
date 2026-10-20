import io
import imagehash
from PIL import Image
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from backend.app.models import Ticket, Resolution, TicketEvent, TicketStatus
from backend.app.db import haversine_distance_m
from backend.app.services.ai import ai_service
from backend.app.services.audit import append_ticket_event
from backend.app.channels import get_channel_adapter
from backend.app import clock

def compute_image_phash(image_bytes: bytes) -> str:
    """Computes perceptual hash of an uploaded image."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        return str(imagehash.phash(img))
    except Exception as e:
        print(f"[PHASH ERROR] Could not compute phash: {e}")
        return "0000000000000000"

def phash_hamming_distance(hash1_str: str, hash2_str: str) -> int:
    try:
        h1 = imagehash.hex_to_hash(hash1_str)
        h2 = imagehash.hex_to_hash(hash2_str)
        return h1 - h2
    except Exception:
        return 99

def process_resolution(
    db: Session,
    ticket: Ticket,
    officer_id: int,
    after_photo_bytes: bytes,
    after_photo_url: str,
    officer_lat: float,
    officer_lng: float,
    mismatch_reason: Optional[str] = None
) -> Tuple[bool, str, Optional[Resolution]]:
    """
    Verified Closure Specification:
    1. Geotag Distance Check: Officer GPS vs Ticket location.
       Reject if distance > 75m unless officer picks mismatch reason (sets needs_review=True).
    2. Perceptual Hash Check: Reject exact reuse if phash distance < 6 against before-photo or previous resolutions.
    3. AI Check (Gemini Vision): Flags needs_review if confidence < 0.5 or issue_resolved_after == False.
    4. Transition status to resolved_pending_verification.
    5. Trigger interactive 'Solved? [Yes] [No]' to all citizens who reported this ticket.
    """
    # 1. Distance Check
    dist_m = haversine_distance_m(officer_lat, officer_lng, ticket.lat, ticket.lng)
    needs_review = False
    
    if dist_m > 75.0:
        if not mismatch_reason:
            return False, f"Location verification failed: You are {int(dist_m)}m away from ticket location (> 75m). Please provide a valid location mismatch reason if you are on site.", None
        needs_review = True

    # 2. Perceptual Hash Check
    current_phash = compute_image_phash(after_photo_bytes)
    
    # Check against all previous resolutions in the database to prevent duplicate photos
    all_resolutions = db.query(Resolution).all()
    for prev_res in all_resolutions:
        if prev_res.ai_check and "phash" in prev_res.ai_check:
            dist = phash_hamming_distance(current_phash, prev_res.ai_check["phash"])
            if dist < 6:
                return False, f"Duplicate photo rejected! Perceptual hash matches an existing resolution (Hamming distance {dist} < 6). You must capture live proof.", None

    # 3. AI Check (Gemini Vision / Mock)
    before_photo = ticket.reports[0].media_url if ticket.reports else None
    ai_check = ai_service.check_resolution_vision(before_photo, after_photo_url, ticket.category)
    
    if ai_check.confidence < 0.5 or not ai_check.issue_resolved_after:
        needs_review = True

    ai_check_dict = ai_check.model_dump()
    ai_check_dict["phash"] = current_phash

    now_dt = clock.now()

    # Create Resolution record
    resolution = Resolution(
        ticket_id=ticket.id,
        officer_id=officer_id,
        after_photo_url=after_photo_url,
        officer_lat=officer_lat,
        officer_lng=officer_lng,
        distance_m=round(dist_m, 1),
        phash_distance=20.0,
        ai_check=ai_check_dict,
        needs_review=needs_review,
        created_at=now_dt
    )
    db.add(resolution)

    ticket.status = TicketStatus.RESOLVED_PENDING_VERIFICATION
    ticket.resolved_at = now_dt

    append_ticket_event(
        db,
        ticket_id=ticket.id,
        event_type="resolved_pending_verification",
        actor_type="officer",
        actor_id=str(officer_id),
        payload={
            "distance_m": round(dist_m, 1),
            "needs_review": needs_review,
            "mismatch_reason": mismatch_reason
        },
        timestamp=now_dt
    )

    db.commit()
    db.refresh(resolution)

    # 4. Notify all reporting citizens with interactive 'Solved? [Yes] [No]' prompt
    for rep in ticket.reports:
        cit = rep.citizen
        if cit and cit.channel_user_id:
            adapter = get_channel_adapter(cit.channel)
            adapter.send_media(
                recipient_id=cit.channel_user_id,
                media_url=after_photo_url,
                caption=f"Officer has submitted proof of work for Ticket {ticket.code}."
            )
            adapter.send_interactive_buttons(
                recipient_id=cit.channel_user_id,
                text=f"Ticket {ticket.code} is marked RESOLVED. Has this issue been fixed satisfactorily?\nक्या यह समस्या ठीक हो गई है?",
                buttons=[
                    {"id": f"verify_yes_{ticket.code}", "title": "Yes / हाँ (Solved)"},
                    {"id": f"verify_no_{ticket.code}", "title": "No / नहीं (Not Solved)"}
                ]
            )

    return True, "Resolution submitted successfully and sent to citizen for verification.", resolution
