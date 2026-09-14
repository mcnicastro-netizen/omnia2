"""OMNIA — Matching algorithm: Property ↔ Client (M2.S4 D-025 Layer 1).

Deterministic 0-100 score based on idealista-style search preferences.
Hard incompatibilities (operation mismatch, budget completely out of range) → score 0.
"""
from typing import Any, Dict, List, Optional, Tuple


# Weights — total = 100 (exact); tuned for Italian real-estate market signals.
W = {
    "operation": 14,       # mandatory match
    "property_type": 11,
    "city": 12,
    "zone": 5,
    "price": 17,
    "surface": 7,
    "rooms": 5,
    "bedrooms": 4,
    "bathrooms": 4,
    "conditions": 4,
    "floor": 3,
    "energy": 4,
    "features": 6,
    "multimedia": 4,
}
# Sanity: assert sum(W.values()) == 100  (14+11+12+5+17+7+5+4+4+4+3+4+6+4 = 100)

# Energy class ranking (best to worst). Used for "min class" check.
ENERGY_ORDER = ["A4", "A3", "A2", "A1", "A", "B", "C", "D", "E", "F", "G"]


def _norm_str(s: Optional[str]) -> str:
    return (s or "").strip().lower()


def _energy_idx(cls: Optional[str]) -> Optional[int]:
    """Return rank in ENERGY_ORDER (lower = better). None if unknown."""
    if not cls:
        return None
    up = cls.strip().upper()
    if up in ENERGY_ORDER:
        return ENERGY_ORDER.index(up)
    # tolerate single-letter classes like A4 expressed as 'A4'
    return None


def _in_or_empty(value: Optional[str], allowed: List[str]) -> bool:
    """If `allowed` is empty list/None → True (no constraint). Otherwise value must be in it (case-insensitive)."""
    if not allowed:
        return True
    v = _norm_str(value)
    return v != "" and v in [_norm_str(a) for a in allowed]


def _intersect(values: List[str], allowed: List[str]) -> bool:
    if not allowed:
        return True
    if not values:
        return False
    norm_v = {_norm_str(v) for v in values}
    return any(_norm_str(a) in norm_v for a in allowed)


def _floor_bucket(floor: Optional[Any]) -> Optional[str]:
    """Map numeric floor to bucket. None if unknown."""
    if floor is None or floor == "":
        return None
    try:
        f = int(str(floor))
    except (TypeError, ValueError):
        s = str(floor).lower()
        if "terra" in s or s in ("0", "t", "pt"):
            return "terra"
        if "ultim" in s:
            return "ultimo"
        return None
    return "terra" if f <= 0 else "intermedi"  # 'ultimo' needs total_floors comparison done outside


def _floor_is_top(floor: Optional[Any], total: Optional[Any]) -> bool:
    try:
        return int(str(floor)) == int(str(total)) and int(str(total)) > 0
    except (TypeError, ValueError):
        return False


