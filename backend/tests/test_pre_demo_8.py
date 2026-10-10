"""Pre-demo ≥8 — off-box sync + trash helpers (unit)."""
from __future__ import annotations

import json
from pathlib import Path


def test_offbox_sync_roundtrip(tmp_path, monkeypatch):
    from apps.immoweb import offbox_backup as ob

    hot = tmp_path / "hot"
    off = tmp_path / "off"
    day = "2026-10-10"
    src = hot / day
    src.mkdir(parents=True)
    (src / "agencies.jsonl").write_text(
        json.dumps({"id": "demo-agency-001"}) + "\n", encoding="utf-8"
    )
    (src / "MANIFEST.json").write_text(
        json.dumps({"status": "OK", "created_at": "2026-10-10T10:00:00+00:00"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(ob, "BACKUP_ROOT", hot)
    monkeypatch.setattr(ob, "OFFBOX_ROOT", off)

    report = ob.sync_day_to_offbox(day)
    assert report["ok"] is True
    assert (off / day / "MANIFEST.json").is_file()
    health = ob.read_offbox_health()
    assert health["day"] == day
    assert health["status"] == "OK"


def test_mls_shareable_excludes_trash_shape():
    from apps.immoweb.mls import _shareable_listing_clause

    q = _shareable_listing_clause()
    assert "$and" in q
    # not_trashed clause present
    blob = json.dumps(q)
    assert "deleted_at" in blob


def test_dashboard_kpi_uses_trash_helper():
    import inspect
    from apps.immoweb import dashboard as d

    assert "with_not_trashed" in inspect.getsource(d.get_kpis)
