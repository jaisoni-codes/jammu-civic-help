from backend.app.config import settings
from backend.app.channels.base import ChannelAdapter
from backend.app.channels.console import ConsoleAdapter
from backend.app.channels.telegram import TelegramAdapter
from backend.app.channels.whatsapp import WhatsAppCloudAdapter

def get_channel_adapter(channel_name: str = None) -> ChannelAdapter:
    name = (channel_name or settings.CHANNEL).lower()
    if name == "telegram":
        return TelegramAdapter()
    elif name == "whatsapp":
        return WhatsAppCloudAdapter()
    return ConsoleAdapter()
