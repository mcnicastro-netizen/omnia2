"""OMNIA · Emergent Object Storage client wrapper.

Sprint 4 · GAP #1 — Migrazione foto immobili da Base64 in MongoDB
a Object Storage. Il DB conserva SOLO il path canonical (`omnia/...`),
il backend serve i bytes via `GET /api/media/{path:path}` (pubblico, foto
immobili sono pubbliche sul portale B2C).

Client one-shot init (session-scoped key). Idempotente e thread-safe.
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Optional

import requests

logger = logging.getLogger(__name__)

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "omnia"

_lock = threading.Lock()
_storage_key: Optional[str] = None


class ObjStoreError(RuntimeError):
    """Raised on object-storage failures."""


def _emergent_key() -> str:
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        raise ObjStoreError("EMERGENT_LLM_KEY not configured")
    return key


def init_storage(force: bool = False) -> str:
    """Init the storage session. Idempotent. Returns the storage key."""
    global _storage_key
    with _lock:
        if _storage_key and not force:
            return _storage_key
        resp = requests.post(
            f"{STORAGE_URL}/init",
            json={"emergent_key": _emergent_key()},
            timeout=30,
        )
        resp.raise_for_status()
        _storage_key = resp.json()["storage_key"]
        return _storage_key


def _headers(ct: Optional[str] = None) -> dict:
    key = init_storage()
    h = {"X-Storage-Key": key}
    if ct:
        h["Content-Type"] = ct
    return h


def put_object(path: str, data: bytes, content_type: str) -> dict:
    """Upload `data` at `path` (no leading slash). Returns {path,size,etag}.

    Retries once with fresh key on 403 (expired session).
    """
    for attempt in range(2):
        try:
            resp = requests.put(
                f"{STORAGE_URL}/objects/{path}",
                headers=_headers(content_type),
                data=data,
                timeout=120,
            )
            if resp.status_code == 403 and attempt == 0:
                init_storage(force=True)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            raise ObjStoreError(f"put_object failed: {e} · body={resp.text[:200]}") from e
    raise ObjStoreError("put_object: exhausted retries")


def get_object(path: str) -> tuple[bytes, str]:
    """Fetch `path`. Returns (bytes, content-type). Raises ObjStoreError on miss/error."""
    for attempt in range(2):
        try:
            resp = requests.get(
                f"{STORAGE_URL}/objects/{path}",
                headers=_headers(),
                timeout=60,
            )
        except requests.RequestException as e:
            raise ObjStoreError(f"get_object network error: {e}") from e
        if resp.status_code == 403 and attempt == 0:
            init_storage(force=True)
            continue
        if resp.status_code == 200:
            return resp.content, resp.headers.get("Content-Type", "application/octet-stream")
        # Any other status → treat as miss/failure (upstream returns 500 for
        # unknown paths). The caller (media router) maps this to 404.
        raise ObjStoreError(f"get_object status={resp.status_code} path={path}")
    raise ObjStoreError("get_object: exhausted retries")


def delete_object(path: str) -> None:
    """Emergent storage has no delete API — this is a no-op.

    Callers should soft-delete in MongoDB (mark `is_deleted=True`).
    """
    logger.info("delete_object no-op for path=%s (soft-delete in DB only)", path)
