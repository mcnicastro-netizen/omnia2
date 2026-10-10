#!/usr/bin/env python3
"""S10 / GTM-01 — Demo Readiness smoke (D-104 / K-SC-01).

Verifica:
  1) Percorso prospect (landing/health → portale → demo CRM → demo-status → checkout gate)
  2) Smoke ~20 concurrent: search + media + properties + matches + upload-tmp

Usage:
  python scripts/gtm01_smoke.py
  python scripts/gtm01_smoke.py --workers 20

Writes docs/ops/runs/s10-gtm-01-live.log
"""
from __future__ import annotations

import argparse
import io
import json
import os
import statistics
import struct
import sys
import time
import urllib.error
import urllib.request
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv

load_dotenv(BACKEND / ".env", override=True)

API = (os.environ.get("OMNIA_API_BASE") or "http://127.0.0.1:43121/api").rstrip("/")


def _preview_candidates() -> list[str]:
    """FE preview bases — never use API :43121 as HTML home."""
    out: list[str] = []
    for key in ("OMNIA_PREVIEW_BASE", "OMNIA_PUBLIC_SHARE_URL"):
        v = (os.environ.get(key) or "").strip().rstrip("/")
        if v and ":43121" not in v:
            out.append(v)
    share = Path("/tmp/omnia-stack/SHARE_URL.txt")
    if share.is_file():
        v = share.read_text().strip().rstrip("/")
        if v and ":43121" not in v:
            out.append(v)
    out.append("http://127.0.0.1:43123")
    # de-dupe preserve order
    seen = set()
    uniq = []
    for u in out:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


LOG = ROOT / "docs" / "ops" / "runs" / "s10-gtm-01-live.log"


def _log(line: str, lines: list[str]) -> None:
    print(line)
    lines.append(line)


class ApiClient:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.cookies: dict[str, str] = {}
        self.csrf = None

    def _headers(self, *, json_body: bool = False, multipart: bool = False) -> dict:
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

    def request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        *,
        data: bytes | None = None,
        content_type: str | None = None,
        timeout: float = 45,
    ):
        headers = self._headers(json_body=body is not None and data is None)
        payload = None
        if data is not None:
            payload = data
            if content_type:
                headers["Content-Type"] = content_type
        elif body is not None:
            payload = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=payload,
            headers=headers,
            method=method,
        )
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                self._ingest(r.headers)
                raw = r.read()
                ms = (time.perf_counter() - t0) * 1000
                try:
                    parsed = json.loads(raw.decode()) if raw else {}
                except json.JSONDecodeError:
                    parsed = {"_bytes": len(raw)}
                return r.status, parsed, ms
        except urllib.error.HTTPError as e:
            self._ingest(e.headers)
            raw = e.read()
            ms = (time.perf_counter() - t0) * 1000
            try:
                parsed = json.loads(raw.decode()) if raw else {}
            except json.JSONDecodeError:
                parsed = {"raw": raw[:200].decode(errors="replace")}
            return e.code, parsed, ms
        except Exception as e:
            ms = (time.perf_counter() - t0) * 1000
            return 0, {"error": str(e)[:200]}, ms


def _minimal_png() -> bytes:
    """1×1 PNG."""
    # IHDR + IDAT + IEND
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = zlib.compress(b"\x00\xff\x00\x00")
    idat = chunk(b"IDAT", raw)
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


