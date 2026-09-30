"""O2–O4 unit checks — D-111 frozen · D-105 bak health · D-109 plans SoT."""
from __future__ import annotations

import json
from pathlib import Path

from shared.models.client_request import RequestStatus
from apps.immoweb.backup_job import _status_from_report, read_latest_backup_health
from apps.billing.plans import get_active_catalog, LAUNCH_PLANS


def test_request_status_includes_frozen():
    assert "frozen" in RequestStatus.__args__  # type: ignore[attr-defined]


def test_backup_status_ok_partial_failed(tmp_path, monkeypatch):
    report_ok = {
        "ok": True,
        "collections": {"agencies": 1, "clients": 0},
        "media_copied": True,
    }
    # force media root missing so media_copied False still OK when root absent
    monkeypatch.setattr("apps.immoweb.backup_job.MEDIA_ROOT", tmp_path / "no-media")
    assert _status_from_report(report_ok) == "OK"

    report_partial = {
        "ok": False,
        "collections": {"agencies": 1, "clients": {"error": "x"}},
        "media_copied": True,
    }
    assert _status_from_report(report_partial) == "PARTIAL"

    # all collections error → FAILED
    from apps.immoweb import backup_job as bj
    report_fail = {
        "ok": False,
        "collections": {n: {"error": "e"} for n in bj._COLLECTIONS},
        "media_error": "boom",
    }
    assert _status_from_report(report_fail) == "FAILED"


def test_read_latest_backup_health(tmp_path, monkeypatch):
    monkeypatch.setattr("apps.immoweb.backup_job.BACKUP_ROOT", tmp_path)
    assert read_latest_backup_health()["status"] == "MISSING"
    day = tmp_path / "2026-09-30"
    day.mkdir()
    (day / "MANIFEST.json").write_text(
        json.dumps({
            "created_at": "2026-09-30T03:15:00+00:00",
            "status": "OK",
            "retention_days": 30,
            "report": {"ok": True, "day": "2026-09-30", "collections": {}, "media_copied": False},
        }),
        encoding="utf-8",
    )
    h = read_latest_backup_health()
    assert h["status"] == "OK"
    assert h["day"] == "2026-09-30"


def test_billing_plans_catalog_sot():
    cat = get_active_catalog()
    assert set(cat.keys()) == {"starter", "pro", "agency"}
    assert cat["starter"].price_monthly == LAUNCH_PLANS["starter"].price_monthly
    assert cat["pro"].price_monthly == 99.0
    assert cat["agency"].price_monthly == 299.0
