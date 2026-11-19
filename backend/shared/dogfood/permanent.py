"""D-175 · C3 — Base permanente Dogfood: identità, detection, gate fail-closed.

La base permanente NON è un DB di lavoro. Runtime, clone/wipe/restore ordinari
e migrazioni distruttive devono fallire se la destinazione è permanente.
L'emergenza è uno script separato (vedi scripts/dogfood_permanent_emergency_restore.py).
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from shared.dogfood.backup import (
    LOOPBACK_HOSTS,
    parse_mongo_host_port,
)

PERMANENT_DB_PREFIXES = ("omnia_df_perm", "omnia_df_permanent")
DEFAULT_PERMANENT_DB = "omnia_df_perm_main"
IDENTITY_SCHEMA = "omnia.dogfood.permanent.v1"
IDENTITY_REL = Path("permanent") / "IDENTITY.json"
MARKER_COLLECTION = "_omnia_permanent_identity"

# Ordinary ops that must never target permanent
ORDINARY_OPS = frozenset(
    {
        "runtime",
        "clone",
        "wipe",
        "restore",
        "migrate_destructive",
        "seed",
        "drop",
        "admin_ordinary",
    }
)

EMERGENCY_UNLOCK_ENV = "OMNIA_PERMANENT_UNLOCK"
EMERGENCY_PHRASE_ENV = "OMNIA_PERMANENT_AUTH_PHRASE"
EMERGENCY_CONFIRM1_ENV = "OMNIA_PERMANENT_CONFIRM_1"
EMERGENCY_CONFIRM2_ENV = "OMNIA_PERMANENT_CONFIRM_2"
REQUIRED_AUTH_PHRASE = "OMNIA FOUNDATION UNLOCK PERMANENT BASE"
REQUIRED_CONFIRM_TOKEN = "CONFIRM-PERMANENT-EMERGENCY"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dogfood_root() -> Path:
    raw = (os.environ.get("DOGFOOD_ROOT") or "").strip()
    if raw:
        return Path(raw).resolve()
    return Path(__file__).resolve().parents[3] / "dogfood"


def permanent_identity_path() -> Path:
    override = (os.environ.get("OMNIA_DOGFOOD_PERMANENT_IDENTITY") or "").strip()
    if override:
        return Path(override).resolve()
    return dogfood_root() / IDENTITY_REL


def configured_permanent_db_name() -> str:
    return (
        (os.environ.get("OMNIA_DOGFOOD_PERMANENT_DB") or "").strip()
        or DEFAULT_PERMANENT_DB
    )


def is_permanent_db_name(db_name: str | None) -> bool:
    low = (db_name or "").strip().lower()
    if not low:
        return False
    return any(low == p or low.startswith(p + "_") or low.startswith(p) for p in PERMANENT_DB_PREFIXES)


def _uri_db_name(uri: str) -> str:
    raw = (uri or "").strip()
    if not raw:
        return ""
    try:
        path = urlparse(raw if "://" in raw else f"mongodb://{raw}").path or ""
        return path.lstrip("/").split("?")[0]
    except Exception:  # noqa: BLE001
        return ""


def _uri_user(uri: str) -> str:
    raw = (uri or "").strip()
    if not raw:
        return ""
    try:
        p = urlparse(raw if "://" in raw else f"mongodb://{raw}")
        return (p.username or "").strip()
    except Exception:  # noqa: BLE001
        return ""


def load_identity() -> Optional[dict[str, Any]]:
    path = permanent_identity_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def permanent_endpoint_from_config() -> tuple[str, int, str]:
    """Return (host, port, db) for the registered permanent base.

    Fail-closed: if PERMANENT_URI is set, host/port come from it; else loopback
    dogfood port. DB name from URI path or OMNIA_DOGFOOD_PERMANENT_DB.
    """
    db = configured_permanent_db_name()
    uri = (os.environ.get("OMNIA_DOGFOOD_PERMANENT_URI") or "").strip()
    identity = load_identity() or {}
    if identity.get("db_name"):
        db = str(identity["db_name"])
    if uri:
        host, port = parse_mongo_host_port(uri)
        path_db = _uri_db_name(uri)
        if path_db and path_db.lower() not in ("admin", "local", "config"):
            db = path_db
        return host.lower(), int(port), db
    # Prefer IDENTITY endpoint
    ep = (identity.get("mongo_endpoint") or "").strip()
    if ep and ":" in ep:
        host, _, port_s = ep.rpartition(":")
        try:
            return host.lower(), int(port_s), db
        except ValueError:
            pass
    port = int((os.environ.get("OMNIA_DF_MONGO_PORT") or "27018").strip() or "27018")
    return "127.0.0.1", port, db


def matches_permanent_endpoint(uri: str) -> bool:
    """True if URI host:port equals registered permanent endpoint."""
    try:
        host, port = parse_mongo_host_port(uri)
    except RuntimeError:
        return False
    ph, pp, _ = permanent_endpoint_from_config()
    return host.lower() == ph.lower() and int(port) == int(pp)


def is_permanent_target(
    *,
    uri: str | None = None,
    db_name: str | None = None,
) -> bool:
    """Detect permanent destination by DB name and/or URI endpoint+db.

    Name alone is NOT sufficient for allow; for deny, either signal is enough.
    """
    db = (db_name or "").strip()
    if uri and not db:
        db = _uri_db_name(uri)
    if is_permanent_db_name(db):
        return True
    conf_db = configured_permanent_db_name().lower()
    if db and db.lower() == conf_db:
        return True
    identity = load_identity()
    if identity and db and db.lower() == str(identity.get("db_name") or "").lower():
        return True
    if uri:
        perm_uri = (os.environ.get("OMNIA_DOGFOOD_PERMANENT_URI") or "").strip()
        if perm_uri and uri.strip() == perm_uri:
            return True
        # Same host:port as permanent AND db path is permanent / configured
        if matches_permanent_endpoint(uri):
            path_db = _uri_db_name(uri)
            if is_permanent_db_name(path_db) or (
                path_db and path_db.lower() == conf_db
            ):
                return True
            # URI without path but caller also passed permanent db
            if db_name and is_permanent_db_name(db_name):
                return True
    return False


def is_permanent_runtime_target(*, mongo_url: str, db_name: str) -> bool:
    """Runtime must refuse permanent even with alternate credentials on same instance."""
    if is_permanent_db_name(db_name):
        return True
    if is_permanent_target(uri=mongo_url, db_name=db_name):
        return True
    # Same endpoint + permanent DB name configured while MONGO points there without path
    if mongo_url and matches_permanent_endpoint(mongo_url):
        if is_permanent_db_name(db_name) or db_name.lower() == configured_permanent_db_name().lower():
            return True
        # Exact permanent URI or user is emergency/permanent admin
        user = _uri_user(mongo_url)
        if user in ("omnia_df_emergency", "omnia_df_permanent_admin"):
            return True
    perm_uri = (os.environ.get("OMNIA_DOGFOOD_PERMANENT_URI") or "").strip()
    if perm_uri and mongo_url.strip() == perm_uri:
        return True
    return False


def assert_not_permanent_op(
    op: str,
    *,
    uri: str | None = None,
    db_name: str | None = None,
) -> None:
    """Fail-closed gate for ordinary operations against the permanent base."""
    if op not in ORDINARY_OPS:
        raise RuntimeError(f"unknown_ordinary_op:{op}")
    if is_permanent_target(uri=uri, db_name=db_name):
        raise RuntimeError(f"permanent_op_denied:{op}:{db_name or _uri_db_name(uri or '')}")


def work_copy_db_allowed(db_name: str) -> bool:
    """CLEAN / CONTINUITY / probe / c2 src — allowed ordinary work DBs."""
    low = (db_name or "").strip().lower()
    if not low.startswith("omnia_df_"):
        return False
    if is_permanent_db_name(low):
        return False
    return True


def build_identity_payload(
    *,
    instance_id: str,
    db_name: str,
    host: str,
    port: int,
    git_sha: str,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    if host.lower() not in LOOPBACK_HOSTS:
        raise RuntimeError(f"permanent_host_not_loopback:{host}")
    if int(port) == 27017:
        raise RuntimeError("permanent_port_forbidden_shared:27017")
    if not is_permanent_db_name(db_name):
        raise RuntimeError(f"permanent_db_name_invalid:{db_name}")
    payload = {
        "schema": IDENTITY_SCHEMA,
        "instance_id": instance_id,
        "db_name": db_name,
        "mongo_endpoint": f"{host}:{int(port)}",
        "created_at": _now(),
        "git_sha": git_sha,
        "cycle": "D-175-C3",
        "status": "initialized",
        "frozen": False,
        "note": "Functional seed accounts belong to C4 — not created here.",
    }
    if extra:
        payload["extra"] = extra
    return payload


def write_identity(payload: dict[str, Any]) -> Path:
    path = permanent_identity_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def require_identity_or_raise() -> dict[str, Any]:
    data = load_identity()
    if not data:
        raise RuntimeError("permanent_identity_missing")
    if data.get("schema") != IDENTITY_SCHEMA:
        raise RuntimeError("permanent_identity_schema_invalid")
    if not data.get("instance_id") or not data.get("db_name"):
        raise RuntimeError("permanent_identity_incomplete")
    if not is_permanent_db_name(str(data.get("db_name"))):
        raise RuntimeError("permanent_identity_db_invalid")
    return data


# --- Emergency unlock gates (no destructive side effects here) ---


def emergency_audit_path() -> Path:
    return dogfood_root() / "permanent" / "EMERGENCY_AUDIT.jsonl"


def append_emergency_audit(event: dict[str, Any]) -> Path:
    path = emergency_audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"ts": _now(), **event}, ensure_ascii=False)
    # Append-only: open O_APPEND
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    return path


def check_emergency_unlock_gates(
    *,
    unlock_token: str | None = None,
    auth_phrase: str | None = None,
    confirm1: str | None = None,
    confirm2: str | None = None,
    interactive: bool = False,
) -> dict[str, Any]:
    """Evaluate emergency gates. Never performs restore.

    Returns {ok, errors, gates}. Incomplete/wrong → ok False.
    """
    errors: list[str] = []
    unlock = (
        unlock_token
        if unlock_token is not None
        else (os.environ.get(EMERGENCY_UNLOCK_ENV) or "")
    ).strip()
    phrase = (
        auth_phrase
        if auth_phrase is not None
        else (os.environ.get(EMERGENCY_PHRASE_ENV) or "")
    ).strip()
    c1 = (
        confirm1
        if confirm1 is not None
        else (os.environ.get(EMERGENCY_CONFIRM1_ENV) or "")
    ).strip()
    c2 = (
        confirm2
        if confirm2 is not None
        else (os.environ.get(EMERGENCY_CONFIRM2_ENV) or "")
    ).strip()

    if not unlock:
        errors.append("unlock_missing")
    elif unlock != "1" and not re.fullmatch(r"[A-Za-z0-9_\-]{16,}", unlock):
        # Accept literal "1" for Founder one-shot OR opaque ≥16 token
        errors.append("unlock_invalid")

    if phrase != REQUIRED_AUTH_PHRASE:
        errors.append("auth_phrase_mismatch")

    if interactive:
        # Interactive path must still receive both confirms via env/args for automation tests
        pass
    if c1 != REQUIRED_CONFIRM_TOKEN:
        errors.append("confirm1_incomplete")
    if c2 != REQUIRED_CONFIRM_TOKEN:
        errors.append("confirm2_incomplete")
    if c1 and c2 and c1 == c2 == REQUIRED_CONFIRM_TOKEN:
        pass
    elif c1 != c2 and "confirm1_incomplete" not in errors and "confirm2_incomplete" not in errors:
        errors.append("confirm_mismatch")

    return {
        "ok": not errors,
        "errors": errors,
        "gates": {
            "unlock_present": bool(unlock),
            "phrase_ok": phrase == REQUIRED_AUTH_PHRASE,
            "confirm1_ok": c1 == REQUIRED_CONFIRM_TOKEN,
            "confirm2_ok": c2 == REQUIRED_CONFIRM_TOKEN,
            "required_phrase": REQUIRED_AUTH_PHRASE,
            "required_confirm": REQUIRED_CONFIRM_TOKEN,
        },
    }
