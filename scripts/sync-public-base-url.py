#!/usr/bin/env python3
"""Sync FRONTEND_* / OMNIA_PUBLIC_URL to the live public tunnel URL (P-019).

Also sets COOKIE_SECURE=true on HTTPS trycloudflare (P-051 → CSRF enforce).

Called from omnia-stack when trycloudflare URL is healthy.
- Upserts backend/.env keys (no secret values)
- Exit 0 always; prints CHANGED=1|0 for callers (API reload only when changed)
- Never prints secrets
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV = ROOT / "backend" / ".env"
KEYS = ("FRONTEND_BASE_URL", "FRONTEND_URL", "OMNIA_PUBLIC_URL")
TUNNEL_RE = re.compile(r"^https://[a-z0-9-]+\.trycloudflare\.com/?$")


def upsert(lines: list[str], key: str, val: str) -> tuple[list[str], bool]:
    prefix = f"{key}="
    out: list[str] = []
    found = False
    changed = False
    target = val.rstrip("/")
    for line in lines:
        stripped = line.lstrip()
        is_key = (
            stripped.startswith(prefix)
            or stripped.startswith("#" + prefix)
            or stripped.startswith("# " + prefix)
        )
        if is_key:
            if not found:
                raw = stripped.lstrip("# ").split("=", 1)
                old = raw[1].strip().strip('"').strip("'").rstrip("/") if len(raw) == 2 else ""
                out.append(f"{key}={target}")
                if old != target:
                    changed = True
                found = True
            continue
        out.append(line)
    if not found:
        out.append(f"{key}={target}")
        changed = True
    return out, changed


def normalize_url(url: str) -> str:
    u = (url or "").strip().rstrip("/")
    if not TUNNEL_RE.match(u + "/") and not TUNNEL_RE.match(u):
        # also accept exact without trailing logic
        if not re.match(r"^https://[a-z0-9-]+\.trycloudflare\.com$", u):
            raise SystemExit(f"[sync-public-base-url] refuse non-tunnel url class: {u[:48]}")
    return u


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="Public https://*.trycloudflare.com URL")
    ap.add_argument("--share-file", default="/tmp/omnia-stack/SHARE_URL.txt")
    ap.add_argument("--env", default=str(DEFAULT_ENV))
    args = ap.parse_args()

    url = (args.url or "").strip()
    if not url and args.share_file and Path(args.share_file).is_file():
        url = Path(args.share_file).read_text(encoding="utf-8").strip()
    if not url:
        print("[sync-public-base-url] SKIP no public url")
        print("CHANGED=0")
        return 0

    url = normalize_url(url)
    env_path = Path(args.env)
    lines: list[str] = []
    if env_path.is_file():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    any_changed = False
    for key in KEYS:
        lines, ch = upsert(lines, key, url)
        any_changed = any_changed or ch
        os.environ[key] = url

    # P-051: HTTPS tunnel ⇒ secure cookies + CSRF middleware on
    if url.startswith("https://"):
        lines, ch = upsert(lines, "COOKIE_SECURE", "true")
        any_changed = any_changed or ch
        os.environ["COOKIE_SECURE"] = "true"

    # marker comment once
    marker = "# --- Public base URL (synced from trycloudflare; do not commit secrets) ---"
    if marker not in lines:
        # insert before first FRONTEND_ if present
        idx = next((i for i, ln in enumerate(lines) if ln.startswith("FRONTEND_") or ln.startswith("OMNIA_PUBLIC_URL")), None)
        if idx is None:
            lines.append(marker)
        else:
            lines.insert(idx, marker)

    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # process hint file for other tools
    hint = Path("/tmp/omnia-stack/PUBLIC_BASE_URL.txt")
    hint.parent.mkdir(parents=True, exist_ok=True)
    hint.write_text(url + "\n", encoding="utf-8")

    print(f"[sync-public-base-url] base={url} changed={int(any_changed)}")
    print(f"CHANGED={1 if any_changed else 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
