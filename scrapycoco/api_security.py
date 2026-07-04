import os
import time
import hashlib
import hmac
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request, HTTPException, Header
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# --- Rate Limiter ---

class RateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> bool:
        now = time.time()
        bucket = self._buckets[key]
        bucket[:] = [t for t in bucket if now - t < self.window_seconds]
        if len(bucket) >= self.max_requests:
            return False
        bucket.append(now)
        return True

    def remaining(self, key: str) -> int:
        now = time.time()
        bucket = self._buckets[key]
        bucket[:] = [t for t in bucket if now - t < self.window_seconds]
        return max(0, self.max_requests - len(bucket))


rate_limiter = RateLimiter()


async def check_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail={
            "error": "rate_limit_exceeded",
            "message": f"Límite de {rate_limiter.max_requests} solicitudes por {rate_limiter.window_seconds}s excedido",
            "retry_after": rate_limiter.window_seconds,
        })
    return True


# --- API Key Authentication ---

API_KEYS: dict[str, dict] = {}

def load_api_keys():
    raw = os.environ.get("API_KEYS", "")
    if not raw:
        return
    for part in raw.split(","):
        part = part.strip()
        if ":" in part:
            key, name = part.split(":", 1)
            API_KEYS[key.strip()] = {"name": name.strip(), "created": datetime.now(timezone.utc).isoformat()}


def validate_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    if not API_KEYS:
        return True
    if not x_api_key:
        return False
    return x_api_key in API_KEYS


async def require_api_key(request: Request, x_api_key: Optional[str] = Header(None)):
    if not API_KEYS:
        return True
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail={
            "error": "invalid_api_key",
            "message": "API key inválida o ausente",
        })
    return True


# --- Security Headers Middleware ---

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


# --- Admin Auth ---

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

async def verify_admin(password: str = Header(..., alias="X-Admin-Password")):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Acceso denegado: contraseña de administrador inválida")
    return True


# --- Input Sanitizer ---

import re

def sanitize_string(value: str, max_length: int = 200) -> str:
    if not value:
        return ""
    value = re.sub(r"[<>\"]", "", value)
    value = value.strip()[:max_length]
    return value


def sanitize_dict(data: dict, max_length: int = 200) -> dict:
    return {k: sanitize_string(v, max_length) if isinstance(v, str) else v for k, v in data.items()}


# Init
load_api_keys()
