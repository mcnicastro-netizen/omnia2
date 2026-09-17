#!/usr/bin/env python3
"""Build a slim inventory from an Emergent/local OMNIA zip or folder.

Why: full Emergent zips are too large to upload into Cursor. This script
writes a small JSON (typically <2–5 MB) with path + sha256 + size that you
can drop into the agent chat or into memory/reports/.

Usage (on your machine):
  python3 emergent_zip_inventory.py /path/to/omnia.zip
  python3 emergent_zip_inventory.py /path/to/omnia-folder

Output:
  emergent_inventory_<timestamp>.json
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIR_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".mongo-data",
    "__pycache__",
    ".next",
    "build",
    "dist",
    ".cache",
    "coverage",
    ".pytest_cache",
    ".media",
    ".emergent",
}

SKIP_SUFFIXES = {".pyc", ".pyo", ".log", ".mp4", ".mov", ".zip", ".tar", ".gz"}
SKIP_NAMES = {".ds_store", "thumbs.db"}
SECRET_NAMES = {".env", ".env.local", "test_credentials.env"}

# Skip huge binaries even outside .media
SKIP_BINARY_SUFFIXES = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".woff", ".woff2",
    ".mp3", ".wav", ".webm", ".ico", ".sqlite", ".bson",
}


def _skip_parts(parts: tuple[str, ...]) -> bool:
    lower = {p.lower() for p in parts}
    return bool(lower & {p.lower() for p in SKIP_DIR_PARTS})


def _is_secret(name: str) -> bool:
    n = name.lower()
    if n in SECRET_NAMES:
        return True
    if n.startswith(".env") and "example" not in n:
        true = True
        return true
    return False


def _want_file(rel: str) -> bool:
    p = Path(rel)
    if _skip_parts(p.parts):
        return False
    if p.name.lower() in SKIP_NAMES:
        return False
    if p.suffix.lower() in SKIP_SUFFIXES | SKIP_BINARY_SUFFIXES:
        return False
    return True


def inventory_zip(zpath: Path) -> dict:
    files = {}
    skipped = 0
    with zipfile.ZipFile(zpath) as zf:
        # Detect common root prefix (e.g. "OMNIA/" or "omnia-main/")
        names = [n for n in zf.namelist() if not n.endswith("/")]
        prefix = ""
        if names:
            first = names[0].split("/")[0] + "/"
            if all(n.startswith(first) for n in names):
                prefix = first
        for name in names:
            rel = name[len(prefix) :] if prefix and name.startswith(prefix) else name
            rel = rel.replace("\\", "/")
            if not rel or not _want_file(rel):
                skipped += 1
                continue
            data = zf.read(name)
            secret = _is_secret(Path(rel).name)
            files[rel] = {
                "size": len(data),
                "sha256": None if secret else hashlib.sha256(data).hexdigest(),
                "secret": secret,
            }
    return {"source": str(zpath), "prefix": prefix, "files": files, "skipped": skipped}


def inventory_dir(root: Path) -> dict:
    files = {}
    skipped = 0
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = str(p.relative_to(root)).replace("\\", "/")
        if not _want_file(rel):
            skipped += 1
            continue
        data = p.read_bytes()
        secret = _is_secret(p.name)
        files[rel] = {
            "size": len(data),
            "sha256": None if secret else hashlib.sha256(data).hexdigest(),
            "secret": secret,
        }
    return {"source": str(root), "prefix": "", "files": files, "skipped": skipped}


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    target = Path(sys.argv[1]).expanduser().resolve()
    if not target.exists():
        print(f"not found: {target}", file=sys.stderr)
        return 1
    if target.is_file() and zipfile.is_zipfile(target):
        inv = inventory_zip(target)
    elif target.is_dir():
        inv = inventory_dir(target)
    else:
        print("need a .zip or a folder", file=sys.stderr)
        return 1

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path.cwd() / f"emergent_inventory_{stamp}.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": inv["source"],
        "zip_prefix": inv.get("prefix"),
        "file_count": len(inv["files"]),
        "skipped_runtime_or_binary": inv["skipped"],
        "files": inv["files"],
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    mb = out.stat().st_size / (1024 * 1024)
    print(f"wrote {out} ({mb:.2f} MB, {payload['file_count']} source files, skipped {payload['skipped_runtime_or_binary']})")
    print("→ carica SOLO questo JSON in Cursor (chat / memory/reports/), non lo zip.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