def _multipart_png(field: str = "file", filename: str = "gtm01.png") -> tuple[bytes, str]:
    boundary = "----OmniaGtm01Boundary7MA4YWxkTrZu0gW"
    png = _minimal_png()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + png + f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def prospect_path(lines: list[str]) -> tuple[dict[str, bool], ApiClient, str]:
    checks: dict[str, bool] = {}
    # Landing / preview FE (try local preview + public tunnel)
    fe_st, fe_len, preview_used = 0, 0, ""
    for base in _preview_candidates():
        try:
            req = urllib.request.Request(f"{base}/", method="GET")
            with urllib.request.urlopen(req, timeout=20) as r:
                fe_st = r.status
                fe_len = len(r.read(4000))
            if fe_st == 200 and fe_len > 100:
                preview_used = base
                break
        except Exception as e:
            _log(f"preview_try {base} err={e!s}"[:220], lines)
    _log(f"preview_home status={fe_st} bytes~={fe_len} base={preview_used or 'none'}", lines)
    checks["preview_home_ok"] = fe_st == 200 and fe_len > 100

    c = ApiClient(API)
    st, health, ms = c.request("GET", "/health")
    _log(f"api_health status={st} ms={ms:.0f}", lines)
    checks["api_health_200"] = st == 200

    st, plans, ms = c.request("GET", "/billing/plans")
    _log(
        f"plans status={st} self_serve={plans.get('self_serve_enabled')} "
        f"enabled={plans.get('enabled')} ms={ms:.0f}",
        lines,
    )
    checks["self_serve_on"] = st == 200 and plans.get("self_serve_enabled") is True

    st, search, ms = c.request("GET", "/cloud/search?page_size=12")
    items = []
    if isinstance(search, dict):
        items = search.get("items") or search.get("results") or search.get("properties") or []
        total = search.get("total", len(items))
    else:
        total = 0
    _log(f"portal_search status={st} total={total} ms={ms:.0f}", lines)
    checks["portal_search_ok"] = st == 200

    demo_pw = os.environ.get("DEMO_ADMIN_PASSWORD") or "OmniaDemo2026!"
    st, login, ms = c.request(
        "POST",
        "/auth/login",
        {"email": "demo.admin@omniaecosystem.it", "password": demo_pw},
    )
    _log(f"demo_login status={st} role={login.get('role')} ms={ms:.0f}", lines)
    checks["demo_login"] = st == 200

    st, props, ms = c.request("GET", "/app/properties?page=1&page_size=20")
    p_items = []
    if isinstance(props, dict):
        p_items = props.get("items") or props.get("properties") or props.get("data") or []
        p_total = props.get("total", len(p_items))
    else:
        p_total = 0
    _log(f"crm_properties status={st} total={p_total} ms={ms:.0f}", lines)
    checks["crm_properties_page"] = st == 200

    st, matches, ms = c.request("GET", "/app/matches?min_score=50&limit=10")
    _log(f"crm_matches status={st} ms={ms:.0f}", lines)
    checks["crm_matches_ok"] = st in (200, 204)

    st, demo, ms = c.request("GET", "/billing/demo-status")
    _log(
        f"demo_status status={st} cta={demo.get('cta')} "
        f"checkout_available={demo.get('checkout_available')} ms={ms:.0f}",
        lines,
    )
    checks["demo_status_200"] = st == 200
    # CTA Acquista espone checkout_available solo a sandbox scaduta; self-serve ON = gate aperto
    checks["self_serve_gate_open"] = plans.get("self_serve_enabled") is True

    origin = preview_used or "http://127.0.0.1:43123"
    # Checkout must pass self-serve gate (200 session or 4xx business — not 503 blocked)
    st, chk, ms = c.request(
        "POST",
        "/billing/checkout",
        {
            "plan_tier": "starter",
            "billing_cycle": "monthly",
            "origin": origin,
        },
    )
    detail = chk.get("detail") if isinstance(chk, dict) else chk
    code = detail.get("code") if isinstance(detail, dict) else None
    _log(f"checkout status={st} code={code} ms={ms:.0f} keys={list(chk)[:6] if isinstance(chk, dict) else type(chk)}", lines)
    blocked = st == 503 and (code == "self_serve_blocked" or "self_serve_blocked" in str(detail))
    checks["checkout_past_self_serve_gate"] = not blocked and st in (200, 400, 402, 404, 422)
    if st == 200:
        checks["checkout_session"] = bool(chk.get("url") or chk.get("session_id") or chk.get("id"))

    # Media: serve first public cover if any
    cover = None
    for it in items:
        if isinstance(it, dict) and it.get("cover_url"):
            cover = it["cover_url"]
            break
    if cover:
        path = cover if cover.startswith("/") else f"/{cover}"
        if path.startswith("/api"):
            path = path[len("/api") :]
        st_m, _, ms_m = c.request("GET", path if path.startswith("/") else f"/{path}")
        _log(f"media_cover status={st_m} ms={ms_m:.0f} path={path[:80]}", lines)
        checks["media_serve"] = st_m in (200, 302, 304)
    else:
        _log("media_cover SKIP no cover_url in portal page", lines)
        checks["media_serve_skip"] = True

    return checks, c, origin


