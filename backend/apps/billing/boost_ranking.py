"""Ranking boost portale — modello allineato a Idealista / Immobiliare.it.

Regole (D-127):
1. Tier: TOP > Premium > Vetrina > organico (boost_rank).
2. A parità di tier: rotazione equa (`boost_last_shown_at` ASC) — chi è
   apparso meno di recente sale (anti-gaming su `updated_at`).
3. Poi il sort utente (recente / prezzo / superficie).
4. Vale per **tutti** i sort, non solo `recent`.
5. Impressioni lista: incrementano contatore e aggiornano last_shown.

Riferimento: Imm.it (TOP sopra Premium; a parità qualità/data) · Idealista
(Top/Premium in cima listato; Subidón = rotazione temporale).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger("omnia.boost_ranking")

# Quota soft in cima pagina: max frazione di risultati boostati per pagina
# (resto riempito da organico nello stesso ordinamento globale via sort secondario).
# Con sort globale tier-first l'organico segue comunque i boost; la quota è
# documentata per evoluzioni a interleaving. Oggi usiamo sort globale Imm-like.
FEATURED_SHARE = 0.5

USER_SORT_FIELDS: Dict[str, Dict[str, int]] = {
    "recent": {"updated_at": -1},
    "price_asc": {"price": 1, "rent_monthly": 1},
    "price_desc": {"price": -1, "rent_monthly": -1},
    "surface_desc": {"surface_sqm": -1},
}


def boost_add_fields_stage(now_iso: str) -> Dict[str, Any]:
    """Campi calcolati per ranking boost + rotazione."""
    return {
        "$addFields": {
            "_eff_boost": {
                "$cond": [
                    {"$and": [
                        {"$gt": [{"$ifNull": ["$boost_until", ""]}, now_iso]},
                        {"$gt": [{"$ifNull": ["$boost_rank", 0]}, 0]},
                    ]},
                    "$boost_rank",
                    0,
                ]
            },
            # Mai mostrato → stringa vuota → sale prima nella rotazione ASC
            "_boost_rotate": {
                "$cond": [
                    {"$gt": [{"$ifNull": ["$boost_until", ""]}, now_iso]},
                    {"$ifNull": ["$boost_last_shown_at", ""]},
                    "\uffff",  # organico: dopo tutti i boostati in tie-break rotate
                ]
            },
        }
    }


def boost_sort_stage(sort: str) -> Dict[str, Any]:
    """Sort: tier → rotazione equa → criterio utente."""
    user = dict(USER_SORT_FIELDS.get(sort) or USER_SORT_FIELDS["recent"])
    # Mongo sort: chiavi in ordine di priorità
    sort_doc: Dict[str, int] = {
        "_eff_boost": -1,
        "_boost_rotate": 1,
    }
    sort_doc.update(user)
    # Tie-break stabile
    if "updated_at" not in sort_doc:
        sort_doc["updated_at"] = -1
    sort_doc["id"] = 1
    return {"$sort": sort_doc}


def build_boosted_search_pipeline(
    flt: Dict[str, Any],
    *,
    sort: str,
    skip: int,
    limit: int,
    project_fields: Dict[str, Any],
    now_iso: Optional[str] = None,
) -> List[Dict[str, Any]]:
    now_iso = now_iso or datetime.now(timezone.utc).isoformat()
    proj = {**{k: v for k, v in project_fields.items() if k != "_id"}, "_id": 0}
    return [
        {"$match": flt},
        boost_add_fields_stage(now_iso),
        boost_sort_stage(sort),
        {"$skip": skip},
        {"$limit": limit},
        {"$project": proj},
    ]


async def record_boost_impressions(property_ids: Sequence[str]) -> int:
    """Segna impressioni lista per annunci con boost attivo (fire-and-forget ok)."""
    ids = [pid for pid in property_ids if pid]
    if not ids:
        return 0
    try:
        from shared.db.connection import Database
        db = Database.get()
        now_iso = datetime.now(timezone.utc).isoformat()
        r = await db.properties.update_many(
            {
                "id": {"$in": list(ids)},
                "boost_until": {"$gt": now_iso},
                "boost_rank": {"$gt": 0},
            },
            {
                "$inc": {"boost_impression_count": 1},
                "$set": {"boost_last_shown_at": now_iso},
            },
        )
        return int(r.modified_count or 0)
    except Exception as e:  # noqa: BLE001
        logger.warning("boost impression record failed: %s", e)
        return 0


def schedule_boost_impressions(property_ids: Sequence[str]) -> None:
    """Non blocca la response di search."""
    ids = list(property_ids)
    if not ids:
        return
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(record_boost_impressions(ids))
    except RuntimeError:
        pass


def apply_boost_rotation_reset_fields(paid_at: datetime) -> Dict[str, Any]:
    """Nuovo acquisto: riparte in coda rotazione (mai mostrato) con contatore fresco."""
    return {
        "boost_last_shown_at": None,
        "boost_impression_count": 0,
        "boost_activated_at": paid_at.isoformat(),
    }
