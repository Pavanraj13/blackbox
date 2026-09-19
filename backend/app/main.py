import os
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

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

@app.get("/")
def root():
    from app.config import LLM_PROVIDER, OLLAMA_MODEL, OPENAI_MODEL
    provider = LLM_PROVIDER
    model = OLLAMA_MODEL if provider == "ollama" else OPENAI_MODEL
    return {
        "engine": "Autonomous Black-Box UI/UX & Accessibility Testing Agent API",
        "status": "online",
        "provider": provider,
        "model": model,
        "health": "/api/health",
        "docs": "/docs",
        "dashboard": "http://localhost:3002"
    }

@app.get("/api/health")
def health_check():
    from app.config import LLM_PROVIDER, OLLAMA_MODEL, OPENAI_MODEL
    provider = LLM_PROVIDER
    model = OLLAMA_MODEL if provider == "ollama" else OPENAI_MODEL
    return {
        "status": "ok",
        "browser": "ready",
        "provider": provider,
        "model": model,
        "ai": f"{provider}:{model}"
    }

