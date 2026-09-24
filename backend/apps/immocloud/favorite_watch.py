"""OMNIA — Favorite listing end alerts (D-093 / A-030).

Idealista/Immobiliare pattern: when a watched listing is sold / rented /
withdrawn, notify B2C users who saved it. Price drops already handled in
`saved_searches.run_all_active_saved_searches` + `price_watch`.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

logger = logging.getLogger("omnia.favorite_watch")

TERMINAL_STATUSES: Set[str] = {"sold", "rented", "withdrawn"}

_STATUS_LABEL_IT = {
    "sold": "Venduto",
    "rented": "Affittato",
    "withdrawn": "Ritirato",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def record_listing_ended(
    db,
    *,
    property_id: str,
    existing: Dict[str, Any],
    new_status: str,
) -> Optional[dict]:
    """Stamp end metadata when status moves into a terminal state.

    Returns the stamp dict when a transition happened, else None.
    """
    if new_status not in TERMINAL_STATUSES:
        return None
    old = existing.get("status")
    if old == new_status:
        return None
    if old in TERMINAL_STATUSES and existing.get("listing_ended_at"):
        # Already ended — only refresh status label if changed sold→withdrawn etc.
        pass

    stamp = {
        "listing_ended_at": _now_iso(),
        "listing_end_status": new_status,
        "listing_end_from_status": old,
    }
    await db.properties.update_one({"id": property_id}, {"$set": stamp})
    try:
        await notify_favoriters_listing_ended(db, property_id=property_id, status=new_status)
    except Exception as e:  # noqa: BLE001
        logger.warning("notify favoriters on end failed prop=%s: %s", property_id, e)
    return stamp


async def notify_favoriters_listing_ended(
    db,
    *,
    property_id: str,
    status: str,
) -> Dict[str, Any]:
    """Immediate fan-out to users who favorited this listing."""
    prop = await db.properties.find_one(
        {"id": property_id},
        {"_id": 0, "id": 1, "title": 1, "city": 1, "status": 1,
         "listing_end_status": 1, "price": 1, "rent_monthly": 1, "operation": 1},
    )
    if not prop:
        return {"notified": 0, "reason": "missing"}

    end_status = status or prop.get("listing_end_status") or prop.get("status")
    label = _STATUS_LABEL_IT.get(end_status, end_status or "non disponibile")
    title = prop.get("title") or "Immobile"
    city = prop.get("city") or ""
    frontend = os.environ.get("FRONTEND_BASE_URL", "https://omniarealestateecosystem.it")

    user_ids = [
        d["user_id"]
        async for d in db.favorites.find(
            {"property_id": property_id},
            {"_id": 0, "user_id": 1},
        )
    ]
    notified = 0
    for uid in user_ids:
        if not uid:
            continue
        user = await db.users.find_one(
            {"id": uid, "account_type": "b2c"},
            {"_id": 0, "email": 1, "name": 1, "lang": 1,
             "notification_channels": 1, "notification_email_types": 1},
        )
        if not user:
            continue
        lang = (user.get("lang") or "it")[:2]
        n_title = f"{label} · {title}"
        n_body = city or "Un immobile nei tuoi preferiti non è più disponibile."

        try:
            from shared.notifications.center import (
                TYPE_FAVORITE_ENDED,
                create_notification,
            )
            await create_notification(
                user_id=uid,
                type=TYPE_FAVORITE_ENDED,
                title=n_title[:200],
                body=n_body[:1000],
                link="/cloud/account",
                meta={"property_id": property_id, "status": end_status, "event": "listing_ended"},
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("fav end inbox failed: %s", e)

        from shared.notifications.prefs import user_allows_email
        if user.get("email") and user_allows_email(user, "saved_search_alert"):
            try:
                from apps.immocloud.saved_searches import _send_alert_email
                ended_card = {
                    **prop,
                    "title": f"[{label}] {title}",
                }
                await _send_alert_email(
                    to_email=user["email"],
                    user_name=user.get("name") or "",
                    lang=lang,
                    search_name="I tuoi preferiti",
                    matches=[ended_card],
                    drops=[],
                    frontend_base=frontend,
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("fav end email failed: %s", e)
        notified += 1

    logger.info(
        "favorite_watch ended prop=%s status=%s notified=%s",
        property_id, end_status, notified,
    )
    return {"notified": notified, "property_id": property_id, "status": end_status}


async def cron_favorites_ended_pass(db) -> Dict[str, Any]:
    """Safety-net: pick up ended listings since each user's favorites_ended_watch_at."""
    import os
    frontend = os.environ.get("FRONTEND_BASE_URL", "https://omniarealestateecosystem.it")
    now = _now_iso()
    notices = 0
    emails = 0

    async for row in db.favorites.aggregate([
        {"$group": {"_id": "$user_id", "pids": {"$addToSet": "$property_id"}}},
    ]):
        uid = row["_id"]
        pids = row.get("pids") or []
        if not uid or not pids:
            continue
        user = await db.users.find_one(
            {"id": uid, "account_type": "b2c"},
            {"_id": 0, "email": 1, "name": 1, "lang": 1,
             "notification_channels": 1, "notification_email_types": 1,
             "favorites_ended_watch_at": 1},
        )
        if not user:
            continue
        since = user.get("favorites_ended_watch_at")
        q: Dict[str, Any] = {
            "id": {"$in": pids},
            "listing_ended_at": {"$exists": True},
            "listing_end_status": {"$in": list(TERMINAL_STATUSES)},
        }
        if since:
            q["listing_ended_at"] = {"$gt": since}
        ended = await db.properties.find(
            q,
            {"_id": 0, "id": 1, "title": 1, "city": 1, "listing_end_status": 1,
             "price": 1, "rent_monthly": 1, "operation": 1},
        ).to_list(length=20)
        await db.users.update_one(
            {"id": uid}, {"$set": {"favorites_ended_watch_at": now}},
        )
        if not ended:
            continue
        notices += len(ended)
        labels = []
        for d in ended[:3]:
            st = d.get("listing_end_status") or ""
            lab = _STATUS_LABEL_IT.get(st, st)
            labels.append(f"{lab}: {(d.get('title') or d['id'])[:40]}")
        try:
            from shared.notifications.center import (
                TYPE_FAVORITE_ENDED,
                create_notification,
            )
            await create_notification(
                user_id=uid,
                type=TYPE_FAVORITE_ENDED,
                title=f"Preferiti non più disponibili ({len(ended)})",
                body=", ".join(labels),
                link="/cloud/account",
                meta={"property_ids": [d["id"] for d in ended]},
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("fav ended cron inbox failed: %s", e)

        from shared.notifications.prefs import user_allows_email
        if user.get("email") and user_allows_email(user, "saved_search_alert"):
            try:
                from apps.immocloud.saved_searches import _send_alert_email
                cards = []
                for d in ended:
                    st = d.get("listing_end_status") or ""
                    lab = _STATUS_LABEL_IT.get(st, st)
                    cards.append({**d, "title": f"[{lab}] {d.get('title') or 'Immobile'}"})
                await _send_alert_email(
                    to_email=user["email"],
                    user_name=user.get("name") or "",
                    lang=(user.get("lang") or "it")[:2],
                    search_name="I tuoi preferiti",
                    matches=cards,
                    drops=[],
                    frontend_base=frontend,
                )
                emails += 1
            except Exception as e:  # noqa: BLE001
                logger.warning("fav ended cron email failed: %s", e)

    return {"favorite_ended_notices": notices, "emails_sent": emails, "run_at": now}
