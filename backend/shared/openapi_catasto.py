"""OpenAPI.it Catasto client — visure catastali ufficiali (D-082 path).

Auth: Bearer token from https://console.openapi.com
Docs: https://console.openapi.com/it/apis/catasto/documentation

Flow:
  1. POST /visura_catastale  → request id
  2. GET  /visura_catastale/{id}  → poll until evasa
  3. GET  /visura_catastale/{id}/documento  → PDF/XML bytes
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger("omnia.openapi_catasto")

DEFAULT_BASE = "https://catasto.openapi.it"


def openapi_enabled() -> bool:
    return (os.environ.get("OPENAPI_ENABLED") or "").lower() in {"1", "true", "yes"} and bool(
        (os.environ.get("OPENAPI_TOKEN") or "").strip()
    )


def _headers() -> Dict[str, str]:
    token = (os.environ.get("OPENAPI_TOKEN") or "").strip()
    if not token:
        raise RuntimeError("OPENAPI_TOKEN missing")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _base() -> str:
    return (os.environ.get("OPENAPI_CATASTO_BASE") or DEFAULT_BASE).rstrip("/")


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
    """Create a visura request. Returns OpenAPI response (includes id)."""
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
        r = await client.post(f"{_base()}/visura_catastale", headers=_headers(), json=body)
        if r.status_code >= 400:
            logger.warning("OpenAPI visura create failed: %s %s", r.status_code, r.text[:400])
            raise RuntimeError(f"openapi_visura_create_failed:{r.status_code}:{r.text[:300]}")
        return r.json()


async def get_visura_status(request_id: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"{_base()}/visura_catastale/{request_id}", headers=_headers())
        if r.status_code >= 400:
            raise RuntimeError(f"openapi_visura_status_failed:{r.status_code}:{r.text[:300]}")
        return r.json()


async def download_visura_document(request_id: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(
            f"{_base()}/visura_catastale/{request_id}/documento",
            headers=_headers(),
        )
        if r.status_code >= 400:
            raise RuntimeError(f"openapi_visura_download_failed:{r.status_code}:{r.text[:300]}")
        return r.content


async def ping() -> Dict[str, Any]:
    """Lightweight connectivity check — list recent visure (may be empty)."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(f"{_base()}/visura_catastale", headers=_headers())
        return {
            "ok": r.status_code < 400,
            "status_code": r.status_code,
            "body_preview": (r.text or "")[:200],
        }
