#!/usr/bin/env python3
"""OMNIA — full-platform stress & resilience suite.

Covers (as available in this environment):
  - CRM gestionale hot paths
  - ImmobilCloud portal search/map/detail/advanced
  - API keys gateway (/api/v1)
  - DB connectivity / indexes smoke
  - Security: brute-force lockout, rate limits, unauth walls
  - Payments: Stripe catalog endpoints (test mode / graceful degrade)
  - Anti-crash: concurrent fan-out without 5xx spike

Usage:
  cd backend && source .venv/bin/activate
  python scripts/stress_platform_full.py
  python scripts/stress_platform_full.py --seed-portal 2000
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

API = (os.environ.get("OMNIA_TEST_BASE") or os.environ.get("REACT_APP_BACKEND_URL") or "http://127.0.0.1:43121").rstrip("/")
API_ROOT = API if API.endswith("/api") else API + "/api"
EMAIL = os.environ.get("OMNIA_TEST_EMAIL") or os.environ.get("OMNIA_ADMIN_EMAIL") or "mcnicastro@gmail.com"
PASSWORD = os.environ.get("OMNIA_TEST_PASSWORD") or os.environ.get("OMNIA_ADMIN_PASSWORD") or "OmniaFounder2026!"
AGENCY = os.environ.get("STRESS_AGENCY_ID", "demo-agency-001")
MARKER = "platform_stress_v1"
REPORT_DIR = REPO / "memory" / "reports"


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
        r = session.request(method, f"{API_ROOT}{path}", timeout=kw.pop("timeout", 60), **kw)
        ms = (time.perf_counter() - t0) * 1000
        return {"path": path, "method": method, "status": r.status_code, "ms": round(ms, 1), "bytes": len(r.content or b"")}
    except Exception as e:  # noqa: BLE001
        return {"path": path, "method": method, "status": 0, "ms": None, "error": str(e)[:160]}


def fanout(session: requests.Session, path: str, n: int = 30, workers: int = 15) -> Dict[str, Any]:
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
            if row.get("status") != 200:
                errors += 1
            elif row.get("ms") is not None:
                times.append(row["ms"])
    wall = time.perf_counter() - t0
    times.sort()
    out: Dict[str, Any] = {"path": path, "n": n, "errors": errors, "wall_s": round(wall, 3), "statuses": sorted(set(statuses))}
    if times:
        out.update({
            "p50_ms": round(statistics.median(times), 1),
            "p95_ms": round(times[int(0.95 * (len(times) - 1))], 1),
            "avg_ms": round(statistics.mean(times), 1),
            "max_ms": round(max(times), 1),
        })
    return out


def seed_portal_listings(database, n: int, run_id: str) -> float:
    filt = {"agency_id": AGENCY, "_stress": MARKER}
    t0 = time.perf_counter()
    database.properties.delete_many(filt)
    ops = []
    for i in range(n):
        ops.append(InsertOne({
            "id": f"pstress-prop-{run_id}-{i:05d}",
            "agency_id": AGENCY,
            "title": f"Platform Stress {i}",
            "status": "active",
            "visibility": "public",
            "is_listed_on_immobilcloud": True,
            "moderation_status": "approved",
            "operation": "sale",
            "property_type": "appartamento",
            "city": "Catania" if i % 2 == 0 else "Milano",
            "province": "CT" if i % 2 == 0 else "MI",
            "province_sigla": "CT" if i % 2 == 0 else "MI",
            "price": 120000 + i * 500,
            "surface_sqm": 60 + (i % 40),
            "rooms": 2 + (i % 3),
            "bedrooms": 1 + (i % 3),
            "lat": 37.5 + (i % 100) * 0.001,
            "lng": 15.0 + (i % 100) * 0.001,
            "privacy_level": "L2",
            "_stress": MARKER,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "view_count": i % 50,
        }))
        if len(ops) >= 500:
            database.properties.bulk_write(ops, ordered=False)
            ops = []
    if ops:
        database.properties.bulk_write(ops, ordered=False)
    return time.perf_counter() - t0


def ensure_indexes(database) -> List[str]:
    created = []
    for spec in (
        ([("agency_id", 1), ("status", 1), ("visibility", 1)], "props_agency_vis"),
        ([("is_listed_on_immobilcloud", 1), ("status", 1)], "props_cloud"),
        ([("city", 1), ("operation", 1)], "props_city_op"),
        ([("identifier", 1), ("created_at", -1)], "rate_limit_ident"),
    ):
        try:
            name = database.properties.create_index(spec[0]) if "props" in spec[1] else database.rate_limit_events.create_index(spec[0])
            created.append(str(name))
        except Exception as e:  # noqa: BLE001
            created.append(f"err:{e}")
    return created


def security_checks(session: requests.Session) -> Dict[str, Any]:
    anon = requests.Session()
    checks = {}
    # Unauth walls
    for path in ["/app/clients", "/app/properties", "/app/api-keys", "/cloud/me/favorites", "/cloud/me/saved-searches"]:
        r = anon.get(f"{API_ROOT}{path}", timeout=20)
        checks[f"unauth_{path}"] = {"status": r.status_code, "ok": r.status_code in (401, 403)}
    # Brute force
    bad = requests.Session()
    locked = False
    for i in range(7):
        r = bad.post(f"{API_ROOT}/auth/login", json={"email": EMAIL, "password": "DefinitelyWrongPass999!"}, timeout=20)
        if r.status_code == 429 or (r.status_code == 401 and i >= 4):
            locked = r.status_code in (401, 429, 403)
    checks["brute_force_attempts"] = {"locked_or_rejected": locked}
    # Rate limit smoke on public search (soft — may not trip at 120)
    rl_hit = False
    for _ in range(5):
        r = anon.get(f"{API_ROOT}/cloud/search?operation=sale&page_size=5", timeout=20)
        if r.status_code == 429:
            rl_hit = True
            break
    checks["rate_limit_endpoint_alive"] = {"sample_status": r.status_code, "tripped_in_5": rl_hit, "ok": r.status_code in (200, 429)}
    return checks


def payments_checks(session: requests.Session) -> Dict[str, Any]:
    out = {}
    for path in ["/app/billing/plans", "/cloud/visura/catalog", "/cloud/mutui/config"]:
        out[path] = timed(session, "GET", path)
    # Stripe enabled flag / healthish
    out["stripe_env"] = {
        "STRIPE_ENABLED": os.environ.get("STRIPE_ENABLED", ""),
        "has_secret": bool(os.environ.get("STRIPE_SECRET_KEY")),
        "mode_hint": "test" if (os.environ.get("STRIPE_SECRET_KEY") or "").startswith("sk_test") else "unknown_or_live",
    }
    return out


def api_key_checks(session: requests.Session, database) -> Dict[str, Any]:
    # Prefer an existing active key plaintext is unavailable — probe /api/v1/health (no auth)
    health = timed(requests.Session(), "GET", "/v1/health")
    # List keys as admin (no plaintext)
    listed = timed(session, "GET", "/app/api-keys")
    return {"v1_health": health, "api_keys_list": listed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-portal", type=int, default=0, help="Seed N public listings for portal load")
    ap.add_argument("--cleanup", action="store_true")
    args = ap.parse_args()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    database = db()
    run_id = uuid.uuid4().hex[:8]

    if args.cleanup:
        d = database.properties.delete_many({"_stress": MARKER})
        print({"deleted_properties": d.deleted_count})
        return

    indexes = ensure_indexes(database)
    seed_s = None
    if args.seed_portal:
        seed_s = seed_portal_listings(database, args.seed_portal, run_id)

    session = login()
    anon = requests.Session()

    crm = {
        "clients": timed(session, "GET", "/app/clients?page=1&page_size=50"),
        "clients_smart": timed(session, "GET", "/app/clients/smart?page=1&page_size=50"),
        "properties": timed(session, "GET", "/app/properties?page=1&page_size=50"),
        "kpis": timed(session, "GET", "/app/dashboard/kpis"),
        "analytics_overview": timed(session, "GET", "/app/analytics/agency/overview?days_lookback=30"),
    }
    portal = {
        "search": timed(anon, "GET", "/cloud/search?operation=sale&page_size=20"),
        "facets": timed(anon, "GET", "/cloud/facets?operation=sale"),
        "map": timed(anon, "GET", "/cloud/map?operation=sale&limit=200"),
        "advanced": timed(anon, "POST", "/cloud/search/advanced", json={"operation": "sale", "cities": ["Catania", "Milano"], "page_size": 20, "page": 1}),
        "mls_public": timed(anon, "GET", "/app/mls/search/public?province=CT&limit=24"),
        "valuator_coverage": timed(anon, "GET", "/cloud/valuator/coverage"),
        "mutui_config": timed(anon, "GET", "/cloud/mutui/config"),
    }
    concurrency = {
        "crm_clients": fanout(session, "/app/clients?page=1&page_size=50", n=40, workers=20),
        "portal_search": fanout(anon, "/cloud/search?operation=sale&page_size=20", n=40, workers=20),
        "portal_map": fanout(anon, "/cloud/map?operation=sale&limit=100", n=20, workers=10),
        "clients_smart": fanout(session, "/app/clients/smart?page=1&page_size=50", n=20, workers=10),
    }

    report = {
        "kind": "platform_full_stress",
        "run_id": run_id,
        "api": API_ROOT,
        "agency_id": AGENCY,
        "seed_portal": args.seed_portal or 0,
        "seed_seconds": round(seed_s, 3) if seed_s is not None else None,
        "indexes": indexes,
        "crm": crm,
        "portal": portal,
        "concurrency": concurrency,
        "security": security_checks(session),
        "payments": payments_checks(session),
        "api_keys": api_key_checks(session, database),
        "db": {
            "properties": database.properties.estimated_document_count(),
            "clients": database.clients.estimated_document_count(),
            "users": database.users.estimated_document_count(),
            "rate_limit_events": database.rate_limit_events.estimated_document_count(),
        },
        "finished_at": now_iso(),
    }

    out = REPORT_DIR / f"platform_stress_{run_id}.json"
    latest = REPORT_DIR / "platform_stress_latest.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    latest.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps({
        "wrote": str(out),
        "crm_smart_ms": crm["clients_smart"].get("ms"),
        "portal_search_ms": portal["search"].get("ms"),
        "conc_portal_p95": concurrency["portal_search"].get("p95_ms"),
        "conc_smart_p95": concurrency["clients_smart"].get("p95_ms"),
        "security_ok": all(v.get("ok", True) for k, v in report["security"].items() if isinstance(v, dict) and "ok" in v),
    }, indent=2))


if __name__ == "__main__":
    main()
