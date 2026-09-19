import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE, override=True)

def ensure_env_secrets():
    """Ensure API_KEY and SECRET_KEY exist in .env; generate if missing."""
    needs_save = False
    api_key = os.getenv("API_KEY", "").strip()
    secret_key = os.getenv("SECRET_KEY", "").strip()

    if not api_key:
        api_key = f"bb_{secrets.token_hex(24)}"
        os.environ["API_KEY"] = api_key
        needs_save = True

    if not secret_key:
        secret_key = secrets.token_hex(32)
        os.environ["SECRET_KEY"] = secret_key
        needs_save = True

    if needs_save:
        try:
            existing_lines = []
            if ENV_FILE.exists():
                with open(ENV_FILE, "r", encoding="utf-8") as f:
                    existing_lines = f.readlines()
            
            # Remove any partial keys
            filtered = [
                l for l in existing_lines 
                if not l.startswith("API_KEY=") and not l.startswith("SECRET_KEY=")
            ]
            filtered.append(f"API_KEY={api_key}\n")
            filtered.append(f"SECRET_KEY={secret_key}\n")
            
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.writelines(filtered)
        except Exception:
            pass

ensure_env_secrets()

API_KEY = os.getenv("API_KEY", "").strip()
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
ENCRYPT_AT_REST = os.getenv("ENCRYPT_AT_REST", "true").strip().lower() in ("1", "true", "yes")

def get_openai_api_key():
    load_dotenv(ENV_FILE, override=True)
    return os.getenv("OPENAI_API_KEY", "").strip()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")

# Model Architecture
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.6:35b")
OLLAMA_PLANNER_MODEL = os.getenv("OLLAMA_PLANNER_MODEL", "qwen3.6:35b").strip()
OLLAMA_ANALYZER_MODEL = os.getenv("OLLAMA_ANALYZER_MODEL", "qwen3.6:35b").strip()

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
