"""ANNCSU — Archivio Nazionale dei Numeri Civici e Strade Urbane.

Integration with the public ISTAT/Agenzia Entrate registry to validate
and normalize Italian addresses. Used as an OPTIONAL enrichment layer
on top of the Nominatim fallback in valuator.py.

Endpoint: POST /api/cloud/anncsu/lookup
Input: { "address": "Via Roma 12, Milano" }
Output: { ok, normalized, comune, provincia_sigla, regione, cap, lat, lon, source }

ANNCSU offers a public ArcGIS endpoint with limited rate, so we
implement a thin async wrapper with graceful fallback to Nominatim.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from apps.immocloud.data.province_prices import PROVINCE_PRICES, PROVINCE_NAMES

logger = logging.getLogger("omnia.anncsu")

router = APIRouter(prefix="/anncsu", tags=["anncsu"])

# Public ArcGIS service exposed by ISTAT for ANNCSU (rate-limited but free)
ANNCSU_GEOCODE_URL = (
    "https://geoservizi.istat.it/server/rest/services/Indirizzi/Geocode_ANNCSU/"
    "GeocodeServer/findAddressCandidates"
)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

_TIMEOUT = 5.0
_HEADERS = {"User-Agent": "OMNIA-Valuator/1.0 (mcnicastro@gmail.com)"}


class AnncsuRequest(BaseModel):
    address: str = Field(min_length=3, max_length=300)


async def _suggest_anncsu(address: str, limit: int) -> list[Dict[str, Any]]:
    """ArcGIS ANNCSU suggest. Returns up to `limit` candidates."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(
                ANNCSU_GEOCODE_URL,
                params={
                    "f": "json",
                    "SingleLine": address,
                    "maxLocations": limit,
                    "outFields": "*",
                },
            )
        if r.status_code != 200:
            return []
        data = r.json()
        cands = data.get("candidates") or []
        out: list[Dict[str, Any]] = []
        for c in cands[:limit]:
            attrs = c.get("attributes", {}) or {}
            loc = c.get("location", {}) or {}
            comune = attrs.get("City") or attrs.get("Comune") or ""
            sigla = _COMUNE_INDEX.get(comune.lower())
            out.append({
                "source": "anncsu",
                "normalized": _normalize(attrs.get("Match_addr") or c.get("address") or address),
                "comune": comune,
                "provincia_sigla": sigla,
                "regione": attrs.get("Region") or attrs.get("Regione") or "",
                "cap": attrs.get("Postal") or attrs.get("Cap") or "",
                "lat": loc.get("y"),
                "lon": loc.get("x"),
                "score": c.get("score"),
            })
        return out
    except Exception as e:
        logger.debug("ANNCSU suggest failed: %s", e)
        return []


async def _suggest_nominatim(address: str, limit: int) -> list[Dict[str, Any]]:
    """Nominatim OSM suggest fallback."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(
                NOMINATIM_URL,
                params={
                    "q": f"{address}, Italia",
                    "format": "json",
                    "limit": limit,
                    "addressdetails": 1,
                    "countrycodes": "it",
                },
                headers=_HEADERS,
            )
        if r.status_code != 200:
            return []
        data = r.json()
        out: list[Dict[str, Any]] = []
        for item in data[:limit]:
            addr = item.get("address", {}) or {}
            iso = addr.get("ISO3166-2-lvl6") or addr.get("ISO3166-2-lvl4") or ""
            sigla = None
            if isinstance(iso, str) and iso.startswith("IT-") and len(iso) >= 5:
                s = iso.split("-")[-1].upper()
                if s in PROVINCE_PRICES:
                    sigla = s
            comune = (
                addr.get("city") or addr.get("town")
                or addr.get("village") or addr.get("municipality") or ""
            )
            if not sigla and comune:
                sigla = _COMUNE_INDEX.get(comune.lower())
            out.append({
                "source": "nominatim",
                "normalized": _normalize(item.get("display_name") or address),
                "comune": comune,
                "provincia_sigla": sigla,
                "regione": addr.get("state") or "",
                "cap": addr.get("postcode") or "",
                "lat": float(item["lat"]) if item.get("lat") else None,
                "lon": float(item["lon"]) if item.get("lon") else None,
                "score": float(item.get("importance") or 0) * 100,
            })
        return out
    except Exception as e:
        logger.debug("Nominatim suggest failed: %s", e)
        return []


# Mappa comune name (lowercase) → sigla provincia, popolata lazy dalla nostra tabella
def _build_comune_to_sigla_index() -> Dict[str, str]:
    """At module import: empty. Populated on first call via PROVINCE_NAMES capoluoghi."""
    idx: Dict[str, str] = {}
    for sigla, name in PROVINCE_NAMES.items():
        idx[name.lower()] = sigla
    return idx


_COMUNE_INDEX = _build_comune_to_sigla_index()


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


async def _try_anncsu(address: str) -> Optional[Dict[str, Any]]:
    """ArcGIS ANNCSU lookup. Returns None on failure."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(
                ANNCSU_GEOCODE_URL,
                params={
                    "f": "json",
                    "SingleLine": address,
                    "maxLocations": 1,
                    "outFields": "*",
                },
            )
        if r.status_code != 200:
            return None
        data = r.json()
        cands = data.get("candidates") or []
        if not cands:
            return None
        c = cands[0]
        attrs = c.get("attributes", {}) or {}
        loc = c.get("location", {}) or {}
        # ANNCSU returns fields like Match_addr, City, Region, etc.
        comune = attrs.get("City") or attrs.get("Comune") or ""
        regione = attrs.get("Region") or attrs.get("Regione") or ""
        cap = attrs.get("Postal") or attrs.get("Cap") or ""
        normalized = attrs.get("Match_addr") or c.get("address") or address

        sigla = _COMUNE_INDEX.get(comune.lower())
        return {
            "source": "anncsu",
            "normalized": _normalize(normalized),
            "comune": comune,
            "provincia_sigla": sigla,
            "provincia_name": PROVINCE_NAMES.get(sigla) if sigla else None,
            "regione": regione,
            "cap": cap,
            "lat": loc.get("y"),
            "lon": loc.get("x"),
            "score": c.get("score"),
        }
    except Exception as e:
        logger.debug("ANNCSU lookup failed: %s", e)
        return None


