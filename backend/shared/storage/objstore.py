"""OMNIA object storage — local filesystem (default) or Emergent (legacy).

STORAGE_BACKEND=local|emergent (default: local)
LOCAL_STORAGE_ROOT=backend/.media (default)
"""
from __future__ import annotations

import logging
import mimetypes
import os
import threading
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "omnia"

_lock = threading.Lock()
_storage_key: Optional[str] = None


class ObjStoreError(RuntimeError):
    """Raised on object-storage failures."""


def _backend() -> str:
    return (os.environ.get("STORAGE_BACKEND") or "local").strip().lower()


def _local_root() -> Path:
    raw = os.environ.get("LOCAL_STORAGE_ROOT")
    if raw:
        root = Path(raw)
    else:
        root = Path(__file__).resolve().parents[2] / ".media"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _emergent_key() -> str:
    key = (
        os.environ.get("EMERGENT_LLM_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    if not key:
        raise ObjStoreError("EMERGENT_LLM_KEY not configured (emergent storage backend)")
    return key


def init_storage(force: bool = False) -> str:
    """Init storage session. Local backend returns 'local'."""
    if _backend() == "local":
        _local_root()
        return "local"

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
    path = path.lstrip("/")
    if _backend() == "local":
        dest = _local_root() / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return {"path": path, "size": len(data), "etag": f"local-{len(data)}"}

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
    path = path.lstrip("/")
    if _backend() == "local":
        dest = _local_root() / path
        if not dest.is_file():
            raise ObjStoreError(f"get_object miss path={path}")
        ct = mimetypes.guess_type(str(dest))[0] or "application/octet-type"
        if ct == "application/octet-type":
            ct = "application/octet-stream"
        return dest.read_bytes(), ct

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
        raise ObjStoreError(f"get_object status={resp.status_code} path={path}")
    raise ObjStoreError("get_object: exhausted retries")


def delete_object(path: str) -> None:
    path = path.lstrip("/")
    if _backend() == "local":
        dest = _local_root() / path
        if dest.is_file():
            dest.unlink()
        return
    logger.info("delete_object no-op for emergent path=%s", path)
