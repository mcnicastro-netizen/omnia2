"""O2–O4 unit checks — D-111 frozen · D-105 bak health · D-109 plans SoT · S2 bak O0."""
from __future__ import annotations

import json
import os
from pathlib import Path

from shared.models.client_request import RequestStatus
from apps.immoweb.backup_job import (
    BACKUP_RETENTION_DAYS,
    _purge_old_backups,
    _status_from_report,
    backup_media_tree,
    read_latest_backup_health,
)
from apps.billing.plans import get_active_catalog, LAUNCH_PLANS


def test_request_status_includes_frozen():
    assert "frozen" in RequestStatus.__args__  # type: ignore[attr-defined]


def test_backup_retention_default_is_o0_seven():
    """S2 / O0: source default hot retention is 7 (not 30 as-is)."""
    src = (Path(__file__).resolve().parents[1] / "apps/immoweb" / "backup_job.py").read_text(
        encoding="utf-8"
    )
    assert 'BACKUP_RETENTION_DAYS") or "7"' in src
    # Runtime follows env-or-7
    assert BACKUP_RETENTION_DAYS == int(os.environ.get("BACKUP_RETENTION_DAYS") or "7")


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
            "retention_days": 7,
            "report": {"ok": True, "day": "2026-09-30", "collections": {}, "media_copied": False},
        }),
        encoding="utf-8",
    )
    h = read_latest_backup_health()
    assert h["status"] == "OK"
    assert h["day"] == "2026-09-30"


def test_purge_respects_retention_seven(tmp_path, monkeypatch):
    from datetime import datetime, timezone, timedelta
    import apps.immoweb.backup_job as bj

    monkeypatch.setattr(bj, "BACKUP_ROOT", tmp_path)
    monkeypatch.setattr(bj, "BACKUP_RETENTION_DAYS", 7)
    today = datetime.now(timezone.utc).date()
    keep = today - timedelta(days=3)
    drop = today - timedelta(days=10)
    for d in (keep, drop):
        p = tmp_path / d.isoformat()
        p.mkdir()
        (p / "MANIFEST.json").write_text("{}", encoding="utf-8")
    purged = _purge_old_backups()
    assert drop.isoformat() in purged
    assert keep.isoformat() not in purged
    assert (tmp_path / keep.isoformat()).is_dir()
    assert not (tmp_path / drop.isoformat()).exists()


def test_media_incremental_hardlinks(tmp_path, monkeypatch):
    import apps.immoweb.backup_job as bj

    media = tmp_path / "live"
    bak = tmp_path / "bak"
    media.mkdir()
    bak.mkdir()
    (media / "a.bin").write_bytes(b"x" * 4096)
    monkeypatch.setattr(bj, "MEDIA_ROOT", media)
    monkeypatch.setattr(bj, "BACKUP_ROOT", bak)

    d1 = bak / "2026-10-01"
    d1.mkdir()
    s1, ok1 = backup_media_tree("2026-10-01", d1)
    assert ok1 and s1["mode"] == "full_copytree"
    assert s1["files_copied"] == 1

    # day 2: unchanged file → hardlink
    d2 = bak / "2026-10-02"
    d2.mkdir()
    s2, ok2 = backup_media_tree("2026-10-02", d2)
    assert ok2 and s2["mode"] == "incremental_hardlink"
    assert s2["files_hardlinked"] == 1
    assert s2["files_copied"] == 0
    f1 = d1 / "media" / "a.bin"
    f2 = d2 / "media" / "a.bin"
    assert f1.stat().st_ino == f2.stat().st_ino

    # day 3: mutate size → copy new inode (mtime-only same-second would be ambiguous)
    (media / "a.bin").write_bytes(b"y" * 8192)
    d3 = bak / "2026-10-03"
    d3.mkdir()
    s3, ok3 = backup_media_tree("2026-10-03", d3)
    assert ok3 and s3["mode"] == "incremental_hardlink"
    assert s3["files_copied"] == 1
    assert (d3 / "media" / "a.bin").stat().st_ino != f2.stat().st_ino
    assert (d3 / "media" / "a.bin").read_bytes() == b"y" * 8192


def test_billing_plans_catalog_sot():
    cat = get_active_catalog()
    assert set(cat.keys()) == {"starter", "pro", "agency"}
    assert cat["starter"].price_monthly == LAUNCH_PLANS["starter"].price_monthly
    assert cat["pro"].price_monthly == 99.0
    assert cat["agency"].price_monthly == 299.0
