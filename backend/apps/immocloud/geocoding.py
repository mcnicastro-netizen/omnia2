"""OMNIA — Geocoding helper (M3.S3).

Uses Nominatim (OpenStreetMap) — free, no API key required. Rate limit: 1 req/s,
so we make this fire-and-forget on property create/update (best effort).

Docs: https://nominatim.org/release-docs/develop/api/Search/
Usage policy: must set a User-Agent identifying the application.
"""
import asyncio
import logging
from typing import Optional, Tuple

import httpx

logger = logging.getLogger("omnia.geocoding")

NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "OMNIA-RealEstate/1.0 (contact: support@omniarealestateecosystem.it)"
HTTP_TIMEOUT = 8.0


async def geocode_address(
    address: Optional[str] = None,
    city: Optional[str] = None,
    province: Optional[str] = None,
    postal_code: Optional[str] = None,
    country: str = "Italy",
) -> Optional[Tuple[float, float]]:
    """Best-effort geocoding via Nominatim. Returns (lat, lng) or None.

    Strategy: try with full address first; if no result, fall back to city only.
    """
    parts = [p for p in [address, postal_code, city, province, country] if p]
    if not parts or not city:
        return None
    query = ", ".join(parts)

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get(
                NOMINATIM_BASE,
                params={"q": query, "format": "json", "limit": 1, "addressdetails": 0},
                headers={"User-Agent": USER_AGENT},
            )
            if r.status_code == 200:
                data = r.json()
                if data and isinstance(data, list):
                    lat = float(data[0]["lat"])
                    lng = float(data[0]["lon"])
                    return (lat, lng)

            # Fallback: city + country only
            if address or postal_code:
                fallback_q = ", ".join([city, country])
                r2 = await client.get(
                    NOMINATIM_BASE,
                    params={"q": fallback_q, "format": "json", "limit": 1},
                    headers={"User-Agent": USER_AGENT},
                )
                if r2.status_code == 200:
                    data = r2.json()
                    if data:
                        return (float(data[0]["lat"]), float(data[0]["lon"]))
    except Exception as e:
        logger.warning("geocoding failed for '%s': %s", query, e)
    return None


def schedule_geocode(db, property_id: str, address_dict: dict) -> None:
    """Fire-and-forget background geocoding task. Updates the property doc
    with lat/lng once Nominatim responds. Safe to call from a request handler.
    """
    async def _task():
        coords = await geocode_address(
            address=address_dict.get("address"),
            city=address_dict.get("city"),
            province=address_dict.get("province"),
            postal_code=address_dict.get("postal_code"),
        )
        if coords:
            lat, lng = coords
            try:
                await db.properties.update_one(
                    {"id": property_id},
                    {"$set": {"lat": lat, "lng": lng}},
                )
                logger.info("geocoded property %s -> (%s, %s)", property_id, lat, lng)
            except Exception as e:
                logger.warning("failed to save geocoded coords: %s", e)

    try:
        asyncio.create_task(_task())
    except RuntimeError:
        # No running loop — skip (e.g. during tests)
        pass
