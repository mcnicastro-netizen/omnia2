#!/usr/bin/env python3
"""S9 LIVE probe — self-serve ON: plans flag + checkout past self_serve_blocked."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = os.environ.get("OMNIA_API_BASE", "http://127.0.0.1:43121/api").rstrip("/")
OUT = ROOT / "docs/ops/runs/s9-o6-self-serve-live.log"


class ApiClient:
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

    def _ingest(self, headers) -> None:
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
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=data,
            headers=self._headers(json_body=body is not None),
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                self._ingest(resp.headers)
                raw = resp.read().decode()
                return resp.status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            self._ingest(e.headers)
            raw = e.read().decode()
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                payload = {"raw": raw[:300]}
            return e.code, payload


def main() -> int:
    lines: list[str] = []
    ts = datetime.now(timezone.utc).isoformat()
    lines.append(f"=== S9 LIVE {ts} ===")
    env_flag = os.environ.get("OMNIA_SELF_SERVE_ENABLED")
    lines.append(f"env_OMNIA_SELF_SERVE_ENABLED={env_flag!r}")

    # Load .env into process if present
    env_path = ROOT / "backend" / ".env"
    if env_path.is_file():
        for line in env_path.read_text().splitlines():
            if line.startswith("OMNIA_SELF_SERVE_ENABLED="):
                os.environ["OMNIA_SELF_SERVE_ENABLED"] = line.split("=", 1)[1].strip()
                lines.append(f"env_from_dotenv={os.environ['OMNIA_SELF_SERVE_ENABLED']!r}")

    c = ApiClient(API)
    st, plans = c.request("GET", "/billing/plans")
    lines.append(f"plans_status={st} self_serve_enabled={plans.get('self_serve_enabled')} enabled={plans.get('enabled')} mode={plans.get('mode')}")

    email = os.environ.get("ADMIN_EMAIL") or os.environ.get("OMNIA_ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD") or os.environ.get("OMNIA_ADMIN_PASSWORD")
    # Prefer demo agency for checkout story
    demo_email = "demo.admin@omniaecosystem.it"
    demo_pwd = os.environ.get("DEMO_ADMIN_PASSWORD") or "DemoAdmin2026!"
    st_login, _ = c.request("POST", "/auth/login", {"email": demo_email, "password": demo_pwd})
    if st_login != 200 and email and password:
        st_login, _ = c.request("POST", "/auth/login", {"email": email, "password": password})
    lines.append(f"login_status={st_login}")

    st_co, body_co = c.request(
        "POST",
        "/billing/checkout",
        {"plan_tier": "starter", "billing_cycle": "monthly", "origin": "http://127.0.0.1:43123"},
    )
    detail = body_co.get("detail") if isinstance(body_co, dict) else body_co
    lines.append(f"checkout_status={st_co} detail={detail!r}"[:500])

    blocked = False
    if isinstance(detail, dict) and detail.get("code") == "self_serve_blocked":
        blocked = True
    if st_co == 503 and "self_serve_blocked" in str(detail):
        blocked = True

    # Success criteria: plans flag true AND checkout not blocked by self_serve
    # (200 with session url, or 4xx stripe/plan errors OK — just not 503 self_serve)
    ok_plans = plans.get("self_serve_enabled") is True
    ok_checkout = not blocked and st_co != 503
    # If stripe misconfigured may be 503 with different code — still fail open check
    if st_co == 503 and not blocked:
        ok_checkout = False
        lines.append("NOTE: checkout 503 but not self_serve_blocked — infra Stripe?")

    checks = {
        "plans_self_serve_true": ok_plans,
        "checkout_not_self_serve_blocked": not blocked,
        "checkout_not_503_gate": ok_checkout or st_co in (200, 400, 402, 404),
    }
    # Accept 200 (session) or business 4xx; reject only self_serve gate
    if st_co == 200:
        checks["checkout_session_ok"] = bool(body_co.get("url") or body_co.get("session_id") or body_co.get("id"))
    elif not blocked and st_co in (400, 402, 404, 422):
        checks["checkout_past_gate"] = True
    elif not blocked and st_co == 200:
        checks["checkout_past_gate"] = True
    else:
        checks["checkout_past_gate"] = not blocked and st_co < 500

    failed = [k for k, v in checks.items() if not v]
    lines.append(f"checks={checks}")
    lines.append(f"ESITO={'PASS' if not failed else 'FAIL'} failed={failed}")
    lines.append("LIMITI: Stripe resta mode=test; S10 = GTM-01 / live keys separati.")

    text = "\n".join(lines) + "\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(text)
    return 0 if not failed else 1


if __name__ == "__main__":
    # Load backend .env for credentials
    env_file = ROOT / "backend" / ".env"
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
    sys.exit(main())
