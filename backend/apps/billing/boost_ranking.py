"""Ranking boost portale — modello allineato a Idealista / Immobiliare.it.

Regole (D-127 + densità):
1. Tier: TOP > Premium > Vetrina > organico (boost_rank).
2. A parità di tier: rotazione equa (`boost_last_shown_at` ASC).
3. Poi il sort utente (recente / prezzo / superficie).
4. Vale per **tutti** i sort.
5. Impressioni lista: contatore + last_shown.
6. **Cap densità**: max FEATURED_SHARE dei risultati per pagina sono boostati;
   il resto è organico. Con filtro città i due pool sono già scoped alla città
   (densità locale). Se un pool è scarso, si riempie dall'altro (niente buchi).

Riferimento: Imm.it / Idealista (evidenza in cima) + protezione organico
quando il volume di boost cresce in una città.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("omnia.boost_ranking")

# Max frazione di slot boostati per pagina (resto riservato all'organico).
FEATURED_SHARE = 0.5

USER_SORT_FIELDS: Dict[str, Dict[str, int]] = {
    "recent": {"updated_at": -1},
    "price_asc": {"price": 1, "rent_monthly": 1},
    "price_desc": {"price": -1, "rent_monthly": -1},
    "surface_desc": {"surface_sqm": -1},
}


def featured_slots_for_page(page_size: int, share: float = FEATURED_SHARE) -> int:
    """Quanti posti boostati al massimo in una pagina (almeno 1 se page_size≥1)."""
    if page_size <= 0:
        return 0
    return max(1, int(round(page_size * share)))


def active_boost_match(now_iso: str) -> Dict[str, Any]:
    return {
        "boost_until": {"$gt": now_iso},
        "boost_rank": {"$gt": 0},
    }


def organic_match(now_iso: str) -> Dict[str, Any]:
    """Non ha boost attivo (scaduto / assente / rank 0)."""
    return {
        "$or": [
            {"boost_until": {"$exists": False}},
            {"boost_until": None},
            {"boost_until": {"$lte": now_iso}},
            {"boost_rank": {"$exists": False}},
            {"boost_rank": None},
            {"boost_rank": {"$lte": 0}},
        ]
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
            "_boost_rotate": {
                "$cond": [
                    {"$gt": [{"$ifNull": ["$boost_until", ""]}, now_iso]},
                    {"$ifNull": ["$boost_last_shown_at", ""]},
                    "\uffff",
                ]
            },
        }
    }


def boost_sort_stage(sort: str) -> Dict[str, Any]:
    """Sort: tier → rotazione equa → criterio utente."""
    user = dict(USER_SORT_FIELDS.get(sort) or USER_SORT_FIELDS["recent"])
    sort_doc: Dict[str, int] = {
        "_eff_boost": -1,
        "_boost_rotate": 1,
    }
    sort_doc.update(user)
    if "updated_at" not in sort_doc:
        sort_doc["updated_at"] = -1
    sort_doc["id"] = 1
    return {"$sort": sort_doc}


def user_sort_stage(sort: str) -> Dict[str, Any]:
    user = dict(USER_SORT_FIELDS.get(sort) or USER_SORT_FIELDS["recent"])
    if "updated_at" not in user:
        user["updated_at"] = -1
    user["id"] = 1
    return {"$sort": user}


def build_boosted_search_pipeline(
    flt: Dict[str, Any],
    *,
    sort: str,
    skip: int,
    limit: int,
    project_fields: Dict[str, Any],
    now_iso: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Pipeline unica (legacy / fallback senza split densità)."""
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


def _pipeline(
    flt: Dict[str, Any],
    *,
    sort_stage: Dict[str, Any],
    skip: int,
    limit: int,
    project_fields: Dict[str, Any],
    now_iso: str,
    with_boost_fields: bool,
) -> List[Dict[str, Any]]:
    proj = {**{k: v for k, v in project_fields.items() if k != "_id"}, "_id": 0}
    stages: List[Dict[str, Any]] = [{"$match": flt}]
    if with_boost_fields:
        stages.append(boost_add_fields_stage(now_iso))
    stages.append(sort_stage)
    stages.append({"$skip": max(0, skip)})
    stages.append({"$limit": max(0, limit)})
    stages.append({"$project": proj})
    return stages


