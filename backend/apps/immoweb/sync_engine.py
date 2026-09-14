"""OMNIA — Publishing Sync Engine (M2.6b, D-053).

Responsibilities:
1. Iterate all active AgencyPortalConnection entries with `status=active`
   and run a sync attempt for each.
2. Persist a `PortalSyncLog` per attempt (started_at, ended_at, status,
   items_ok/failed, error_message, retry_count).
3. Update connection metadata (`last_sync_at`, `next_sync_at`, counters).
4. Support both PULL (feed_pull) and PUSH (api_push) portals:
   - PULL: we just refresh timestamp + ensure feed is warm (no external call —
     portals fetch our public feed).
   - PUSH: stub for now; real integrations will land in M2.6c (Social) and
     M2.6d (Universal Portal Wizard). We record a "simulated_push" status.
5. Retry with exponential backoff on failure (1min, 5min, 30min).

Scheduler is APScheduler AsyncIOScheduler, wired up in server.py lifespan.
It runs daily at 06:00 UTC (~07:00 CET winter / 08:00 CEST summer).

All logic is safe to invoke manually via POST /publishing/connections/{id}/sync-now.
"""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from shared.db.connection import Database
from shared.validators.compliance import validate_property

logger = logging.getLogger(__name__)

# ---------- Constants ----------

DAILY_SYNC_HOUR_UTC = 6         # 06:00 UTC daily job
DAILY_SYNC_MINUTE_UTC = 0

# Retry schedule (seconds) — exponential-ish
RETRY_DELAYS_SEC = [60, 300, 1800]
MAX_RETRIES = len(RETRY_DELAYS_SEC)


