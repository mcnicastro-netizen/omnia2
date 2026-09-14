"""OMNIA · Media (Object Storage passthrough).

Sprint 4 · GAP #1 — Serve i binari immagine caricati su Emergent Object Storage.
Rotte:
- `GET /api/media/{path:path}` — PUBBLICO (le foto immobili sono pubbliche sul
  portale B2C). Non richiede auth. Restituisce i bytes con content-type
  originale.

Il DB conserva SOLO l'url relativa `/api/media/{path}`.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from shared.storage import get_object, ObjStoreError

router = APIRouter(prefix="/media", tags=["media"])
logger = logging.getLogger(__name__)


@router.get("/{path:path}")
async def serve_media(path: str) -> Response:
    if not path or ".." in path:
        raise HTTPException(status_code=400, detail="invalid_path")
    try:
        data, ct = get_object(path)
    except ObjStoreError as e:
        logger.warning("media miss path=%s err=%s", path, e)
        raise HTTPException(status_code=404, detail="not_found") from e
    return Response(
        content=data,
        media_type=ct,
        headers={"Cache-Control": "public, max-age=86400"},
    )
