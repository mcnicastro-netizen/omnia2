#!/usr/bin/env python3
"""S7 LIVE probe — demo story ripetibile (seed → CRM → portale → scadenza → Acquista).

Usage:
  python scripts/demo_story_probe.py --twice
  python scripts/demo_story_probe.py --round 1

Writes docs/ops/runs/s7-demo-story-live.log (append).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from dotenv import load_dotenv

load_dotenv(BACKEND / ".env", override=True)

API = os.environ.get("OMNIA_API_BASE") or "http://127.0.0.1:43121/api"
LOG = ROOT / "docs" / "ops" / "runs" / "s7-demo-story-live.log"


def _log(line: str, lines: list[str]) -> None:
    print(line)
    lines.append(line)


class ApiClient:
    """Cookie client that keeps Secure cookies even on http://127.0.0.1 (Cloud)."""

    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.cookies: dict[str, str] = {}
        self.csrf = None

    def _headers(self, *, json_body: bool = False) -> dict:
        h = {"Accept": "application/json"}
        if json_body:
            h["Content-Type"] = "application/json"
        if self.cookies:
            h["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        if self.csrf:
            h["X-CSRF-Token"] = self.csrf
        return h

    def _ingest_set_cookie(self, headers) -> None:
        # HTTPMessage may have multiple Set-Cookie
        raw_list = []
        if hasattr(headers, "get_all"):
            raw_list = headers.get_all("Set-Cookie") or []
        elif "Set-Cookie" in headers:
            raw_list = [headers["Set-Cookie"]]
        for raw in raw_list:
            part = raw.split(";", 1)[0]
            if "=" not in part:
                continue
            name, val = part.split("=", 1)
            self.cookies[name.strip()] = val.strip()
            if name.strip() == "omnia_csrf":
                self.csrf = val.strip()

    def request(self, method: str, path: str, body: dict | None = None):
        data = None
        if body is not None:
            data = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=data,
            headers=self._headers(json_body=body is not None),
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                self._ingest_set_cookie(r.headers)
                raw = r.read().decode()
                payload = json.loads(raw) if raw else {}
                return r.status, payload
        except urllib.error.HTTPError as e:
            self._ingest_set_cookie(e.headers)
            raw = e.read().decode()
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                payload = {"raw": raw[:300]}
            return e.code, payload


async def seed_and_window(*, force_expired: bool, refresh: bool) -> dict:
    from motor.motor_asyncio import AsyncIOMotorClient
    import seed_demo_gestionale as seed
    from shared.demo_story import ensure_demo_window

    mongo_url = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
    db_name = os.environ.get("DB_NAME", "omnia")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    await seed.main()
    status = await ensure_demo_window(
        db, refresh=refresh, force_expired=force_expired
    )
    client.close()
    return status


def run_round(round_n: int) -> bool:
    lines: list[str] = []
    ts = datetime.now(timezone.utc).isoformat()
    _log(f"=== S7 LIVE round={round_n} {ts} ===", lines)
    _log(f"api={API}", lines)

    active = asyncio.run(seed_and_window(force_expired=False, refresh=True))
    _log(f"seed_active={json.dumps(active, ensure_ascii=False)}", lines)
    checks = {
        "seed_demo_story": bool(active.get("is_demo_story")),
        "seed_not_expired": active.get("expired") is False,
        "cta_use_sandbox": active.get("cta") == "use_sandbox",
    }

    client = ApiClient(API)
    demo_pw = os.environ.get("DEMO_ADMIN_PASSWORD") or "OmniaDemo2026!"
    st, body = client.request(
        "POST",
        "/auth/login",
        {"email": "demo.admin@omniaecosystem.it", "password": demo_pw},
    )
    login_ok = st == 200 and body.get("role") == "agency_admin"
    access = "access_token" in client.cookies
    _log(
        f"login_status={st} role={body.get('role')} access={access} csrf={bool(client.csrf)}",
        lines,
    )
    checks["login_demo_admin"] = login_ok
    checks["session_cookie"] = access

    st, props = client.request("GET", "/app/properties?page_size=50")
    if isinstance(props, dict):
        items = props.get("items") or props.get("properties") or props.get("data") or []
        total = props.get("total", len(items))
    else:
        items, total = props or [], len(props or [])
    _log(f"crm_properties status={st} total={total}", lines)
    checks["crm_properties_ge1"] = st == 200 and int(total or 0) >= 1

    st, search = client.request("GET", "/cloud/search?page_size=20")
    if isinstance(search, dict):
        s_total = search.get("total") or len(
            search.get("items") or search.get("results") or []
        )
    else:
        s_total = 0
    _log(f"portal_search status={st} total={s_total}", lines)
    checks["portal_listings_ge1"] = st == 200 and int(s_total or 0) >= 1

    st, demo = client.request("GET", "/billing/demo-status")
    _log(
        f"demo_status_active status={st} body={json.dumps(demo, ensure_ascii=False)}",
        lines,
    )
    checks["demo_status_200"] = st == 200
    checks["demo_status_active"] = (
        st == 200 and demo.get("is_demo_story") and not demo.get("expired")
    )

    expired_st = asyncio.run(seed_and_window(force_expired=True, refresh=False))
    _log(f"force_expired={json.dumps(expired_st, ensure_ascii=False)}", lines)
    checks["force_expired"] = expired_st.get("expired") is True

    st, demo2 = client.request("GET", "/billing/demo-status")
    _log(
        f"demo_status_expired status={st} cta={demo2.get('cta')} "
        f"checkout={demo2.get('checkout_available')}",
        lines,
    )
    checks["cta_acquista"] = st == 200 and demo2.get("cta") == "acquista_pacchetto"
    checks["checkout_blocked_pre_s9"] = (
        st == 200 and demo2.get("checkout_available") is False
    )

    st, chk = client.request(
        "POST",
        "/billing/checkout",
        {"plan_tier": "pro", "billing_cycle": "monthly"},
    )
    detail = chk.get("detail") if isinstance(chk, dict) else chk
    code = None
    if isinstance(detail, dict):
        code = detail.get("code") or detail.get("error")
    _log(f"checkout_status={st} code={code}", lines)
    checks["checkout_503_self_serve"] = st == 503 and code == "self_serve_blocked"

    restored = asyncio.run(seed_and_window(force_expired=False, refresh=True))
    _log(f"restored_active expired={restored.get('expired')}", lines)
    checks["restored_active"] = restored.get("expired") is False

    failed = [k for k, v in checks.items() if not v]
    esito = "PASS" if not failed else "FAIL"
    _log(f"checks={checks}", lines)
    _log(f"ESITO={esito} failed={failed}", lines)
    _log(
        "LIMITI: checkout B2B aperto da S9 (OMNIA_SELF_SERVE_ENABLED); "
        "Nicastro ≠ percorso GTM; trial default 7g (OMNIA_DEMO_TRIAL_DAYS).",
        lines,
    )

    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return esito == "PASS"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--twice", action="store_true", help="run round 1 and 2")
    args = ap.parse_args()
    if args.twice:
        return 0 if (run_round(1) and run_round(2)) else 1
    return 0 if run_round(args.round) else 1


if __name__ == "__main__":
    raise SystemExit(main())
