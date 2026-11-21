"""Environment expectations for W3 staging verification."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StagingExpectation:
    key: str
    expected: str
    source_of_truth: str
    verify_how: str
    acceptance: str
    local_evidence: str
    staging_only: bool = False


EXPECTATIONS: List[StagingExpectation] = [
    StagingExpectation(
        key="backend_base_url",
        expected="HTTPS API on Railway staging (path prefix /api)",
        source_of_truth="Railway service URL / FRONTEND REACT_APP_BACKEND_URL",
        verify_how="GET {base}/api/health → 200 JSON",
        acceptance="status ok + mongo reachable flag if exposed",
        local_evidence="http://127.0.0.1:43121/api/health",
        staging_only=True,
    ),
    StagingExpectation(
        key="frontend_base_url",
        expected="Vercel preview/staging Immoweb",
        source_of_truth="Vercel project deployment",
        verify_how="HTTP 200 on /",
        acceptance="SPA loads; no mixed-content to prod API",
        local_evidence="preview-server.js local",
        staging_only=True,
    ),
    StagingExpectation(
        key="runtime_python",
        expected="Python 3.11+ (match Dockerfile/Railway)",
        source_of_truth="backend Dockerfile / Railway nixpacks",
        verify_how="health or /api/version if present; Railway runtime",
        acceptance="same major as local CI",
        local_evidence=f"local {sys.version.split()[0]}",
    ),
    StagingExpectation(
        key="mongo_url",
        expected="MongoDB Atlas/Railway plugin dedicated staging DB",
        source_of_truth="MONGO_URL secret",
        verify_how="ping via harness mongo preflight (staging only)",
        acceptance="ping ok; DB_NAME matches staging",
        local_evidence="mongodb://127.0.0.1:27017 DB_NAME=omnia",
        staging_only=True,
    ),
    StagingExpectation(
        key="jwt_secret",
        expected="Shared JWT_SECRET across all API replicas",
        source_of_truth="Railway env JWT_SECRET",
        verify_how="same token accepted by two instances (multi-replica)",
        acceptance="identical auth outcomes across instances",
        local_evidence="test_w3_multiprocess_local.py",
    ),
    StagingExpectation(
        key="replicas",
        expected="≥2 API replicas for B8/session revoke proof",
        source_of_truth="Railway service scaling",
        verify_how="health instance_id diversity OR Railway metrics",
        acceptance="≥2 distinct instance_id in sample window",
        local_evidence="2 local uvicorn (43121+43122) — NOT Railway-equivalent",
        staging_only=True,
    ),
    StagingExpectation(
        key="email_provider",
        expected="Resend with kill-switch provider_flags",
        source_of_truth="RESEND_API_KEY + Mongo provider_flags",
        verify_how="L5 evidence / B8 kill (staging mandate)",
        acceptance="kill blocks send; no real customer email in harness",
        local_evidence="provider_flags unit + health resend_kill",
        staging_only=True,
    ),
    StagingExpectation(
        key="stripe",
        expected="Stripe test mode keys only on staging",
        source_of_truth="STRIPE_SECRET_KEY / webhook secret",
        verify_how="key prefix sk_test; webhook endpoint staging",
        acceptance="no live charges",
        local_evidence="local vault may hold test keys — never charged in W3 cycle",
        staging_only=True,
    ),
    StagingExpectation(
        key="synthetic_data_prefix",
        expected="All harness docs tagged w3stg-<run_id>",
        source_of_truth="this harness",
        verify_how="cleanup deletes only tagged ids",
        acceptance="zero leftover tagged docs",
        local_evidence="w3dt-/w3mp-/w3stg- prefixes in tests",
    ),
]


@dataclass
class HarnessConfig:
    mode: str = "local"  # local | staging
    base_url: str = field(
        default_factory=lambda: os.environ.get(
            "REACT_APP_BACKEND_URL", "http://127.0.0.1:43121"
        ).rstrip("/")
    )
    mongo_url: str = field(
        default_factory=lambda: os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
    )
    db_name: str = field(default_factory=lambda: os.environ.get("DB_NAME", "omnia"))
    allow_staging: bool = field(
        default_factory=lambda: os.environ.get("OMNIA_STAGING_VERIFY", "").strip() == "1"
    )
    run_id: Optional[str] = None

    def api(self) -> str:
        return f"{self.base_url}/api"
