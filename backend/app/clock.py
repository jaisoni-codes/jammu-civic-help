from datetime import datetime, timezone, timedelta
from backend.app.config import settings

# In-memory offset override so demo panel can advance time dynamically
_current_demo_offset_hours: float = settings.DEMO_OFFSET_HOURS

def now() -> datetime:
    """
    Returns current UTC datetime plus DEMO_OFFSET_HOURS (timezone-naive for clean SQLite & Postgres parity).
    Enables instant fast-forwarding of time for demoing SLAs, auto-closure, etc.
    """
    global _current_demo_offset_hours
    return datetime.utcnow() + timedelta(hours=_current_demo_offset_hours)

def get_demo_offset() -> float:
    global _current_demo_offset_hours
    return _current_demo_offset_hours

def set_demo_offset(hours: float) -> float:
    global _current_demo_offset_hours
    _current_demo_offset_hours = hours
    return _current_demo_offset_hours

def advance_demo_offset(hours: float) -> float:
    global _current_demo_offset_hours
    _current_demo_offset_hours += hours
    return _current_demo_offset_hours

def reset_clock() -> float:
    global _current_demo_offset_hours
    _current_demo_offset_hours = 0.0
    return _current_demo_offset_hours
