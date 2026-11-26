"""S4 — Un solo contratto di visibilità pubblica (portale + brand site).

Contraddizione C4: ImmobilCloud e `/p/{slug}` potevano mostrare verità diverse
sullo stesso immobile. Qui c’è la SoT Mongo condivisa.

Regola comune (`public_surface_base`):
  status=active · visibility=public · moderation ∉ {pending,rejected} · non trashed

Delta intenzionali (documentati, non bug):
  · Portale: + is_listed_on_immobilcloud ≠ false · privacy ∉ {L3,L4} (feed anon)
  · Brand:   + agency_id · L3/L4 ammessi (sito agenzia) · listing ImmobilCloud non richiesto
"""
from __future__ import annotations

from typing import Any, Dict, Optional  # noqa: F401 — Optional used by helpers

from shared.db.trash import with_not_trashed


def public_surface_base() -> Dict[str, Any]:
    """Superficie pubblica condivisa — stessa verità “è un annuncio pubblico”."""
    return {
        "status": "active",
        "visibility": "public",
        "moderation_status": {"$nin": ["pending", "rejected"]},
    }


def portal_listing_filter(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Filtro ImmobilCloud (search/detail/facets/map)."""
    base = {
        **public_surface_base(),
        "is_listed_on_immobilcloud": {"$ne": False},
        "privacy_level": {"$nin": ["L3", "L4"]},
    }
    if extra:
        base.update(extra)
    return with_not_trashed(base)


def brand_site_filter(agency_id: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Filtro sito brand `/p/{slug}` — stessa superficie pubblica + tenant agency.

    Non richiede `is_listed_on_immobilcloud` (opt-out portale ≠ nascosto sul proprio sito).
    Non esclude L3/L4 (sito agenzia può mostrare schede riservate ai visitatori del brand).
    """
    base = {
        **public_surface_base(),
        "agency_id": agency_id,
    }
    if extra:
        base.update(extra)
    return with_not_trashed(base)


def intentional_deltas() -> Dict[str, str]:
    """Per docs / Founder Ops — cosa può differire di proposito."""
    return {
        "is_listed_on_immobilcloud": (
            "Solo portale: false nasconde da ImmobilCloud ma non dal sito brand."
        ),
        "privacy_level_L3_L4": (
            "Solo portale: esclusi da feed/detail anon. Brand: ammessi."
        ),
        "agency_scope": "Solo brand: filtra per agency_id / slug.",
    }


def portal_photo_filter(property_id: str) -> Dict[str, Any]:
    """ACL foto per superficie ImmobilCloud (D02) — stessa verità del portale."""
    return portal_listing_filter({"id": property_id})


def brand_photo_filter(agency_id: str, property_id: str) -> Dict[str, Any]:
    """ACL foto per superficie brand `/p/{slug}` (D02) — SoT brand, non portal-only."""
    return brand_site_filter(agency_id, {"id": property_id})


# D01 — campi agency ammessi sulle superfici pubbliche ImmobilCloud / brand HTML
AGENCY_PUBLIC_PROJ: Dict[str, int] = {
    "_id": 0,
    "slug": 1,
    "display_name": 1,
    "logo_url": 1,
    "phone": 1,
    "email": 1,
    "city": 1,
    "address": 1,
    "description": 1,
}


def public_agency_card(agency: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Proiezione commerciale agenzia senza identificativi tecnici interni (D01)."""
    if not agency:
        return None
    return {
        "slug": agency.get("slug"),
        "name": agency.get("display_name") or agency.get("name"),
        "display_name": agency.get("display_name") or agency.get("name"),
        "logo_url": agency.get("logo_url"),
        "phone": agency.get("phone"),
        "email": agency.get("email"),
        "city": agency.get("city"),
        "address": agency.get("address"),
        "description": agency.get("description"),
    }


def strip_internal_property_fields(prop: Dict[str, Any]) -> Dict[str, Any]:
    """Rimuove ID interni da payload destinati a HTML/API pubblici (non altera query)."""
    out = dict(prop)
    for k in (
        "agency_id",
        "owner",
        "owner_user_id",
        "seller_client_id",
        "listing_agent_id",
        "commission_pct",
        "lead_count",
        "view_count",
        "contact_public",
        "safety_gate",
        "moderation_reviewed_by",
        "moderation_notes",
        "commercial_customer_id",
    ):
        out.pop(k, None)
    return out
