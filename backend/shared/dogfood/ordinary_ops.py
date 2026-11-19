"""D-175 C3 — Ordinary Dogfood ops gates (clone / wipe / restore / migrate).

These helpers are imported by ordinary scripts. They never unlock the permanent
base; emergency restore lives in a separate sealed script.
"""
from __future__ import annotations

from typing import Any, Optional

from shared.dogfood.permanent import (
    assert_not_permanent_op,
    is_permanent_target,
    work_copy_db_allowed,
)


def deny_if_permanent_target(op: str, *, uri: str | None = None, db_name: str | None = None) -> None:
    assert_not_permanent_op(op, uri=uri, db_name=db_name)


def assert_work_copy_target(db_name: str, *, op: str = "clone") -> str:
    name = (db_name or "").strip()
    if not work_copy_db_allowed(name):
        if is_permanent_target(db_name=name):
            raise RuntimeError(f"permanent_op_denied:{op}:{name}")
        raise RuntimeError(f"work_copy_db_invalid:{name}")
    return name


def ordinary_restore_allowed(*, uri: str, target_db: str) -> dict[str, Any]:
    """Probe/work-copy restore only — permanent always denied."""
    try:
        deny_if_permanent_target("restore", uri=uri, db_name=target_db)
        assert_work_copy_target(target_db, op="restore")
        return {"ok": True, "target_db": target_db}
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}


def ordinary_wipe_allowed(*, uri: str, db_name: str) -> dict[str, Any]:
    try:
        deny_if_permanent_target("wipe", uri=uri, db_name=db_name)
        assert_work_copy_target(db_name, op="wipe")
        return {"ok": True, "db_name": db_name}
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}


def ordinary_clone_allowed(*, source_uri: str, target_db: str) -> dict[str, Any]:
    """Clone destination must never be permanent. Source may be permanent (read)."""
    try:
        # Only the TARGET is gated — reading permanent for CLEAN is allowed later (C4).
        deny_if_permanent_target("clone", db_name=target_db)
        assert_work_copy_target(target_db, op="clone")
        _ = source_uri  # reserved for future source-endpoint checks
        return {"ok": True, "target_db": target_db}
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}


def ordinary_migrate_destructive_allowed(*, uri: str, db_name: str) -> dict[str, Any]:
    try:
        deny_if_permanent_target("migrate_destructive", uri=uri, db_name=db_name)
        assert_work_copy_target(db_name, op="migrate_destructive")
        return {"ok": True, "db_name": db_name}
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}