async def fetch_search_page_with_density_cap(
    db,
    flt: Dict[str, Any],
    *,
    sort: str = "recent",
    page: int = 1,
    page_size: int = 20,
    project_fields: Dict[str, Any],
    featured_share: float = FEATURED_SHARE,
    now_iso: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Pagina search con cap densità boost.

    Se `flt` include già `city` (o regex città), i pool boost/organico sono
    naturalmente scoped a quella città → densità locale.
    """
    now_iso = now_iso or datetime.now(timezone.utc).isoformat()
    page = max(1, int(page))
    page_size = max(1, int(page_size))
    featured_n = featured_slots_for_page(page_size, featured_share)
    organic_n = max(0, page_size - featured_n)

    boost_flt: Dict[str, Any] = {"$and": [flt, active_boost_match(now_iso)]}
    org_flt: Dict[str, Any] = {"$and": [flt, organic_match(now_iso)]}

    feat_skip = (page - 1) * featured_n
    org_skip = (page - 1) * organic_n

    boosted = await db.properties.aggregate(
        _pipeline(
            boost_flt,
            sort_stage=boost_sort_stage(sort),
            skip=feat_skip,
            limit=featured_n,
            project_fields=project_fields,
            now_iso=now_iso,
            with_boost_fields=True,
        )
    ).to_list(length=featured_n)

    organic = await db.properties.aggregate(
        _pipeline(
            org_flt,
            sort_stage=user_sort_stage(sort),
            skip=org_skip,
            limit=organic_n,
            project_fields=project_fields,
            now_iso=now_iso,
            with_boost_fields=False,
        )
    ).to_list(length=organic_n)

    merged: List[Dict[str, Any]] = list(boosted) + list(organic)
    seen = {p.get("id") for p in merged if p.get("id")}

    # Riempi buchi: prima altro organico, poi altro boost (oltre il cap)
    if len(merged) < page_size:
        need = page_size - len(merged)
        more_org = await db.properties.aggregate(
            _pipeline(
                org_flt,
                sort_stage=user_sort_stage(sort),
                skip=org_skip + len(organic),
                limit=need + 5,
                project_fields=project_fields,
                now_iso=now_iso,
                with_boost_fields=False,
            )
        ).to_list(length=need + 5)
        for p in more_org:
            if p.get("id") in seen:
                continue
            merged.append(p)
            seen.add(p.get("id"))
            if len(merged) >= page_size:
                break

    if len(merged) < page_size:
        need = page_size - len(merged)
        more_boost = await db.properties.aggregate(
            _pipeline(
                boost_flt,
                sort_stage=boost_sort_stage(sort),
                skip=feat_skip + len(boosted),
                limit=need + 5,
                project_fields=project_fields,
                now_iso=now_iso,
                with_boost_fields=True,
            )
        ).to_list(length=need + 5)
        for p in more_boost:
            if p.get("id") in seen:
                continue
            merged.append(p)
            seen.add(p.get("id"))
            if len(merged) >= page_size:
                break

    merged = merged[:page_size]
    boosted_on_page = sum(
        1 for p in merged
        if (p.get("boost_until") or "") > now_iso and int(p.get("boost_rank") or 0) > 0
    )
    density_scope = "city" if "city" in flt else "global"
    meta = {
        "featured_share": featured_share,
        "featured_slots": featured_n,
        "organic_slots": organic_n,
        "boosted_on_page": boosted_on_page,
        "organic_on_page": len(merged) - boosted_on_page,
        "density_scope": density_scope,
        "density_capped": boosted_on_page <= featured_n or len(organic) > 0,
    }
    return merged, meta


async def record_boost_impressions(property_ids: Sequence[str]) -> int:
    """Segna impressioni lista per annunci con boost attivo."""
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
    ids = list(property_ids)
    if not ids:
        return
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(record_boost_impressions(ids))
    except RuntimeError:
        pass


def apply_boost_rotation_reset_fields(paid_at: datetime) -> Dict[str, Any]:
    return {
        "boost_last_shown_at": None,
        "boost_impression_count": 0,
        "boost_activated_at": paid_at.isoformat(),
    }
