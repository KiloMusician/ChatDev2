"""
app/backend/replit_auth.py — Replit Auth (OpenID Connect) for FastAPI.

Implements Replit's OIDC provider using PKCE + session cookies.
Users can log in with Google, GitHub, Apple, X, or email/password —
all handled by Replit's identity provider.

Routes registered:
  GET /auth/login      — start OIDC flow, redirect to Replit
  GET /auth/callback   — handle code exchange, set session
  GET /auth/logout     — clear session, redirect to Replit end_session
  GET /auth/me         — return current user JSON
  GET /auth/error      — error page

FastAPI dependencies:
  get_current_user(request) → dict | None   (optional, never raises)
  require_login             → dict           (raises 401 if not logged in)

Usage in a route:
    from .replit_auth import require_login, get_current_user

    @app.get("/protected")
    def protected(user=Depends(require_login)):
        return {"hello": user["first_name"]}

    @app.get("/optional")
    def optional_auth(user=Depends(get_current_user)):
        if user:
            return {"logged_in": True, "name": user.get("first_name")}
        return {"logged_in": False}
"""
from __future__ import annotations

import base64
import hashlib
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.routing import APIRouter

# ── Config ─────────────────────────────────────────────────────────────
ISSUER_URL = os.environ.get("ISSUER_URL", "https://replit.com/oidc")
_AUTH_URL = ISSUER_URL + "/auth"
_TOKEN_URL = ISSUER_URL + "/token"
_END_SESSION_URL = ISSUER_URL + "/session/end"
_JWKS_URI = ISSUER_URL + "/jwks"

_HERE = Path(__file__).parent.parent.parent  # repo root

# JWKS client is module-level so keys are cached across requests
_jwks_client: Optional[PyJWKClient] = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(_JWKS_URI, cache_keys=True, lifespan=3600)
    return _jwks_client


_DB_PATH = _HERE / ".devmentor" / "agent_memory.db"

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Database: replit_users table ────────────────────────────────────────

def _db():
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_users_table() -> None:
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS replit_users (
                id          TEXT PRIMARY KEY,
                email       TEXT,
                first_name  TEXT,
                last_name   TEXT,
                profile_image_url TEXT,
                created_at  REAL DEFAULT (unixepoch()),
                updated_at  REAL DEFAULT (unixepoch())
            )
        """)
        conn.commit()


def _upsert_user(claims: dict) -> dict:
    user = {
        "id":                claims.get("sub", ""),
        "email":             claims.get("email"),
        "first_name":        claims.get("first_name"),
        "last_name":         claims.get("last_name"),
        "profile_image_url": claims.get("profile_image_url"),
    }
    with _db() as conn:
        conn.execute("""
            INSERT INTO replit_users (id, email, first_name, last_name, profile_image_url, updated_at)
            VALUES (:id, :email, :first_name, :last_name, :profile_image_url, unixepoch())
            ON CONFLICT(id) DO UPDATE SET
              email=excluded.email,
              first_name=excluded.first_name,
              last_name=excluded.last_name,
              profile_image_url=excluded.profile_image_url,
              updated_at=unixepoch()
        """, user)
        conn.commit()
    return user


# ── PKCE helpers ────────────────────────────────────────────────────────

def _pkce_pair() -> tuple[str, str]:
    """Generate (verifier, challenge) for PKCE S256."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def _callback_uri(request: Request) -> str:
    """Build the absolute callback URI using X-Forwarded headers (Replit proxy)."""
    # Prefer https since Replit proxies all traffic via https
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "localhost")
    return f"https://{host}/auth/callback"


# ── Auth routes ─────────────────────────────────────────────────────────

@router.get("/login")
async def login(request: Request, next: str = "/"):
    """Start the Replit OIDC auth flow."""
    repl_id = os.environ.get("REPL_ID", "")
    if not repl_id:
        raise HTTPException(500, "REPL_ID environment variable not set")

    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)
    redirect_uri = _callback_uri(request)

    request.session.update({
        "oauth_state": state,
        "pkce_verifier": verifier,
        "redirect_uri": redirect_uri,
        "next_url": next,
    })

    params = urlencode({
        "client_id":             repl_id,
        "response_type":         "code",
        "scope":                 "openid profile email offline_access",
        "redirect_uri":          redirect_uri,
        "state":                 state,
        "code_challenge":        challenge,
        "code_challenge_method": "S256",
        "prompt":                "login consent",
    })
    return RedirectResponse(f"{_AUTH_URL}?{params}", status_code=302)


