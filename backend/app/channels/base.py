from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class ChannelAdapter(ABC):
    """
    Abstract Channel Interface.
    All business logic talks strictly through this adapter.
    """
    @abstractmethod
    def send_text(self, recipient_id: str, text: str) -> bool:
        pass

    @abstractmethod
    def send_interactive_buttons(
        self,
        recipient_id: str,
        text: str,
        buttons: List[Dict[str, str]], # [{"id": "yes", "title": "Yes / हाँ"}, ...]
        header: Optional[str] = None
    ) -> bool:
        pass

    @abstractmethod
    def send_media(
        self,
        recipient_id: str,
        media_url: str,
        caption: Optional[str] = None
    ) -> bool:
        pass
