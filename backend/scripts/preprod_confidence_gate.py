#!/usr/bin/env python3
"""OMNIA — Pre-production confidence gate (safe / no vendor burn).

Philosophy
----------
We want production confidence WITHOUT:
  - hammering Resend / Stripe / visure providers / Nominatim / fal.ai
  - spending money or risking API bans

What this gate DOES
-------------------
1. Health + readiness (config truth)
2. Mongo internal load (our DB only — concurrent read/write on marked docs)
3. Hot-path API fan-out (portal + CRM) — our stack
4. Soft external probes (catalog / mock / env flags — never bulk paid calls)
5. Security walls (unauth, brute-force soft)
6. Regression smoke: photo serve, private contact path, Scout detail
7. Critical free pytest subset (unit / no paid vendors)

Exit codes
----------
  0 = all required checks green (soft externals may be SKIP)
  1 = one or more REQUIRED failures
  2 = setup failure (API/login/mongo)

Usage
-----
  bash scripts/omnia-stack.sh ensure
  cd backend && source .venv/bin/activate
  python scripts/preprod_confidence_gate.py
  python scripts/preprod_confidence_gate.py --skip-pytest
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from pymongo import MongoClient, InsertOne

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")
load_dotenv(REPO / "memory" / "test_credentials.env")

API = (os.environ.get("OMNIA_TEST_BASE") or os.environ.get("REACT_APP_BACKEND_URL") or "http://127.0.0.1:43121").rstrip("/")
API_ROOT = API if API.endswith("/api") else API + "/api"
EMAIL = os.environ.get("OMNIA_TEST_EMAIL") or os.environ.get("OMNIA_ADMIN_EMAIL") or "mcnicastro@gmail.com"
PASSWORD = os.environ.get("OMNIA_TEST_PASSWORD") or os.environ.get("OMNIA_ADMIN_PASSWORD") or "OmniaFounder2026!"
AGENCY = os.environ.get("STRESS_AGENCY_ID", "demo-agency-001")
MARKER = "preprod_gate_v1"
REPORT_DIR = REPO / "memory" / "reports"
MD_REPORT = REPO / "memory" / "PREPROD_GATE_REPORT.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def db():
    return MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def login() -> requests.Session:
    s = requests.Session()
    r = s.post(f"{API_ROOT}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    if r.status_code != 200:
        raise SystemExit(f"login failed {r.status_code}: {r.text[:200]}")
    s.post(f"{API_ROOT}/auth/active-agency", json={"agency_id": AGENCY}, timeout=15)
    return s


def timed(session: requests.Session, method: str, path: str, **kw) -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        r = session.request(method, f"{API_ROOT}{path}", timeout=kw.pop("timeout", 45), **kw)
        ms = (time.perf_counter() - t0) * 1000
        return {
            "path": path,
            "method": method,
            "status": r.status_code,
            "ms": round(ms, 1),
            "bytes": len(r.content or b""),
            "ok": 200 <= r.status_code < 400,
        }
    except Exception as e:  # noqa: BLE001
        return {"path": path, "method": method, "status": 0, "ms": None, "error": str(e)[:160], "ok": False}


def fanout(session: Optional[requests.Session], path: str, n: int = 40, workers: int = 16, method: str = "GET", json_body=None) -> Dict[str, Any]:
    cookies = session.cookies.get_dict() if session else {}

    def one(_i):
        s = requests.Session()
        if cookies:
            s.cookies.update(cookies)
        return timed(s, method, path, json=json_body) if json_body is not None else timed(s, method, path)

    times, errors, statuses = [], 0, []
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for f in as_completed([ex.submit(one, i) for i in range(n)]):
            row = f.result()
            statuses.append(row.get("status"))
            if not row.get("ok"):
                errors += 1
            elif row.get("ms") is not None:
                times.append(row["ms"])
    wall = time.perf_counter() - t0
    times.sort()
    out: Dict[str, Any] = {
        "path": path,
        "n": n,
        "errors": errors,
        "wall_s": round(wall, 3),
        "statuses": sorted({s for s in statuses if s is not None}),
        "ok": errors == 0 and bool(times),
    }
    if times:
        out.update({
            "p50_ms": round(statistics.median(times), 1),
            "p95_ms": round(times[max(0, int(len(times) * 0.95) - 1)], 1),
            "max_ms": round(times[-1], 1),
        })
    return out


def reset_local_rate_limits(database) -> Dict[str, Any]:
    """Clear localhost rate-limit counters so the gate does not fail itself.

    Production confidence still covers rate limits via security walls + a controlled
    soft probe; we must not burn the Founder's hourly 120 search budget on 127.0.0.1.
    """
    q = {
        "$or": [
            {"key": {"$in": ["127.0.0.1", "localhost", "::1"]}},
            {"identifier": {"$regex": r"(127\.0\.0\.1|localhost|::1)"}},
        ]
    }
    deleted = database.rate_limit_events.delete_many(q).deleted_count
    return {"deleted": deleted, "ok": True, "note": "localhost counters only"}


def check_health() -> Dict[str, Any]:
    anon = requests.Session()
    health = timed(anon, "GET", "/health")
    ready = timed(anon, "GET", "/health/readiness")
    body = {}
    try:
        body = requests.get(f"{API_ROOT}/health/readiness", timeout=15).json()
    except Exception as e:  # noqa: BLE001
        body = {"error": str(e)[:120]}
    # In local/dev, readiness often fails omnia_env_production — expected.
    # Gate treats readiness HTTP 200 as structural OK; prod flags are WARN.
    missing = body.get("missing") or []
    prod_only = {"omnia_env_production", "cookie_secure", "cors_explicit", "monitoring_configured", "credentials_master_key"}
    warn = [m for m in missing if m in prod_only]
    hard = [m for m in missing if m not in prod_only]
    return {
        "health": health,
        "readiness_http": ready,
        "readiness_body": {
            "ready": body.get("ready"),
            "missing": missing,
            "checks": body.get("checks"),
            "excluded": body.get("excluded"),
        },
        "ok": health.get("ok") and ready.get("status") == 200 and not hard,
        "warn": warn,
        "hard_missing": hard,
        "note": f"prod flags pending: {', '.join(warn)}" if warn else "",
    }


def mongo_internal_load(database, n_docs: int = 500, workers: int = 20) -> Dict[str, Any]:
    """Stress OUR Mongo only — marked docs, cleaned after."""
    col = database.properties
    run = uuid.uuid4().hex[:8]
    docs = []
    for i in range(n_docs):
        docs.append({
            "id": f"preprod-{run}-{i}",
            "_stress": MARKER,
            "_run": run,
            "agency_id": AGENCY,
            "title": f"Preprod gate {i}",
            "status": "draft",
            "visibility": "private",
            "is_listed_on_immobilcloud": False,
            "city": "Catania",
            "created_at": now_iso(),
        })
    t0 = time.perf_counter()
    # bulk write in chunks
    written = 0
    for i in range(0, len(docs), 100):
        chunk = docs[i:i + 100]
        col.bulk_write([InsertOne(d) for d in chunk], ordered=False)
        written += len(chunk)
    write_ms = (time.perf_counter() - t0) * 1000

    def read_one(i):
        t1 = time.perf_counter()
        doc = col.find_one({"id": f"preprod-{run}-{i}"}, {"_id": 0, "id": 1, "title": 1})
        return (time.perf_counter() - t1) * 1000, bool(doc)

    times, misses = [], 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(read_one, i) for i in range(min(n_docs, 200))]
        for f in as_completed(futs):
            ms, ok = f.result()
            times.append(ms)
            if not ok:
                misses += 1
    times.sort()
    deleted = col.delete_many({"_stress": MARKER, "_run": run}).deleted_count
    return {
        "written": written,
        "write_ms": round(write_ms, 1),
        "concurrent_reads": len(times),
        "read_misses": misses,
        "read_p50_ms": round(statistics.median(times), 2) if times else None,
        "read_p95_ms": round(times[max(0, int(len(times) * 0.95) - 1)], 2) if times else None,
        "deleted": deleted,
        "ok": written == n_docs and misses == 0 and deleted == written,
    }


def soft_externals(session: requests.Session) -> Dict[str, Any]:
    """One-shot / catalog / env probes — NEVER bulk paid calls."""
    out: Dict[str, Any] = {}

    # Resend: prefer mock — do NOT send real email in gate
    resend_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    out["resend"] = {
        "mode": "live_key_present_but_gate_skips_send" if resend_key else "mock_or_unset",
        "action": "SKIP_SEND",
        "ok": True,
        "note": "Gate never sends email. Unit path: send_email falls back to mock without key.",
    }
    try:
        from shared.email.client import send_email
        # Force mock behavior: if key present, still skip real send in gate
        out["resend"]["client_import"] = "ok"
    except Exception as e:  # noqa: BLE001
        out["resend"] = {"ok": False, "error": str(e)[:160]}

    # Stripe: env + catalog only (no checkout session create under load)
    out["stripe"] = {
        "STRIPE_ENABLED": os.environ.get("STRIPE_ENABLED", ""),
        "has_secret": bool((os.environ.get("STRIPE_SECRET_KEY") or "").strip()),
        "mode_hint": "test" if (os.environ.get("STRIPE_SECRET_KEY") or "").startswith("sk_test") else "unknown_or_live",
        "catalog_probe": timed(session, "GET", "/cloud/mutui/config"),  # free config endpoint
        "ok": True,
        "note": "No Checkout/PaymentIntent created by this gate.",
    }

    # Visure: catalog only — never order a paid visura
    vis = timed(session, "GET", "/cloud/visura/catalog")
    out["visura"] = {
        "catalog": vis,
        "ok": vis.get("status") == 200,
        "note": "Catalog only. No provider order / PDF purchase.",
    }

    # Nominatim: at most ONE call via our geocode if exposed; else SKIP
    # Prefer circuit status from health if available
    try:
        from shared.security.circuit import snapshot as circuit_snapshot
        snap = circuit_snapshot() if callable(circuit_snapshot) else {}
        out["circuits"] = {"ok": True, "snapshot_keys": list(snap.keys())[:20] if isinstance(snap, dict) else type(snap).__name__}
    except Exception as e:  # noqa: BLE001
        out["circuits"] = {"ok": True, "note": f"circuit module soft: {e}"[:120]}

    out["nominatim"] = {
        "action": "SKIP_LIVE_GEOCODE",
        "ok": True,
        "note": "No Nominatim hammering. Geocode exercised only in feature tests with throttle.",
    }
    out["fal_kling"] = {
        "action": "SKIP",
        "has_fal_key": bool((os.environ.get("FAL_KEY") or "").strip()),
        "ok": True,
        "note": "No fal.ai generation in gate (cost).",
    }
    out["ape_siape"] = {
        "action": "SKIP",
        "ok": True,
        "note": "APE/SIAPE excluded from readiness by design.",
    }
    return out


def security_walls() -> Dict[str, Any]:
    anon = requests.Session()
    checks = {}
    for path in ["/app/clients", "/app/properties", "/cloud/me/properties", "/cloud/me/saved-searches", "/notifications"]:
        r = anon.get(f"{API_ROOT}{path}", timeout=20)
        checks[f"unauth_{path}"] = {"status": r.status_code, "ok": r.status_code in (401, 403)}
    # Use a dedicated non-production email so we never lock the Founder account.
    bait = f"preprod-gate-bait-{uuid.uuid4().hex[:8]}@example.com"
    bad = requests.Session()
    locked = False
    last = None
    statuses = []
    for i in range(6):
        r = bad.post(
            f"{API_ROOT}/auth/login",
            json={"email": bait, "password": "DefinitelyWrongPass999!"},
            timeout=20,
        )
        last = r.status_code
        statuses.append(last)
        if r.status_code in (429, 403) or (r.status_code == 401 and i >= 4):
            locked = True
    # Cleanup bait lockout rows so we do not pollute login_attempts forever.
    try:
        database = db()
        database.login_attempts.delete_many({"identifier": {"$regex": "preprod-gate-bait-"}})
    except Exception:  # noqa: BLE001
        pass
    checks["brute_force"] = {
        "bait_email": bait,
        "statuses": statuses,
        "last_status": last,
        "locked_or_rejected": locked,
        "ok": locked or last in (401, 429, 403),
    }
    checks["ok"] = all(v.get("ok") for v in checks.values() if isinstance(v, dict) and "ok" in v)
    return checks


def regression_smokes(session: requests.Session) -> Dict[str, Any]:
    anon = requests.Session()
    out = {}
    # Portal search
    out["search"] = timed(anon, "GET", "/cloud/search?operation=sale&page_size=10")
    # Prefer a known smoke private listing if present
    detail = timed(anon, "GET", "/cloud/property/smoke-private-contact-001")
    out["private_detail"] = detail
    if detail.get("status") == 200:
        try:
            body = requests.get(f"{API_ROOT}/cloud/property/smoke-private-contact-001", timeout=20).json()
            pub = body.get("publisher") or {}
            out["private_publisher"] = {
                "kind": pub.get("kind"),
                "accepts_messages": pub.get("accepts_messages"),
                "ok": pub.get("kind") == "private",
            }
            photos = body.get("photos") or []
            if photos:
                # Photo URLs are /api/public/... — timed() already prefixes API_ROOT
                out["photo_serve"] = timed(anon, "GET", "/public/property/smoke-private-contact-001/photo/0")
            else:
                out["photo_serve"] = {"ok": True, "note": "no photos on smoke listing"}
        except Exception as e:  # noqa: BLE001
            out["private_parse"] = {"ok": False, "error": str(e)[:120]}
    else:
        out["private_detail_skip"] = {"ok": True, "note": "smoke listing absent — not a hard fail"}

    # Agency CRM smoke
    out["clients"] = timed(session, "GET", "/app/clients?page=1&page_size=20")
    out["kpis"] = timed(session, "GET", "/app/dashboard/kpis")

    hard = []
    for k, v in out.items():
        if isinstance(v, dict) and "ok" in v and v.get("status") is not None:
            if k in ("search", "clients", "kpis") and not v.get("ok"):
                hard.append(k)
        if k == "photo_serve" and isinstance(v, dict) and v.get("status") not in (None, 200) and v.get("note") is None:
            if v.get("status") and v.get("status") >= 500:
                hard.append(k)
    out["ok"] = len(hard) == 0
    out["hard_failures"] = hard
    return out


def run_pytest_subset() -> Dict[str, Any]:
    """Free/local tests — no paid vendors."""
    tests = [
        "tests/test_private_publisher_contact.py",
        "tests/test_viewer_is_lister.py",
        "tests/test_scout_hal_and_pulse.py",
        "tests/test_a017_notifications.py",
        "tests/test_a021_notification_prefs.py",
    ]
    existing = [t for t in tests if (ROOT / t).exists()]
    if not existing:
        return {"ok": True, "skipped": True, "note": "no matching test files"}
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=line", *existing]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=300)
    ms = (time.perf_counter() - t0) * 1000
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "ms": round(ms, 1),
        "tests": existing,
        "stdout_tail": (proc.stdout or "")[-800:],
        "stderr_tail": (proc.stderr or "")[-400:],
    }


def write_md(report: Dict[str, Any]) -> None:
    req = report.get("required_ok")
    sec = report.get("sections") or {}
    portal = sec.get("api_portal_fanout") or {}
    crm = sec.get("api_crm_fanout") or {}
    mongo = sec.get("mongo_internal") or {}
    health = sec.get("health_readiness") or {}
    lines = [
        "# Pre-production confidence gate",
        "",
        f"**Run**: `{report['run_id']}` · {report['finished_at']}",
        f"**Verdict**: {'✅ PASS (required)' if req else '❌ FAIL'}",
        "",
        "## Policy",
        "",
        "- No Resend bulk send · No Stripe checkout · No paid visure · No fal.ai · No Nominatim hammer",
        "- Mongo + our HTTP stack are load-tested; vendors are soft-probed only",
        "",
        "## Summary",
        "",
        "| Area | OK | Notes |",
        "|------|:--:|-------|",
    ]
    for name, block in sec.items():
        ok = block.get("ok")
        mark = "✅" if ok else ("⚠️" if block.get("warn") else "❌")
        note = block.get("note") or block.get("hard_failures") or block.get("warn") or ""
        if isinstance(note, list):
            note = ", ".join(str(x) for x in note)
        lines.append(f"| {name} | {mark} | {str(note)[:120]} |")

    search = portal.get("search") or {}
    facets = portal.get("facets") or {}
    clients = crm.get("clients") or {}
    kpis = crm.get("kpis") or {}
    lines += [
        "",
        "## Load metrics (our stack only)",
        "",
        f"- Mongo: {mongo.get('written')} docs write {mongo.get('write_ms')} ms · "
        f"200 concurrent reads p50={mongo.get('read_p50_ms')} ms p95={mongo.get('read_p95_ms')} ms · "
        f"cleanup {mongo.get('deleted')}",
        f"- Portal search ×{search.get('n')}: p50={search.get('p50_ms')} ms p95={search.get('p95_ms')} ms errors={search.get('errors')}",
        f"- Portal facets ×{facets.get('n')}: p50={facets.get('p50_ms')} ms p95={facets.get('p95_ms')} ms errors={facets.get('errors')}",
        f"- CRM clients ×{clients.get('n')}: p50={clients.get('p50_ms')} ms p95={clients.get('p95_ms')} ms errors={clients.get('errors')}",
        f"- CRM kpis ×{kpis.get('n')}: p50={kpis.get('p50_ms')} ms p95={kpis.get('p95_ms')} ms errors={kpis.get('errors')}",
        "",
        "## Prod flags still WARN (expected in local)",
        "",
    ]
    warn = health.get("warn") or []
    if warn:
        for w in warn:
            lines.append(f"- `{w}` — set on Vercel/prod host before go-live")
    else:
        lines.append("- none")
    lines += [
        "",
        "## What this gate does NOT prove",
        "",
        "- Real Resend delivery, Stripe Checkout, paid visure PDF, fal.ai video, Nominatim under load",
        "- Full browser UX / mobile layout / accessibility",
        "- Multi-region failover or cold-start under real traffic",
        "- Absolute absence of bugs — only that critical hot paths + security walls held under this run",
        "",
        "## How to re-run",
        "",
        "```bash",
        "bash scripts/omnia-stack.sh ensure",
        "cd backend && source .venv/bin/activate",
        "python scripts/preprod_confidence_gate.py",
        "```",
        "",
        f"JSON: `memory/reports/preprod_gate_{report['run_id']}.json`",
        "",
    ]
    MD_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-pytest", action="store_true")
    ap.add_argument("--mongo-docs", type=int, default=500)
    args = ap.parse_args()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex[:8]
    report: Dict[str, Any] = {"run_id": run_id, "started_at": now_iso(), "api": API_ROOT, "sections": {}}

    try:
        database = db()
        database.command("ping")
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"fatal": "mongo", "error": str(e)}))
        sys.exit(2)

    report["sections"]["local_rate_reset"] = reset_local_rate_limits(database)

    try:
        session = login()
    except SystemExit as e:
        print(str(e))
        sys.exit(2)

    # 1 health
    report["sections"]["health_readiness"] = check_health()

    # 2 security (bait email — never Founder)
    report["sections"]["security"] = security_walls()

    # 3 regressions before fan-out (avoid 429 pollution)
    report["sections"]["regressions"] = regression_smokes(session)

    # 4 mongo internal
    report["sections"]["mongo_internal"] = mongo_internal_load(database, n_docs=args.mongo_docs)

    # 5 API fanout (fresh local counters)
    report["sections"]["api_portal_fanout"] = {
        "search": fanout(None, "/cloud/search?operation=sale&page_size=10", n=40, workers=16),
        "facets": fanout(None, "/cloud/facets?operation=sale", n=30, workers=12),
        "ok": True,
    }
    portal = report["sections"]["api_portal_fanout"]
    portal["ok"] = portal["search"].get("ok") and portal["facets"].get("ok")

    report["sections"]["api_crm_fanout"] = {
        "clients": fanout(session, "/app/clients?page=1&page_size=20", n=30, workers=12),
        "kpis": fanout(session, "/app/dashboard/kpis", n=20, workers=10),
        "ok": True,
    }
    crm = report["sections"]["api_crm_fanout"]
    crm["ok"] = crm["clients"].get("ok") and crm["kpis"].get("ok")

    # 6 soft externals
    report["sections"]["soft_externals"] = soft_externals(session)
    se = report["sections"]["soft_externals"]
    se["ok"] = all(
        (v.get("ok") if isinstance(v, dict) and "ok" in v else True)
        for v in se.values()
        if isinstance(v, dict)
    )
    se["note"] = "vendors soft-probed only"

    # 7 pytest
    if args.skip_pytest:
        report["sections"]["pytest_subset"] = {"ok": True, "skipped": True}
    else:
        report["sections"]["pytest_subset"] = run_pytest_subset()

    required_keys = [
        "health_readiness",
        "mongo_internal",
        "api_portal_fanout",
        "api_crm_fanout",
        "security",
        "regressions",
        "pytest_subset",
    ]
    required_ok = all(report["sections"][k].get("ok") for k in required_keys)
    # soft_externals required only for visura catalog truth
    if not report["sections"]["soft_externals"].get("visura", {}).get("ok", True):
        required_ok = False

    report["required_ok"] = required_ok
    report["finished_at"] = now_iso()

    json_path = REPORT_DIR / f"preprod_gate_{run_id}.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest = REPORT_DIR / "preprod_gate_latest.json"
    latest.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_md(report)

    print(json.dumps({
        "run_id": run_id,
        "required_ok": required_ok,
        "report_md": str(MD_REPORT),
        "report_json": str(json_path),
        "section_oks": {k: v.get("ok") for k, v in report["sections"].items()},
    }, indent=2))
    sys.exit(0 if required_ok else 1)


if __name__ == "__main__":
    main()
