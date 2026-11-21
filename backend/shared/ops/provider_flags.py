"""Kill-switch persistente per fornitori esterni (Cabina · Onda 2).

Mongo ``provider_flags`` + mirror in-memory su circuit holds.

D-175 PRE-C (DEF-03/04/05):
- Persistent SoT is Mongo (or test file override for multi-process local tests).
- ``send_email`` must re-read SoT before transport (see ``shared.email.client``).
- Boot in staging/dogfood fails closed if holds cannot be loaded.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from shared.db.connection import Database
from shared.security import circuit as circuit_mod

logger = logging.getLogger("omnia.provider_flags")

KNOWN = ("resend", "fal", "gemini", "llm", "stripe", "openai", "tavily", "mongodb")

# File-backed SoT for local multi-process tests (never used in prod).
# Set OMNIA_PROVIDER_KILL_FILE=/tmp/....json with {"resend": true}
_KILL_FILE_ENV = "OMNIA_PROVIDER_KILL_FILE"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fail_closed_env() -> bool:
    """Environments where unreadable kill SoT must block sends / block boot."""
    env = (os.environ.get("OMNIA_ENV") or "").strip().lower()
    if env in ("dogfood", "staging", "stage"):
        return True
    if (os.environ.get("OMNIA_PROVIDER_KILL_FAIL_CLOSED") or "").strip() == "1":
        return True
    return False


def env_resend_killed() -> bool:
    """Railway/env belt: shared by all processes after redeploy."""
    return (os.environ.get("OMNIA_RESEND_KILLED") or "").strip() in ("1", "true", "TRUE", "yes")


def _db_raw():
    """Prefer raw DB (provider_flags is not tenant-scoped)."""
    try:
        return Database.get_raw()
    except Exception:
        return Database.get()


def _read_kill_file() -> Tuple[Optional[bool], Optional[str]]:
    """Return (killed, error) from test kill file if configured."""
    path = (os.environ.get(_KILL_FILE_ENV) or "").strip()
    if not path:
        return None, None
    try:
        raw = Path(path).read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            return None, "kill_file_not_object"
        if "resend" not in data:
            return False, None
        return bool(data.get("resend")), None
    except FileNotFoundError:
        return None, "kill_file_missing"
    except Exception as e:  # noqa: BLE001
        return None, f"kill_file_error:{type(e).__name__}"


async def read_resend_killed_persistent() -> Tuple[Optional[bool], Optional[str]]:
    """Authoritative persistent kill for Resend.

    Returns:
        (True/False, None) on success
        (None, error_code) when SoT cannot be read
    """
    file_val, file_err = _read_kill_file()
    if file_err:
        return None, file_err
    if file_val is not None and (os.environ.get(_KILL_FILE_ENV) or "").strip():
        # Explicit file mode (even False) short-circuits Mongo for tests
        return file_val, None

    # Unit-test processes often have no Mongo; memory/env belts still apply.
    # A missing client is not a SoT read failure — fail-closed applies when a
    # connected client errors mid-query.
    if getattr(Database, "_db", None) is None and getattr(Database, "_client", None) is None:
        return False, None

    try:
        db = _db_raw()
        doc = await db.provider_flags.find_one({"id": "resend"}, {"_id": 0, "killed": 1})
        if not doc:
            return False, None
        return bool(doc.get("killed")), None
    except Exception as e:  # noqa: BLE001
        logger.exception("read_resend_killed_persistent failed")
        return None, f"mongo_error:{type(e).__name__}"


async def resend_must_block_send() -> Tuple[bool, str]:
    """Pre-transport decision helper.

    Returns (must_block, reason).
    Linearization point for persistent kill: caller must invoke this immediately
    before ``resend.Emails.send``. In-flight sends that already passed this check
    may still complete (see D175 post-forensic report).
    """
    if env_resend_killed():
        return True, "env_OMNIA_RESEND_KILLED"
    killed, err = await read_resend_killed_persistent()
    if err is not None:
        if fail_closed_env():
            return True, f"persistent_unreadable_fail_closed:{err}"
        # Production: do not invent kill; rely on memory hold / other gates
        return False, f"persistent_unreadable_open:{err}"
    if killed:
        return True, "provider_flags_resend_killed"
    return False, "persistent_clear"


async def load_holds_into_circuit(*, raise_on_error: Optional[bool] = None) -> int:
    """All'avvio API: ripristina kill-switch da Mongo → circuit holds.

    When ``raise_on_error`` is True (default in staging/dogfood via fail_closed_env),
    load failure aborts startup instead of returning 0.
    """
    if raise_on_error is None:
        raise_on_error = fail_closed_env()
    try:
        db = _db_raw()
        docs = await db.provider_flags.find({"killed": True}, {"_id": 0, "id": 1}).to_list(
            length=50
        )
        n = 0
        for d in docs:
            pid = (d.get("id") or "").strip()
            if not pid:
                continue
            circuit_mod.force_hold(pid)
            if pid == "gemini":
                circuit_mod.force_hold("llm")
            n += 1
        if n:
            logger.warning("provider kill-switches restored: %s", n)
        # Env belt
        if env_resend_killed():
            circuit_mod.force_hold("resend", "OMNIA_RESEND_KILLED")
        return n
    except Exception as e:  # noqa: BLE001
        logger.exception("load_holds_into_circuit failed")
        if raise_on_error:
            raise RuntimeError(f"provider_flags_load_failed:{type(e).__name__}") from e
        return 0


async def list_flags() -> List[Dict[str, Any]]:
    db = _db_raw()
    docs = await db.provider_flags.find({}, {"_id": 0}).to_list(length=50)
    by_id = {d["id"]: d for d in docs if d.get("id")}
    out = []
    for pid in KNOWN:
        d = by_id.get(pid) or {"id": pid, "killed": False}
        out.append(
            {
                "id": pid,
                "killed": bool(d.get("killed")),
                "updated_at": d.get("updated_at"),
                "updated_by_email": d.get("updated_by_email"),
                "note": d.get("note") or "",
                "held": circuit_mod.is_held(pid) or (pid == "gemini" and circuit_mod.is_held("llm")),
            }
        )
    return out


async def set_killed(
    provider_id: str,
    *,
    killed: bool,
    user: Optional[dict] = None,
    note: str = "",
) -> Dict[str, Any]:
    """Persist kill then update local memory.

    Linearization for *new* sends on other processes: Mongo (or kill file) write
    completes before this returns. Other processes that re-read SoT after this
    write must block. Local ``force_hold`` only affects *this* process.
    """
    pid = (provider_id or "").strip().lower()
    if pid not in KNOWN:
        raise ValueError("unknown_provider")
    now = _now()
    doc = {
        "id": pid,
        "killed": bool(killed),
        "updated_at": now,
        "updated_by": (user or {}).get("id"),
        "updated_by_email": (user or {}).get("email"),
        "note": (note or "").strip()[:500],
    }

    # Test file SoT (multi-process local)
    kill_path = (os.environ.get(_KILL_FILE_ENV) or "").strip()
    if kill_path:
        p = Path(kill_path)
        try:
            cur = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        except Exception:
            cur = {}
        if not isinstance(cur, dict):
            cur = {}
        cur[pid] = bool(killed)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(cur) + "\n", encoding="utf-8")
        tmp.replace(p)
    else:
        db = _db_raw()
        await db.provider_flags.update_one({"id": pid}, {"$set": doc}, upsert=True)

    if killed:
        circuit_mod.force_hold(pid)
        if pid == "gemini":
            circuit_mod.force_hold("llm")
    else:
        circuit_mod.clear_hold(pid)
        if pid == "gemini":
            circuit_mod.clear_hold("llm")
    logger.warning(
        "provider_flag id=%s killed=%s by=%s",
        pid,
        killed,
        (user or {}).get("email"),
    )
    return doc
