"""OMNIA — ImmobilCloud routes (B2C portal)."""
from fastapi import APIRouter, Header
from typing import Optional

from shared.models.base import HealthResponse
from shared.utils.i18n import t, normalize_lang
from shared.db.connection import set_current_lang
from apps.immocloud.public_portal import router as public_portal_router
from apps.immocloud.cloud_auth import router as cloud_auth_router
from apps.immocloud.private_listings import router as private_listings_router
from apps.immocloud.valuator import router as valuator_router
from apps.immocloud.valuation_pdf import router as valuation_pdf_router
from apps.immocloud.mutui import router as mutui_router
from apps.immocloud.anncsu import router as anncsu_router
from apps.immocloud.saved_searches import router as saved_searches_router
from apps.immoweb.micro_tour_video import public_router as micro_tour_public_router

router = APIRouter(prefix="/cloud", tags=["immocloud"])


@router.get("/health", response_model=HealthResponse)
async def cloud_health(accept_language: Optional[str] = Header(None)):
    lang = normalize_lang(accept_language)
    set_current_lang(lang)
    return HealthResponse(
        app="immocloud",
        lang=lang,
        message={"text": t("app.immocloud", lang=lang)},
    )


router.include_router(public_portal_router)
router.include_router(cloud_auth_router)
router.include_router(private_listings_router)
router.include_router(valuator_router)
router.include_router(valuation_pdf_router)
router.include_router(mutui_router)
router.include_router(anncsu_router)
router.include_router(saved_searches_router)
router.include_router(micro_tour_public_router)
