import httpx
from typing import List, Dict, Any, Optional
from backend.app.channels.base import ChannelAdapter
from backend.app.config import settings

class WhatsAppCloudAdapter(ChannelAdapter):
    def __init__(self):
        self.token = settings.WHATSAPP_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.base_url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages" if self.phone_number_id else ""

    def send_text(self, recipient_id: str, text: str) -> bool:
        if not self.token or not self.phone_number_id:
            print(f"[WHATSAPP MOCK -> {recipient_id}] {text}")
            return True
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "text",
            "text": {"body": text}
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(self.base_url, headers=headers, json=payload)
                return res.status_code in [200, 201]
        except Exception as e:
            print(f"[WHATSAPP ERROR] {e}")
            return False

    def send_interactive_buttons(
        self,
        recipient_id: str,
        text: str,
        buttons: List[Dict[str, str]],
        header: Optional[str] = None
    ) -> bool:
        if not self.token or not self.phone_number_id:
            print(f"[WHATSAPP MOCK BUTTONS -> {recipient_id}] {text} {[b['title'] for b in buttons]}")
            return True
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        action_buttons = []
        for b in buttons[:3]:  # WhatsApp limits quick reply buttons to 3
            action_buttons.append({
                "type": "reply",
                "reply": {"id": b["id"], "title": b["title"][:20]}
            })

        interactive: Dict[str, Any] = {
            "type": "button",
            "body": {"text": text},
            "action": {"buttons": action_buttons}
        }
        if header:
            interactive["header"] = {"type": "text", "text": header}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "interactive",
            "interactive": interactive
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(self.base_url, headers=headers, json=payload)
                return res.status_code in [200, 201]
        except Exception as e:
            print(f"[WHATSAPP ERROR] {e}")
            return False

    def send_media(
        self,
        recipient_id: str,
        media_url: str,
        caption: Optional[str] = None
    ) -> bool:
        if not self.token or not self.phone_number_id:
            print(f"[WHATSAPP MOCK MEDIA -> {recipient_id}] {media_url} {caption}")
            return True
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "image",
            "image": {"link": media_url, "caption": caption or ""}
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(self.base_url, headers=headers, json=payload)
                return res.status_code in [200, 201]
        except Exception as e:
            print(f"[WHATSAPP ERROR] {e}")
            return False
