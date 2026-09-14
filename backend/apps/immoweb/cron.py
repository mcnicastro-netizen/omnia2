"""OMNIA — Admin cron triggers (M3.S7).

Endpoints that an external scheduler (k8s CronJob, cron, GitHub Actions)
can call to run periodic jobs. Admin-protected so we can also call them
manually from the dashboard.
"""
from fastapi import APIRouter, Depends, HTTPException

from shared.auth.dependencies import get_current_user
from apps.immocloud.saved_searches import run_all_active_saved_searches

router = APIRouter(prefix="/cron", tags=["cron"])

ALLOWED_ROLES = {"super_admin"}


@router.post("/saved-searches/run-all")
async def cron_run_saved_searches(user: dict = Depends(get_current_user)):
    if user.get("role") not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="cron_forbidden")
    result = await run_all_active_saved_searches()
    return {"ok": True, **result}
