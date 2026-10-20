import httpx
from typing import List, Dict, Any, Optional
from backend.app.channels.base import ChannelAdapter
from backend.app.config import settings

class TelegramAdapter(ChannelAdapter):
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""

    def send_text(self, recipient_id: str, text: str) -> bool:
        if not self.token:
            print(f"[TELEGRAM MOCK -> {recipient_id}] {text}")
            return True
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    f"{self.base_url}/sendMessage",
                    json={"chat_id": recipient_id, "text": text, "parse_mode": "Markdown"}
                )
                return res.status_code == 200
        except Exception as e:
            print(f"[TELEGRAM ERROR] {e}")
            return False

    def send_interactive_buttons(
        self,
        recipient_id: str,
        text: str,
        buttons: List[Dict[str, str]],
        header: Optional[str] = None
    ) -> bool:
        if not self.token:
            print(f"[TELEGRAM MOCK BUTTONS -> {recipient_id}] {text} {[b['title'] for b in buttons]}")
            return True
        try:
            keyboard = [[{"text": b["title"], "callback_data": b["id"]}] for b in buttons]
            msg_text = f"*{header}*\n\n{text}" if header else text
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": recipient_id,
                        "text": msg_text,
                        "parse_mode": "Markdown",
                        "reply_markup": {"inline_keyboard": keyboard}
                    }
                )
                return res.status_code == 200
        except Exception as e:
            print(f"[TELEGRAM ERROR] {e}")
            return False

    def send_media(
        self,
        recipient_id: str,
        media_url: str,
        caption: Optional[str] = None
    ) -> bool:
        if not self.token:
            print(f"[TELEGRAM MOCK PHOTO -> {recipient_id}] {media_url} {caption}")
            return True
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    f"{self.base_url}/sendPhoto",
                    json={"chat_id": recipient_id, "photo": media_url, "caption": caption or ""}
                )
                return res.status_code == 200
        except Exception as e:
            print(f"[TELEGRAM ERROR] {e}")
            return False
