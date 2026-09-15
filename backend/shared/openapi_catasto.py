"""OpenAPI.it Catasto client — visure catastali ufficiali (sandbox → prod).

Auth (OAuth V2):
  POST {OPENAPI_OAUTH_BASE}/tokens
  Basic auth: OPENAPI_EMAIL : OPENAPI_API_KEY
  JSON body: {"grant_type":"client_credentials","scopes":"..."}
  → data.token used as Bearer on Catasto API

Docs: https://console.openapi.com/it/apis/catasto/documentation

Flow:
  1. POST /visura_catastale  → request id
  2. GET  /visura_catastale/{id}  → poll until evasa
  3. GET  /visura_catastale/{id}/documento  → PDF bytes
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

import httpx

logger = logging.getLogger("omnia.openapi_catasto")

DEFAULT_BASE = "https://catasto.openapi.it"
DEFAULT_OAUTH = "https://oauth.openapi.com"
DEFAULT_SANDBOX_BASE = "https://test.catasto.openapi.it"
DEFAULT_SANDBOX_OAUTH = "https://test.oauth.openapi.com"

# Process-local token cache: (token, expire_epoch)
_token_cache: Tuple[Optional[str], float] = (None, 0.0)


def _truthy(name: str) -> bool:
    return (os.environ.get(name) or "").lower() in {"1", "true", "yes"}


def openapi_enabled() -> bool:
    if not _truthy("OPENAPI_ENABLED"):
        return False
    if (os.environ.get("OPENAPI_TOKEN") or "").strip():
        return True
    email = (os.environ.get("OPENAPI_EMAIL") or "").strip()
    key = (os.environ.get("OPENAPI_API_KEY") or "").strip()
    return bool(email and key)


def _base() -> str:
    return (os.environ.get("OPENAPI_CATASTO_BASE") or DEFAULT_BASE).rstrip("/")


def _oauth_base() -> str:
    explicit = (os.environ.get("OPENAPI_OAUTH_BASE") or "").strip()
    if explicit:
        return explicit.rstrip("/")
    # Infer sandbox OAuth from catasto base
    if "test.catasto" in _base():
        return DEFAULT_SANDBOX_OAUTH
    return DEFAULT_OAUTH


def _default_scopes() -> str:
    host = _base().replace("https://", "").replace("http://", "").split("/")[0]
    return f"*:{host}/*"


def _unwrap(payload: Dict[str, Any]) -> Dict[str, Any]:
    """OpenAPI wraps resources in {success, data, ...}."""
    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return payload


async def _mint_oauth_token() -> str:
    """Mint (or return cached) Bearer token from email + API key."""
    global _token_cache
    cached, expires = _token_cache
    # Refresh 60s before expiry
    if cached and time.time() < expires - 60:
        return cached

    email = (os.environ.get("OPENAPI_EMAIL") or "").strip()
    key = (os.environ.get("OPENAPI_API_KEY") or "").strip()
    if not email or not key:
        raise RuntimeError("OPENAPI_EMAIL/OPENAPI_API_KEY missing")

    scopes = (os.environ.get("OPENAPI_SCOPES") or "").strip() or _default_scopes()
    url = f"{_oauth_base()}/tokens"
    body = {"grant_type": "client_credentials", "scopes": scopes}

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            url,
            auth=(email, key),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=body,
        )
        if r.status_code >= 400:
            logger.warning("OpenAPI OAuth mint failed: %s %s", r.status_code, r.text[:300])
            raise RuntimeError(f"openapi_oauth_failed:{r.status_code}:{r.text[:200]}")
        payload = r.json()
        data = _unwrap(payload) if isinstance(payload, dict) else {}
        token = str(data.get("token") or payload.get("token") or "").strip()
        if not token:
            raise RuntimeError("openapi_oauth_empty_token")
        # Prefer expireAt from API; fallback 24h
        expire_at = data.get("expireAt") or data.get("expire_at")
        if isinstance(expire_at, str) and "T" in expire_at:
            try:
                from datetime import datetime

                # OpenAPI returns +00:00
                dt = datetime.fromisoformat(expire_at.replace("Z", "+00:00"))
                expires_epoch = dt.timestamp()
            except Exception:
                expires_epoch = time.time() + 86400
        else:
            expires_epoch = time.time() + 86400
        _token_cache = (token, expires_epoch)
        logger.info("OpenAPI OAuth token minted (expires epoch=%s)", int(expires_epoch))
        return token


async def _bearer() -> str:
    static = (os.environ.get("OPENAPI_TOKEN") or "").strip()
    if static:
        return static
    return await _mint_oauth_token()


async def _headers() -> Dict[str, str]:
    token = await _bearer()
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


async def request_visura_catastale(
    *,
    provincia: str,
    comune: str,
    foglio: str,
    particella: str,
    subalterno: Optional[str] = None,
    tipo_catasto: str = "F",  # F=fabbricati, T=terreni
    tipo_visura: str = "ordinaria",  # ordinaria | storica
    sezione: Optional[str] = None,
    richiedente: Optional[str] = None,
    formato: str = "pdf",
    callback_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a visura request. Returns unwrapped data dict (includes id, stato)."""
    body: Dict[str, Any] = {
        "entita": "immobile",
        "tipo_visura": tipo_visura,
        "provincia": provincia.strip().upper()[:2],
        "comune": comune.strip(),
        "foglio": str(foglio).strip(),
        "particella": str(particella).strip(),
        "tipo_catasto": tipo_catasto.strip().upper()[:1],
    }
    if subalterno:
        body["subalterno"] = str(subalterno).strip()
    if sezione:
        body["sezione"] = sezione
    if richiedente:
        body["richiedente"] = richiedente
    if formato:
        body["formato"] = formato
    if callback_url:
        body["callback"] = {"url": callback_url}

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{_base()}/visura_catastale",
            headers=await _headers(),
            json=body,
        )
        if r.status_code >= 400:
            logger.warning("OpenAPI visura create failed: %s %s", r.status_code, r.text[:400])
            raise RuntimeError(f"openapi_visura_create_failed:{r.status_code}:{r.text[:300]}")
        return _unwrap(r.json())


async def get_visura_status(request_id: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            f"{_base()}/visura_catastale/{request_id}",
            headers=await _headers(),
        )
        if r.status_code >= 400:
            raise RuntimeError(f"openapi_visura_status_failed:{r.status_code}:{r.text[:300]}")
        return _unwrap(r.json())


async def download_visura_document(request_id: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(
            f"{_base()}/visura_catastale/{request_id}/documento",
            headers=await _headers(),
        )
        if r.status_code >= 400:
            raise RuntimeError(f"openapi_visura_download_failed:{r.status_code}:{r.text[:300]}")
        return r.content


async def ping() -> Dict[str, Any]:
    """Mint token + list visure — proves OAuth + Catasto auth."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(f"{_base()}/visura_catastale", headers=await _headers())
        return {
            "ok": r.status_code < 400,
            "status_code": r.status_code,
            "auth": "oauth" if not (os.environ.get("OPENAPI_TOKEN") or "").strip() else "static_token",
            "base": _base(),
            "oauth_base": _oauth_base(),
            "body_preview": (r.text or "")[:200],
        }
