"""Immutable per-run artifact directories under artifacts/d7/<run_id>/."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .run_id import validate_run_id


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def artifacts_d7_root() -> Path:
    return (repo_root() / "artifacts" / "d7").resolve()


def new_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rid = f"{ts}_{secrets.token_hex(4)}"
    return validate_run_id(rid)


def run_dir(run_id: str, *, create: bool = True) -> Path:
    rid = validate_run_id(run_id)
    base = artifacts_d7_root()
    d = (base / rid).resolve()
    # Ensure resolved path is strictly under artifacts/d7/
    try:
        d.relative_to(base)
    except ValueError as e:
        raise RuntimeError(f"run_dir_escapes_artifacts_d7:{d}") from e
    if d == base:
        raise RuntimeError("run_dir_is_artifacts_root")
    if create:
        if d.exists():
            raise RuntimeError(f"artifact_dir_exists_refusing_overwrite:{d}")
        d.mkdir(parents=True, exist_ok=False)
        (d / "secrets").mkdir(mode=0o700)
    return d


def write_json(path: Path, obj: Any) -> None:
    if path.exists():
        raise RuntimeError(f"refusing_overwrite:{path}")
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")


def write_json_overwrite(path: Path, obj: Any) -> None:
    """Allowed only for inventory-style mutable run bookkeeping (not used for secrets)."""
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")


def write_secrets_file(run_path: Path, secrets_obj: dict) -> Path:
    """Write secrets with mode 0600 under the run directory — never /tmp world-readable."""
    p = run_path / "secrets" / "fixtures_secrets.json"
    if p.exists():
        raise RuntimeError(f"refusing_overwrite:{p}")
    fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(secrets_obj, f, indent=2)
        f.write("\n")
    os.chmod(p, 0o600)
    return p


def append_console(run_path: Path, line: str) -> None:
    with open(run_path / "console.log", "a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")


def write_manifest(run_path: Path, manifest: dict) -> None:
    manifest = {
        **manifest,
        "harness_version": __version__,
        "written_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(run_path / "MANIFEST.json", manifest)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_checksums(run_path: Path) -> None:
    lines = []
    for p in sorted(run_path.rglob("*")):
        if p.is_file() and p.name != "sha256sums.txt":
            rel = p.relative_to(run_path).as_posix()
            lines.append(f"{sha256_file(p)}  {rel}")
    out = run_path / "sha256sums.txt"
    if out.exists():
        raise RuntimeError(f"refusing_overwrite:{out}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
