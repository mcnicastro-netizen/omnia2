"""OMNIA — ImmoWeb routes (B2B agency CRM)."""
from fastapi import APIRouter, Header
from typing import Optional

from shared.models.base import HealthResponse
from shared.utils.i18n import t, normalize_lang
from shared.db.connection import set_current_lang

from apps.immoweb.agencies import router as agencies_router
from apps.immoweb.domain_vault import router as domain_vault_router
from apps.immoweb.groups import router as groups_router
from apps.immoweb.api_keys import router as api_keys_router
from apps.immoweb.xml_import import router as xml_import_router
from apps.immoweb.publishing import router as publishing_router, feed_router as publishing_feed_router
from apps.immoweb.social_publisher import router as social_publisher_router
from apps.immoweb.hal_knowledge import router as hal_knowledge_router, ingest_corpus as hal_ingest_corpus
from apps.immoweb.property_privacy import router as property_privacy_router
from apps.immoweb.analytics_ab import router as analytics_ab_router
from apps.immoweb.micro_tour_video import router as micro_tour_router, public_router as micro_tour_public_router
from apps.immoweb.invites import router as invites_router
from apps.immoweb.dashboard import router as dashboard_router
from apps.immoweb.properties import router as properties_router
import apps.immoweb.properties_import  # noqa: F401 — registra le route import CSV/XML sul router (L9)
from apps.immoweb.clients import router as clients_router
from apps.immoweb.clients_smart import router as clients_smart_router
from apps.immoweb.clients_ai_import import router as clients_ai_import_router
from apps.immoweb.matches import router as matches_router
from apps.immoweb.brand_extractor import router as brand_router
from apps.immoweb.custom_domain import router as custom_domain_router
from apps.immoweb.themes import router as themes_router
from apps.immoweb.moderation import router as moderation_router
from apps.immoweb.cron import router as cron_router
from apps.immoweb.al_agent import router as al_agent_router
from apps.immoweb.al_legal.router import router as al_legal_router
from apps.immoweb.virtual_staging import router as virtual_staging_router
from apps.immoweb.fascicolo import router as fascicolo_router

router = APIRouter(prefix="/app", tags=["immoweb"])


@router.get("/health", response_model=HealthResponse)
async def app_health(accept_language: Optional[str] = Header(None)):
    lang = normalize_lang(accept_language)
    set_current_lang(lang)
    return HealthResponse(
        app="immoweb",
        lang=lang,
        message={"text": t("app.immoweb", lang=lang)},
    )


# Mount sub-routers
router.include_router(agencies_router)
router.include_router(domain_vault_router)
router.include_router(groups_router)
router.include_router(api_keys_router)
router.include_router(xml_import_router)
router.include_router(publishing_router)
router.include_router(social_publisher_router)
router.include_router(hal_knowledge_router)
router.include_router(property_privacy_router)
router.include_router(analytics_ab_router)
router.include_router(micro_tour_router)
router.include_router(publishing_feed_router)  # public feed at /api/feed/portals/{slug}.xml
router.include_router(invites_router)
router.include_router(dashboard_router)
router.include_router(properties_router)
router.include_router(clients_smart_router)
router.include_router(clients_ai_import_router)
router.include_router(clients_router)
router.include_router(matches_router)
router.include_router(brand_router)
router.include_router(custom_domain_router)
router.include_router(themes_router)
router.include_router(moderation_router)
router.include_router(cron_router)
router.include_router(al_agent_router)
router.include_router(al_legal_router)
router.include_router(virtual_staging_router)
router.include_router(fascicolo_router)