def compute_match(prop: Dict[str, Any], client: Dict[str, Any]) -> Dict[str, Any]:
    """Compute deterministic match score Property ↔ Client.

    Returns:
        {
          "score": int 0-100,
          "is_compatible": bool,
          "breakdown": {criterion: {got: int, max: int}},
          "missing": list[str],   # human-readable mismatches
        }
    """
    prefs = (client.get("preferences") or {}) if isinstance(client, dict) else {}
    breakdown: Dict[str, Dict[str, int]] = {}
    missing: List[str] = []

    def award(key: str, got: float):
        breakdown[key] = {"got": round(got), "max": W[key]}

    # --- Hard: Operation ---
    op_pref = prefs.get("operation")
    op_prop = prop.get("operation")
    if op_pref and op_pref != op_prop:
        # Hard incompatibility: client wants 'sale' but property is 'rent'
        for k in W:
            breakdown[k] = {"got": 0, "max": W[k]}
        missing.append(f"operation:{op_pref}!={op_prop}")
        return {"score": 0, "is_compatible": False, "breakdown": breakdown, "missing": missing}
    award("operation", W["operation"])

    # --- Property type ---
    if _in_or_empty(prop.get("property_type"), prefs.get("property_types") or []):
        award("property_type", W["property_type"])
    else:
        award("property_type", 0)
        missing.append("property_type")

    # --- City (case-insensitive) ---
    if _in_or_empty(prop.get("city"), prefs.get("cities") or []):
        award("city", W["city"])
    else:
        award("city", 0)
        missing.append("city")

    # --- Zone (case-insensitive) ---
    z_allowed = prefs.get("zones") or []
    if not z_allowed:
        award("zone", W["zone"])  # no constraint → full
    elif _in_or_empty(prop.get("zone"), z_allowed):
        award("zone", W["zone"])
    else:
        award("zone", 0)
        missing.append("zone")

    # --- Price range (with soft tolerance ±10%) ---
    price_field = "rent_monthly" if op_prop == "rent" else "price"
    pv = prop.get(price_field)
    pmin = prefs.get("price_min")
    pmax = prefs.get("price_max")
    score_price = 0.0
    if pv is None:
        score_price = W["price"] * 0.5  # uncertain → partial credit
    else:
        # Bounds with 10% tolerance for soft scoring
        lo = float(pmin) if pmin not in (None, "") else None
        hi = float(pmax) if pmax not in (None, "") else None
        if lo is not None and float(pv) < lo:
            # under budget = bonus capped at full
            score_price = W["price"]
        elif hi is not None and float(pv) > hi:
            # over budget → linear penalty
            overshoot = (float(pv) - hi) / max(hi, 1.0)
            if overshoot <= 0.10:
                score_price = W["price"] * (1.0 - overshoot * 5)  # -50% at +10%
            elif overshoot <= 0.30:
                score_price = W["price"] * 0.25
            else:
                score_price = 0
                missing.append("price_over_budget")
        else:
            score_price = W["price"]
    award("price", score_price)

    # --- Surface range ---
    sv = prop.get("surface_sqm")
    smin = prefs.get("surface_min")
    smax = prefs.get("surface_max")
    score_surf = 0.0
    if sv is None:
        score_surf = W["surface"] * 0.5
    else:
        lo = float(smin) if smin not in (None, "") else None
        hi = float(smax) if smax not in (None, "") else None
        if (lo is not None and float(sv) < lo) or (hi is not None and float(sv) > hi):
            score_surf = W["surface"] * 0.4
            missing.append("surface")
        else:
            score_surf = W["surface"]
    award("surface", score_surf)

    # --- Rooms min/max ---
    rv = prop.get("rooms")
    rmin = prefs.get("rooms_min")
    rmax = prefs.get("rooms_max")
    score_r = 0.0
    if rv is None:
        score_r = W["rooms"] * 0.5
    else:
        ok_min = rmin in (None, "") or int(rv) >= int(rmin)
        ok_max = rmax in (None, "") or int(rv) <= int(rmax)
        if ok_min and ok_max:
            score_r = W["rooms"]
        else:
            score_r = 0
            missing.append("rooms")
    award("rooms", score_r)

    # --- Bedrooms min ---
    bv = prop.get("bedrooms")
    bmin = prefs.get("bedrooms_min")
    score_b = 0.0
    if bv is None or bmin in (None, ""):
        score_b = W["bedrooms"]
    elif int(bv) >= int(bmin):
        score_b = W["bedrooms"]
    else:
        missing.append("bedrooms")
    award("bedrooms", score_b)

    # --- Bathrooms min ---
    bav = prop.get("bathrooms")
    bamin = prefs.get("bathrooms_min")
    score_ba = 0.0
    if bav is None or bamin in (None, ""):
        score_ba = W["bathrooms"]
    elif int(bav) >= int(bamin):
        score_ba = W["bathrooms"]
    else:
        missing.append("bathrooms")
    award("bathrooms", score_ba)

    # --- Conditions list (allowed) ---
    c_allowed = prefs.get("conditions") or []
    if not c_allowed or _in_or_empty(prop.get("condition"), c_allowed):
        award("conditions", W["conditions"])
    else:
        award("conditions", 0)
        missing.append("condition")

    # --- Floor preference ---
    f_allowed = prefs.get("floor_preferences") or []
    if not f_allowed:
        award("floor", W["floor"])
    else:
        bucket = _floor_bucket(prop.get("floor"))
        if _floor_is_top(prop.get("floor"), prop.get("total_floors")):
            bucket = "ultimo"
        if bucket and bucket in [_norm_str(x) for x in f_allowed]:
            award("floor", W["floor"])
        else:
            award("floor", 0)
            missing.append("floor")

    # --- Energy min class ---
    energy_block = prop.get("energy") or {}
    cls = energy_block.get("energy_class") if isinstance(energy_block, dict) else None
    needed = prefs.get("energy_min_class")
    if not needed:
        award("energy", W["energy"])
    else:
        p_idx = _energy_idx(cls)
        n_idx = _energy_idx(needed)
        if p_idx is None or n_idx is None:
            award("energy", W["energy"] * 0.5)
        elif p_idx <= n_idx:  # better or equal
            award("energy", W["energy"])
        else:
            award("energy", 0)
            missing.append(f"energy<{needed}")

    # --- Must-have features ---
    needed_feats: List[str] = prefs.get("must_have_features") or []
    if not needed_feats:
        award("features", W["features"])
    else:
        p_feats = prop.get("features") or {}
        # features stored as dict {key: bool} OR list[str]
        if isinstance(p_feats, dict):
            have = {k for k, v in p_feats.items() if v}
        elif isinstance(p_feats, list):
            have = set(p_feats)
        else:
            have = set()
        matched = sum(1 for f in needed_feats if f in have)
        ratio = matched / len(needed_feats)
        award("features", W["features"] * ratio)
        if ratio < 1.0:
            missing.append(f"features:{len(needed_feats) - matched}_missing")

    # --- Multimedia requirements ---
    photos = prop.get("photos") or []
    has_photos = len(photos) > 0
    vtour = prop.get("virtual_tour_url")
    mm = W["multimedia"]
    score_mm = mm
    if prefs.get("needs_photos") and not has_photos:
        score_mm -= mm * 0.6
        missing.append("photos_required")
    if prefs.get("needs_virtual_tour") and not vtour:
        score_mm -= mm * 0.6
        missing.append("vtour_required")
    award("multimedia", max(score_mm, 0))

    total = sum(b["got"] for b in breakdown.values())
    return {
        "score": int(round(total)),
        "is_compatible": True,
        "breakdown": breakdown,
        "missing": missing,
    }


def is_searcher(client: Dict[str, Any]) -> bool:
    """Only buyer/tenant/investor clients actively search; sellers/landlords don't."""
    ct = (client.get("client_type") or "").lower()
    return ct in ("buyer", "tenant", "investor")
