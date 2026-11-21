"""Isolation prechecks — must all PASS before any mutative step."""
from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any

from . import config
from .classify import expect_predicate, is_5xx
from .http_client import StagingClient
from .mongo_util import assert_staging_project, connect_staging_db


def run_precheck() -> dict[str, Any]:
    steps = []
    # P1 FE reachable
    fe_status, fe_html = _get(config.STAGING_FE_URL)
    steps.append(
        expect_predicate(
            "P1_fe_http",
            fe_status == 200 and not is_5xx(fe_status),
            status=fe_status,
            reason="fe_not_200",
        )
    )
    # P2 FE bundle points only at staging API
    api_refs = set(re.findall(r"https://[a-zA-Z0-9._\-]+\.up\.railway\.app", fe_html or ""))
    for m in re.findall(r'src="(/static/js/[^"]+)"', fe_html or ""):
        st, js = _get(config.STAGING_FE_URL + m)
        if st == 200 and isinstance(js, str):
            api_refs.update(re.findall(r"https://[a-zA-Z0-9._\-]+\.up\.railway\.app", js))
    only_staging = api_refs == {config.STAGING_API_URL} or (
        config.STAGING_API_URL in api_refs and all("85845f42" in u for u in api_refs)
    )
    steps.append(
        expect_predicate(
            "P2_fe_api_refs",
            only_staging,
            reason="fe_api_refs_unexpected",
            detail={"api_refs": sorted(api_refs)},
        )
    )
    # P3/P4/P5 Railway + DB
    tok = os.environ.get("RAILWAY_API_TOKEN") or os.environ.get("RAILWAY_TOKEN")
    if not tok:
        steps.append(
            {
                "step": "P3_railway_project",
                "result": "BLOCKED",
                "reason": "missing_RAILWAY_API_TOKEN",
            }
        )
        return {"steps": steps, "classification": "BLOCKED"}
    try:
        proj = assert_staging_project(tok)
        steps.append(
            expect_predicate(
                "P3_railway_project",
                proj["name"] == config.RAILWAY_PROJECT_NAME,
                detail=proj,
            )
        )
        db = connect_staging_db()
        steps.append(
            expect_predicate(
                "P4_db_name",
                db.name == config.STAGING_DB_NAME,
                detail={"db": db.name},
            )
        )
        steps.append(
            expect_predicate(
                "P5_mongo_ping",
                True,
                detail={"ok": 1},
            )
        )
    except Exception as e:
        steps.append(
            {
                "step": "P3_P5_railway_mongo",
                "result": "FAIL",
                "reason": "exception",
                "detail": str(e)[:500],
            }
        )
    # P6 FE pin via Vercel API if token present; else BLOCKED note (not PASS)
    vtok = os.environ.get("VERCEL_TOKEN")
    if vtok:
        try:
            req = urllib.request.Request(
                "https://api.vercel.com/v6/deployments?app=omnia-frontend-staging&limit=5",
                headers={"Authorization": "Bearer " + vtok},
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                deps = json.load(r)
            sha = None
            for d in deps.get("deployments") or []:
                sha = (d.get("meta") or {}).get("githubCommitSha") or (
                    d.get("meta") or {}
                ).get("gitCommitSha")
                if sha:
                    break
            steps.append(
                expect_predicate(
                    "P6_fe_pin",
                    bool(sha) and str(sha).startswith(config.AUTHORIZED_FE_PIN[:7]),
                    detail={"sha": sha, "pin": config.AUTHORIZED_FE_PIN},
                    reason="fe_pin_mismatch",
                )
            )
        except Exception as e:
            steps.append(
                {
                    "step": "P6_fe_pin",
                    "result": "FAIL",
                    "reason": "vercel_lookup_failed",
                    "detail": str(e)[:300],
                }
            )
    else:
        steps.append(
            {
                "step": "P6_fe_pin",
                "result": "BLOCKED",
                "reason": "missing_VERCEL_TOKEN",
            }
        )
    # P7 health
    c = StagingClient()
    st, health = c.health()
    db_ok = isinstance(health, dict) and (
        (health.get("message") or {}).get("db") == "ok" or health.get("status") == "ok"
    )
    steps.append(
        expect_predicate(
            "P7_health",
            st == 200 and db_ok and not is_5xx(st),
            status=st,
            detail=health if isinstance(health, dict) else {"raw": health},
            reason="health_not_ok",
        )
    )
    # P8 no prod markers in harness config usage
    steps.append(
        expect_predicate(
            "P8_staging_urls_configured",
            "omnia-frontend-staging" in config.STAGING_FE_URL
            and config.STAGING_DB_NAME == "omnia_staging_e2e",
            reason="config_not_staging",
        )
    )

    from .classify import aggregate

    return {"steps": steps, "classification": aggregate(steps)}


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "omnia-d7-e2e/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return 0, str(e)
