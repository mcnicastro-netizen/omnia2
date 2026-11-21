"""Isolation prechecks — must all PASS before any mutative step (fail-closed)."""
from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any

from . import config
from .classify import aggregate, expect_predicate, is_5xx
from .http_client import StagingClient
from .mongo_util import assert_staging_project, connect_staging_db

# Coverage note (documented): we fetch HTML then every ``src="/static/js/..."``
# and also ``src='/static/js/...'``, ``href=`` to same, and absolute same-origin
# ``/static/js/`` URLs. We do NOT parse modulepreload of non-js, CSS, or remote
# CDN hosts. If the FE ships API URLs only inside non-matched assets, P2 may
# fail-closed (empty refs) rather than PASS.
_JS_SRC_RE = re.compile(
    r"""(?:src|href)=["'](/static/js/[^"']+)["']""",
    re.IGNORECASE,
)
_RAILWAY_API_RE = re.compile(r"https://[a-zA-Z0-9._\-]+\.up\.railway\.app")


def run_precheck() -> dict[str, Any]:
    steps: list[dict] = []

    # P0 — pin drift: env override must not redefine identity vs canonical
    drift = config.pin_drift_report()
    steps.append(
        expect_predicate(
            "P0_canonical_pin_no_drift",
            drift["ok"],
            reason="identity_env_override_differs_from_canonical",
            detail={"mismatches": drift["drifts_mismatch"]},
        )
    )

    # P1 FE reachable (canonical URL only)
    fe_status, fe_html = _get(config.CANONICAL_STAGING_FE_URL)
    steps.append(
        expect_predicate(
            "P1_fe_http",
            fe_status == 200 and not is_5xx(fe_status),
            status=fe_status,
            reason="fe_not_200",
        )
    )

    # P2 FE bundle points exactly at canonical staging API (no substring match)
    api_refs: set[str] = set()
    if isinstance(fe_html, str):
        api_refs.update(_RAILWAY_API_RE.findall(fe_html))
        for m in _JS_SRC_RE.findall(fe_html):
            st, js = _get(config.CANONICAL_STAGING_FE_URL + m)
            if st == 200 and isinstance(js, str):
                api_refs.update(_RAILWAY_API_RE.findall(js))
    only_exact = api_refs == {config.CANONICAL_STAGING_API_URL}
    steps.append(
        expect_predicate(
            "P2_fe_api_refs_exact",
            only_exact,
            reason="fe_api_refs_not_exact_canonical",
            detail={
                "api_refs": sorted(api_refs),
                "canonical": config.CANONICAL_STAGING_API_URL,
                "coverage": (
                    "HTML + /static/js/ script|href assets only; "
                    "non-js/modulepreload/CDN not scanned — empty refs ⇒ fail"
                ),
            },
        )
    )

    # P3/P4/P5 Railway + DB against CANONICAL ids
    tok = os.environ.get("RAILWAY_API_TOKEN") or os.environ.get("RAILWAY_TOKEN")
    if not tok:
        steps.append(
            {
                "step": "P3_railway_project",
                "result": "BLOCKED",
                "reason": "missing_RAILWAY_API_TOKEN",
            }
        )
        return {"steps": steps, "classification": aggregate(steps)}
    try:
        proj = assert_staging_project(tok)
        steps.append(
            expect_predicate(
                "P3_railway_project",
                proj["id"] == config.CANONICAL_RAILWAY_PROJECT_ID
                and proj["name"] == config.CANONICAL_RAILWAY_PROJECT_NAME,
                detail={"id": proj.get("id"), "name": proj.get("name")},
            )
        )
        db = connect_staging_db()
        steps.append(
            expect_predicate(
                "P4_db_name",
                db.name == config.CANONICAL_STAGING_DB_NAME,
                detail={"db": db.name, "canonical": config.CANONICAL_STAGING_DB_NAME},
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

    # P6 FE pin via Vercel — BLOCKED if token missing (never PASS)
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
                    bool(sha) and str(sha).startswith(config.CANONICAL_FE_PIN[:7]),
                    detail={"sha": sha, "pin": config.CANONICAL_FE_PIN},
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

    # P7 health — require explicit DB ok (not status==ok alone)
    c = StagingClient(
        api_base=config.CANONICAL_STAGING_API_URL,
        origin=config.CANONICAL_STAGING_FE_URL,
    )
    st, health = c.health()
    db_ok = (
        isinstance(health, dict)
        and isinstance(health.get("message"), dict)
        and health["message"].get("db") == "ok"
    )
    steps.append(
        expect_predicate(
            "P7_health_db_ok",
            st == 200 and db_ok and not is_5xx(st),
            status=st,
            detail=health if isinstance(health, dict) else {"raw": health},
            reason="health_db_not_ok",
        )
    )

    # P8 — identity refs against CANONICAL constants (not env-derived aliases)
    steps.append(
        expect_predicate(
            "P8_canonical_identity",
            config.CANONICAL_STAGING_FE_URL.endswith("omnia-frontend-staging.vercel.app")
            and config.CANONICAL_STAGING_DB_NAME == "omnia_staging_e2e"
            and config.CANONICAL_RAILWAY_PROJECT_NAME == "omnia-api-staging"
            and config.STAGING_API_URL == config.CANONICAL_STAGING_API_URL
            and config.STAGING_FE_URL == config.CANONICAL_STAGING_FE_URL
            and config.STAGING_DB_NAME == config.CANONICAL_STAGING_DB_NAME,
            reason="canonical_identity_mismatch",
            detail={
                "api": config.CANONICAL_STAGING_API_URL,
                "fe": config.CANONICAL_STAGING_FE_URL,
                "db": config.CANONICAL_STAGING_DB_NAME,
                "project": config.CANONICAL_RAILWAY_PROJECT_NAME,
            },
        )
    )

    return {"steps": steps, "classification": aggregate(steps)}


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "omnia-d7-e2e/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return 0, str(e)
