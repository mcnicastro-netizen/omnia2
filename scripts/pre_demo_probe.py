#!/usr/bin/env python3
"""Pre-demo ≥8 probe — bak → off-box → dry-run → ops preflight → prospect smoke.

Usage:
  python scripts/pre_demo_probe.py

Writes docs/ops/runs/pre-demo-8-live.log
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / "scripts"))

from dotenv import load_dotenv

load_dotenv(BACKEND / ".env", override=True)

API = (os.environ.get("OMNIA_API_BASE") or "http://127.0.0.1:43121/api").rstrip("/")
LOG = ROOT / "docs" / "ops" / "runs" / "pre-demo-8-live.log"
PY = str(BACKEND / ".venv" / "bin" / "python")
if not Path(PY).is_file():
    PY = sys.executable


def _log(line: str, lines: list[str]) -> None:
    print(line)
    lines.append(line)


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
            with urllib.request.urlopen(req, timeout=180) as r:
                self._ingest(r.headers)
                raw = r.read().decode()
                return r.status, json.loads(raw) if raw else {}
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
    _log(f"=== PRE-DEMO-8 LIVE {ts} ===", lines)
    checks: dict[str, bool] = {}

    # 1) Trigger bak via Founder login
    c = ApiClient(API)
    email = os.environ.get("ADMIN_EMAIL") or os.environ.get("OMNIA_ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD") or os.environ.get("OMNIA_ADMIN_PASSWORD")
    st, login = c.request("POST", "/auth/login", {"email": email, "password": password})
    _log(f"founder_login status={st} role={login.get('role')}", lines)
    checks["founder_login"] = st == 200

    st, bak = c.request("POST", "/app/ops/backup/run")
    _log(
        f"backup_run status={st} bak_status={bak.get('status')} "
        f"offbox_ok={(bak.get('offbox') or {}).get('ok')} day={bak.get('day')}",
        lines,
    )
    checks["backup_run_ok"] = st == 200 and bak.get("status") in ("OK", "PARTIAL")
    checks["offbox_ok"] = bool((bak.get("offbox") or {}).get("ok")) or (
        (bak.get("offbox") or {}).get("status") not in (None, "MISSING")
        and st == 200
    )

    # 2) Dry-run restore hot + offbox
    env = os.environ.copy()
    if bak.get("day"):
        env["DAY"] = str(bak["day"])
    r = subprocess.run(
        [PY, str(ROOT / "scripts" / "restore_dry_run.py"), "--offbox"],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    _log(f"restore_dry_run exit={r.returncode}", lines)
    for line in (r.stdout or "").strip().splitlines()[-8:]:
        _log(f"  dry|{line}", lines)
    checks["restore_dry_run"] = r.returncode == 0

    # 3) Preflight
    st, pre = c.request("GET", "/app/ops/preflight")
    _log(
        f"preflight status={st} esito={pre.get('esito')} failed={pre.get('failed')} "
        f"soft={pre.get('soft_failed')}",
        lines,
    )
    checks["preflight_pass"] = st == 200 and pre.get("esito") == "PASS"

    # 4) GTM-01 smoke (prospect + 20 concurrent) — skip seed for speed
    r2 = subprocess.run(
        [PY, str(ROOT / "scripts" / "gtm01_smoke.py"), "--workers", "20", "--skip-seed"],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    _log(f"gtm01_smoke exit={r2.returncode}", lines)
    for line in (r2.stdout or "").strip().splitlines()[-6:]:
        _log(f"  gtm|{line}", lines)
    checks["gtm01_pass"] = r2.returncode == 0

    failed = [k for k, v in checks.items() if not v]
    esito = "PASS" if not failed else "FAIL"
    _log(f"checks={checks}", lines)
    _log(f"ESITO={esito} failed={failed}", lines)
    _log(
        "LIMITI: off-box default=/tmp (Cloud); in prod punta OFFBOX_BACKUP_ROOT a volume esterno. "
        "Stripe resta test. Outreach solo con «vai».",
        lines,
    )

    LOG.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines) + "\n"
    LOG.write_text(text, encoding="utf-8")
    try:
        art = Path("/opt/cursor/artifacts/pre-demo-8-live.log")
        art.parent.mkdir(parents=True, exist_ok=True)
        art.write_text(text, encoding="utf-8")
    except Exception:
        pass
    return 0 if esito == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
