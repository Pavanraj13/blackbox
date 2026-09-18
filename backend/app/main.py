import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import SCREENSHOTS_DIR, REPORTS_DIR, get_openai_api_key
from app.database import engine, Base
from app.routes import agent, runs, reports

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Autonomous UI/UX & Accessibility Testing Agent API",
    version="1.0.0",
    description="Black-box autonomous agentic UI/UX testing framework."
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for screenshots & reports
app.mount("/screenshots", StaticFiles(directory=str(SCREENSHOTS_DIR)), name="screenshots")
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")

# Include routers
app.include_router(agent.router)
app.include_router(runs.router)
app.include_router(reports.router)

@app.get("/api/health")
def health_check():
    key = get_openai_api_key()
    ai_status = "configured" if key else "semantic_fallback_active"
    return {
        "status": "ok",
        "browser": "ready",
        "ai": ai_status
    }

