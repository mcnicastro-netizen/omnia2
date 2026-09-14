"""OMNIA — Pro valuation coefficients (UNI 10750 / DPR 138/1998 + merito + regionali).

Used by `valuator.py` to compute professional-grade property valuations
that match the structure of bank appraisals (perizia bancaria).

Sources:
- UNI 10750:1998 — Criteri per la determinazione della superficie commerciale
- DPR 138/1998 — Regolamento per la revisione delle zone censuarie
- ABI/Borsino/OMI cross-references for regional coefficients
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

# ============================================================
# 1. SUPERFICIE COMMERCIALE PONDERATA (UNI 10750)
# ============================================================
# Maps each surface component to its weight when computing
# the commercial surface used as the multiplier for €/m² OMI.

SURFACE_WEIGHTS = {
    "principale_mq":          1.00,   # vani abitabili
    "veranda_mq":             0.60,   # vani semicoperti
    "terrazzo_mq":            0.30,   # scoperti fino 25 mq (oltre: pesi diversi, vedi sotto)
    "balcone_mq":             0.30,
    "cantina_mq":             0.25,   # non abitabile
    "soffitta_mq":            0.25,
    "box_auto_mq":            0.50,   # box / posto auto coperto
    "posto_auto_scoperto_mq": 0.20,
    "giardino_villa_mq":      0.10,   # esclusivo villa, fino 25 mq
    "giardino_condom_mq":     0.00,   # condominiale → no peso
    "taverna_mq":             0.60,   # vano interrato abitabile
    "mansarda_abitabile_mq":  0.80,   # con h media ≥ 2,40
}

# Soglie progressive UNI 10750 per terrazzi/balconi/giardini
PROGRESSIVE_THRESHOLDS = {
    "terrazzo_mq": [(25, 0.30), (10_000, 0.10)],
    "balcone_mq":  [(25, 0.30), (10_000, 0.10)],
    "giardino_villa_mq": [(25, 0.10), (200, 0.05), (10_000, 0.02)],
}


def compute_commercial_surface(surfaces: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """Return (total_commercial_mq, breakdown_per_component)."""
    breakdown: Dict[str, float] = {}
    total = 0.0
    for key, raw in surfaces.items():
        if not raw or raw <= 0:
            continue
        if key in PROGRESSIVE_THRESHOLDS:
            # Progressive bands
            remaining = float(raw)
            weighted = 0.0
            prev = 0.0
            for threshold, weight in PROGRESSIVE_THRESHOLDS[key]:
                band = min(remaining, threshold - prev)
                if band <= 0:
                    break
                weighted += band * weight
                remaining -= band
                prev = threshold
                if remaining <= 0:
                    break
            breakdown[key] = round(weighted, 2)
            total += weighted
        else:
            w = SURFACE_WEIGHTS.get(key, 0.0)
            if w == 0.0:
                continue
            v = round(raw * w, 2)
            breakdown[key] = v
            total += v
    return round(total, 2), breakdown


# ============================================================
# 2. COEFFICIENTI DI MERITO (UNI 10750)
# ============================================================
# Applied as a single multiplicative adjustment to the base €/m².

# Piano
FLOOR_ADJUST = {
    "seminterrato":  -0.15,
    "piano_terra":   -0.08,
    "piano_1":       -0.02,
    "piano_intermedio": 0.0,
    "ultimo_no_asc": -0.05,    # ultimo piano senza ascensore
    "ultimo_con_asc": 0.04,    # ultimo piano con ascensore
    "attico_panoramico": 0.10, # plus se panoramico
}

# Esposizione
EXPOSURE_ADJUST = {
    "sud":            0.05,
    "sud_est":        0.04,
    "sud_ovest":      0.04,
    "est":            0.02,
    "ovest":          0.01,
    "nord_est":      -0.02,
    "nord_ovest":    -0.02,
    "nord":          -0.04,
    "cieca":         -0.07,
    "doppia_esp":     0.03,   # doppia esposizione: bonus aggiuntivo
}

# Affaccio
VIEW_ADJUST = {
    "interno":       -0.04,
    "cortile":       -0.03,
    "strada":         0.00,
    "verde":          0.04,
    "panoramico":     0.08,
    "mare":           0.12,
    "lago_montagna":  0.10,
}

# Riscaldamento
HEATING_ADJUST = {
    "autonomo":       0.03,
    "centralizzato": -0.02,
    "pompa_calore":   0.04,
    "assente":       -0.08,
}

# Asensore
ELEVATOR_ADJUST = {
    "presente":       0.0,    # baseline
    "presente_piano_alto":  0.03,   # piano >= 4 e ascensore
    "assente_piano_basso":  0.0,    # piano <= 2 e no ascensore: irrilevante
    "assente_piano_alto":  -0.10,   # piano >= 3 e no ascensore: forte penalità
}

# Vincoli / situazioni particolari
SPECIAL_ADJUST = {
    "vincolo_storico":   -0.10,   # tutela art. 10 D.Lgs. 42/2004
    "vincolo_paesag":    -0.05,
    "locazione_libera_breve":  -0.05,  # contratto in essere ma a scadenza breve
    "locazione_lunga":   -0.15,         # contratto in essere lungo termine
    "nuda_proprieta":    -0.30,         # variabile, semplificato
}

# Età immobile (deprezzamento)
def age_adjustment(year_built: Optional[int], current_year: int = 2026) -> float:
    """Half a percent per year over 30, capped at -20%."""
    if not year_built:
        return 0.0
    age = current_year - year_built
    if age <= 30:
        return 0.0
    excess = age - 30
    return max(-0.20, -0.005 * excess)


def compute_merit_adjustment(merit: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """Return (cumulative_pct, breakdown). Capped at [-0.40, +0.30]."""
    breakdown: Dict[str, float] = {}
    total = 0.0

    if (k := merit.get("floor_class")) in FLOOR_ADJUST:
        breakdown["floor"] = FLOOR_ADJUST[k]
        total += FLOOR_ADJUST[k]

    if (k := merit.get("exposure")) in EXPOSURE_ADJUST:
        breakdown["exposure"] = EXPOSURE_ADJUST[k]
        total += EXPOSURE_ADJUST[k]

    if (k := merit.get("view")) in VIEW_ADJUST:
        breakdown["view"] = VIEW_ADJUST[k]
        total += VIEW_ADJUST[k]

    if (k := merit.get("heating")) in HEATING_ADJUST:
        breakdown["heating"] = HEATING_ADJUST[k]
        total += HEATING_ADJUST[k]

    if (k := merit.get("elevator")) in ELEVATOR_ADJUST:
        breakdown["elevator"] = ELEVATOR_ADJUST[k]
        total += ELEVATOR_ADJUST[k]

    # Special
    for special_key in ("vincolo_storico", "vincolo_paesag", "locazione_libera_breve", "locazione_lunga", "nuda_proprieta"):
        if merit.get(special_key):
            breakdown[special_key] = SPECIAL_ADJUST[special_key]
            total += SPECIAL_ADJUST[special_key]

    # Età
    age_adj = age_adjustment(merit.get("year_built"))
    if age_adj != 0:
        breakdown["age"] = age_adj
        total += age_adj

    # Cap
    capped = max(-0.40, min(0.30, total))
    return capped, breakdown


# ============================================================
# 3. COEFFICIENTI REGIONALI (liquidità + trend semestrale)
# ============================================================
# Liquidità di mercato (time-to-sell) → discount factor sulla stima
# Trend semestrale → adjustment a chi compra "oggi" rispetto al dato OMI

REGIONAL_LIQUIDITY = {
    # Region: (avg time-to-sell months, liquidity_factor)
    # liquidity_factor < 0 = mercato lento → prezzi reali più bassi della media OMI
    "lombardia":              ( 3, 0.00),
    "lazio":                  ( 4, 0.00),
    "emilia_romagna":         ( 4, 0.00),
    "veneto":                 ( 5, -0.01),
    "piemonte":               ( 6, -0.02),
    "toscana":                ( 5, -0.01),
    "liguria":                ( 5, -0.01),
    "trentino_alto_adige":    ( 4, 0.00),
    "friuli_venezia_giulia":  ( 7, -0.03),
    "marche":                 ( 7, -0.03),
    "umbria":                 ( 8, -0.04),
    "abruzzo":                ( 8, -0.04),
    "campania":               ( 7, -0.03),
    "puglia":                 ( 8, -0.04),
    "sicilia":                (10, -0.06),
    "sardegna":               ( 9, -0.05),
    "calabria":               (12, -0.08),
    "basilicata":             (11, -0.07),
    "molise":                 (11, -0.07),
    "valle_d_aosta":          ( 6, -0.02),
}

# Trend prezzi annuo (2024→2025), source ABI/Idealista/OMI cross
REGIONAL_TREND_YOY = {
    "lombardia":              0.025,
    "lazio":                  0.018,
    "emilia_romagna":         0.020,
    "veneto":                 0.015,
    "piemonte":               0.008,
    "toscana":                0.022,
    "liguria":                0.012,
    "trentino_alto_adige":    0.028,
    "friuli_venezia_giulia":  0.005,
    "marche":                 0.005,
    "umbria":                -0.002,
    "abruzzo":                0.003,
    "campania":               0.012,
    "puglia":                 0.010,
    "sicilia":               -0.005,
    "sardegna":               0.008,
    "calabria":              -0.010,
    "basilicata":            -0.005,
    "molise":                -0.008,
    "valle_d_aosta":          0.010,
}


def compute_regional_adjustment(region: Optional[str], months_since_omi: int = 6) -> Tuple[float, Dict[str, float]]:
    """Return (cumulative_pct, breakdown).

    months_since_omi: months elapsed since the OMI snapshot date used in base prices.
    """
    if not region or region not in REGIONAL_LIQUIDITY:
        return 0.0, {}

    liquidity = REGIONAL_LIQUIDITY[region][1]
    yoy = REGIONAL_TREND_YOY.get(region, 0.0)
    trend = yoy * (months_since_omi / 12.0)

    breakdown = {"liquidity": liquidity, "trend_inflation": round(trend, 4)}
    return round(liquidity + trend, 4), breakdown


# ============================================================
# 4. FOI ISTAT (rivalutazione)
# ============================================================
# Coefficiente FOI cumulato per rivalutare prezzi storici a oggi.
# Aggiornato manualmente ogni semestre (procedura semplice 2h).

FOI_ANNUAL_INDEX = {
    2020: 1.000,
    2021: 1.019,   # +1.9%
    2022: 1.103,   # +8.1% (post-crisi energetica)
    2023: 1.157,   # +4.9%
    2024: 1.171,   # +1.2%
    2025: 1.187,   # +1.4% (stima)
    2026: 1.205,   # +1.5% (stima)
}

def foi_revaluation(from_year: int, to_year: int = 2026) -> float:
    """Multiplier to revalue a price from `from_year` to `to_year`."""
    if from_year not in FOI_ANNUAL_INDEX or to_year not in FOI_ANNUAL_INDEX:
        return 1.0
    return FOI_ANNUAL_INDEX[to_year] / FOI_ANNUAL_INDEX[from_year]
