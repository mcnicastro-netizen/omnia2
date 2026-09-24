"""OMNIA — Property coach «cosa manca» for scheda immobile (A-028d).

Deterministic gaps from compliance HARD/SOFT + actionable field anchors.
No LLM cost until the agent clicks «Migliora con HAL».
"""
from __future__ import annotations

from typing import Any, Dict, List

from shared.validators.compliance import validate_property

# code → (label IT, form field / section to scroll-focus, severity)
_GAP_META = {
    "missing_price": ("Manca il prezzo (o canone)", "price", "hard"),
    "missing_surface": ("Manca la superficie (m²)", "surface_sqm", "hard"),
    "missing_energy_class": ("Manca la classe energetica APE", "energy", "hard"),
    "invalid_energy_class": ("Classe energetica non valida", "energy", "hard"),
    "less_than_3_photos": ("Servono almeno 3 foto per i portali", "photos", "hard"),
    "no_valid_photo_url": ("Nessuna foto con URL valido", "photos", "hard"),
    "missing_address": ("Mancano città e/o provincia", "city", "hard"),
    "title_too_short": ("Titolo troppo corto (min. 10 caratteri)", "title", "soft"),
    "description_too_short": ("Descrizione assente o troppo corta (min. 50 caratteri)", "description", "soft"),
    "rooms_not_specified": ("Numero locali non indicato", "rooms", "soft"),
    "ipe_missing": ("IPE numerico non indicato", "energy", "soft"),
}


def build_coach_report(prop: Dict[str, Any]) -> Dict[str, Any]:
    """Return publish readiness + actionable gaps for the property form."""
    v = validate_property(prop)
    gaps: List[Dict[str, Any]] = []
    for code in v["hard_violations"]:
        label, field, sev = _GAP_META.get(code, (code, None, "hard"))
        gaps.append({
            "code": code,
            "label": label,
            "field": field,
            "severity": sev,
            "hal_action": None,
        })
    for code in v["soft_warnings"]:
        label, field, sev = _GAP_META.get(code, (code, None, "soft"))
        hal = "description" if code == "description_too_short" else (
            "title" if code == "title_too_short" else None
        )
        gaps.append({
            "code": code,
            "label": label,
            "field": field,
            "severity": sev,
            "hal_action": hal,
        })

    n_hard = sum(1 for g in gaps if g["severity"] == "hard")
    n_soft = sum(1 for g in gaps if g["severity"] == "soft")
    if n_hard == 0 and n_soft == 0:
        summary = "Annuncio pronto per i portali — nessun blocco HARD."
    elif n_hard == 0:
        summary = f"Pubblicabile, con {n_soft} miglioramento/i consigliato/i."
    else:
        summary = f"{n_hard} blocco/i HARD da risolvere prima dei portali."

    return {
        "property_id": prop.get("id"),
        "publishable": v["publishable"],
        "summary": summary,
        "gaps": gaps,
        "hard_count": n_hard,
        "soft_count": n_soft,
        "hint": (
            "HAL può riscrivere titolo e descrizione dai dati già compilati. "
            "Foto, prezzo e APE restano a carico dell'agente."
        ),
    }
