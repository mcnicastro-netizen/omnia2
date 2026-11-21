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


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def new_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}_{secrets.token_hex(4)}"


def run_dir(run_id: str, *, create: bool = True) -> Path:
    d = repo_root() / "artifacts" / "d7" / run_id
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
            # Never checksum secrets content into a world-readable summary with values —
            # still hash the file bytes for integrity without printing secrets.
            lines.append(f"{sha256_file(p)}  {rel}")
    out = run_path / "sha256sums.txt"
    if out.exists():
        raise RuntimeError(f"refusing_overwrite:{out}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
