from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.db import get_db, Base, engine
from backend.app import clock
from backend.app.api.public import router as public_router
from backend.app.api.webhooks import router as webhooks_router
from backend.app.api.auth import router as auth_router
from backend.app.api.officer import router as officer_router
from backend.app.api.admin import router as admin_router
from backend.app.api.demo import router as demo_router

# Create database tables if not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="WhatsApp-first Civic Trust Engine for Jammu Smart City",
    version="1.0.0"
)

# CORS setup for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public_router)
app.include_router(webhooks_router)
app.include_router(auth_router)
app.include_router(officer_router)
app.include_router(admin_router)
app.include_router(demo_router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "env": settings.ENV,
        "mock_ai": settings.MOCK_AI,
        "channel": settings.CHANNEL,
        "clock_now": clock.now().isoformat(),
        "demo_offset_hours": clock.get_demo_offset(),
    }
