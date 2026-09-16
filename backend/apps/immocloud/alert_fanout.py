"""Event-driven fan-out for saved-search / price-drop alerts (near-instant).

Called when a listing goes live or drops price — Idealista-style speed without
waiting for the hourly cron. Cron remains as safety net for daily/weekly.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from shared.db.connection import Database

logger = logging.getLogger("omnia.alert_fanout")


def _listing_matches_filters(prop: dict, filters: dict) -> bool:
    if not filters:
        return True
    if filters.get("operation") and prop.get("operation") != filters["operation"]:
        return False
    if filters.get("property_type") and prop.get("property_type") != filters["property_type"]:
        return False
    if filters.get("city"):
        city = (prop.get("city") or "").lower()
        if not city.startswith(str(filters["city"]).lower()):
            return False
    if filters.get("rooms_min") and (prop.get("rooms") or 0) < int(filters["rooms_min"]):
        return False
    if filters.get("bedrooms_min") and (prop.get("bedrooms") or 0) < int(filters["bedrooms_min"]):
        return False
    if filters.get("bathrooms_min") and (prop.get("bathrooms") or 0) < int(filters["bathrooms_min"]):
        return False
    if filters.get("surface_min") and (prop.get("surface_sqm") or 0) < float(filters["surface_min"]):
        return False
    if filters.get("energy_class"):
        energy = (prop.get("energy") or {}).get("energy_class") if isinstance(prop.get("energy"), dict) else prop.get("energy_class")
        if energy != filters["energy_class"]:
            return False
    op = filters.get("operation") or prop.get("operation") or "sale"
    price = prop.get("rent_monthly") if op == "rent" else prop.get("price")
    if filters.get("price_min") and (price or 0) < int(filters["price_min"]):
        return False
    if filters.get("price_max") and price is not None and price > int(filters["price_max"]):
        return False
    return True


async def fanout_listing_event(
    property_id: str,
    *,
    event: str = "new",  # "new" | "price_drop"
) -> Dict[str, Any]:
    """Notify B2C users whose active saved searches match this listing."""
    db = Database.get()
    prop = await db.properties.find_one(
        {"id": property_id, "status": "active"},
        {"_id": 0},
    )
    if not prop:
        return {"notified": 0, "reason": "listing_not_active"}

    # Instant searches always; price_drop also wakes daily watchers once
    cursor = db.saved_searches.find({"is_active": True})
    notified = 0
    frontend = os.environ.get("FRONTEND_BASE_URL", "https://omniarealestateecosystem.it")
    async for s in cursor:
        freq = s.get("frequency") or "instant"
        if event == "new" and freq not in ("instant",):
            continue
        if event == "price_drop" and freq == "weekly":
            continue
        if not _listing_matches_filters(prop, s.get("filters") or {}):
            continue
        user = await db.users.find_one(
            {"id": s["user_id"], "account_type": "b2c"},
            {"_id": 0, "email": 1, "name": 1, "lang": 1,
             "notification_channels": 1, "notification_email_types": 1},
        )
        if not user:
            continue
        lang = (user.get("lang") or "it")[:2]
        title = prop.get("title") or "Immobile"
        city = prop.get("city") or ""
        if event == "price_drop":
            drop = prop.get("last_price_drop") or {}
            pct = drop.get("drop_pct")
            n_title = f"Ribasso · {title}"
            n_body = f"{city}" + (f" −{pct}%" if pct else "")
        else:
            n_title = f"Nuovo · {s.get('name') or 'Ricerca'}"
            n_body = f"{title} · {city}"

        try:
            from shared.notifications.center import TYPE_SAVED_SEARCH, create_notification
            await create_notification(
                user_id=s["user_id"],
                type=TYPE_SAVED_SEARCH,
                title=n_title[:200],
                body=n_body[:1000],
                link=f"/cloud/property/{property_id}",
                meta={"property_id": property_id, "event": event, "saved_search_id": s["id"]},
            )
        except Exception as e:
            logger.warning("fanout inbox failed: %s", e)

        # Web push
        channels = user.get("notification_channels") or []
        if "push" in channels:
            try:
                from shared.notifications.web_push import send_push_to_user
                await send_push_to_user(
                    s["user_id"],
                    title=n_title,
                    body=n_body,
                    url=f"/{lang}/cloud/property/{property_id}",
                )
            except Exception as e:
                logger.warning("fanout push failed: %s", e)

        from shared.notifications.prefs import user_allows_email
        if user_allows_email(user, "saved_search_alert"):
            try:
                from apps.immocloud.saved_searches import _send_alert_email
                matches = [prop] if event == "new" else []
                drops = [prop] if event == "price_drop" else []
                await _send_alert_email(
                    to_email=user["email"],
                    user_name=user.get("name") or "",
                    lang=lang,
                    search_name=s.get("name") or "Ricerca",
                    matches=matches,
                    drops=drops,
                    frontend_base=frontend,
                )
            except Exception as e:
                logger.warning("fanout email failed: %s", e)
        notified += 1

    logger.info("fanout event=%s prop=%s notified=%s", event, property_id, notified)
    return {"notified": notified, "event": event, "property_id": property_id}
