"""OMNIA — Admin cron triggers (M3.S7) · D-108.

Owner automatico dei job = APScheduler (sync_engine.start_scheduler).
Questi endpoint HTTP sono **solo trigger manuali / fallback controllato**
per super_admin — non una seconda autorità di scheduling parallela.
Non registrare CronJob esterni che li chiamino in parallelo allo scheduler.
"""
from fastapi import APIRouter, Depends, HTTPException

from shared.auth.dependencies import get_current_user
from apps.immocloud.saved_searches import run_all_active_saved_searches
from apps.immoweb.trash import run_trash_purge
from apps.immoweb.backup_job import run_daily_backup
from apps.immoweb.request_matching_job import run_all_request_matching
from apps.billing.b2c_listing_publish import run_expire_paid_listing_slots
from apps.immoweb.private_listing_matching import run_private_listing_request_matching

router = APIRouter(prefix="/cron", tags=["cron"])

ALLOWED_ROLES = {"super_admin"}


@router.post("/saved-searches/run-all")
async def cron_run_saved_searches(user: dict = Depends(get_current_user)):
    """Trigger manuale (D-108) — owner automatico = APScheduler."""
    if user.get("role") not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="cron_forbidden")
    result = await run_all_active_saved_searches()
    return {"ok": True, "trigger": "manual", "owner": "apscheduler", **result}


@router.post("/requests/matching")
async def cron_run_request_matching(user: dict = Depends(get_current_user)):
    """D-090 — matching notturno. Trigger manuale (D-108)."""
    if user.get("role") not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="cron_forbidden")
    result = await run_all_request_matching()
    return {"ok": True, "trigger": "manual", "owner": "apscheduler", **result}


@router.post("/trash/purge")
async def cron_purge_trash(user: dict = Depends(get_current_user)):
    """Svuota dal Cestino immobili/clienti oltre i 30 giorni. Trigger manuale."""
    if user.get("role") not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="cron_forbidden")
    result = await run_trash_purge()
    return {**(result if isinstance(result, dict) else {"result": result}), "trigger": "manual", "owner": "apscheduler"}


@router.post("/backup/daily")
async def cron_daily_backup(user: dict = Depends(get_current_user)):
    """Backup giornaliero (DB + media). Trigger manuale (D-108) — D-085/D-105."""
    if user.get("role") not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="cron_forbidden")
    report = await run_daily_backup()
    return {"ok": True, "trigger": "manual", "owner": "apscheduler", **report}


@router.post("/listings/expire-paid-slots")
async def cron_expire_paid_listing_slots(user: dict = Depends(get_current_user)):
    """Ritira annunci privati con slot Stripe 90gg scaduto. Trigger manuale (D-108)."""
    if user.get("role") not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="cron_forbidden")
    report = await run_expire_paid_listing_slots()
    return {"ok": True, "trigger": "manual", "owner": "apscheduler", **report}


@router.post("/listings/match-private")
async def cron_match_private_listings(user: dict = Depends(get_current_user)):
    """Match annunci privati → richieste CRM tutte le agenzie. Trigger manuale (D-108)."""
    if user.get("role") not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="cron_forbidden")
    report = await run_private_listing_request_matching()
    return {"ok": True, "trigger": "manual", "owner": "apscheduler", **report}
