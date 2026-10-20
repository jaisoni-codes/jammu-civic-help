from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.config import settings
from backend.app.services.intake import process_citizen_intake

router = APIRouter(prefix="/webhook", tags=["Webhooks"])

class SimulateMessage(BaseModel):
    channel: str = "console"
    sender_id: str
    text: Optional[str] = None
    media_url: Optional[str] = None
    audio_url: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    button_reply_id: Optional[str] = None

@router.post("/simulate")
def simulate_incoming(msg: SimulateMessage, db: Session = Depends(get_db)):
    """Receives simulated chat message for testing and /sim chat console."""
    result = process_citizen_intake(
        db=db,
        channel=msg.channel,
        channel_user_id=msg.sender_id,
        text=msg.text,
        media_url=msg.media_url,
        audio_url=msg.audio_url,
        lat=msg.lat,
        lng=msg.lng,
        button_reply_id=msg.button_reply_id
    )
    return {"status": "ok", "result": result}

@router.get("/whatsapp")
def verify_whatsapp_webhook(request: Request):
    """WhatsApp Cloud API Webhook Verification."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(content="Verification failed", status_code=403)

@router.post("/whatsapp")
async def handle_whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """Handles incoming WhatsApp Cloud API messages."""
    data = await request.json()
    try:
        entries = data.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                val = change.get("value", {})
                messages = val.get("messages", [])
                for m in messages:
                    sender = m.get("from")
                    m_type = m.get("type")
                    text = None
                    button_id = None
                    lat = None
                    lng = None

                    if m_type == "text":
                        text = m.get("text", {}).get("body")
                    elif m_type == "interactive":
                        button_id = m.get("interactive", {}).get("button_reply", {}).get("id")
                    elif m_type == "location":
                        lat = m.get("location", {}).get("latitude")
                        lng = m.get("location", {}).get("longitude")

                    if sender:
                        process_citizen_intake(
                            db=db,
                            channel="whatsapp",
                            channel_user_id=str(sender),
                            text=text,
                            lat=lat,
                            lng=lng,
                            button_reply_id=button_id
                        )
    except Exception as e:
        print(f"[WHATSAPP WEBHOOK ERROR] {e}")
    return {"status": "received"}

@router.post("/telegram")
async def handle_telegram_webhook(request: Request, db: Session = Depends(get_db)):
    """Handles incoming Telegram bot updates."""
    data = await request.json()
    try:
        if "message" in data:
            msg = data["message"]
            sender_id = str(msg.get("chat", {}).get("id"))
            text = msg.get("text")
            loc = msg.get("location")
            lat = loc.get("latitude") if loc else None
            lng = loc.get("longitude") if loc else None

            process_citizen_intake(
                db=db,
                channel="telegram",
                channel_user_id=sender_id,
                text=text,
                lat=lat,
                lng=lng
            )
        elif "callback_query" in data:
            cq = data["callback_query"]
            sender_id = str(cq.get("message", {}).get("chat", {}).get("id"))
            data_val = cq.get("data")
            process_citizen_intake(
                db=db,
                channel="telegram",
                channel_user_id=sender_id,
                button_reply_id=data_val
            )
    except Exception as e:
        print(f"[TELEGRAM WEBHOOK ERROR] {e}")
    return {"status": "ok"}
