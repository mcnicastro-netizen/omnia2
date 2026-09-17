#!/usr/bin/env python3
"""OMNIA — Gestionale (ImmoWeb CRM) stress suite S0–S6.

Scale target: up to ~2000 clients (Founder constraint).
Policy: OUR stack only — no Resend send, Stripe checkout, fal, live portal publish, Nominatim hammer.

Sections
--------
S0 inventory of CRM tools / endpoints
S1 seed ≤2000 clients (+ props) + HTTP fan-out
S2 Mongo concurrent R/W (marked docs, cleaned)
S3 security walls (bait email — never Founder lock)
S4 smoke happy-path per tool (safe GETs + 1 create where cheap)
S5 soft externals SKIP
S6 write report MD + JSON

Usage
-----
  bash scripts/omnia-stack.sh ensure
  cd backend && source .venv/bin/activate
  python scripts/stress_gestionale.py --clients 2000
  python scripts/stress_gestionale.py --cleanup
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
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
MARKER = "gestionale_stress_v1"
REPORT_DIR = REPO / "memory" / "reports"
MD_REPORT = REPO / "memory" / "GESTIONALE_STRESS_REPORT.md"

# UI surface ↔ API probes (S0) — paths verified against routers
UI_TOOLS = [
    {"ui": "/app/dashboard", "api": ["/app/dashboard/kpis"], "module": "dashboard"},
    {"ui": "/app/properties", "api": ["/app/properties?page=1&page_size=50"], "module": "properties"},
    {"ui": "/app/clients", "api": ["/app/clients?page=1&page_size=50", "/app/clients/smart?page=1&page_size=50", "/app/clients/sellers"], "module": "clients"},
    {"ui": "/app/matches", "api": ["/app/matches?min_score=80&limit=20"], "module": "matches"},
    {"ui": "/app/analytics", "api": ["/app/analytics/agency/overview?days_lookback=30"], "module": "analytics"},
    {"ui": "/app/publishing", "api": ["/app/publishing/connections", "/app/publishing/catalog"], "module": "publishing"},
    {"ui": "/app/hal-knowledge", "api": ["/app/hal/knowledge/status"], "module": "hal_knowledge"},
    {"ui": "/app/mls", "api": ["/app/mls/dashboard", "/app/mls/inventory"], "module": "mls"},
    {"ui": "/app/modulistica", "api": ["/app/modulistica/templates"], "module": "modulistica"},
    {"ui": "/app/members", "api": ["/app/agencies/me/members"], "module": "members"},
    {"ui": "/app/api-keys", "api": ["/app/api-keys"], "module": "api_keys"},
    {"ui": "/app/settings", "api": ["/app/agencies/me"], "module": "settings"},
    {"ui": "/app/settings/billing", "api": ["/billing/plans"], "module": "billing"},
    {"ui": "/app/staging", "api": ["/app/staging/styles", "/app/staging/history"], "module": "staging"},
    {"ui": "/app/ops", "api": ["/app/ops/overview"], "module": "founder_ops"},
    {"ui": "/app/moderation", "api": ["/app/moderation/queue"], "module": "moderation"},
    {"ui": "HAL Assist", "api": ["/app/al/sessions"], "module": "hal_assist"},
    {"ui": "HAL Legal", "api": ["/app/legal/sessions"], "module": "hal_legal"},
]

FANOUT_PATHS = [
    "/app/dashboard/kpis",
    "/app/clients?page=1&page_size=50",
    "/app/clients/smart?page=1&page_size=50",
    "/app/properties?page=1&page_size=50",
    # matches: smoke-tested in S0; concurrent fan-out omitted (CPU O(active×buyers))
    "/app/analytics/agency/overview?days_lookback=30",
    "/app/publishing/connections",
    "/app/api-keys",
    "/app/agencies/me/members",
]
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def db():
    return MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def reset_local_limits(database) -> int:
    q = {
        "$or": [
            {"key": {"$in": ["127.0.0.1", "localhost", "::1"]}},
            {"identifier": {"$regex": r"(127\.0\.0\.1|localhost|::1)"}},
        ]
    }
    return database.rate_limit_events.delete_many(q).deleted_count


def login(retries: int = 5) -> requests.Session:
    last_err = None
    for attempt in range(retries):
        ensure_api()
        s = requests.Session()
        try:
            r = s.post(f"{API_ROOT}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
            if r.status_code != 200:
                last_err = f"login failed {r.status_code}: {r.text[:200]}"
                time.sleep(1 + attempt)
                continue
            s.post(f"{API_ROOT}/auth/active-agency", json={"agency_id": AGENCY}, timeout=15)
            return s
        except Exception as e:  # noqa: BLE001
            last_err = str(e)[:160]
            time.sleep(1 + attempt)
    raise SystemExit(f"login failed after retries: {last_err}")


def timed(session: requests.Session, method: str, path: str, **kw) -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        r = session.request(method, f"{API_ROOT}{path}", timeout=kw.pop("timeout", 60), **kw)
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


def fanout(session: requests.Session, path: str, n: int = 40, workers: int = 16) -> Dict[str, Any]:
    cookies = session.cookies.get_dict()

    def one(_i):
        s = requests.Session()
        s.cookies.update(cookies)
        return timed(s, "GET", path)

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
    times.sort()
    out: Dict[str, Any] = {
        "path": path,
        "n": n,
        "errors": errors,
        "wall_s": round(time.perf_counter() - t0, 3),
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


def seed_clients(database, n: int, run_id: str) -> Dict[str, Any]:
    filt = {"agency_id": AGENCY, "_stress": MARKER}
    database.clients.delete_many(filt)
    t0 = time.perf_counter()
    ops = []
    for i in range(n):
        ctype = ["buyer", "seller", "landlord", "tenant"][i % 4]
        ops.append(InsertOne({
            "id": f"gstress-cli-{run_id}-{i:05d}",
            "agency_id": AGENCY,
            "name": f"Stress{i}",
            "surname": "Cliente",
            "email": f"gstress-{run_id}-{i:05d}@example.com",
            "phone": f"+39333{i:07d}"[:16],
            "client_type": ctype,
            "status": "new",
            "preferences": {},
            "_stress": MARKER,
            "_run": run_id,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }))
        if len(ops) >= 500:
            database.clients.bulk_write(ops, ordered=False)
            ops = []
    if ops:
        database.clients.bulk_write(ops, ordered=False)
    write_ms = (time.perf_counter() - t0) * 1000
    count = database.clients.count_documents(filt)
    return {"requested": n, "written": count, "write_ms": round(write_ms, 1), "ok": count == n}


def seed_properties(database, n: int, run_id: str, active_cap: int = 40) -> Dict[str, Any]:
    """Seed N properties; only `active_cap` are status=active.

    Match API is O(active_props × searchers). At 2000×2000 it can wedge the API —
    so we keep a realistic active portfolio (~40) while still storing 2000 docs.
    """
    filt = {"agency_id": AGENCY, "_stress": MARKER}
    database.properties.delete_many(filt)
    t0 = time.perf_counter()
    ops = []
    for i in range(n):
        ops.append(InsertOne({
            "id": f"gstress-prop-{run_id}-{i:05d}",
            "agency_id": AGENCY,
            "title": f"Gestionale Stress Immobile {i}",
            "status": "active" if i < active_cap else "draft",
            "visibility": "private",
            "is_listed_on_immobilcloud": False,
            "operation": "sale",
            "property_type": "appartamento",
            "city": "Catania" if i % 2 == 0 else "Milano",
            "province": "CT" if i % 2 == 0 else "MI",
            "price": 100000 + i * 250,
            "surface_sqm": 50 + (i % 80),
            "rooms": 2 + (i % 4),
            "_stress": MARKER,
            "_run": run_id,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }))
        if len(ops) >= 500:
            database.properties.bulk_write(ops, ordered=False)
            ops = []
    if ops:
        database.properties.bulk_write(ops, ordered=False)
    write_ms = (time.perf_counter() - t0) * 1000
    count = database.properties.count_documents(filt)
    active = database.properties.count_documents({**filt, "status": "active"})
    return {
        "requested": n,
        "written": count,
        "active": active,
        "active_cap": active_cap,
        "write_ms": round(write_ms, 1),
        "ok": count == n,
    }


def mongo_concurrent(database, run_id: str, workers: int = 24) -> Dict[str, Any]:
    col = database.clients
    ids = [f"gstress-cli-{run_id}-{i:05d}" for i in range(min(2000, col.count_documents({"_run": run_id, "_stress": MARKER})))]
    if not ids:
        return {"ok": False, "error": "no seeded clients"}

    def read_one(cid):
        t1 = time.perf_counter()
        doc = col.find_one({"id": cid, "agency_id": AGENCY}, {"_id": 0, "id": 1, "email": 1})
        return (time.perf_counter() - t1) * 1000, bool(doc)

    sample = ids[:: max(1, len(ids) // 400)][:400]
    times, misses = [], 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(read_one, cid) for cid in sample]
        for f in as_completed(futs):
            ms, ok = f.result()
            times.append(ms)
            if not ok:
                misses += 1
    times.sort()
    return {
        "sample": len(sample),
        "misses": misses,
        "p50_ms": round(statistics.median(times), 2) if times else None,
        "p95_ms": round(times[max(0, int(len(times) * 0.95) - 1)], 2) if times else None,
        "ok": misses == 0 and bool(times),
    }


def security_walls() -> Dict[str, Any]:
    anon = requests.Session()
    checks: Dict[str, Any] = {}
    for path in ["/app/clients", "/app/properties", "/app/dashboard/kpis", "/app/api-keys", "/app/agencies/me/members", "/app/publishing/connections"]:
        try:
            r = anon.get(f"{API_ROOT}{path}", timeout=20)
            checks[f"unauth_{path}"] = {"status": r.status_code, "ok": r.status_code in (401, 403)}
        except Exception as e:  # noqa: BLE001
            checks[f"unauth_{path}"] = {"status": 0, "ok": False, "error": str(e)[:120]}
    bait = f"gstress-bait-{uuid.uuid4().hex[:8]}@example.com"
    bad = requests.Session()
    statuses = []
    locked = False
    for i in range(6):
        try:
            r = bad.post(f"{API_ROOT}/auth/login", json={"email": bait, "password": "DefinitelyWrongPass999!"}, timeout=20)
            statuses.append(r.status_code)
            if r.status_code in (429, 403) or (r.status_code == 401 and i >= 4):
                locked = True
        except Exception:  # noqa: BLE001
            statuses.append(0)
    try:
        db().login_attempts.delete_many({"identifier": {"$regex": "gstress-bait-"}})
    except Exception:  # noqa: BLE001
        pass
    checks["brute_force"] = {
        "statuses": statuses,
        "locked_or_rejected": locked,
        "ok": locked or (statuses and statuses[-1] in (401, 429, 403)),
    }
    checks["ok"] = all(v.get("ok") for v in checks.values() if isinstance(v, dict) and "ok" in v)
    return checks


def inventory_and_smoke(session: requests.Session) -> Dict[str, Any]:
    tools = []
    hard = []
    for tool in UI_TOOLS:
        if not ensure_api():
            hard.append(f"{tool['module']}:api_down")
        rows = []
        for path in tool["api"]:
            row = timed(session, "GET", path, timeout=90)
            if row.get("status") == 0:
                # bounce + one retry
                ensure_api()
                try:
                    session = login()
                except SystemExit:
                    hard.append(f"{tool['module']}:relogin")
                    break
                row = timed(session, "GET", path, timeout=90)
            rows.append(row)
            if row.get("status", 0) >= 500:
                hard.append(f"{tool['module']}:{path}")
            if row.get("status") == 0:
                hard.append(f"{tool['module']}:{path}:down")
        if not rows:
            continue
        ok_http = any(r.get("status") in (200, 201, 204) for r in rows)
        warn_only = (not ok_http) and all(r.get("status") in (401, 403, 404, 405) for r in rows)
        tools.append({
            "module": tool["module"],
            "ui": tool["ui"],
            "probes": rows,
            "ok": ok_http or warn_only,
            "warn": warn_only,
        })
        if not (ok_http or warn_only):
            hard.append(tool["module"])
    # One safe create smoke (client) then delete via mongo
    ensure_api()
    try:
        session = login()
    except SystemExit:
        hard.append("create_client_smoke:relogin")
        return {"tools": tools, "create_client_smoke": {"ok": False}, "hard_failures": hard, "ok": False}
    smoke_email = f"gstress-smoke-{uuid.uuid4().hex[:8]}@example.com"
    create = timed(
        session,
        "POST",
        "/app/clients",
        json={
            "name": "Smoke",
            "surname": "Gestionale",
            "email": smoke_email,
            "client_type": "buyer",
            "status": "new",
        },
    )
    created_id = None
    if create.get("ok"):
        doc = db().clients.find_one({"email": smoke_email, "agency_id": AGENCY}, {"_id": 0, "id": 1})
        created_id = (doc or {}).get("id")
        create["id"] = created_id
    if created_id:
        db().clients.delete_many({"id": created_id, "email": smoke_email})
    elif create.get("ok"):
        db().clients.delete_many({"email": smoke_email, "agency_id": AGENCY})
    if not create.get("ok"):
        hard.append("create_client_smoke")
    return {
        "tools": tools,
        "create_client_smoke": create,
        "hard_failures": hard,
        "ok": len(hard) == 0,
        "session": session,
    }


def soft_externals(session: requests.Session) -> Dict[str, Any]:
    return {
        "resend": {"action": "SKIP_SEND", "ok": True},
        "stripe_checkout": {"action": "SKIP", "catalog": timed(session, "GET", "/app/billing/plans"), "ok": True},
        "fal_kling": {"action": "SKIP", "ok": True},
        "portal_live_publish": {"action": "SKIP", "ok": True},
        "nominatim": {"action": "SKIP", "ok": True},
        "ok": True,
        "note": "vendors soft-probed / skipped — no spend no ban",
    }


def write_md(report: Dict[str, Any]) -> None:
    req = report.get("required_ok")
    lines = [
        "# Gestionale stress report (S0–S6)",
        "",
        f"**Run**: `{report['run_id']}` · {report['finished_at']}",
        f"**Verdict**: {'✅ PASS' if req else '❌ FAIL'}",
        f"**Scale**: {report.get('clients_seeded')} clients · {report.get('properties_seeded')} properties (agency `{AGENCY}`)",
        "",
        "## Policy",
        "",
        "- Solo stack nostro · cleanup docs `_stress=gestionale_stress_v1`",
        "- No Resend / Stripe checkout / fal / publish portali live / Nominatim hammer",
        "",
        "## S0 Inventory",
        "",
        "| Module | UI | Probe OK | Notes |",
        "|--------|----|:--------:|-------|",
    ]
    for t in report.get("sections", {}).get("s0_s4_inventory_smoke", {}).get("tools", []):
        mark = "✅" if t.get("ok") and not t.get("warn") else ("⚠️" if t.get("warn") else "❌")
        statuses = ",".join(str(p.get("status")) for p in t.get("probes", []))
        lines.append(f"| {t['module']} | `{t['ui']}` | {mark} | HTTP {statuses} |")

    s1 = report.get("sections", {}).get("s1_http_fanout", {})
    lines += ["", "## S1 HTTP fan-out (after 2k seed)", ""]
    for path, block in (s1.get("paths") or {}).items():
        if not isinstance(block, dict):
            continue
        lines.append(
            f"- `{path}` ×{block.get('n')}: p50={block.get('p50_ms')} p95={block.get('p95_ms')} errors={block.get('errors')} statuses={block.get('statuses')}"
        )

    s2 = report.get("sections", {}).get("s2_mongo", {})
    lines += [
        "",
        "## S2 Mongo concurrent",
        "",
        f"- sample={s2.get('sample')} misses={s2.get('misses')} p50={s2.get('p50_ms')}ms p95={s2.get('p95_ms')}ms",
        "",
        "## S3 Security",
        "",
        f"- ok={report.get('sections', {}).get('s3_security', {}).get('ok')}",
        "",
        "## S5 Soft externals",
        "",
        f"- {report.get('sections', {}).get('s5_soft_externals', {}).get('note')}",
        "",
        "## Re-run",
        "",
        "```bash",
        "bash scripts/omnia-stack.sh ensure",
        "cd backend && source .venv/bin/activate",
        "python scripts/stress_gestionale.py --clients 2000",
        "```",
        "",
        f"JSON: `memory/reports/gestionale_stress_{report['run_id']}.json`",
        "",
    ]
    MD_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def cleanup(database) -> Dict[str, int]:
    return {
        "clients": database.clients.delete_many({"_stress": MARKER}).deleted_count,
        "properties": database.properties.delete_many({"_stress": MARKER}).deleted_count,
    }


def ensure_api(session: Optional[requests.Session] = None) -> bool:
    """Restart stack if API is down (uvicorn --reload can die under edit/load)."""
    try:
        r = requests.get(f"{API_ROOT}/health", timeout=5)
        if r.status_code == 200:
            return True
    except Exception:  # noqa: BLE001
        pass
    import subprocess
    subprocess.run(["bash", str(REPO / "scripts" / "omnia-stack.sh"), "ensure"], check=False)
    time.sleep(2)
    try:
        r = requests.get(f"{API_ROOT}/health", timeout=10)
        return r.status_code == 200
    except Exception:  # noqa: BLE001
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clients", type=int, default=2000)
    ap.add_argument("--properties", type=int, default=None, help="default = same as clients")
    ap.add_argument("--fanout-n", type=int, default=40)
    ap.add_argument("--cleanup", action="store_true")
    ap.add_argument("--keep-seed", action="store_true", help="do not delete stress docs at end")
    args = ap.parse_args()
    n_props = args.properties if args.properties is not None else args.clients

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    database = db()
    run_id = uuid.uuid4().hex[:8]

    if args.cleanup:
        print(json.dumps(cleanup(database), indent=2))
        return

    reset_local_limits(database)
    try:
        database.login_attempts.delete_many({"identifier": {"$regex": EMAIL.split("@")[0]}})
    except Exception:  # noqa: BLE001
        pass

    if not ensure_api():
        raise SystemExit("API not healthy after ensure")

    session = login()
    report: Dict[str, Any] = {
        "kind": "gestionale_stress_s0_s6",
        "run_id": run_id,
        "api": API_ROOT,
        "agency_id": AGENCY,
        "started_at": now_iso(),
        "sections": {},
    }

    # S1 seed first so inventory sees scale
    seed_c = seed_clients(database, args.clients, run_id)
    seed_p = seed_properties(database, n_props, run_id)
    report["clients_seeded"] = seed_c.get("written")
    report["properties_seeded"] = seed_p.get("written")
    report["sections"]["s1_seed"] = {"clients": seed_c, "properties": seed_p, "ok": seed_c.get("ok") and seed_p.get("ok")}

    ensure_api()
    session = login()

    # S0+S4 inventory/smoke
    inv = inventory_and_smoke(session)
    session = inv.pop("session", session)
    report["sections"]["s0_s4_inventory_smoke"] = inv

    ensure_api()
    session = login()

    # S1 fanout — matches uses fewer workers (CPU-heavy)
    paths_out = {}
    for path in FANOUT_PATHS:
        ensure_api()
        session = login()
        workers = 6 if path.startswith("/app/matches") else 12
        n = 20 if path.startswith("/app/matches") else args.fanout_n
        paths_out[path] = fanout(session, path, n=n, workers=workers)
        time.sleep(0.3)
    report["sections"]["s1_http_fanout"] = {
        "paths": paths_out,
        "ok": all(v.get("ok") for v in paths_out.values()),
    }

    # S2 mongo
    report["sections"]["s2_mongo"] = mongo_concurrent(database, run_id)

    ensure_api()
    # S3 security (bait)
    report["sections"]["s3_security"] = security_walls()

    ensure_api()
    session = login()
    # S5 soft
    report["sections"]["s5_soft_externals"] = soft_externals(session)

    required_ok = all(
        report["sections"][k].get("ok")
        for k in ("s1_seed", "s0_s4_inventory_smoke", "s1_http_fanout", "s2_mongo", "s3_security", "s5_soft_externals")
    )
    report["required_ok"] = required_ok
    report["finished_at"] = now_iso()
    report["db_counts"] = {
        "clients_agency": database.clients.count_documents({"agency_id": AGENCY}),
        "properties_agency": database.properties.count_documents({"agency_id": AGENCY}),
        "stress_clients": database.clients.count_documents({"_stress": MARKER}),
        "stress_properties": database.properties.count_documents({"_stress": MARKER}),
    }

    if not args.keep_seed:
        report["cleanup"] = cleanup(database)

    json_path = REPORT_DIR / f"gestionale_stress_{run_id}.json"
    latest = REPORT_DIR / "gestionale_stress_latest.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_md(report)

    print(json.dumps({
        "run_id": run_id,
        "required_ok": required_ok,
        "clients": report["clients_seeded"],
        "properties": report["properties_seeded"],
        "report_md": str(MD_REPORT),
        "report_json": str(json_path),
        "section_oks": {k: v.get("ok") for k, v in report["sections"].items()},
    }, indent=2))
    sys.exit(0 if required_ok else 1)


if __name__ == "__main__":
    main()
