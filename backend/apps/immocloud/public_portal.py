"""OMNIA — ImmobilCloud B2C Public Portal (M3.S1).

MOVE-ONLY split:
  portal_common.py  — helpers / cards / geo / viewer
  portal_search.py  — /search · /search/advanced · /map · /facets
  portal_detail.py  — /property/{id} · /agency/{slug}
  portal_contact.py — /property/{id}/contact

This module keeps the aggregated router + re-exports used by tests and siblings.
Mounted under `/api/cloud/*` via `immocloud.routes`.
"""
from __future__ import annotations

from fastapi import APIRouter

from apps.immocloud.portal_common import (
    LIST_FIELDS,
    PUBLIC_FIELDS,
    _active_boost_tier,
    _base_filter,
    _cover_photo,
    _digits_phone,
    _haversine_km,
    _point_in_polygon,
    _public_publisher,
    _scout_hint,
    _to_card,
    _viewer_is_lister,
)
from apps.immocloud.portal_contact import public_property_contact
from apps.immocloud.portal_contact import router as contact_router
from apps.immocloud.portal_detail import public_agency_card, public_property_detail
from apps.immocloud.portal_detail import router as detail_router
from apps.immocloud.portal_search import (
    public_facets,
    public_map_markers,
    public_search,
    public_search_advanced,
)
from apps.immocloud.portal_search import router as search_router

router = APIRouter(tags=["immobilcloud"])
router.include_router(search_router)
router.include_router(detail_router)
router.include_router(contact_router)

__all__ = [
    "router",
    "PUBLIC_FIELDS",
    "LIST_FIELDS",
    "_base_filter",
    "_cover_photo",
    "_digits_phone",
    "_public_publisher",
    "_active_boost_tier",
    "_to_card",
    "_scout_hint",
    "_haversine_km",
    "_point_in_polygon",
    "_viewer_is_lister",
    "public_search",
    "public_search_advanced",
    "public_map_markers",
    "public_facets",
    "public_property_detail",
    "public_agency_card",
    "public_property_contact",
]
