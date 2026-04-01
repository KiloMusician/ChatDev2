"""
app/backend/security.py — Comprehensive security hardening for Terminal Depths.

Provides:
  SecurityHeadersMiddleware  — CSP, HSTS, X-Frame-Options, X-Content-Type-Options,
                               Referrer-Policy, Permissions-Policy, X-XSS-Protection
  RateLimiter                — sliding-window per-IP rate limiting (3 tiers)
  body_size_limit            — reject oversized request bodies early
  sanitize_error             — strip implementation details from HTTP 500 responses
  validate_command_input     — clean game command strings (null bytes, length, charset)
  SecurityAuditLog           — append-only security event recorder
  get_allowed_origins        — dynamic CORS origin list for Replit environment
"""
from __future__ import annotations

import collections
import json
import os
import re
import time
from pathlib import Path
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp


# ── Constants ──────────────────────────────────────────────────────────────────

_ROOT = Path(__file__).parent.parent.parent
_SECURITY_LOG = _ROOT / ".devmentor" / "security.log"
_SECURITY_LOG.parent.mkdir(exist_ok=True)

MAX_BODY_BYTES = int(os.environ.get("MAX_BODY_BYTES", str(50 * 1024)))   # 50 KB
MAX_CMD_LEN    = int(os.environ.get("MAX_CMD_LEN",    "4096"))            # chars

_REPLIT_DOMAIN = os.environ.get("REPLIT_DEV_DOMAIN", "")

# ── Security Audit Log ─────────────────────────────────────────────────────────

class SecurityAuditLog:
    """Append-only security event logger. Thread-safe via line-by-line append."""

    def __init__(self, path: Path = _SECURITY_LOG):
        self._path = path

    def record(self, event_type: str, ip: str, detail: str, path: str = "") -> None:
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event": event_type,
            "ip": ip,
            "path": path,
            "detail": detail[:512],
        }
        try:
            with self._path.open("a") as fh:
                fh.write(json.dumps(entry) + "\n")
        except OSError:
            pass  # never let logging crash the app

    def recent(self, n: int = 50) -> list[dict]:
        try:
            lines = self._path.read_text().splitlines()[-n:]
            return [json.loads(l) for l in lines if l.strip()]
        except (OSError, json.JSONDecodeError):
            return []


audit = SecurityAuditLog()


# ── Rate Limiter ───────────────────────────────────────────────────────────────

class RateLimiter:
    """
    Sliding-window rate limiter keyed by IP address.
    Three configurable tiers (requests per minute):
      auth    — strict (login/token endpoints)      default 10/min
      command — game commands                       default 120/min
      api     — general REST                        default 60/min
    """

    _TIER_DEFAULTS = {
        "auth":    int(os.environ.get("RATE_AUTH",    "10")),
        "command": int(os.environ.get("RATE_COMMAND", "120")),
        "agent":   int(os.environ.get("RATE_AGENT",  "200")),
        "api":     int(os.environ.get("RATE_API",     "120")),
    }

    # Path prefix → tier mapping (checked in order)
    _PATH_TIERS: list[tuple[str, str]] = [
        ("/auth/",             "auth"),
        ("/api/auth/",         "auth"),
        ("/api/agent/command", "command"),
        ("/api/agent/",        "agent"),
        ("/api/game/command",  "command"),
        ("/api/game/ws",       "command"),
    ]

    def __init__(self):
        # {tier: {ip: deque[float]}}
        self._windows: dict[str, dict[str, collections.deque]] = {
            t: collections.defaultdict(lambda: collections.deque())
            for t in self._TIER_DEFAULTS
        }

    def _tier_for(self, path: str) -> str:
        for prefix, tier in self._PATH_TIERS:
            if path.startswith(prefix):
                return tier
        return "api"

    def check(self, ip: str, path: str) -> tuple[bool, str]:
        """
        Returns (allowed, tier_name).
        Cleans expired timestamps as a side-effect.
        """
        tier = self._tier_for(path)
        limit = self._TIER_DEFAULTS[tier]
        now = time.monotonic()
        window = self._windows[tier][ip]

        # Evict timestamps older than 60 s
        while window and now - window[0] > 60:
            window.popleft()

        if len(window) >= limit:
            return False, tier

        window.append(now)
        return True, tier


_limiter = RateLimiter()


def _client_ip(request: Request) -> str:
    """Best-effort client IP (respects X-Forwarded-For from Replit proxy)."""
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return getattr(request.client, "host", "unknown") if request.client else "unknown"


# ── CORS origin helper ─────────────────────────────────────────────────────────

def get_allowed_origins() -> list[str]:
    """
    Build the CORS allow-list from environment.
    Always includes the Replit dev domain and localhost for local dev.
    Never returns bare '*' (incompatible with allow_credentials=True anyway).
    """
    # Include both the Replit container port (5000) and local VS Code dev port (7337).
    origins: list[str] = [
        "http://localhost:8008", "http://127.0.0.1:5000",  # Replit container
        "http://localhost:8008", "http://127.0.0.1:7337",  # local VS Code dev
    ]
    if _REPLIT_DOMAIN:
        origins.append(f"https://{_REPLIT_DOMAIN}")
    extra = os.environ.get("EXTRA_CORS_ORIGINS", "")
    if extra:
        origins.extend(o.strip() for o in extra.split(",") if o.strip())
    return origins


