"""OMNIA · Media (Object Storage passthrough).

Sprint 4 · GAP #1 — Serve i binari caricati su Object Storage (foto + video).
Rotte:
- `GET /api/media/{path:path}` — PUBBLICO solo per media destinati a pubblicazione
  (foto/video listing). Supporta Range (206) per playback HTML5 video.

D-095 / O1a — path sensibili (fascicolo, modulistica) NON sono serviti qui.
Accesso solo tramite endpoint autenticati (es. fascicolo download).

P-009 — `omnia/private/{user_id}/…` (foto annunci B2C) richiede sessione del
proprietario (o super_admin). Anon → 404 (non rivelare esistenza).
Il portale pubblico serve le foto via `/api/public/property/{pid}/photo/{idx}`.

Il DB conserva SOLO l'url relativa `/api/media/{path}`.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from shared.auth.dependencies import get_optional_user
from shared.storage import get_object, ObjStoreError

router = APIRouter(prefix="/media", tags=["media"])
logger = logging.getLogger(__name__)

_RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")

# D-095 — never served on this public passthrough
_BLOCKED_PREFIXES = (
    "omnia/fascicolo/",
    "omnia/modulistica/",
)

# P-009 — owner-scoped private B2C uploads
_B2C_PRIVATE_RE = re.compile(r"^omnia/private/([^/]+)/")


def _normalize_path(path: str) -> str:
    return (path or "").lstrip("/")


def _is_blocked_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in _BLOCKED_PREFIXES)


def _b2c_private_owner_id(path: str) -> Optional[str]:
    m = _B2C_PRIVATE_RE.match(path)
    return m.group(1) if m else None


def _can_read_b2c_private(user: Optional[dict], owner_id: str) -> bool:
    if not user or not owner_id:
        return False
    if user.get("role") == "super_admin":
        return True
    return user.get("id") == owner_id


@router.get("/{path:path}")
async def serve_media(path: str, request: Request) -> Response:
    if not path or ".." in path:
        raise HTTPException(status_code=400, detail="invalid_path")
    path = _normalize_path(path)

    if _is_blocked_path(path):
        # 404: non rivelare esistenza; AuthZ via fascicolo/modulistica download
        raise HTTPException(status_code=404, detail="not_found")

    owner_id = _b2c_private_owner_id(path)
    if owner_id:
        user = await get_optional_user(request)
        if not _can_read_b2c_private(user, owner_id):
            raise HTTPException(status_code=404, detail="not_found")

    try:
        data, ct = get_object(path)
    except ObjStoreError as e:
        logger.warning("media miss path=%s err=%s", path, e)
        raise HTTPException(status_code=404, detail="not_found") from e

    size = len(data)
    cache = "private, max-age=3600" if owner_id else "public, max-age=86400"
    headers = {
        "Cache-Control": cache,
        "Accept-Ranges": "bytes",
        "Content-Length": str(size),
    }

    range_header = request.headers.get("range")
    if range_header:
        m = _RANGE_RE.match(range_header.strip())
        if not m:
            raise HTTPException(status_code=416, detail="invalid_range")
        start_s, end_s = m.group(1), m.group(2)
        start = int(start_s) if start_s else 0
        end = int(end_s) if end_s else size - 1
        if start < 0 or end < start or start >= size:
            raise HTTPException(status_code=416, detail="invalid_range")
        end = min(end, size - 1)
        chunk = data[start : end + 1]
        headers["Content-Length"] = str(len(chunk))
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
        return Response(content=chunk, status_code=206, media_type=ct, headers=headers)

    return Response(content=data, media_type=ct, headers=headers)
