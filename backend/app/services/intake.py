from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models import Ticket, Report, Citizen, TicketStatus
from backend.app.business_rules import CATEGORIES_CONFIG
from backend.app.services.ai import ai_service
from backend.app.services.clustering import find_duplicate_ticket
from backend.app.services.routing import find_nearest_ward, route_ticket
from backend.app.services.priority import compute_priority_score
from backend.app.services.audit import append_ticket_event
from backend.app.channels import get_channel_adapter
from backend.app.config import settings
from backend.app import clock

# In-memory conversational state machine per citizen channel ID
# States: WELCOME -> AWAITING_LOCATION -> CONFIRMING_REPORT -> IDLE
citizen_sessions: Dict[str, Dict[str, Any]] = {}

def process_citizen_intake(
    db: Session,
    channel: str,
    channel_user_id: str,
    text: Optional[str] = None,
    media_url: Optional[str] = None,
    audio_url: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    button_reply_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main State Machine for Citizen Channel Conversation Flow:
    1. First contact / lang selection
    2. Grievance message (text/voice/photo)
    3. Location resolution
    4. Confirmation -> Duplicate Cluster or New Ticket
    5. Returns dict with response status & created/joined ticket
    """
    adapter = get_channel_adapter(channel)

    # 1. Fetch or create citizen
    citizen = db.query(Citizen).filter(Citizen.channel_user_id == channel_user_id).first()
    if not citizen:
        citizen = Citizen(
            channel=channel,
            channel_user_id=channel_user_id,
            lang="en",
            subscribed=True,
            created_at=clock.now()
        )
        db.add(citizen)
        db.commit()
        db.refresh(citizen)

    session = citizen_sessions.get(channel_user_id, {"state": "IDLE"})

    # Check for commands
    cmd = (text or button_reply_id or "").strip().lower()
    if cmd in ["status", "my tickets"]:
        # List recent tickets reported by citizen
        user_reports = db.query(Report).filter(Report.citizen_id == citizen.id).all()
        ticket_ids = list(set([r.ticket_id for r in user_reports]))
        tickets = db.query(Ticket).filter(Ticket.id.in_(ticket_ids)).order_by(Ticket.created_at.desc()).limit(5).all()
        if not tickets:
            msg = "You have no active grievances recorded. / आपका कोई सक्रिय टिकट नहीं है।"
        else:
            lines = ["📋 *Your Recent Grievances / आपके हालिया टिकट:*"]
            for t in tickets:
                lines.append(f"• `{t.code}` ({t.category.replace('_', ' ').title()}): Status: *{t.status.value.upper()}*")
            msg = "\n".join(lines)
        adapter.send_text(channel_user_id, msg)
        return {"action": "status", "tickets": len(tickets)}

    if cmd in ["lang", "language"]:
        session["state"] = "SELECT_LANG"
        citizen_sessions[channel_user_id] = session
        adapter.send_interactive_buttons(
            channel_user_id,
            "Please select your preferred language / अपनी पसंदीदा भाषा चुनें:",
            [{"id": "lang_en", "title": "English"}, {"id": "lang_hi", "title": "हिंदी"}]
        )
        return {"action": "select_lang"}

    if cmd.startswith("lang_"):
        chosen_lang = "hi" if "hi" in cmd else "en"
        citizen.lang = chosen_lang
        db.commit()
        session["state"] = "IDLE"
        citizen_sessions[channel_user_id] = session
        msg = "भाषा हिंदी सेट हो गई है। आप अपनी समस्या लिख सकते हैं या बोल कर भेज सकते हैं।" if chosen_lang == "hi" else "Language set to English. You can report any civic issue by text, photo or voice note."
    # Check verification replies (Yes/No from citizen on resolved tickets)
    if cmd.startswith("verify_yes_"):
        ticket_code = cmd.replace("verify_yes_", "").upper()
        ticket = db.query(Ticket).filter(Ticket.code == ticket_code).first()
        if ticket:
            ticket.status = TicketStatus.VERIFIED_CLOSED
            ticket.closed_at = clock.now()
            from backend.app.models import Verification, VerificationResult
            ver = Verification(
                ticket_id=ticket.id,
                citizen_id=citizen.id,
                result=VerificationResult.SOLVED,
                rating=5,
                created_at=clock.now()
            )
            db.add(ver)
            append_ticket_event(
                db,
                ticket_id=ticket.id,
                event_type="verified_closed",
                actor_type="citizen",
                actor_id=str(citizen.id),
                payload={"verified": True, "rating": 5},
                timestamp=clock.now()
            )
            db.commit()
            adapter.send_interactive_buttons(
                channel_user_id,
                f"🎉 Thank you! Ticket {ticket.code} is now VERIFIED CLOSED.\nHow satisfied were you with the municipal response? (1 to 5 Stars):",
                [
                    {"id": f"rating_5_{ticket.code}", "title": "⭐⭐⭐⭐⭐ (5)"},
                    {"id": f"rating_4_{ticket.code}", "title": "⭐⭐⭐⭐ (4)"},
                    {"id": f"rating_3_{ticket.code}", "title": "⭐⭐⭐ (3)"}
                ]
            )
            return {"action": "verified_closed", "ticket_code": ticket.code}

    if cmd.startswith("verify_no_"):
        ticket_code = cmd.replace("verify_no_", "").upper()
        ticket = db.query(Ticket).filter(Ticket.code == ticket_code).first()
        if ticket:
            ticket.status = TicketStatus.REOPENED
            ticket.reopen_count += 1
            ticket.escalation_level = min(2, ticket.escalation_level + 1)
            from backend.app.models import Verification, VerificationResult
            ver = Verification(
                ticket_id=ticket.id,
                citizen_id=citizen.id,
                result=VerificationResult.NOT_SOLVED,
                rating=1,
                created_at=clock.now()
            )
            db.add(ver)
            append_ticket_event(
                db,
                ticket_id=ticket.id,
                event_type="reopened",
                actor_type="citizen",
                actor_id=str(citizen.id),
                payload={"reopen_count": ticket.reopen_count, "new_escalation": ticket.escalation_level},
                timestamp=clock.now()
            )
            db.commit()
            adapter.send_text(
                channel_user_id,
                f"⚠️ *Ticket {ticket.code} Reopened!* We apologize that the work was incomplete. The ticket has been escalated (Level {ticket.escalation_level}) and assigned supervisors have been alerted."
            )
            return {"action": "reopened", "ticket_code": ticket.code, "escalation_level": ticket.escalation_level}

    if cmd.startswith("rating_"):
        parts = cmd.split("_")
        stars = int(parts[1]) if len(parts) > 1 else 5
        adapter.send_text(channel_user_id, f"🙏 Thank you for rating ({stars} Stars)! Your feedback directly powers the Ward Trust Index.")
        return {"action": "rated", "stars": stars}

    # Voice transcription if audio present
    transcript = None
    if audio_url:
        transcription = ai_service.transcribe_audio(audio_url)
        transcript = transcription.get("transcript")
        text = transcript

    # Handling Confirmation Step
    if session.get("state") == "AWAITING_CONFIRMATION":
        if cmd in ["confirm_yes", "yes", "ha", "haan"]:
            pending = session.get("pending_report", {})
            ticket, is_new = _commit_ticket_or_cluster(
                db, citizen, pending["text"], pending.get("media_url"),
                pending.get("audio_url"), pending.get("transcript"),
                pending["lat"], pending["lng"], pending["classification"]
            )
            session["state"] = "IDLE"
            citizen_sessions[channel_user_id] = session

            track_url = f"{settings.BASE_URL}/t/{ticket.code}"
            if is_new:
                resp_text = (
                    f"✅ *Grievance Registered: {ticket.code}*\n"
                    f"Department: {ticket.department.name}\n"
                    f"Ward: {ticket.ward.name}\n"
                    f"Live Public Tracker: {track_url}\n\n"
                    f"आपकी शिकायत दर्ज कर ली गई है।"
                )
            else:
                resp_text = (
                    f"🤝 *Collective Voice: Joined Existing Ticket!*\n"
                    f"You and {ticket.affected_count - 1} other citizens reported this issue at this location.\n"
                    f"Ticket: `{ticket.code}`\n"
                    f"Higher collective reports raise priority!\n"
                    f"Live Tracker: {track_url}"
                )

            adapter.send_text(channel_user_id, resp_text)
            return {"action": "confirmed", "ticket_code": ticket.code, "is_new": is_new}
        else:
            session["state"] = "IDLE"
            citizen_sessions[channel_user_id] = session
            adapter.send_text(channel_user_id, "Report cancelled. Please send your grievance again when ready.")
            return {"action": "cancelled"}

    # Handling Missing Location
    if session.get("state") == "AWAITING_LOCATION":
        if lat is not None and lng is not None:
            pending = session.get("pending_report", {})
            pending["lat"] = lat
            pending["lng"] = lng
            session["pending_report"] = pending
            session["state"] = "AWAITING_CONFIRMATION"
            citizen_sessions[channel_user_id] = session

            cat = pending["classification"].category
            label = CATEGORIES_CONFIG.get(cat, {}).get("label", cat)
            adapter.send_interactive_buttons(
                channel_user_id,
                f"Confirm reporting '{label}' at this location?",
                [{"id": "confirm_yes", "title": "Yes / हाँ"}, {"id": "confirm_no", "title": "Cancel / रद्द"}]
            )
            return {"action": "location_received_awaiting_confirm"}

    # New Grievance Intake
    if text or media_url or audio_url:
        classification = ai_service.classify_complaint(text or "Photo report", media_url)

        # If location not provided, default to Ward 1 centroid or ask
        if lat is None or lng is None:
            # For quick demo fallback, use Ward 1 centroid if citizen has ward
            if citizen.ward_id:
                ward = db.query(Ward).get(citizen.ward_id)
                lat, lng = ward.centroid_lat, ward.centroid_lng
            else:
                lat, lng = 32.7285, 74.8631  # Central Jammu

        pending_report = {
            "text": text,
            "media_url": media_url,
            "audio_url": audio_url,
            "transcript": transcript,
            "lat": lat,
            "lng": lng,
            "classification": classification
        }

        # Auto-confirm or prompt confirmation
        session["pending_report"] = pending_report
        session["state"] = "AWAITING_CONFIRMATION"
        citizen_sessions[channel_user_id] = session

        cat_label = CATEGORIES_CONFIG.get(classification.category, {}).get("label", classification.category)
        adapter.send_interactive_buttons(
            channel_user_id,
            f"Detected Issue: *{cat_label}*\nSeverity: {classification.severity}/5\nSummary: {classification.summary}\n\nSubmit this report?",
            [{"id": "confirm_yes", "title": "Submit / हाँ"}, {"id": "confirm_no", "title": "Cancel / रद्द"}]
        )
        return {"action": "prompt_confirm", "category": classification.category}

    return {"action": "noop"}

def _commit_ticket_or_cluster(
    db: Session,
    citizen: Citizen,
    text: Optional[str],
    media_url: Optional[str],
    audio_url: Optional[str],
    transcript: Optional[str],
    lat: float,
    lng: float,
    classification: Any
) -> Tuple[Ticket, bool]:
    embedding = ai_service.get_embedding(text or classification.summary)

    # Check for duplicate cluster
    existing_ticket = find_duplicate_ticket(
        db,
        category=classification.category,
        lat=lat,
        lng=lng,
        embedding=embedding
    )

    now_dt = clock.now()

    if existing_ticket:
        # Join existing ticket: Collective Voice
        existing_ticket.affected_count += 1
        
        # Save individual report
        report = Report(
            ticket_id=existing_ticket.id,
            citizen_id=citizen.id,
            text=text,
            media_url=media_url,
            audio_url=audio_url,
            transcript=transcript,
            lang=citizen.lang,
            lat=lat,
            lng=lng,
            created_at=now_dt
        )
        db.add(report)

        # Recompute priority
        new_score, reasons = compute_priority_score(
            db,
            affected_count=existing_ticket.affected_count,
            severity=existing_ticket.severity,
            created_at=existing_ticket.created_at,
            safety_flag=existing_ticket.safety_flag,
            lat=existing_ticket.lat,
            lng=existing_ticket.lng
        )
        existing_ticket.priority_score = new_score
        existing_ticket.priority_reason = reasons

        append_ticket_event(
            db,
            ticket_id=existing_ticket.id,
            event_type="citizen_joined",
            actor_type="citizen",
            actor_id=str(citizen.id),
            payload={"affected_count": existing_ticket.affected_count, "new_priority": new_score},
            timestamp=now_dt
        )
        db.commit()
        db.refresh(existing_ticket)
        return existing_ticket, False

    # Create brand new ticket
    nearest_ward = find_nearest_ward(db, lat, lng)
    citizen.ward_id = nearest_ward.id

    dept, assigned_officer = route_ticket(db, classification.category, nearest_ward.id)
    cat_cfg = CATEGORIES_CONFIG.get(classification.category, CATEGORIES_CONFIG["other"])
    sla_hours = cat_cfg["sla_hours"]
    sla_due_at = now_dt + timedelta(hours=sla_hours)

    score, reasons = compute_priority_score(
        db,
        affected_count=1,
        severity=classification.severity,
        created_at=now_dt,
        safety_flag=classification.safety_flag,
        lat=lat,
        lng=lng
    )

    next_num = db.query(Ticket).count() + 1
    ticket_code = f"BH-{next_num:04d}"

    ticket = Ticket(
        code=ticket_code,
        category=classification.category,
        department_id=dept.id,
        ward_id=nearest_ward.id,
        lat=lat,
        lng=lng,
        address_text=f"Near Ward {nearest_ward.id}, Jammu",
        status=TicketStatus.ASSIGNED if assigned_officer else TicketStatus.OPEN,
        severity=classification.severity,
        safety_flag=classification.safety_flag,
        affected_count=1,
        priority_score=score,
        priority_reason=reasons,
        sla_due_at=sla_due_at,
        escalation_level=0,
        assigned_officer_id=assigned_officer.id if assigned_officer else None,
        embedding=embedding,
        reopen_count=0,
        created_at=now_dt,
        first_response_at=now_dt if assigned_officer else None,
        is_synthetic=False
    )
    db.add(ticket)
    db.flush()

    report = Report(
        ticket_id=ticket.id,
        citizen_id=citizen.id,
        text=text,
        media_url=media_url,
        audio_url=audio_url,
        transcript=transcript,
        lang=citizen.lang,
        lat=lat,
        lng=lng,
        created_at=now_dt
    )
    db.add(report)

    # Hash chain genesis event
    append_ticket_event(
        db,
        ticket_id=ticket.id,
        event_type="created",
        actor_type="citizen",
        actor_id=str(citizen.id),
        payload={"category": ticket.category, "severity": ticket.severity, "sla_hours": sla_hours},
        timestamp=now_dt
    )
    if assigned_officer:
        append_ticket_event(
            db,
            ticket_id=ticket.id,
            event_type="assigned",
            actor_type="system",
            actor_id="auto_router",
            payload={"officer_id": assigned_officer.id, "officer_name": assigned_officer.name},
            timestamp=now_dt
        )

    db.commit()
    db.refresh(ticket)
    return ticket, True
