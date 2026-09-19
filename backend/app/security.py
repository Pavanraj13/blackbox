import os
import re
import base64
import hashlib
import secrets
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import API_KEY, SECRET_KEY, ENCRYPT_AT_REST

class AESCipher:
    """AES-256-GCM authenticated encryption/decryption for data at rest."""
    def __init__(self, key_material: Optional[str] = None):
        raw_key = (key_material or SECRET_KEY or "blackbox-default-secret-key-32b").encode("utf-8")
        # Ensure 32 bytes via SHA-256
        self.key = hashlib.sha256(raw_key).digest()
        self.aesgcm = AESGCM(self.key)

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        if not ENCRYPT_AT_REST:
            return plaintext
        nonce = secrets.token_bytes(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        payload = nonce + ciphertext
        return "enc:" + base64.b64encode(payload).decode("utf-8")

    def decrypt(self, token: str) -> str:
        if not token:
            return ""
        if not token.startswith("enc:"):
            # Not encrypted (legacy data or encryption disabled)
            return token
        try:
            payload = base64.b64decode(token[4:])
            nonce = payload[:12]
            ciphertext = payload[12:]
            decrypted = self.aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted.decode("utf-8")
        except Exception:
            # Fallback if decryption fails (e.g. key changed)
            return token

cipher = AESCipher()

def generate_api_key() -> str:
    """Generate a random 32-byte secure hex API key."""
    return f"bb_{secrets.token_hex(24)}"

def verify_api_key(provided_key: Optional[str], expected_key: str) -> bool:
    """Constant-time comparison for API keys."""
    if not provided_key or not expected_key:
        return False
    return secrets.compare_digest(provided_key.strip(), expected_key.strip())

class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces API key authentication on protected endpoints.
    Allows exemptions for public documentation, health checks, preflight requests,
    read-only reports/summaries, and local loopback requests without credentials.
    """
    EXEMPT_PREFIXES = (
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/key-info",
        "/api/health",
        "/api/models",
        "/static",
        "/screenshots",
        "/reports",
    )
    EXEMPT_SUFFIXES = (
        "/report",
        "/summary",
        "/export",
    )

    async def dispatch(self, request: Request, call_next) -> Response:
        # Preflight CORS requests are always allowed
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        # Check exempt prefixes
        if any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
            return await call_next(request)

        # Check exempt suffixes (direct browser access to HTML/JSON reports and downloads)
        if any(path.endswith(suffix) for suffix in self.EXEMPT_SUFFIXES):
            return await call_next(request)

        # Root route exempt for status
        if path == "/":
            return await call_next(request)

        # If API_KEY is not configured or blank, allow requests in dev mode
        if not API_KEY:
            return await call_next(request)

        # Extract API Key from Header, Authorization bearer, or Query Param
        provided_key = request.headers.get("X-API-Key")
        if not provided_key:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                provided_key = auth_header[7:].strip()
        if not provided_key:
            provided_key = request.query_params.get("api_key")

        # If valid key provided, proceed
        if provided_key and verify_api_key(provided_key, API_KEY):
            return await call_next(request)

        # Allow local loopback clients (localhost / 127.0.0.1 / ::1) when no key was explicitly provided
        client_host = request.client.host if request.client else ""
        is_loopback = client_host in ("127.0.0.1", "::1", "localhost", "testclient")
        origin = request.headers.get("origin", "")
        is_local_origin = not origin or "localhost" in origin or "127.0.0.1" in origin

        if is_loopback and is_local_origin and not provided_key:
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={
                "detail": "Unauthorized: Missing or invalid API key. Provide header 'X-API-Key' or parameter 'api_key'."
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )

# Sensitive data redaction patterns
REDACTION_PATTERNS = [
    # Credit cards (16 digits with optional spaces or dashes)
    (re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"), "[CARD_REDACTED]"),
    # Social Security Numbers (SSN)
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REDACTED]"),
    # Phone numbers (US and international formats)
    (re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[PHONE_REDACTED]"),
    # Passwords or auth tokens in key-value format
    (
        re.compile(
            r"""(?i)(password|passwd|secret|token|api_key|authorization)\s*[:=]\s*['"]?([^\s,'"]+)"""
        ),
        r"\1: [SECRET_REDACTED]",
    ),
]

def redact_sensitive(text: str) -> str:
    """Redact PII, payment info, and secrets from text before sending to LLM."""
    if not text:
        return ""
    sanitized = text
    for pattern, replacement in REDACTION_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized
