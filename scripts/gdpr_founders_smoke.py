#!/usr/bin/env python3
"""Onda 9 / D-099 — smoke DSAR path: register → export → erase → login fail.

Usage:
  OMNIA_API_BASE=http://127.0.0.1:43121/api \\
    backend/.venv/bin/python scripts/gdpr_founders_smoke.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

API = (os.environ.get("OMNIA_API_BASE") or "http://127.0.0.1:43121/api").rstrip("/")
ARTIFACT = Path(
    os.environ.get(
        "GDPR_SMOKE_ARTIFACT",
        f"/opt/cursor/artifacts/onda9-gdpr-smoke-{datetime.now(timezone.utc).date()}.log",
    )
)
REPO_RUN = Path(__file__).resolve().parents[1] / "docs" / "ops" / "runs" / ARTIFACT.name


def log(lines: list[str], msg: str) -> None:
    print(msg, flush=True)
    lines.append(msg)


def main() -> int:
    lines: list[str] = []
    email = f"gdpr.smoke.{uuid.uuid4().hex[:8]}@example.com"
    password = "GdprSmoke2026!"
    log(lines, f"=== Onda9 GDPR smoke {datetime.now(timezone.utc).isoformat()} ===")
    log(lines, f"API={API} email={email}")

    s = requests.Session()
    r = s.post(
        f"{API}/cloud/auth/register",
        json={
            "email": email,
            "password": password,
            "name": "GDPR Smoke",
            "intents": ["buy"],
            "gdpr_consent": True,
            "age_confirmed": True,
            "marketing_consent": False,
            "lang": "it",
        },
        timeout=30,
    )
    log(lines, f"register status={r.status_code}")
    if r.status_code not in (200, 201):
        log(lines, f"FAIL register body={r.text[:300]}")
        ARTIFACT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 1

    # Cookies are Secure+SameSite=None — on plain http:// localhost Session
    # will not attach them. Prefer Bearer from jar / Set-Cookie.
    token = s.cookies.get("access_token")
    if not token:
        # parse Set-Cookie manually
        for part in (r.headers.get("Set-Cookie") or "").split(","):
            part = part.strip()
            if part.startswith("access_token="):
                token = part.split(";", 1)[0].split("=", 1)[1]
                break
    if not token:
        log(lines, "FAIL no access_token after register")
        ARTIFACT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 1
    auth = {"Authorization": f"Bearer {token}"}

    r = s.get(f"{API}/auth/me/export", headers=auth, timeout=30)
    log(lines, f"export status={r.status_code}")
    if r.status_code != 200:
        log(lines, f"FAIL export body={r.text[:300]}")
        ARTIFACT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 1
    data = r.json()
    ok_export = data.get("format") == "omnia_b2c_export_v1" and (
        (data.get("profile") or {}).get("email") == email
    )
    log(lines, f"export_ok={ok_export} format={data.get('format')}")
    if not ok_export:
        ARTIFACT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 1

    r = s.post(
        f"{API}/auth/me/erase",
        headers=auth,
        json={"confirm": "DELETE", "password": password},
        timeout=30,
    )
    log(lines, f"erase status={r.status_code}")
    if r.status_code != 200:
        log(lines, f"FAIL erase body={r.text[:400]}")
        ARTIFACT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 1
    body = r.json()
    erase_ok = body.get("status") == "erased"
    log(lines, f"erase_ok={erase_ok} report_keys={list((body.get('report') or {}).keys())}")

    s2 = requests.Session()
    r = s2.post(
        f"{API}/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )
    # erased email tombstoned → login must fail
    login_blocked = r.status_code in (401, 403, 404)
    log(lines, f"post_erase_login status={r.status_code} blocked={login_blocked}")

    esito = "PASS" if erase_ok and login_blocked else "FAIL"
    log(lines, f"ESITO={esito}")
    text = "\n".join(lines) + "\n"
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(text, encoding="utf-8")
    REPO_RUN.parent.mkdir(parents=True, exist_ok=True)
    REPO_RUN.write_text(text, encoding="utf-8")
    log(lines, f"ARTIFACT={ARTIFACT}")
    log(lines, f"REPO_RUN={REPO_RUN}")
    return 0 if esito == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
