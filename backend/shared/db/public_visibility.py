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

from typing import Any, Dict, Optional

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