async def _try_nominatim(address: str) -> Optional[Dict[str, Any]]:
    """Nominatim OSM fallback."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(
                NOMINATIM_URL,
                params={
                    "q": f"{address}, Italia",
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1,
                    "countrycodes": "it",
                },
                headers=_HEADERS,
            )
        if r.status_code != 200:
            return None
        data = r.json()
        if not data:
            return None
        item = data[0]
        addr = item.get("address", {}) or {}
        iso = addr.get("ISO3166-2-lvl6") or addr.get("ISO3166-2-lvl4") or ""
        sigla = None
        if isinstance(iso, str) and iso.startswith("IT-") and len(iso) >= 5:
            sigla = iso.split("-")[-1].upper()
            if sigla not in PROVINCE_PRICES:
                sigla = None

        comune = (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("municipality")
            or ""
        )
        # If sigla still missing, try via comune index
        if not sigla and comune:
            sigla = _COMUNE_INDEX.get(comune.lower())

        regione = addr.get("state") or ""
        return {
            "source": "nominatim",
            "normalized": _normalize(item.get("display_name") or address),
            "comune": comune,
            "provincia_sigla": sigla,
            "provincia_name": PROVINCE_NAMES.get(sigla) if sigla else None,
            "regione": regione,
            "cap": addr.get("postcode") or "",
            "lat": float(item["lat"]) if item.get("lat") else None,
            "lon": float(item["lon"]) if item.get("lon") else None,
            "score": float(item.get("importance") or 0) * 100,
        }
    except Exception as e:
        logger.debug("Nominatim lookup failed: %s", e)
        return None


@router.post("/lookup")
async def lookup_address(payload: AnncsuRequest) -> Dict[str, Any]:
    """Try ANNCSU first, fallback to Nominatim, return structured address.

    Returns 404 if neither service finds the address.
    """
    address = _normalize(payload.address)

    # 1. ANNCSU primary
    result = await _try_anncsu(address)

    # 2. Nominatim fallback
    if not result:
        result = await _try_nominatim(address)

    if not result:
        raise HTTPException(status_code=404, detail="address_not_found")

    return {
        "ok": True,
        **result,
        "input": payload.address,
    }


@router.get("/suggest")
async def suggest_address(
    q: str = Query(..., min_length=3, max_length=200, description="Partial address query"),
    limit: int = Query(5, ge=1, le=10),
) -> Dict[str, Any]:
    """Live autocomplete: returns up to `limit` Italian address candidates.

    Tries ANNCSU first; if it returns 0, falls back to Nominatim OSM.
    Never raises 404 on empty — returns `{ok: true, candidates: []}`.
    """
    query = _normalize(q)
    candidates = await _suggest_anncsu(query, limit)
    if not candidates:
        candidates = await _suggest_nominatim(query, limit)
    return {"ok": True, "candidates": candidates, "input": q}


@router.get("/health")
async def anncsu_health() -> Dict[str, Any]:
    return {
        "service": "anncsu",
        "primary_provider": "ANNCSU ArcGIS (ISTAT)",
        "fallback_provider": "Nominatim OSM",
        "comune_index_size": len(_COMUNE_INDEX),
    }
