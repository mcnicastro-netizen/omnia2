#!/usr/bin/env python3
"""OMNIA stress scale ladder — CRM clients + hot HTTP paths (D-072).

Scales synthetic CRM *clienti* (and light property set) then times critical APIs.

Usage (API must be up on :43121, from backend/ with venv):
  python scripts/stress_scale_ladder.py --tier 10
  python scripts/stress_scale_ladder.py --all
  python scripts/stress_scale_ladder.py --all --cleanup

Ladder: 10 → 50 → 500 → 1_000 → 5_000 → 10_000 clienti in ONE stress agency.
Also reports concurrent read fan-out (20 workers) at each tier.
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
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv
from pymongo import MongoClient, InsertOne

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")
load_dotenv(REPO / "memory" / "test_credentials.env")

TIERS = [10, 50, 500, 1000, 5000, 10000]
API = (os.environ.get("OMNIA_TEST_BASE") or os.environ.get("REACT_APP_BACKEND_URL") or "http://127.0.0.1:43121").rstrip("/")
if not API.endswith("/api") and "/api" not in API:
    # REACT_APP may be origin without /api
    pass
BASE = API if API.endswith("/api") or API.rstrip("/").endswith("43121") else API
# Normalize to http://host:port then /api
if BASE.rstrip("/").endswith("/api"):
    API_ROOT = BASE.rstrip("/")
else:
    API_ROOT = BASE.rstrip("/") + "/api"

EMAIL = os.environ.get("OMNIA_TEST_EMAIL") or os.environ.get("OMNIA_ADMIN_EMAIL") or "mcnicastro@gmail.com"
PASSWORD = os.environ.get("OMNIA_TEST_PASSWORD") or os.environ.get("OMNIA_ADMIN_PASSWORD") or "OmniaFounder2026!"

STRESS_AGENCY_ID = os.environ.get("STRESS_AGENCY_ID", "demo-agency-001")
STRESS_MARKER = "stress_ladder_v1"
REPORT_DIR = REPO / "memory" / "reports"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def db():
    return MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def ensure_agency_and_admin(database) -> str:
    """Ensure Founder is linked to stress agency; return user id."""
    admin = database.users.find_one({"email": EMAIL}, {"id": 1, "agency_ids": 1})
    if not admin:
        raise SystemExit(f"admin user {EMAIL} not found — login seed first")
    uid = admin["id"]
    if not database.agencies.find_one({"id": STRESS_AGENCY_ID}):
        raise SystemExit(
            f"agency {STRESS_AGENCY_ID} missing — set STRESS_AGENCY_ID or seed demo agency"
        )
    database.users.update_one(
        {"id": uid},
        {
            "$addToSet": {"agency_ids": STRESS_AGENCY_ID},
            "$set": {"active_agency_id": STRESS_AGENCY_ID, "updated_at": now_iso()},
        },
    )
    # Prefer stress agency as first id so /agencies/me (legacy first-id) matches
    u2 = database.users.find_one({"id": uid}, {"agency_ids": 1})
    ids = list(u2.get("agency_ids") or [])
    if ids and ids[0] != STRESS_AGENCY_ID and STRESS_AGENCY_ID in ids:
        ids = [STRESS_AGENCY_ID] + [x for x in ids if x != STRESS_AGENCY_ID]
        database.users.update_one({"id": uid}, {"$set": {"agency_ids": ids}})
    return uid


def seed_clients(database, n: int, run_id: str) -> float:
    """Replace stress clients to reach exactly n. Returns seconds."""
    filt = {"agency_id": STRESS_AGENCY_ID, "_stress": STRESS_MARKER}
    t0 = time.perf_counter()
    # Always wipe prior stress clients for this agency so schema stays valid
    database.clients.delete_many(filt)
    ops = []
    batch = 1000
    left = n
    idx = 0
    while left > 0:
        take = min(batch, left)
        for i in range(take):
            cid = f"stress-cli-{run_id}-{idx:06d}"
            ops.append(
                InsertOne(
                    {
                        "id": cid,
                        "agency_id": STRESS_AGENCY_ID,
                        "name": f"Cliente{idx}",
                        "surname": f"Stress{idx % 997}",
                        "email": f"stress{idx}@example.com",
                        "phone": f"+39333{idx:07d}"[:16],
                        "client_type": "buyer" if idx % 3 else "seller",
                        "status": "new",
                        "source": "stress_ladder",
                        "preferences": {
                            "cities": ["Catania" if idx % 2 == 0 else "Milano"],
                            "price_max": float(150000 + (idx % 50) * 10000),
                            "rooms_min": 2 + (idx % 3),
                            "operation": "sale",
                        },
                        "gdpr_consent": True,
                        "_stress": STRESS_MARKER,
                        "_stress_run": run_id,
                        "created_at": now_iso(),
                        "updated_at": now_iso(),
                    }
                )
            )
            idx += 1
        database.clients.bulk_write(ops, ordered=False)
        ops = []
        left -= take
    # light property set (max 200) for list pressure
    pfilt = {"agency_id": STRESS_AGENCY_ID, "_stress": STRESS_MARKER}
    database.properties.delete_many(pfilt)
    target_props = min(200, max(20, n // 50))
    pops = []
    for i in range(target_props):
        pops.append(
            InsertOne(
                {
                    "id": f"stress-prop-{run_id}-{i:04d}",
                    "agency_id": STRESS_AGENCY_ID,
                    "title": f"Stress Immobile {i}",
                    "status": "active",
                    "operation": "sale",
                    "property_type": "appartamento",
                    "city": "Catania",
                    "province": "CT",
                    "price": 120000 + i * 1000,
                    "surface_sqm": 60 + i,
                    "rooms": 3,
                    "visibility": "public",
                    "_stress": STRESS_MARKER,
                    "created_at": now_iso(),
                    "updated_at": now_iso(),
                }
            )
        )
    if pops:
        database.properties.bulk_write(pops, ordered=False)
    return time.perf_counter() - t0


def login_session() -> requests.Session:
    s = requests.Session()
    r = s.post(
        f"{API_ROOT}/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=30,
    )
    if r.status_code != 200:
        raise SystemExit(f"login failed {r.status_code}: {r.text[:200]}")
    # pin active agency
    s.post(
        f"{API_ROOT}/auth/active-agency",
        json={"agency_id": STRESS_AGENCY_ID},
        timeout=15,
    )
    return s


def time_get(session: requests.Session, path: str, timeout: float = 60) -> Tuple[int, float, int]:
    t0 = time.perf_counter()
    r = session.get(f"{API_ROOT}{path}", timeout=timeout)
    ms = (time.perf_counter() - t0) * 1000
    size = len(r.content or b"")
    return r.status_code, ms, size


def bench_endpoints(session: requests.Session) -> Dict[str, Any]:
    paths = [
        "/app/agencies/me",
        "/app/dashboard/kpis",
        "/app/clients?page=1&page_size=50",
        "/app/clients/smart?limit=50",
        "/app/properties?page=1&page_size=50",
        "/app/matches?min_score=40&limit=20",
        "/notifications?limit=20",
        "/notifications/unread-count",
        "/auth/me",
    ]
    out: Dict[str, Any] = {}
    for p in paths:
        try:
            code, ms, size = time_get(session, p)
            out[p] = {"status": code, "ms": round(ms, 1), "bytes": size}
        except Exception as e:  # noqa: BLE001
            out[p] = {"status": 0, "ms": None, "error": str(e)[:120]}
    return out


def concurrent_reads(session_factory, path: str, n: int = 40, workers: int = 20) -> Dict[str, Any]:
    """Fan-out GETs with fresh cookies from one logged session (reuse cookies)."""
    # Use one session cookies copied into threads via requests.Session
    base = session_factory()
    cookies = base.cookies.get_dict()

    def one(_i: int):
        s = requests.Session()
        s.cookies.update(cookies)
        return time_get(s, path)

    times: List[float] = []
    errors = 0
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(one, i) for i in range(n)]
        for f in as_completed(futs):
            code, ms, _ = f.result()
            if code != 200:
                errors += 1
            else:
                times.append(ms)
    wall = time.perf_counter() - t0
    if not times:
        return {"n": n, "errors": errors, "wall_s": round(wall, 3)}
    times.sort()
    p95 = times[int(0.95 * (len(times) - 1))]
    return {
        "path": path,
        "n": n,
        "workers": workers,
        "errors": errors,
        "wall_s": round(wall, 3),
        "p50_ms": round(statistics.median(times), 1),
        "p95_ms": round(p95, 1),
        "avg_ms": round(statistics.mean(times), 1),
        "max_ms": round(max(times), 1),
    }


def cleanup_stress(database) -> Dict[str, int]:
    deleted = {}
    for col in ("clients", "properties", "leads"):
        r = database[col].delete_many({"_stress": STRESS_MARKER})
        deleted[col] = r.deleted_count
    # keep agency for reuse unless --purge-agency
    return deleted


def run_tier(n: int, run_id: str, do_concurrency: bool) -> Dict[str, Any]:
    database = db()
    ensure_agency_and_admin(database)
    # ensure indexes helpful for list
    database.clients.create_index([("agency_id", 1), ("created_at", -1)])
    database.clients.create_index([("agency_id", 1), ("_stress", 1)])

    seed_s = seed_clients(database, n, run_id)
    count = database.clients.count_documents(
        {"agency_id": STRESS_AGENCY_ID, "_stress": STRESS_MARKER}
    )
    props = database.properties.count_documents(
        {"agency_id": STRESS_AGENCY_ID, "_stress": STRESS_MARKER}
    )

    session = login_session()
    endpoints = bench_endpoints(session)
    conc = None
    if do_concurrency:
        conc = {
            "clients_list": concurrent_reads(login_session, "/app/clients?page=1&page_size=50", n=40, workers=20),
            "dashboard": concurrent_reads(login_session, "/app/dashboard/kpis", n=40, workers=20),
            "properties": concurrent_reads(login_session, "/app/properties?page=1&page_size=50", n=40, workers=20),
            "clients_smart": concurrent_reads(login_session, "/app/clients/smart?limit=50", n=20, workers=10),
        }

    return {
        "tier_clients": n,
        "clients_in_db": count,
        "properties_in_db": props,
        "seed_seconds": round(seed_s, 3),
        "endpoints": endpoints,
        "concurrency": conc,
        "ts": now_iso(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", type=int, choices=TIERS)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--no-concurrency", action="store_true")
    ap.add_argument("--cleanup", action="store_true", help="Delete stress docs after run")
    ap.add_argument("--cleanup-only", action="store_true")
    args = ap.parse_args()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    database = db()

    if args.cleanup_only:
        print(cleanup_stress(database))
        return

    run_id = uuid.uuid4().hex[:8]
    tiers = TIERS if args.all else [args.tier or 10]
    results = []
    print(f"API={API_ROOT} run_id={run_id} tiers={tiers}")
    for n in tiers:
        print(f"\n=== CLIENTS TIER {n} ===")
        row = run_tier(n, run_id, do_concurrency=not args.no_concurrency)
        results.append(row)
        # compact stdout
        ep = row["endpoints"]
        print(
            f"seed={row['seed_seconds']}s clients={row['clients_in_db']} "
            f"GET /clients={ep.get('/app/clients?page=1&page_size=50')} "
            f"KPI={ep.get('/app/dashboard/kpis')}"
        )
        if row.get("concurrency"):
            print("concurrency:", json.dumps(row["concurrency"], ensure_ascii=False))

    report = {
        "kind": "crm_clients_ladder",
        "run_id": run_id,
        "api": API_ROOT,
        "agency_id": STRESS_AGENCY_ID,
        "tiers": results,
        "finished_at": now_iso(),
    }
    out_path = REPORT_DIR / f"stress_clients_{run_id}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest = REPORT_DIR / "stress_clients_latest.json"
    latest.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")

    if args.cleanup:
        print("cleanup:", cleanup_stress(database))


if __name__ == "__main__":
    main()
