"""Staging constants and isolation gates — D7 harness v1.

SoT staging (D1–D3 / D7 Founder pin). Do not point at production.
IDs may be overridden via env for local/agent use.
"""
from __future__ import annotations

import os

# --- Authorized staging identity (D7) — overridable via env ---
RAILWAY_PROJECT_ID = os.environ.get(
    "OMNIA_D7_RAILWAY_PROJECT_ID",
    "23ad930c-5061-4d8a-924c-30796f6d80d2",  # pragma: allowlist secret
)
RAILWAY_PROJECT_NAME = os.environ.get("OMNIA_D7_RAILWAY_PROJECT_NAME", "omnia-api-staging")
RAILWAY_ENV_ID = os.environ.get(
    "OMNIA_D7_RAILWAY_ENV_ID",
    "0c3a72f1-d5a9-4ee4-a3b4-7b7f7b3bf15d",  # pragma: allowlist secret
)
RAILWAY_MONGO_SERVICE_ID = os.environ.get(
    "OMNIA_D7_RAILWAY_MONGO_SERVICE_ID",
    "4b37fa1e-fc6d-46fc-889a-77e64e2721e5",  # pragma: allowlist secret
)
RAILWAY_API_SERVICE_ID = os.environ.get(
    "OMNIA_D7_RAILWAY_API_SERVICE_ID",
    "cebad879-fe99-4411-8037-ac71aa708cab",  # pragma: allowlist secret
)

STAGING_API_URL = os.environ.get(
    "OMNIA_D7_STAGING_API_URL",
    "https://omnia-api-production-85845f42.up.railway.app",
)
STAGING_FE_URL = os.environ.get(
    "OMNIA_D7_STAGING_FE_URL",
    "https://omnia-frontend-staging.vercel.app",
)
STAGING_DB_NAME = os.environ.get("OMNIA_D7_STAGING_DB_NAME", "omnia_staging_e2e")
STAGING_MONGO_HOST_MARKER = os.environ.get("OMNIA_D7_MONGO_HOST_MARKER", "mongodb-fk03")
AUTHORIZED_FE_PIN = os.environ.get(
    "OMNIA_D7_FE_PIN",
    "15b1978c63ccb90bddf4a5ea07b668709846ba8b",
)

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
