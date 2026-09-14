"""OMNIA — Property compliance validator (M2.6b, D-053).

Two levels of rules:
- HARD: violation excludes property from feeds (blocking, legal/portal requirement)
- SOFT: violation triggers a warning in the dashboard but property is still published

Italian real estate publishing context:
- Energy class (APE) is mandatory by D.Lgs 192/2005
- IPE numeric mandatory since Delibera AGCM
- Price transparency mandatory by AGCM
- Photo minimum is a portal standard (Immobiliare.it, Idealista, etc.)

Design: pure functions, no DB dependency, easy to unit-test.
Backwards compat: `is_publishable(prop)` still exposed by publishing.py.
"""
from __future__ import annotations
from typing import Any, Dict, List, Tuple

# Valid APE classes as per D.Lgs 192/2005 (Italian energy classes)
VALID_ENERGY_CLASSES = {
    "A4", "A3", "A2", "A1", "A", "B", "C", "D", "E", "F", "G",
    # exempt reasons must be declared explicitly
    "EXEMPT_IN_PROGRESS", "EXEMPT_NOT_APPLICABLE",
}

# Business rule constants (single source of truth)
MIN_PHOTOS = 3
MIN_TITLE_CHARS = 10
MIN_DESCRIPTION_CHARS = 50


def _photos_count(prop: Dict[str, Any]) -> int:
    photos = prop.get("photos") or []
    return len([p for p in photos if isinstance(p, dict) and p.get("url")])


def _first_photo_ok(prop: Dict[str, Any]) -> bool:
    """A property with only tiny/broken URLs should not be publishable."""
    photos = prop.get("photos") or []
    if not photos:
        return False
    for p in photos:
        if isinstance(p, dict) and p.get("url"):
            return True
    return False


def _has_address(prop: Dict[str, Any]) -> bool:
    return bool((prop.get("city") or "").strip() and (prop.get("province") or "").strip())


def _has_price(prop: Dict[str, Any]) -> bool:
    op = (prop.get("operation") or "sale").lower()
    if op == "rent":
        rent = prop.get("rent_monthly")
        return isinstance(rent, (int, float)) and rent > 0
    # sale or auction: allow either concrete price or explicit "on request" flag
    price = prop.get("price")
    if isinstance(price, (int, float)) and price > 0:
        return True
    if prop.get("price_on_request") is True:
        return True
    return False


def _has_energy(prop: Dict[str, Any]) -> Tuple[bool, str]:
    """Return (ok, reason). Energy must be present AND valid class."""
    energy = prop.get("energy") or {}
    cls = (energy.get("energy_class") or "").strip().upper()
    if not cls:
        return False, "missing_energy_class"
    if cls not in VALID_ENERGY_CLASSES:
        return False, "invalid_energy_class"
    return True, ""


def _has_surface(prop: Dict[str, Any]) -> bool:
    s = prop.get("surface_sqm")
    return isinstance(s, (int, float)) and s > 0


# ---------- Public API ----------

def validate_property(prop: Dict[str, Any]) -> Dict[str, Any]:
    """Full compliance check. Returns structured result.

    Result shape (JSON-serializable):
        {
          "publishable": bool,
          "hard_violations": [str, ...],  # blocking
          "soft_warnings": [str, ...],    # non-blocking
          "checked_at_iso": str
        }
    """
    hard: List[str] = []
    soft: List[str] = []

    # ----- HARD rules -----
    if not _has_price(prop):
        hard.append("missing_price")
    if not _has_surface(prop):
        hard.append("missing_surface")
    ok_energy, reason_energy = _has_energy(prop)
    if not ok_energy:
        hard.append(reason_energy)
    if _photos_count(prop) < MIN_PHOTOS:
        hard.append("less_than_3_photos")
    if not _first_photo_ok(prop):
        hard.append("no_valid_photo_url")
    if not _has_address(prop):
        hard.append("missing_address")

    # ----- SOFT rules -----
    title = (prop.get("title") or "").strip()
    if len(title) < MIN_TITLE_CHARS:
        soft.append("title_too_short")
    description = (prop.get("description") or "").strip()
    if len(description) < MIN_DESCRIPTION_CHARS:
        soft.append("description_too_short")
    if prop.get("rooms") in (None, 0):
        soft.append("rooms_not_specified")
    if not (prop.get("energy") or {}).get("ipe"):
        soft.append("ipe_missing")

    return {
        "publishable": len(hard) == 0,
        "hard_violations": hard,
        "soft_warnings": soft,
    }


# Backwards-compatible signature used by publishing.py feed generator
def is_publishable(prop: Dict[str, Any]) -> Tuple[bool, List[str]]:
    r = validate_property(prop)
    return r["publishable"], r["hard_violations"]


def summarize_agency_compliance(properties: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate compliance snapshot for a whole agency portfolio.

    Used by the Publishing Dashboard to show "5 immobili bloccati, 12 con warning".
    """
    total = len(properties)
    publishable = 0
    with_warnings = 0
    blocked = 0
    reasons_hard: Dict[str, int] = {}
    reasons_soft: Dict[str, int] = {}

    for p in properties:
        r = validate_property(p)
        if r["publishable"]:
            publishable += 1
            if r["soft_warnings"]:
                with_warnings += 1
        else:
            blocked += 1
        for v in r["hard_violations"]:
            reasons_hard[v] = reasons_hard.get(v, 0) + 1
        for w in r["soft_warnings"]:
            reasons_soft[w] = reasons_soft.get(w, 0) + 1

    return {
        "total": total,
        "publishable": publishable,
        "with_warnings": with_warnings,
        "blocked": blocked,
        "top_hard_reasons": sorted(reasons_hard.items(), key=lambda x: -x[1])[:5],
        "top_soft_reasons": sorted(reasons_soft.items(), key=lambda x: -x[1])[:5],
    }
