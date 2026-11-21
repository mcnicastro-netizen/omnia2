"""Staging constants and isolation gates — D7 harness v1.

Canonical pins are HARDCODED (Founder D1–D3 / D7). Environment overrides may
exist for operational wiring (e.g. Mongo TCP proxy host) but MUST NOT redefine
the identity against which precheck validates. See ``pin_drift_report()``.
"""
from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# CANONICAL pins — immutable Source of Truth (never read from OMNIA_D7_* env)
# ---------------------------------------------------------------------------
CANONICAL_RAILWAY_PROJECT_ID = "23ad930c-5061-4d8a-924c-30796f6d80d2"  # pragma: allowlist secret
CANONICAL_RAILWAY_PROJECT_NAME = "omnia-api-staging"
CANONICAL_RAILWAY_ENV_ID = "0c3a72f1-d5a9-4ee4-a3b4-7b7f7b3bf15d"  # pragma: allowlist secret
CANONICAL_RAILWAY_MONGO_SERVICE_ID = "4b37fa1e-fc6d-46fc-889a-77e64e2721e5"  # pragma: allowlist secret
CANONICAL_RAILWAY_API_SERVICE_ID = "cebad879-fe99-4411-8037-ac71aa708cab"  # pragma: allowlist secret
CANONICAL_STAGING_API_URL = "https://omnia-api-production-85845f42.up.railway.app"
CANONICAL_STAGING_FE_URL = "https://omnia-frontend-staging.vercel.app"
CANONICAL_STAGING_DB_NAME = "omnia_staging_e2e"
CANONICAL_STAGING_MONGO_HOST_MARKER = "mongodb-fk03"
CANONICAL_FE_PIN = "15b1978c63ccb90bddf4a5ea07b668709846ba8b"

# Proxy host/port are operational (TCP reachability), not identity pins.
DEFAULT_MONGO_PROXY_HOST = os.environ.get("OMNIA_D7_MONGO_PROXY_HOST", "sakura.proxy.rlwy.net")
DEFAULT_MONGO_PROXY_PORT = int(os.environ.get("OMNIA_D7_MONGO_PROXY_PORT", "46223"))

EMAIL_DOMAIN = "example.com"
RUN_TAG_FIELD = "d7_run_id"
LEGACY_TAG_FIELD = "d7_tag"

HISTORICAL_ARTIFACTS = (
    "/opt/cursor/artifacts/d7_t3_api.json",
    "/opt/cursor/artifacts/d7_t4_api.json",
    "/opt/cursor/artifacts/d7_fixtures_meta.json",
    "/tmp/d7_seed_staging.py",
    "/tmp/d7_t3_t4_run.py",
)

FORENSIC_A6_NOT_SOT = True

# Env keys that MUST equal canonical when set (identity). Proxy host/port excluded.
_IDENTITY_ENV_KEYS = (
    ("OMNIA_D7_RAILWAY_PROJECT_ID", CANONICAL_RAILWAY_PROJECT_ID),
    ("OMNIA_D7_RAILWAY_PROJECT_NAME", CANONICAL_RAILWAY_PROJECT_NAME),
    ("OMNIA_D7_RAILWAY_ENV_ID", CANONICAL_RAILWAY_ENV_ID),
    ("OMNIA_D7_RAILWAY_MONGO_SERVICE_ID", CANONICAL_RAILWAY_MONGO_SERVICE_ID),
    ("OMNIA_D7_RAILWAY_API_SERVICE_ID", CANONICAL_RAILWAY_API_SERVICE_ID),
    ("OMNIA_D7_STAGING_API_URL", CANONICAL_STAGING_API_URL),
    ("OMNIA_D7_STAGING_FE_URL", CANONICAL_STAGING_FE_URL),
    ("OMNIA_D7_STAGING_DB_NAME", CANONICAL_STAGING_DB_NAME),
    ("OMNIA_D7_MONGO_HOST_MARKER", CANONICAL_STAGING_MONGO_HOST_MARKER),
    ("OMNIA_D7_FE_PIN", CANONICAL_FE_PIN),
)


def pin_drift_report() -> dict:
    """Compare identity-related env overrides to canonical pins.

    An override that differs from canonical is drift: it would otherwise let an
    operator retarget both the client AND the validator. Fail-closed in precheck.
    """
    drifts = []
    for env_key, canonical in _IDENTITY_ENV_KEYS:
        raw = os.environ.get(env_key)
        if raw is None or raw == "":
            continue
        if raw != canonical:
            drifts.append({"env": env_key, "matches_canonical": False})
        else:
            drifts.append({"env": env_key, "matches_canonical": True})
    return {
        "drifts_mismatch": [d for d in drifts if not d["matches_canonical"]],
        "overrides_ok": [d for d in drifts if d["matches_canonical"]],
        "ok": not any(not d["matches_canonical"] for d in drifts),
    }


# ---------------------------------------------------------------------------
# Runtime aliases — ALWAYS the canonical pin (never env for identity)
# ---------------------------------------------------------------------------
RAILWAY_PROJECT_ID = CANONICAL_RAILWAY_PROJECT_ID
RAILWAY_PROJECT_NAME = CANONICAL_RAILWAY_PROJECT_NAME
RAILWAY_ENV_ID = CANONICAL_RAILWAY_ENV_ID
RAILWAY_MONGO_SERVICE_ID = CANONICAL_RAILWAY_MONGO_SERVICE_ID
RAILWAY_API_SERVICE_ID = CANONICAL_RAILWAY_API_SERVICE_ID
STAGING_API_URL = CANONICAL_STAGING_API_URL
STAGING_FE_URL = CANONICAL_STAGING_FE_URL
STAGING_DB_NAME = CANONICAL_STAGING_DB_NAME
STAGING_MONGO_HOST_MARKER = CANONICAL_STAGING_MONGO_HOST_MARKER
AUTHORIZED_FE_PIN = CANONICAL_FE_PIN

# Collections written by seed (tagged) and/or T3/T4 API (inventory by id)
SEED_TAGGED_COLLECTIONS = (
    "users",
    "agencies",
    "properties",
    "api_keys",
    "clients",
    "commercial_customers",
    "organizations",
    "branches",
    "agency_invites",
)

# Real backend collection names (see apps/immoweb/collaborations.py, deals.py)
MLS_RUNTIME_COLLECTIONS = (
    "mls_collaborations",
    "mls_visits",
    "mls_visit_feedback",
    "mls_chat_threads",
    "mls_chat_messages",
    "mls_document_requests",  # revoke may touch; inventory if created
)
DEALS_COLLECTION = "deals"

# Side-effects from invite accept (inventory by id only — never delete by user_id alone)
SIDE_EFFECT_COLLECTIONS = (
    "memberships",
    "notifications",
)
