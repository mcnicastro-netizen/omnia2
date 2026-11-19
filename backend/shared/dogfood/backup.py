"""D-175 C2 — Dogfood backup / restore (isolated; never permanent).

Manifest never stores passwords, tokens, or credential-bearing URIs.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse, urlunparse

from apps.immoweb.backup_scope import DOGFOOD_BACKUP_COLLECTIONS

logger = logging.getLogger("omnia.dogfood.backup")

FORBIDDEN_TARGET_DB = frozenset(
    {
        "omnia",
        "omnia_prod",
        "omnia-production",
        "production",
        "prod",
        "admin",
        "local",
        "omnia_local",
        "test",
    }
)

PERMANENT_DB_PREFIXES = ("omnia_df_perm", "omnia_df_permanent")
PROBE_DB_PREFIX = "omnia_df_probe"
SOURCE_DB_PREFIX = "omnia_df_"

# Shared Cloud / default mongod — never authorized for Dogfood backup/restore,
# even if OMNIA_DF_MONGO_PORT or OMNIA_DOGFOOD_MONGO_ENDPOINTS tries to opt in.
FORBIDDEN_MONGO_PORTS = frozenset({27017})
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_sha() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(Path(__file__).resolve().parents[3]),
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def redact_mongo_uri(uri: str) -> str:
    """Strip userinfo from Mongo URI for manifests."""
    raw = (uri or "").strip()
    if not raw:
        return ""
    try:
        if "://" not in raw:
            return "mongodb://[redacted-host]"
        p = urlparse(raw)
        host = p.hostname or ""
        port = f":{p.port}" if p.port else ""
        path = p.path or ""
        return f"{p.scheme}://{host}{port}{path}"
    except Exception:  # noqa: BLE001
        return "mongodb://[unparseable]"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_tree(root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    if not root.exists():
        return {"file_count": 0, "bytes": 0, "files": [], "tree_sha256": hashlib.sha256(b"").hexdigest()}
    digest = hashlib.sha256()
    total = 0
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(root)).replace("\\", "/")
        file_sha = sha256_file(p)
        size = p.stat().st_size
        total += size
        files.append({"path": rel, "bytes": size, "sha256": file_sha})
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_sha.encode("ascii"))
        digest.update(b"\0")
        digest.update(str(size).encode("ascii"))
        digest.update(b"\n")
    return {
        "file_count": len(files),
        "bytes": total,
        "files": files,
        "tree_sha256": digest.hexdigest(),
    }


def assert_safe_db_name(db_name: str, *, role: str) -> str:
    """role: source | target_probe | deny_check"""
    name = (db_name or "").strip()
    if not name:
        raise RuntimeError("db_name_missing")
    low = name.lower()
    if low in FORBIDDEN_TARGET_DB:
        raise RuntimeError(f"db_forbidden_shared:{name}")
    if any(low.startswith(p) for p in PERMANENT_DB_PREFIXES):
        raise RuntimeError(f"db_forbidden_permanent:{name}")
    if role == "target_probe":
        if not low.startswith(PROBE_DB_PREFIX):
            raise RuntimeError(f"restore_target_must_be_probe:{name}")
    if role == "source":
        if not low.startswith(SOURCE_DB_PREFIX):
            raise RuntimeError(f"source_must_be_dogfood_prefix:{name}")
        if low.startswith(PROBE_DB_PREFIX):
            raise RuntimeError(f"source_must_not_be_probe:{name}")
    return name


def assert_dogfood_mongo_port(port: int) -> int:
    """Hard-deny shared Cloud mongod port — not overridable by env allowlist."""
    p = int(port)
    if p in FORBIDDEN_MONGO_PORTS:
        raise RuntimeError(f"mongo_port_forbidden_shared:{p}")
    if p <= 0 or p > 65535:
        raise RuntimeError(f"mongo_port_invalid:{p}")
    return p


def assert_dogfood_mongo_host(host: str) -> str:
    h = (host or "").strip().lower()
    if h not in LOOPBACK_HOSTS:
        raise RuntimeError(f"mongo_host_not_loopback:{h}")
    return h


def authorized_dogfood_mongo_endpoints() -> set[tuple[str, int]]:
    """Fail-closed allowlist of (host, port) for Dogfood backup/restore.

    Default: loopback on ``OMNIA_DF_MONGO_PORT`` (27018).
    Override: ``OMNIA_DOGFOOD_MONGO_ENDPOINTS=127.0.0.1:27018,localhost:27018``

    Port **27017** and non-loopback hosts are **always** rejected — even if
    listed in the override or selected via ``OMNIA_DF_MONGO_PORT``.
    """
    raw = (os.environ.get("OMNIA_DOGFOOD_MONGO_ENDPOINTS") or "").strip()
    out: set[tuple[str, int]] = set()
    if raw:
        for part in raw.replace(";", ",").split(","):
            part = part.strip().lower()
            if not part:
                continue
            if ":" in part:
                host, _, port_s = part.rpartition(":")
                try:
                    port = int(port_s)
                except ValueError as e:
                    raise RuntimeError(f"mongo_endpoint_invalid:{part}") from e
                host = assert_dogfood_mongo_host(host.strip())
                port = assert_dogfood_mongo_port(port)
                out.add((host, port))
            else:
                raise RuntimeError(f"mongo_endpoint_missing_port:{part}")
        if not out:
            raise RuntimeError("mongo_endpoint_allowlist_empty")
        return out
    port = assert_dogfood_mongo_port(
        int((os.environ.get("OMNIA_DF_MONGO_PORT") or "27018").strip() or "27018")
    )
    return {("127.0.0.1", port), ("localhost", port), ("::1", port)}


def parse_mongo_host_port(uri: str) -> tuple[str, int]:
    raw = (uri or "").strip()
    if not raw:
        raise RuntimeError("mongo_uri_missing")
    try:
        p = urlparse(raw if "://" in raw else f"mongodb://{raw}")
    except Exception as e:  # noqa: BLE001
        raise RuntimeError("mongo_uri_unparseable") from e
    host = (p.hostname or "").lower()
    if not host:
        raise RuntimeError("mongo_uri_host_missing")
    # mongodb://host/db with no port → 27017; Dogfood must be explicit
    port = p.port if p.port is not None else 27017
    return host, int(port)


def assert_dogfood_mongo_endpoint(uri: str) -> tuple[str, int]:
    """Ensure URI targets the authorized Dogfood Mongo instance (host+port).

    Also denies permanent URI equality and forbidden DB names in the path.
    Probe DB name alone is NOT sufficient isolation — endpoint must match.
    Shared port 27017 and non-loopback hosts are hard-denied.
    """
    perm = (os.environ.get("OMNIA_DOGFOOD_PERMANENT_URI") or "").strip()
    if perm and uri.strip() == perm:
        raise RuntimeError("uri_is_permanent_forbidden")

    host, port = parse_mongo_host_port(uri)
    # Absolute bans before allowlist (misconfig of OMNIA_DF_MONGO_PORT=27017)
    assert_dogfood_mongo_host(host)
    assert_dogfood_mongo_port(port)
    allowed = authorized_dogfood_mongo_endpoints()
    if (host, port) not in allowed:
        raise RuntimeError(f"mongo_endpoint_not_allowed:{host}:{port}")

    # Refuse if URI path/db suggests permanent or shared app DB.
    # Ignore Mongo system DBs used only as authSource (admin/local/config).
    try:
        path = urlparse(uri if "://" in uri else f"mongodb://{uri}").path or ""
        db = path.lstrip("/").split("?")[0]
        if db and db.lower() not in ("admin", "local", "config", ""):
            assert_safe_db_name(db, role="deny_check")
    except RuntimeError:
        raise
    except Exception:  # noqa: BLE001
        pass
    return host, port


# Back-compat alias used by early C2 call sites
def assert_not_permanent_uri(uri: str) -> None:
    assert_dogfood_mongo_endpoint(uri)


def default_dogfood_root() -> Path:
    raw = (os.environ.get("DOGFOOD_ROOT") or "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parents[3] / "dogfood"


def _uri_for_tool(mongo_uri: str) -> str:
    """Normalize URI so --db can be passed separately (no path DB conflict)."""
    raw = (mongo_uri or "").strip()
    if not raw:
        return raw
    try:
        p = urlparse(raw if "://" in raw else f"mongodb://{raw}")
        # Keep netloc + query (authSource); clear path DB
        return urlunparse((p.scheme, p.netloc, "/", "", p.query, ""))
    except Exception:  # noqa: BLE001
        return raw


def run_mongodump(
    *,
    mongo_uri: str,
    db_name: str,
    out_dir: Path,
    collections: Optional[list[str]] = None,
) -> dict[str, Any]:
    assert_dogfood_mongo_endpoint(mongo_uri)
    db_name = assert_safe_db_name(db_name, role="source")
    out_dir.mkdir(parents=True, exist_ok=True)
    dump_dir = out_dir / "mongodump" / db_name
    if dump_dir.exists():
        shutil.rmtree(dump_dir)
    dump_dir.parent.mkdir(parents=True, exist_ok=True)
    colls = list(collections or DOGFOOD_BACKUP_COLLECTIONS)
    tool_uri = _uri_for_tool(mongo_uri)
    # mongodump whole DB then we record which collections existed
    cmd = [
        "mongodump",
        f"--uri={tool_uri}",
        f"--db={db_name}",
        f"--out={out_dir / 'mongodump'}",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"mongodump_failed:{proc.returncode}:{proc.stderr[-500:]}"
        )
    present = []
    missing = []
    bson_dir = out_dir / "mongodump" / db_name
    for c in colls:
        bson = bson_dir / f"{c}.bson"
        if bson.is_file():
            present.append(c)
        else:
            missing.append(c)
    return {
        "ok": True,
        "dump_dir": str(bson_dir),
        "collections_requested": colls,
        "collections_present": present,
        "collections_missing_empty": missing,
        "stderr_tail": (proc.stderr or "")[-300:],
    }


def run_mongorestore(
    *,
    mongo_uri: str,
    target_db: str,
    dump_db_dir: Path,
    drop: bool = True,
) -> dict[str, Any]:
    assert_dogfood_mongo_endpoint(mongo_uri)
    target_db = assert_safe_db_name(target_db, role="target_probe")
    if not dump_db_dir.is_dir():
        raise RuntimeError(f"dump_dir_missing:{dump_db_dir}")
    tool_uri = _uri_for_tool(mongo_uri)
    # dump_db_dir contains *.bson for one DB; --db remaps into target probe DB.
    cmd = [
        "mongorestore",
        f"--uri={tool_uri}",
        f"--db={target_db}",
        str(dump_db_dir),
    ]
    if drop:
        cmd.insert(-1, "--drop")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"mongorestore_failed:{proc.returncode}:{proc.stderr[-800:]}"
        )
    return {
        "ok": True,
        "target_db": target_db,
        "stderr_tail": (proc.stderr or "")[-300:],
    }


def backup_media(src: Path, dest: Path) -> dict[str, Any]:
    """Copy media into backup dest.

    Missing source is a **blocking** failure unless
    ``OMNIA_DOGFOOD_ALLOW_MISSING_MEDIA=1`` is set explicitly (documented opt-out).
    """
    dest.mkdir(parents=True, exist_ok=True)
    media_dest = dest / "media"
    anomalies: list[str] = []
    allow_missing = (
        (os.environ.get("OMNIA_DOGFOOD_ALLOW_MISSING_MEDIA") or "").strip() == "1"
    )
    if not src.exists():
        anomalies.append("media_src_missing")
        empty_inv = (
            sha256_tree(media_dest)
            if media_dest.exists()
            else {"file_count": 0, "bytes": 0, "files": [], "tree_sha256": hashlib.sha256(b"").hexdigest()}
        )
        if allow_missing:
            anomalies.append("media_missing_allowed_by_OMNIA_DOGFOOD_ALLOW_MISSING_MEDIA")
            return {
                "ok": True,
                "copied": False,
                "anomalies": anomalies,
                "inventory": empty_inv,
            }
        return {
            "ok": False,
            "copied": False,
            "anomalies": anomalies,
            "inventory": empty_inv,
            "error": "media_src_missing",
        }
    if media_dest.exists():
        shutil.rmtree(media_dest)
    try:
        shutil.copytree(src, media_dest)
    except Exception as e:  # noqa: BLE001
        anomalies.append(f"media_copy_error:{e}")
        return {"ok": False, "copied": False, "anomalies": anomalies}
    inv = sha256_tree(media_dest)
    return {
        "ok": True,
        "copied": True,
        "anomalies": anomalies,
        "inventory": inv,
    }


def write_manifest(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Hard scrub any accidental secrets
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    for bad in ("password", "passwd", "secret", "token", "://"):
        # URIs already redacted; still refuse raw userinfo patterns
        if re.search(r"://[^/\s]+:[^/\s]+@", text):
            raise RuntimeError("manifest_contains_credential_uri")
    path.write_text(text, encoding="utf-8")
    return path


def build_manifest(
    *,
    backup_id: str,
    source_db: str,
    source_uri_redacted: str,
    dump_report: dict[str, Any],
    media_report: dict[str, Any],
    dump_sha: dict[str, Any],
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    return {
        "schema": "omnia.dogfood.backup.v1",
        "backup_id": backup_id,
        "created_at": _now(),
        "git_sha": _git_sha(),
        "cycle": "D-175-C2",
        "environment": {
            "OMNIA_ENV": (os.environ.get("OMNIA_ENV") or "").strip() or None,
            "source_db": source_db,
            "source_mongo_uri_redacted": source_uri_redacted,
        },
        "collections": {
            "requested": dump_report.get("collections_requested"),
            "present": dump_report.get("collections_present"),
            "missing_or_empty": dump_report.get("collections_missing_empty"),
        },
        "mongodump": {
            "ok": dump_report.get("ok"),
            "dump_dir": dump_report.get("dump_dir"),
        },
        "media": {
            "ok": media_report.get("ok"),
            "copied": media_report.get("copied"),
            "anomalies": media_report.get("anomalies") or [],
            "file_count": (media_report.get("inventory") or {}).get("file_count"),
            "bytes": (media_report.get("inventory") or {}).get("bytes"),
            "tree_sha256": (media_report.get("inventory") or {}).get("tree_sha256"),
        },
        "integrity": {
            "dump_tree_sha256": dump_sha.get("tree_sha256"),
            "dump_file_count": dump_sha.get("file_count"),
            "dump_bytes": dump_sha.get("bytes"),
        },
        "anomalies": list(media_report.get("anomalies") or []),
        "extra": extra or {},
    }