def concurrent_smoke(base_client: ApiClient, workers: int, lines: list[str]) -> dict:
    # Clone session cookies for workers
    cookie_hdr = "; ".join(f"{k}={v}" for k, v in base_client.cookies.items())
    csrf = base_client.csrf

    def one(i: int) -> dict:
        c = ApiClient(API)
        c.cookies = dict(base_client.cookies)
        c.csrf = csrf
        kind = i % 5
        if kind == 0:
            st, body, ms = c.request("GET", "/cloud/search?page_size=8&page=1")
            return {"i": i, "op": "search", "status": st, "ms": ms, "ok": st == 200}
        if kind == 1:
            st, body, ms = c.request("GET", "/app/properties?page=1&page_size=20")
            return {"i": i, "op": "properties", "status": st, "ms": ms, "ok": st == 200}
        if kind == 2:
            st, body, ms = c.request("GET", "/app/matches?min_score=40&limit=5")
            return {"i": i, "op": "matches", "status": st, "ms": ms, "ok": st in (200, 204)}
        if kind == 3:
            st, body, ms = c.request("GET", "/health")
            # also hit portal advanced lightly
            st2, _, ms2 = c.request("GET", "/cloud/search?page_size=4")
            return {
                "i": i,
                "op": "health+search",
                "status": st2,
                "ms": ms + ms2,
                "ok": st == 200 and st2 == 200,
            }
        # upload-tmp small png + read/serve
        data, ctype = _multipart_png()
        st, body, ms = c.request(
            "POST",
            "/app/properties/photos/upload-tmp",
            data=data,
            content_type=ctype,
            timeout=60,
        )
        ok = st in (200, 201)
        serve_st = None
        if ok and isinstance(body, dict) and body.get("url"):
            url = body["url"]
            path = url[len("/api") :] if url.startswith("/api/") else url
            serve_st, _, ms2 = c.request("GET", path if path.startswith("/") else f"/{path}")
            ms += ms2
            ok = ok and serve_st in (200, 302, 304)
        return {
            "i": i,
            "op": "upload_tmp",
            "status": st,
            "serve_status": serve_st,
            "ms": ms,
            "ok": ok,
            "detail": (body.get("detail") if isinstance(body, dict) else None),
        }

    results = []
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(one, i) for i in range(workers)]
        for f in as_completed(futs):
            results.append(f.result())
    wall = (time.perf_counter() - t0) * 1000

    oks = [r for r in results if r.get("ok")]
    fails = [r for r in results if not r.get("ok")]
    lat = [r["ms"] for r in results if r.get("ms") is not None]
    p50 = statistics.median(lat) if lat else 0
    p95 = sorted(lat)[max(0, int(len(lat) * 0.95) - 1)] if lat else 0
    by_op: dict[str, list] = {}
    for r in results:
        by_op.setdefault(r["op"], []).append(r)

    summary = {
        "workers": workers,
        "ok": len(oks),
        "fail": len(fails),
        "error_rate": round(len(fails) / max(1, workers), 3),
        "wall_ms": round(wall, 1),
        "p50_ms": round(p50, 1),
        "p95_ms": round(p95, 1),
        "by_op": {
            k: {
                "n": len(v),
                "ok": sum(1 for x in v if x.get("ok")),
                "fail_status": [x.get("status") for x in v if not x.get("ok")][:5],
            }
            for k, v in by_op.items()
        },
    }
    _log(f"smoke_concurrent={json.dumps(summary, ensure_ascii=False)}", lines)
    if fails:
        _log(f"smoke_fails_sample={fails[:5]}", lines)

    # Gates (Demo Readiness, not P0): error_rate ≤ 10%, p95 < 15s, ≥80% ok
    checks = {
        "smoke_workers_ge_20": workers >= 20,
        "smoke_error_rate_le_10pct": summary["error_rate"] <= 0.10,
        "smoke_ok_ratio_ge_80pct": (len(oks) / max(1, workers)) >= 0.80,
        "smoke_p95_lt_15s": summary["p95_ms"] < 15000,
        "smoke_upload_attempted": "upload_tmp" in by_op,
        "smoke_upload_ok_ge_1": by_op.get("upload_tmp", [{}]) and any(
            x.get("ok") for x in by_op.get("upload_tmp", [])
        ),
    }
    return summary, checks


def ensure_demo_seed(lines: list[str]) -> None:
    try:
        import asyncio
        from motor.motor_asyncio import AsyncIOMotorClient
        sys.path.insert(0, str(BACKEND / "scripts"))
        import seed_demo_gestionale as seed
        from shared.demo_story import ensure_demo_window

        async def _run():
            mongo_url = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
            db_name = os.environ.get("DB_NAME", "omnia")
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            await seed.main()
            st = await ensure_demo_window(db, refresh=True, force_expired=False)
            client.close()
            return st

        st = asyncio.run(_run())
        _log(f"seed_demo={json.dumps(st, ensure_ascii=False)}", lines)
    except Exception as e:
        _log(f"seed_demo_warn={e!s}"[:300], lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--skip-seed", action="store_true")
    args = ap.parse_args()

    lines: list[str] = []
    ts = datetime.now(timezone.utc).isoformat()
    _log(f"=== S10 GTM-01 LIVE {ts} ===", lines)
    _log(f"api={API} preview_candidates={_preview_candidates()} workers={args.workers}", lines)

    if not args.skip_seed:
        ensure_demo_seed(lines)

    prospect_checks, client, origin = prospect_path(lines)
    _log(f"checkout_origin={origin}", lines)
    smoke_summary, smoke_checks = concurrent_smoke(client, args.workers, lines)

    checks = {**prospect_checks, **smoke_checks}
    # media_serve_skip is soft OK
    hard = {k: v for k, v in checks.items() if k not in ("media_serve_skip",)}
    if checks.get("media_serve_skip") and "media_serve" not in checks:
        hard["media_serve_or_skip"] = True
    elif "media_serve" in checks:
        hard["media_serve_or_skip"] = checks["media_serve"]

    failed = [k for k, v in hard.items() if not v]
    esito = "PASS" if not failed else "FAIL"
    _log(f"checks={hard}", lines)
    _log(f"ESITO={esito} failed={failed}", lines)
    _log(
        "LIMITI: smoke ~20 ≠ stress 5k; Stripe mode=test; outreach ~5k solo dopo PASS; "
        "object storage solo se smoke media fallisce (K-AD-02).",
        lines,
    )

    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # also artifact copy path for agent
    art = Path("/opt/cursor/artifacts/s10-gtm-01-live.log")
    try:
        art.parent.mkdir(parents=True, exist_ok=True)
        art.write_text(LOG.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass
    return 0 if esito == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
