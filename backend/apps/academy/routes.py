"""OMNIA — Academy routes (LMS for agent training)."""
from fastapi import APIRouter, Header
from typing import Optional

from shared.models.base import HealthResponse
from shared.utils.i18n import t, normalize_lang
from shared.db.connection import set_current_lang

router = APIRouter(prefix="/learn", tags=["academy"])


@router.get("/health", response_model=HealthResponse)
async def academy_health(accept_language: Optional[str] = Header(None)):
    lang = normalize_lang(accept_language)
    set_current_lang(lang)
    return HealthResponse(
        app="academy",
        lang=lang,
        message={"text": t("app.academy", lang=lang)},
    )
