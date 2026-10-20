"""Live: Brand Studio iframe needs SAMEORIGIN on /api/p/{slug}/."""
from __future__ import annotations

import os

import pytest
import requests

BASE = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or os.environ.get("OMNIA_API_BASE")
    or "http://127.0.0.1:43121"
).rstrip("/")
if not BASE.startswith("http"):
    BASE = "http://127.0.0.1:43121"


@pytest.mark.skipif(os.environ.get("OMNIA_SKIP_LIVE_MONGO") == "1", reason="live off")
def test_public_site_x_frame_sameorigin():
    r = requests.get(f"{BASE}/api/p/nicastroimmobiliare/", timeout=20)
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    xfo = (r.headers.get("X-Frame-Options") or r.headers.get("x-frame-options") or "").upper()
    assert xfo == "SAMEORIGIN", f"expected SAMEORIGIN got {xfo!r}"


@pytest.mark.skipif(os.environ.get("OMNIA_SKIP_LIVE_MONGO") == "1", reason="live off")
def test_api_default_still_deny_frame():
    r = requests.get(f"{BASE}/api/app/website/themes", timeout=10)
    # unauth → 401/403 but headers still applied
    xfo = (r.headers.get("X-Frame-Options") or r.headers.get("x-frame-options") or "").upper()
    assert xfo == "DENY"
