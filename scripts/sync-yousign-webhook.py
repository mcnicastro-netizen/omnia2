#!/usr/bin/env python3
"""YouTrust webhook helper — produzione only.

Sandbox YouTrust: webhook non disponibili (né API né App). In sandbox OMNIA usa
polling `POST /api/app/modulistica/documents/{id}/sync-esign`.

Questo script:
  - se YOUSIGN_API_BASE contiene «sandbox» → SKIP (exit 0) con messaggio chiaro
  - altrimenti prova a creare/aggiornare la subscription webhook di produzione
"""
from __future__ import annotations

import argparse
import os
import re
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

DESC = "OMNIA modulistica esign"
EVENTS = [
    "signature_request.done",
    "signature_request.declined",
    "signature_request.canceled",
    "signature_request.expired",
]


def _read_env(key: str) -> str:
    path = BACKEND / ".env"
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _write_env(key: str, value: str) -> None:
    path = BACKEND / ".env"
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    out = []
    found = False
    for line in lines:
        if line.startswith(f"{key}="):
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(line)
    if not found:
        if out and out[-1].strip():
            out.append("")
        out.append("# YouTrust webhook HMAC (produzione — sync-yousign-webhook.py)")
        out.append(f"{key}={value}")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def _public_base(arg: str | None, share_file: str, prefer_api: bool) -> str:
    if arg:
        return arg.strip().rstrip("/")
    if prefer_api:
        api = (os.environ.get("OMNIA_API_PUBLIC_URL") or _read_env("OMNIA_API_PUBLIC_URL") or "").strip().rstrip("/")
        api = api.removeprefix("OMNIA_API_PUBLIC_URL=")
        if api.startswith("https://"):
            return api
    for path in (share_file, "/tmp/omnia-stack/PUBLIC_BASE_URL.txt", "/tmp/omnia-stack/SHARE_URL.txt"):
        p = Path(path)
        if p.is_file():
            u = p.read_text(encoding="utf-8").strip().splitlines()[0].rstrip("/")
            if re.match(r"^https://[a-z0-9-]+\.trycloudflare\.com$", u) or u.startswith("https://"):
                return u
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--share-file", default="/tmp/omnia-stack/SHARE_URL.txt")
    ap.add_argument("--railway", action="store_true")
    ap.add_argument("--force-prod", action="store_true", help="Skip sandbox guard (prod API key)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    api_key = (os.environ.get("YOUSIGN_API_KEY") or _read_env("YOUSIGN_API_KEY") or "").strip()
    base_api = (
        os.environ.get("YOUSIGN_API_BASE")
        or _read_env("YOUSIGN_API_BASE")
        or "https://api-sandbox.yousign.app/v3"
    ).rstrip("/")
    if not api_key:
        print("[sync-yousign-webhook] SKIP YOUSIGN_API_KEY missing")
        return 0

    if "sandbox" in base_api.lower() and not args.force_prod:
        print(
            "[sync-yousign-webhook] SKIP sandbox — YouTrust non espone webhook in sandbox. "
            "Completion = POST …/sync-esign (poll). Webhook solo con key/API produzione."
        )
        return 0

    public = _public_base(args.url, args.share_file, prefer_api=args.railway or True)
    if not public:
        print("[sync-yousign-webhook] SKIP no public HTTPS base")
        return 0
    endpoint = f"{public}/api/app/modulistica/esign/webhook"

    secret = (os.environ.get("YOUSIGN_WEBHOOK_SECRET") or _read_env("YOUSIGN_WEBHOOK_SECRET") or "").strip()
    if secret and len(secret) != 32:
        print("[sync-yousign-webhook] WARN existing secret len != 32 — regenerating")
        secret = ""
    secret_was_new = False
    if not secret:
        secret = secrets.token_hex(16)
        secret_was_new = True

    if args.dry_run:
        print(f"[sync-yousign-webhook] DRY endpoint={endpoint}")
        return 0

    try:
        import httpx
    except ImportError:
        print("[sync-yousign-webhook] SKIP httpx missing")
        return 1

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    body = {
        "endpoint": endpoint,
        "description": DESC,
        "sandbox": False,
        "subscribed_events": EVENTS,
        "scopes": ["*"],
        "workspaces": ["*"],
        "auto_retry": True,
        "enabled": True,
        "secret_key": secret,
    }

    with httpx.Client(timeout=45.0) as client:
        existing = []
        r = client.get(f"{base_api}/webhooks", headers=headers)
        if r.status_code < 400:
            data = r.json()
            if isinstance(data, list):
                existing = data
            elif isinstance(data, dict):
                existing = data.get("data") or data.get("items") or []
        else:
            print(f"[sync-yousign-webhook] list failed http={r.status_code}")

        ours = [w for w in existing if (w.get("description") or "") == DESC]
        if ours:
            wid = ours[0].get("id")
            patch = {
                "endpoint": endpoint,
                "subscribed_events": EVENTS,
                "enabled": True,
                "auto_retry": True,
                "secret_key": secret,
            }
            r2 = client.patch(f"{base_api}/webhooks/{wid}", headers=headers, json=patch)
            if r2.status_code >= 400:
                print(f"[sync-yousign-webhook] PATCH failed http={r2.status_code} body={r2.text[:200]}")
                return 1
            print(f"[sync-yousign-webhook] UPDATED id={wid} endpoint={endpoint}")
        else:
            r2 = client.post(f"{base_api}/webhooks", headers=headers, json=body)
            if r2.status_code >= 400:
                print(f"[sync-yousign-webhook] CREATE failed http={r2.status_code} body={r2.text[:300]}")
                return 1
            created = r2.json() if r2.content else {}
            returned = (created.get("secret_key") or "").strip()
            if returned and len(returned) == 32:
                secret = returned
                secret_was_new = True
            print(f"[sync-yousign-webhook] CREATED id={created.get('id')} endpoint={endpoint}")

    if secret_was_new or not _read_env("YOUSIGN_WEBHOOK_SECRET"):
        _write_env("YOUSIGN_WEBHOOK_SECRET", secret)
        os.environ["YOUSIGN_WEBHOOK_SECRET"] = secret
        print("[sync-yousign-webhook] YOUSIGN_WEBHOOK_SECRET persisted to backend/.env (not printed)")
    else:
        print("[sync-yousign-webhook] secret unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
