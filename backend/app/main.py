import os
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import SCREENSHOTS_DIR, REPORTS_DIR, API_KEY, ENCRYPT_AT_REST, get_openai_api_key
from app.database import engine, Base
from app.routes import agent, runs, reports
from app.security import APIKeyMiddleware
from app.models import migrate_db

# Create database tables & apply lightweight migrations
Base.metadata.create_all(bind=engine)
migrate_db()

app = FastAPI(
    title="Autonomous UI/UX & Accessibility Testing Agent API",
    version="2.0.0",
    description="Black-box autonomous agentic UI/UX testing framework."
)

# API Key Middleware (enforces auth on non-exempt routes)
app.add_middleware(APIKeyMiddleware)

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

@app.get("/api/key-info")
def get_key_info(request: Request):
    client_host = request.client.host if request.client else ""
    is_local = client_host in ("127.0.0.1", "::1", "localhost", "testclient")
    key_preview = f"{API_KEY[:6]}...{API_KEY[-4:]}" if API_KEY and len(API_KEY) > 10 else ""
    return {
        "auth_enabled": bool(API_KEY),
        "api_key": API_KEY if (is_local or not API_KEY) else "",
        "key_preview": key_preview,
        "encryption_enabled": ENCRYPT_AT_REST,
    }

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

@app.get("/api/models")
async def get_models():
    import httpx
    from app.config import OLLAMA_BASE_URL, get_openai_api_key

    models = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                for m in data.get("models", []):
                    tag = m.get("name", "")
                    size_gb = round(m.get("size", 0) / (1024**3), 1)
                    label = tag
                    if "qwen3.6" in tag:
                        label = f"{tag} ({size_gb}GB) - Recommended Default"
                    elif "qwen2.5" in tag:
                        label = f"{tag} ({size_gb}GB) - High Speed"
                    else:
                        label = f"{tag} ({size_gb}GB)"
                    models.append({
                        "id": tag,
                        "name": label,
                        "provider": "ollama",
                        "size_gb": size_gb,
                        "is_default": "qwen3.6" in tag
                    })
    except Exception:
        pass

    if not models:
        models = [
            {"id": "qwen3.6:35b", "name": "qwen3.6:35b (22GB) - Recommended Default", "provider": "ollama", "is_default": True},
            {"id": "qwen2.5:7b", "name": "qwen2.5:7b (4.7GB) - High Speed", "provider": "ollama", "is_default": False},
        ]

    # Ensure qwen3.6:35b is first
    models.sort(key=lambda x: 0 if "qwen3.6" in x["id"] else 1)

    if get_openai_api_key():
        models.append({
            "id": "gpt-4o-mini",
            "name": "gpt-4o-mini (OpenAI Cloud)",
            "provider": "openai",
            "is_default": False
        })

    return {
        "models": models,
        "default": "qwen3.6:35b"
    }


