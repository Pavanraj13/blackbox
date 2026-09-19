import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=True)

def get_openai_api_key():
    load_dotenv(BASE_DIR / ".env", override=True)
    return os.getenv("OPENAI_API_KEY", "").strip()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.6:35b")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "90.0"))

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TARGET_URL = os.getenv("TARGET_URL", "http://localhost:3001")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/autonomous_ui_agent.db")

SCREENSHOTS_DIR = BASE_DIR / "screenshots"
REPORTS_DIR = BASE_DIR / "reports"

SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

