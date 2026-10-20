import hashlib

def hash_pin(pin: str) -> str:
    """Deterministic salted SHA-256 hash for demo PINs."""
    salt = "bharosa_jammu_salt_2026"
    return hashlib.sha256(f"{salt}{pin}".encode("utf-8")).hexdigest()

def verify_pin(pin: str, hashed: str) -> bool:
    return hash_pin(pin) == hashed
