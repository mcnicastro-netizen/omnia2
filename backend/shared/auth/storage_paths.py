"""OMNIA — Object Storage path AuthZ helpers (D-095 / Onda 6).

After Mongo is scoped to agency/property, still refuse to serve a blob whose
`storage_path` does not match the expected tenant prefix (spoofed DB field /
copy-paste across tenants).
"""
from __future__ import annotations

from fastapi import HTTPException


def normalize_storage_path(path: str) -> str:
    return (path or "").lstrip("/")


def assert_storage_under_prefix(path: str, prefix: str, *, detail: str = "not_found") -> str:
    """Return normalized path or 404 if outside prefix / traversal."""
    norm = normalize_storage_path(path)
    pref = normalize_storage_path(prefix)
    if not pref.endswith("/"):
        pref = pref + "/"
    if not norm or ".." in norm or not norm.startswith(pref):
        raise HTTPException(status_code=404, detail=detail)
    return norm


def fascicolo_prefix(property_id: str) -> str:
    return f"omnia/fascicolo/{property_id}/"


def modulistica_prefix(agency_id: str) -> str:
    return f"omnia/modulistica/{agency_id}/"
