from typing import List, Dict, Any, Optional
from backend.app.channels.base import ChannelAdapter

# In-memory message store for console channel so /sim chat simulator and tests can inspect messages
outbox_messages: List[Dict[str, Any]] = []

class ConsoleAdapter(ChannelAdapter):
    def send_text(self, recipient_id: str, text: str) -> bool:
        msg = {
            "type": "text",
            "recipient_id": recipient_id,
            "text": text,
        }
        outbox_messages.append(msg)
        try:
            print(f"[CONSOLE OUT -> {recipient_id}] {text}")
        except UnicodeEncodeError:
            print(f"[CONSOLE OUT -> {recipient_id}] {text.encode('ascii', errors='replace').decode('ascii')}")
        return True

    def send_interactive_buttons(
        self,
        recipient_id: str,
        text: str,
        buttons: List[Dict[str, str]],
        header: Optional[str] = None
    ) -> bool:
        msg = {
            "type": "buttons",
            "recipient_id": recipient_id,
            "header": header,
            "text": text,
            "buttons": buttons
        }
        outbox_messages.append(msg)
        btn_labels = " | ".join([f"[{b['title']}]" for b in buttons])
        try:
            print(f"[CONSOLE OUT -> {recipient_id}] {text}\n  Options: {btn_labels}")
        except UnicodeEncodeError:
            print(f"[CONSOLE OUT -> {recipient_id}] {text.encode('ascii', errors='replace').decode('ascii')}\n  Options: {btn_labels}")
        return True

    def send_media(
        self,
        recipient_id: str,
        media_url: str,
        caption: Optional[str] = None
    ) -> bool:
        msg = {
            "type": "media",
            "recipient_id": recipient_id,
            "media_url": media_url,
            "caption": caption
        }
        outbox_messages.append(msg)
        try:
            print(f"[CONSOLE OUT -> {recipient_id}] [MEDIA: {media_url}] {caption or ''}")
        except UnicodeEncodeError:
            print(f"[CONSOLE OUT -> {recipient_id}] [MEDIA: {media_url}] {(caption or '').encode('ascii', errors='replace').decode('ascii')}")
        return True

def get_outbox(drain: bool = False) -> List[Dict[str, Any]]:
    """Return current outbox. If drain=True, atomically clear after reading."""
    global outbox_messages
    msgs = list(outbox_messages)
    if drain:
        outbox_messages.clear()
    return msgs

def drain_outbox() -> List[Dict[str, Any]]:
    """Atomically read and clear the outbox in one operation."""
    global outbox_messages
    msgs = list(outbox_messages)
    outbox_messages.clear()
    return msgs

def clear_outbox():
    global outbox_messages
    outbox_messages.clear()