# ---------- Helpers ----------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_daily_at_iso() -> str:
    now = datetime.now(timezone.utc)
    target = now.replace(hour=DAILY_SYNC_HOUR_UTC, minute=DAILY_SYNC_MINUTE_UTC,
                        second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target.isoformat()


async def _fetch_properties(agency_id: str, is_all: bool,
                             property_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    db = Database.get()
    q: Dict[str, Any] = {"agency_id": agency_id, "status": "active"}
    if not is_all and property_ids:
        q["id"] = {"$in": property_ids}
    return await db.properties.find(q).limit(2000).to_list(2000)


async def _record_log(agency_id: str, portal_slug: str, connection_id: str,
                      status: str, items_ok: int, items_failed: int,
                      started_at: str, error_message: Optional[str] = None,
                      retry_count: int = 0, trigger: str = "scheduled") -> Dict[str, Any]:
    db = Database.get()
    doc = {
        "id": str(uuid4()),
        "agency_id": agency_id,
        "portal_slug": portal_slug,
        "connection_id": connection_id,
        "started_at": started_at,
        "ended_at": _now_iso(),
        "status": status,
        "items_ok": items_ok,
        "items_failed": items_failed,
        "error_message": error_message,
        "retry_count": retry_count,
        "trigger": trigger,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await db.publishing_sync_logs.insert_one(doc)
    # `insert_one` mutates `doc` adding `_id` (ObjectId, non JSON-serializable).
    # Strip it so callers can safely return the dict via FastAPI.
    doc.pop("_id", None)
    return doc


async def _update_connection_after_sync(connection_id: str, agency_id: str,
                                         items_ok: int, items_failed: int,
                                         status: str, error: Optional[str]) -> None:
    db = Database.get()
    update: Dict[str, Any] = {
        "last_sync_at": _now_iso(),
        "next_sync_at": _next_daily_at_iso(),
        "items_published": items_ok,
        "items_failed": items_failed,
        "last_error": error,
        "updated_at": _now_iso(),
    }
    # Only escalate "status" to "error" on repeated failures; success clears it.
    if status == "success":
        update["last_error"] = None
    await db.publishing_connections.update_one(
        {"id": connection_id, "agency_id": agency_id},
        {"$set": update},
    )


# ---------- Core sync ----------

async def sync_connection(connection: Dict[str, Any], trigger: str = "scheduled",
                          retry_count: int = 0) -> Dict[str, Any]:
    """Run a single sync for one AgencyPortalConnection.

    Returns a dict summarizing what happened. Never raises: all errors are
    captured and stored in the sync log.
    """
    db = Database.get()
    agency_id = connection["agency_id"]
    portal_slug = connection["portal_slug"]
    connection_id = connection["id"]
    started_at = _now_iso()

    try:
        # 1. Load catalog entry to know integration_type
        portal = await db.publishing_catalog.find_one({"slug": portal_slug})
        if not portal:
            log = await _record_log(agency_id, portal_slug, connection_id,
                                    "failed", 0, 0, started_at,
                                    "portal_not_in_catalog", retry_count, trigger)
            await _update_connection_after_sync(connection_id, agency_id, 0, 0,
                                                "failed", "portal_not_in_catalog")
            return {"ok": False, "log": log}

        # 2. Load properties eligible for this connection
        properties = await _fetch_properties(agency_id, connection.get("is_all_properties", True))
        publishable: List[Dict[str, Any]] = []
        blocked = 0
        blocked_reasons: List[str] = []
        for p in properties:
            r = validate_property(p)
            if r["publishable"]:
                publishable.append(p)
            else:
                blocked += 1
                blocked_reasons.extend(r["hard_violations"])

        # 3. Execute per-integration-type action
        integration_type = portal.get("integration_type", "feed_pull")
        if integration_type == "feed_pull":
            # We just make sure the feed will be served on next poll.
            # No external call — portals pull our /publishing/feed URL.
            action_status = "success"
            action_error: Optional[str] = None
        elif integration_type == "api_push":
            # Real push integrations arrive in M2.6c/M2.6d. For now: simulated.
            action_status = "simulated_push"
            action_error = None
        else:
            action_status = "failed"
            action_error = f"unsupported_integration_type:{integration_type}"

        # 4. Log
        final_status = "success" if action_status in ("success", "simulated_push") else "failed"
        error_message = action_error
        if blocked > 0 and final_status == "success":
            final_status = "partial"
            error_message = f"blocked_by_compliance:{blocked}"

        log = await _record_log(agency_id, portal_slug, connection_id,
                                final_status, len(publishable), blocked, started_at,
                                error_message, retry_count, trigger)
        await _update_connection_after_sync(connection_id, agency_id,
                                            len(publishable), blocked,
                                            final_status, error_message)

        return {
            "ok": final_status != "failed",
            "log": log,
            "publishable_count": len(publishable),
            "blocked_count": blocked,
            "integration_type": integration_type,
            "action_status": action_status,
        }
    except Exception as e:  # never let scheduler die
        logger.exception("sync_connection failure agency=%s portal=%s",
                         agency_id, portal_slug)
        log = await _record_log(agency_id, portal_slug, connection_id,
                                "failed", 0, 0, started_at, str(e),
                                retry_count, trigger)
        await _update_connection_after_sync(connection_id, agency_id, 0, 0,
                                            "failed", str(e))
        return {"ok": False, "log": log, "error": str(e)}


async def sync_connection_with_retry(connection: Dict[str, Any],
                                     trigger: str = "scheduled") -> Dict[str, Any]:
    """Run sync + up to MAX_RETRIES retries with exponential backoff.

    NOTE: for manual "sync now" trigger we bypass retries to keep response snappy.
    """
    result = await sync_connection(connection, trigger=trigger, retry_count=0)
    if result.get("ok") or trigger == "manual":
        return result
    for attempt, delay in enumerate(RETRY_DELAYS_SEC, start=1):
        await asyncio.sleep(delay)
        # Reload connection each time in case it was disabled meanwhile
        db = Database.get()
        fresh = await db.publishing_connections.find_one(
            {"id": connection["id"], "status": "active"})
        if not fresh:
            return result
        result = await sync_connection(fresh, trigger=trigger, retry_count=attempt)
        if result.get("ok"):
            return result
    return result


async def run_all_active_syncs(trigger: str = "scheduled") -> Dict[str, Any]:
    """Iterate all `status=active` connections and sync each.

    Called by the daily APScheduler job AND by the admin cron endpoint.
    Failures on one connection do NOT abort the others.
    """
    db = Database.get()
    conns = await db.publishing_connections.find({"status": "active"}).to_list(1000)
    logger.info("run_all_active_syncs starting: %d active connections", len(conns))
    results = []
    for c in conns:
        try:
            r = await sync_connection_with_retry(c, trigger=trigger)
            results.append({"connection_id": c["id"], "portal_slug": c["portal_slug"],
                            "ok": r.get("ok"), "publishable": r.get("publishable_count", 0),
                            "blocked": r.get("blocked_count", 0)})
        except Exception as e:
            logger.exception("Unhandled sync error connection=%s", c.get("id"))
            results.append({"connection_id": c["id"], "portal_slug": c.get("portal_slug"),
                            "ok": False, "error": str(e)})
    return {"triggered_at": _now_iso(), "total": len(conns), "results": results}


# ---------- APScheduler wiring ----------

_scheduler = None


def start_scheduler() -> None:
    """Start the AsyncIOScheduler and register the daily job.

    Called from server.py lifespan. Idempotent (safe if called twice in
    hot-reload dev).
    """
    global _scheduler
    if _scheduler is not None:
        return
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning("APScheduler not installed — daily sync disabled")
        return
    sched = AsyncIOScheduler(timezone="UTC")
    sched.add_job(
        run_all_active_syncs,
        CronTrigger(hour=DAILY_SYNC_HOUR_UTC, minute=DAILY_SYNC_MINUTE_UTC),
        kwargs={"trigger": "scheduled"},
        id="publishing_daily_sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    sched.start()
    _scheduler = sched
    logger.info("Publishing scheduler started (daily at %02d:%02d UTC)",
                DAILY_SYNC_HOUR_UTC, DAILY_SYNC_MINUTE_UTC)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:  # pragma: no cover
            pass
        _scheduler = None