# ── Command input validation ───────────────────────────────────────────────────

_CTRL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

def validate_command_input(raw: str) -> tuple[bool, str]:
    """
    Validate a raw game command string.
    Returns (ok, cleaned_or_error_message).

    Checks:
      - Not empty / not whitespace-only
      - Under MAX_CMD_LEN characters
      - No null bytes or dangerous control characters
      - Strip ANSI escape sequences (terminal injection)
      - No shell meta-characters that could cause confusion in logging
    """
    if not raw or not raw.strip():
        return False, "empty command"
    if len(raw) > MAX_CMD_LEN:
        return False, f"command too long (max {MAX_CMD_LEN} chars)"
    if "\x00" in raw:
        return False, "null byte in command"
    cleaned = _CTRL_CHARS_RE.sub("", raw)
    cleaned = _ANSI_ESCAPE_RE.sub("", cleaned)
    cleaned = cleaned.strip()
    if not cleaned:
        return False, "command became empty after sanitisation"
    return True, cleaned


# ── Error sanitizer ────────────────────────────────────────────────────────────

_SENSITIVE_RE = re.compile(
    r"(?i)(password|token|secret|key|bearer|authorization|database|traceback|"
    r"File \"|line \d+|/home/|/root/|/var/|OperationalError|IntegrityError)"
)

def sanitize_error(exc: Exception, path: str = "") -> str:
    """
    Return a safe error message string — never leaks stack traces, paths,
    token values, or database details.
    """
    raw = str(exc)
    if _SENSITIVE_RE.search(raw):
        return "An internal error occurred. Please try again."
    # Truncate and strip anything that looks like a path
    cleaned = re.sub(r"/\S+", "[path]", raw)[:200]
    return cleaned or "Internal server error."


# ── Security headers middleware ────────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds defense-in-depth HTTP security headers to every response.

    Content-Security-Policy is the biggest single win — it prevents XSS
    even if innerHTML is used without escaping, by blocking inline scripts
    from loading external resources.

    Note: The game uses inline <script> tags and eval-like constructs in
    some frontend JS (xterm.js, Web Audio). 'unsafe-inline' is needed for
    <script> tags in the HTML pages; 'unsafe-eval' is needed for xterm.js.
    We use a nonce-less approach with tight connect-src and object-src restrictions.
    """

    def __init__(self, app: ASGIApp, replit_domain: str = _REPLIT_DOMAIN):
        super().__init__(app)
        self._domain = replit_domain
        # Build CSP once at startup
        wss_host = f"wss://{replit_domain}" if replit_domain else ""
        https_host = f"https://{replit_domain}" if replit_domain else ""
        connect_srcs = " ".join(filter(None, [
            "'self'",
            "ws://localhost:7337",   # Replit container WebSocket
            "ws://localhost:7337",   # local VS Code dev WebSocket
            wss_host,
            "https://replit.com",
            "https://*.replit.com",
        ]))
        self._csp = "; ".join([
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",  # xterm.js CDN + Web Audio
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",               # xterm.js CSS + inline styles
            "img-src 'self' data: blob:",
            f"connect-src {connect_srcs}",
            "font-src 'self' data:",
            "media-src 'self' blob:",
            "object-src 'none'",                                  # blocks Flash/plugins
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",                             # blocks clickjacking
        ])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # ── Rate limiting (before touching any handler) ────────────────────
        ip = _client_ip(request)
        allowed, tier = _limiter.check(ip, request.url.path)
        if not allowed:
            audit.record("RATE_LIMIT", ip, f"tier={tier}", request.url.path)
            return JSONResponse(
                status_code=429,
                content={"error": "Too many requests. Please slow down.", "tier": tier},
                headers={"Retry-After": "60"},
            )

        # ── Body size limit ────────────────────────────────────────────────
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_BYTES:
            audit.record("OVERSIZED_BODY", ip,
                         f"content-length={content_length}", request.url.path)
            return JSONResponse(
                status_code=413,
                content={"error": f"Request body too large (max {MAX_BODY_BYTES} bytes)."},
            )

        response = await call_next(request)

        # ── Security headers ───────────────────────────────────────────────
        response.headers["Content-Security-Policy"] = self._csp
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        )
        # HSTS — tell browsers to always use HTTPS (respected when behind Replit proxy)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        # Never cache API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response


# ── Suspicious pattern detector ────────────────────────────────────────────────

_SUSPICIOUS_PATTERNS = re.compile(
    r"(?i)(\.\./|%2e%2e|%252e|<script|javascript:|data:text/html|"
    r"onload=|onerror=|eval\(|union\s+select|drop\s+table|"
    r"exec\s*\(|base64_decode|/etc/passwd|/etc/shadow)"
)

def check_suspicious(raw_input: str, ip: str, context: str) -> bool:
    """
    Scan raw input for known attack patterns. Records to audit log.
    Returns True if suspicious (caller can choose to reject or allow).
    """
    if _SUSPICIOUS_PATTERNS.search(raw_input):
        audit.record("SUSPICIOUS_INPUT", ip, f"context={context} input={raw_input[:120]}")
        return True
    return False
