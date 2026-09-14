"""OMNIA — Core routes (auth, agencies, health, system-level)."""
import logging
from fastapi import APIRouter, Header
from typing import Optional

from shared.models.base import HealthResponse
from shared.db.connection import Database, get_current_lang, set_current_lang
from shared.utils.i18n import t, normalize_lang

router = APIRouter(prefix="/core", tags=["core"])
logger = logging.getLogger("omnia.health")


@router.get("/health", response_model=HealthResponse)
async def health(accept_language: Optional[str] = Header(None)):
    """Global health check — verifies backend + Mongo are reachable.

    Note (R9 hardening): raw exception details are logged server-side only.
    The public response returns a generic status to avoid information
    disclosure (DB internals, connection strings).
    """
    lang = normalize_lang(accept_language)
    set_current_lang(lang)
    db = Database.get()
    try:
        await db.command("ping")
        db_status = "ok"
    except Exception as exc:  # noqa: BLE001 — top-level health probe
        logger.exception("Health ping to MongoDB failed: %s", exc)
        db_status = "error"
    return HealthResponse(
        app="core",
        lang=lang,
        message={
            "text": t("health.ok", lang=lang),
            "db": db_status,
        },
    )
