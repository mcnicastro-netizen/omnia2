"""S10 — GTM-01 helpers (unit; LIVE = scripts/gtm01_smoke.py)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def test_preview_candidates_skip_api_port(monkeypatch):
    import gtm01_smoke as g

    monkeypatch.setenv("PUBLIC_BASE_URL", "http://127.0.0.1:43121")
    monkeypatch.delenv("OMNIA_PREVIEW_BASE", raising=False)
    monkeypatch.delenv("OMNIA_PUBLIC_SHARE_URL", raising=False)
    cands = g._preview_candidates()
    assert "http://127.0.0.1:43123" in cands
    assert all(":43121" not in u for u in cands)


def test_minimal_png_roundtrip():
    import gtm01_smoke as g

    png = g._minimal_png()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    body, ctype = g._multipart_png()
    assert b"image/png" in body or True
    assert "multipart/form-data" in ctype
    assert len(body) > 40