@router.get("/callback")
async def callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """Handle Replit's OIDC redirect — exchange code for tokens."""
    if error:
        return RedirectResponse(f"/auth/error?reason={error}", status_code=302)

    if not code:
        return RedirectResponse("/auth/error?reason=no_code", status_code=302)

    # Validate state to prevent CSRF
    expected_state = request.session.get("oauth_state")
    if not expected_state or state != expected_state:
        return RedirectResponse("/auth/error?reason=invalid_state", status_code=302)

    repl_id   = os.environ.get("REPL_ID", "")
    verifier  = request.session.pop("pkce_verifier", "")
    redir_uri = request.session.pop("redirect_uri", _callback_uri(request))
    next_url  = request.session.pop("next_url", "/")
    request.session.pop("oauth_state", None)

    # Exchange authorization code for tokens
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(_TOKEN_URL, data={
                "grant_type":    "authorization_code",
                "client_id":     repl_id,
                "code":          code,
                "redirect_uri":  redir_uri,
                "code_verifier": verifier,
            }, headers={"Accept": "application/json"})
    except httpx.RequestError as exc:
        return RedirectResponse(f"/auth/error?reason=token_request_failed", status_code=302)

    if not resp.is_success:
        return RedirectResponse(f"/auth/error?reason=token_exchange_failed", status_code=302)

    tokens    = resp.json()
    id_token  = tokens.get("id_token")
    if not id_token:
        return RedirectResponse("/auth/error?reason=no_id_token", status_code=302)

    # Verify JWT signature using Replit's published JWKS keys
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(id_token)
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience=repl_id,
            issuer=ISSUER_URL,
            options={"verify_exp": True},
        )
    except Exception:
        return RedirectResponse("/auth/error?reason=jwt_invalid", status_code=302)
    user   = _upsert_user(claims)

    # Store user in session
    request.session["user_id"] = user["id"]
    request.session["user"]    = user

    return RedirectResponse(next_url or "/", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    """Clear the session and redirect to Replit's end_session endpoint."""
    repl_id = os.environ.get("REPL_ID", "")
    base    = str(request.base_url).rstrip("/")
    request.session.clear()
    params = urlencode({"client_id": repl_id, "post_logout_redirect_uri": base + "/"})
    return RedirectResponse(f"{_END_SESSION_URL}?{params}", status_code=302)


@router.get("/me")
async def me(request: Request):
    """Return the current user's profile (or unauthenticated status)."""
    user = request.session.get("user")
    if not user:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": user}


@router.get("/error", response_class=HTMLResponse)
async def auth_error(reason: str = "unknown"):
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Auth Error</title>
<style>
  body {{ background:#0d1117; color:#f85149; font-family:monospace; padding:3em; }}
  a    {{ color:#58a6ff; text-decoration:none; }}
  h2   {{ color:#f85149; }}
  .box {{ border:1px solid #f85149; padding:1.5em; max-width:480px; border-radius:6px; }}
</style>
</head>
<body>
  <div class="box">
    <h2>Authentication Error</h2>
    <p>Reason: <code>{reason}</code></p>
    <p><a href="/auth/login">Try again</a> &nbsp;|&nbsp; <a href="/">Back home</a></p>
  </div>
</body>
</html>""", status_code=403)


# ── FastAPI dependencies ────────────────────────────────────────────────

def get_current_user(request: Request) -> Optional[dict]:
    """
    Optional dependency — returns the logged-in user dict or None.

    Example:
        @app.get("/home")
        def home(user=Depends(get_current_user)):
            if user: return {"hi": user["first_name"]}
            return {"msg": "please log in"}
    """
    return request.session.get("user")


def require_login(user=Depends(get_current_user)) -> dict:
    """
    Dependency that requires authentication.
    Raises HTTP 401 if the user is not logged in.

    Example:
        @app.get("/profile")
        def profile(user=Depends(require_login)):
            return user
    """
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please log in at /auth/login",
        )
    return user


def get_user_id(request: Request) -> Optional[str]:
    """Convenience dependency — returns just the user ID string."""
    return request.session.get("user_id")
