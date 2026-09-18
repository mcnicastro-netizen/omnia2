"""OMNIA · Media (Object Storage passthrough).

Sprint 4 · GAP #1 — Serve i binari caricati su Object Storage (foto + video).
Rotte:
- `GET /api/media/{path:path}` — PUBBLICO (media immobili sul portale B2C).
  Supporta Range (206) per playback HTML5 video.

Il DB conserva SOLO l'url relativa `/api/media/{path}`.
"""
from __future__ import annotations

import logging
import re

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from shared.storage import get_object, ObjStoreError

router = APIRouter(prefix="/media", tags=["media"])
logger = logging.getLogger(__name__)

_RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


@router.get("/{path:path}")
async def serve_media(path: str, request: Request) -> Response:
    if not path or ".." in path:
        raise HTTPException(status_code=400, detail="invalid_path")
    try:
        data, ct = get_object(path)
    except ObjStoreError as e:
        logger.warning("media miss path=%s err=%s", path, e)
        raise HTTPException(status_code=404, detail="not_found") from e

    size = len(data)
    headers = {
        "Cache-Control": "public, max-age=86400",
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
