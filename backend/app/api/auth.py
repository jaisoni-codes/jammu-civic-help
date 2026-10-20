import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.models import Officer, OfficerRole
from backend.app.config import settings
from backend.app.security import verify_pin
from backend.app import clock

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    officer_id: int
    pin: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    officer: Dict[str, Any]

def create_jwt_token(payload: Dict[str, Any]) -> str:
    to_encode = payload.copy()
    expire = clock.now() + timedelta(minutes=settings.JWT_EXPIRES_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def get_current_officer(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Officer:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    try:
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        officer_id = decoded.get("officer_id")
        if not officer_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        officer = db.query(Officer).get(officer_id)
        if not officer:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Officer not found")
        return officer
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")

@router.post("/login", response_model=TokenResponse)
def officer_login(req: LoginRequest, db: Session = Depends(get_db)):
    officer = db.query(Officer).get(req.officer_id)
    if not officer or not verify_pin(req.pin, officer.pin_hash):
        raise HTTPException(status_code=400, detail="Invalid Officer ID or PIN")

    token = create_jwt_token({
        "officer_id": officer.id,
        "name": officer.name,
        "role": officer.role.value,
        "department_id": officer.department_id,
        "ward_ids": officer.ward_ids
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "officer": {
            "id": officer.id,
            "name": officer.name,
            "role": officer.role.value,
            "department": officer.department.name,
            "department_code": officer.department.code,
            "ward_ids": officer.ward_ids
        }
    }
