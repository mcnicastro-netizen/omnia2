"""OMNIA — Privacy Gate (M3.S9, Sprint 3 · Item #1).

Centralizza la logica di visibilità dei campi Property in base al livello di
autorizzazione del viewer, come da D-062.

Livelli:
    L1 · anonimo pubblico       - default per property.privacy_level=L1
    L2 · B2C authenticated      - default per la maggior parte delle listings
    L3 · qualified (lead+GDPR)  - user ha lasciato un lead e ha confermato email
    L4 · agency internal        - agent proprietario, agency_admin, super_admin

Regole (matrice):
                        L1 anon  L2 auth  L3 qualif  L4 agency
    title, desc          ✓       ✓         ✓          ✓
    photos               ✓ (blur ✓         ✓          ✓
                          exif)
    city, zone (quartiere) ✓     ✓         ✓          ✓
    price / rent         ✓ approx ✓ exact  ✓ exact    ✓ exact
    surface, rooms       ✓       ✓         ✓          ✓
    address esatto       ✗       ✗         ✓          ✓
    postal_code, floor   ✗       ✓ postal  ✓          ✓
    coordinate lat/lng   ✗ approx ✗ approx ✓ exact    ✓ exact
    planimetria          ✗       ✗         ✓          ✓
    virtual_tour_url     ✗       ✓         ✓          ✓
    owner (nome, tel)    ✗       ✗         ✗          ✓
    seller_client_id     ✗       ✗         ✗          ✓
    min_price_negoziable ✗       ✗         ✗          ✓
    seller_notes         ✗       ✗         ✗          ✓
    commission_pct       ✗       ✗         ✗          ✓
    reference_code       ✗       ✗         ✓          ✓
    view_count internal  ✗       ✗         ✗          ✓
    energy full          ✓ class ✓ class   ✓ full     ✓ full
                          only    only

Il campo property.privacy_level RESTRINGE ulteriormente: un immobile con
privacy_level="L3" non è mai visibile ad anonimi anche se viewer è "L1".
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional
from uuid import uuid4

ViewerLevel = str  # "L1" | "L2" | "L3" | "L4"

# Numeric ranking for easy comparisons.
_RANK: Dict[str, int] = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}


def resolve_viewer_level(user: Optional[dict], agency_id_of_property: Optional[str],
                         qualified: bool = False) -> ViewerLevel:
    """Determine the viewer's effective level for a given property."""
    if not user:
        return "L3" if qualified else "L1"
    role = user.get("role")
    # Agency internal (agent+, of the OWNING agency, or super_admin)
    if role == "super_admin":
        return "L4"
    if role in ("agency_admin", "branch_admin", "group_admin", "agent"):
        user_agencies = set(user.get("agency_ids") or [])
        if agency_id_of_property and agency_id_of_property in user_agencies:
            return "L4"
        # agent di altra agenzia → visto come B2C authenticated
        return "L2"
    # b2c_user or others authenticated
    return "L3" if qualified else "L2"


def can_view_property(viewer_level: ViewerLevel, property_privacy: str) -> bool:
    """Return True if viewer has enough authorization to see the property at all.

    Contract (D-062, docstring "Regole matrice"):
    - privacy=L1 (fully public) and privacy=L2 (portal default) → visible to any
      viewer including anonymous (L1). Field masking is applied downstream by
      `apply_privacy_view`.
    - privacy=L3 → requires viewer L3 (qualified lead) or L4 (agency internal).
    - privacy=L4 → only agency internal (L4).
    """
    prop = (property_privacy or "L2").upper()
    if prop in ("L1", "L2"):
        return True
    return _RANK.get(viewer_level, 0) >= _RANK.get(prop, 2)


def _round_price_bucket(price: float) -> float:
    """Round price to a 10% bucket to hide exact figure to L1 (anonimo)."""
    if price is None or price <= 0:
        return price
    if price < 100_000:
        step = 5_000
    elif price < 500_000:
        step = 10_000
    elif price < 1_000_000:
        step = 25_000
    else:
        step = 50_000
    return round(price / step) * step


def _round_coord(v: Optional[float], decimals: int) -> Optional[float]:
    return round(v, decimals) if v is not None else None


def apply_privacy_view(prop: Dict[str, Any], viewer_level: ViewerLevel) -> Dict[str, Any]:
    """Strip / mask fields from a Property document according to viewer level.

    Never mutates the input. Returns a NEW dict safe to serialize.
    """
    out: Dict[str, Any] = {k: v for k, v in prop.items() if k not in {"_id"}}
    lvl = _RANK.get(viewer_level, 1)

    # ---- L4 (agency internal): return everything ---------------------------
    if lvl >= 4:
        return out

    # ---- always strip these below L4 ---------------------------------------
    for f in ("owner", "seller_client_id", "seller_notes", "min_price_negotiable",
              "commission_pct", "view_count", "listing_agent_id",
              "ingested_via", "ingested_api_key_id", "external_id"):
        out.pop(f, None)
    # Energy details beyond class → only from L3
    # NOTE: model field is `energy_class` (see shared/models/property.py::PropertyEnergy)
    energy = out.get("energy") or {}
    if isinstance(energy, dict) and lvl < 3:
        out["energy"] = {"energy_class": energy.get("energy_class")}

    # ---- L3 (qualified user with confirmed GDPR): full address + planimetry
    if lvl >= 3:
        return out

    # ---- L2 (authenticated B2C) -------------------------------------------
    if lvl >= 2:
        # hide exact address (keep only city + zone)
        out.pop("address", None)
        out.pop("floor_plan_url", None)
        # Coordinates rounded to ~1km (2 decimals ≈ 1.1 km at Italian latitudes)
        out["lat"] = _round_coord(out.get("lat"), 2)
        out["lng"] = _round_coord(out.get("lng"), 2)
        # Reference code hidden
        out.pop("reference_code", None)
        return out

    # ---- L1 (anonymous public) -------------------------------------------
    out.pop("address", None)
    out.pop("floor_plan_url", None)
    out.pop("virtual_tour_url", None)
    out.pop("postal_code", None)
    out.pop("floor", None)
    out.pop("reference_code", None)
    # Coordinates rounded to ~10km (1 decimal)
    out["lat"] = _round_coord(out.get("lat"), 1)
    out["lng"] = _round_coord(out.get("lng"), 1)
    # Prices in 10% buckets so competitor scrapers can't cross-index exactly
    if out.get("price") is not None:
        out["price"] = _round_price_bucket(out["price"])
        out["price_is_approximate"] = True
    if out.get("rent_monthly") is not None:
        out["rent_monthly"] = _round_price_bucket(out["rent_monthly"])
        out["price_is_approximate"] = True
    return out


# ---------------------------------------------------------------------------
# Audit trail (M3.S9 requirement — traceability of privacy_level changes)
# ---------------------------------------------------------------------------

async def log_privacy_change(db, property_id: str, actor_id: str, agency_id: str,
                             old_level: str, new_level: str, reason: Optional[str] = None) -> None:
    """Append-only audit trail for privacy_level changes on a property."""
    await db.privacy_audit_events.insert_one({
        "id": str(uuid4()),
        "property_id": property_id,
        "agency_id": agency_id,
        "actor_id": actor_id,
        "from_level": old_level,
        "to_level": new_level,
        "reason": (reason or "")[:500],
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
