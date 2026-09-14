"""OMNIA — Backend entry point.

Logical Monorepo architecture (D-015):
- 1 FastAPI app serves all OMNIA sub-apps under /api/{app}/...
- All routes are tenant-aware via shared.db (multi-tenant pattern D-013)
- i18n native via Accept-Language header (D-014)
"""
import logging
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, Header, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Make backend/ importable as root for `shared` and `apps`
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")

from shared.db.connection import Database, ensure_indexes, set_current_lang  # noqa: E402
from shared.utils.i18n import normalize_lang, _load_locales, t  # noqa: E402
from shared.models.base import HealthResponse  # noqa: E402

from apps.core.routes import router as core_router  # noqa: E402
from apps.core.auth import router as auth_router  # noqa: E402
from apps.core.seed import seed_admin  # noqa: E402
from apps.immocloud.routes import router as immocloud_router  # noqa: E402
from apps.immoweb.routes import router as immoweb_router  # noqa: E402
from apps.academy.routes import router as academy_router  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("omnia")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Database.connect()
    await ensure_indexes()
    _load_locales()
    await seed_admin()
    try:
        from apps.immoweb.publishing import seed_publishing_catalog
        await seed_publishing_catalog()
    except Exception as e:
        logger.warning("publishing_catalog seed failed: %s", e)
    try:
        from apps.immoweb.sync_engine import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.warning("publishing sync scheduler failed to start: %s", e)
    try:
        from apps.immoweb.virtual_staging import reap_stale_jobs
        reaped = await reap_stale_jobs()
        if reaped:
            logger.info("Reaped %d stale virtual staging jobs", reaped)
    except Exception as e:
        logger.warning("Staging reaper failed: %s", e)
    try:
        from apps.immoweb.hal_knowledge import ingest_corpus as _hal_ingest
        report = await _hal_ingest(force=False)
        logger.info(
            "HAL Knowledge corpus: %d files scanned, %d reingested, %d chunks total",
            report["scanned"], len(report["reingested"]), report["total_chunks"],
        )
    except Exception as e:
        logger.warning("HAL Knowledge ingest failed: %s", e)
    # Sprint 4 · GAP #1 — Emergent Object Storage warm-up (best-effort)
    try:
        from shared.storage import init_storage
        init_storage()
        logger.info("Object Storage initialized")
    except Exception as e:
        logger.warning("Object Storage init failed (uploads will retry lazily): %s", e)
    logger.info("OMNIA backend ready.")
    yield
    # Shutdown
    try:
        from apps.immoweb.sync_engine import stop_scheduler
        stop_scheduler()
    except Exception:  # pragma: no cover
        pass
    await Database.close()
    logger.info("OMNIA backend stopped.")


app = FastAPI(
    title="OMNIA Real Estate Ecosystem API",
    version="0.1.0",
    description="Backend per ImmobilCloud + ImmoWeb + Omnia Academy",
    lifespan=lifespan,
)

# CORS (allow Emergent preview + production subdomains)
_cors_env = os.environ.get("CORS_ORIGINS", "").strip()
if _cors_env:
    allowed = _cors_env.split(",")
else:
    allowed = ["*"]
    logger.warning("CORS_ORIGINS not set — using '*' (acceptable in preview only; set explicit origins in production)")
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[o.strip() for o in allowed if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Host-based routing for verified custom domains (M2.S6)
from apps.immoweb.host_routing import HostRoutingMiddleware
app.add_middleware(HostRoutingMiddleware)


@app.middleware("http")
async def language_middleware(request: Request, call_next):
    """Set request language from Accept-Language or ?lang= query."""
    lang_q = request.query_params.get("lang")
    lang_h = request.headers.get("accept-language")
    lang = normalize_lang(lang_q or lang_h)
    set_current_lang(lang)
    response = await call_next(request)
    response.headers["X-OMNIA-Lang"] = lang
    return response


# Main /api router
api_router = APIRouter(prefix="/api")


@api_router.get("/", response_model=HealthResponse)
async def api_root(accept_language: str = Header(None)):
    lang = normalize_lang(accept_language)
    return HealthResponse(
        app="omnia",
        lang=lang,
        message={
            "text": t("welcome.greeting", lang=lang),
            "apps": ["core", "cloud", "app", "learn"],
        },
    )


@api_router.get("/health", response_model=HealthResponse)
async def global_health(accept_language: str = Header(None)):
    lang = normalize_lang(accept_language)
    db_status = "ok"
    try:
        db = Database.get()
        await db.command("ping")
    except Exception as e:
        logger.error("health db ping failed: %s", e)
        db_status = "error"
    return HealthResponse(
        app="omnia",
        lang=lang,
        message={"text": t("health.ok", lang=lang), "db": db_status},
    )


# Mount sub-apps
api_router.include_router(auth_router)
api_router.include_router(core_router)
api_router.include_router(immocloud_router)
api_router.include_router(immoweb_router)
api_router.include_router(academy_router)

# Public Feed (OSF v1.0) — M2.S5 Layer B (no auth, portals pull anonymously)
from apps.immoweb.feed import router as public_feed_router  # noqa: E402
api_router.include_router(public_feed_router)

# Public Site (Layer C) — HTML pages crawlable by portals + photo binary serving
from apps.immoweb.site import router as public_site_router  # noqa: E402
api_router.include_router(public_site_router)

# Sprint 4 · GAP #1 — Media passthrough for Emergent Object Storage (public read)
from apps.immoweb.media import router as media_router  # noqa: E402
api_router.include_router(media_router)

from apps.marketing.founders import router as founders_router  # noqa: E402
api_router.include_router(founders_router)

# Domain Ownership Checker (M2.5.4b, D-054) — public, no auth, IP-rate-limited
from apps.marketing.domain_check import router as domain_check_router  # noqa: E402
api_router.include_router(domain_check_router)

# Legal Kit — public PDF generator (M2.5.4c, D-055)
from apps.marketing.legal_kit import router as legal_kit_router  # noqa: E402
api_router.include_router(legal_kit_router)

# Public v1 API Gateway (M2.5.2 Track B, D-041) — Bearer API-key auth
from apps.v1.gateway import router as v1_gateway_router  # noqa: E402
api_router.include_router(v1_gateway_router)

# M2.5.3 — Widget assets (loader.js + widget HTML pages) served from backend.
from apps.v1.widgets import router as v1_widgets_router  # noqa: E402
api_router.include_router(v1_widgets_router)

# M4 (scaffold) — Billing (Stripe subscriptions + credits) — endpoints 503 finché non attivato
from apps.billing.routes import router as billing_router  # noqa: E402
api_router.include_router(billing_router)
from apps.billing.b2c_checkout import router as b2c_checkout_router  # noqa: E402
api_router.include_router(b2c_checkout_router)

# M4 (scaffold) — Docs search (APE via SIAPE + visure OpenAI) — endpoints 503 finché non attivato
from apps.docs_search import router as docs_search_router  # noqa: E402
api_router.include_router(docs_search_router)

# MLS Box public widget — griglia immobili per embed su siti agenzia (stile home Nicastro)
from apps.immoweb.mls_box import router as mls_box_router  # noqa: E402
api_router.include_router(mls_box_router)

app.include_router(api_router)


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    lang = normalize_lang(request.headers.get("accept-language"))
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"detail": t("error.server", lang=lang)},
    )
