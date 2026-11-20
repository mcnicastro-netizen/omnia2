"""D-175 C6 / S2 — Migrate legacy agencies.storage_extra_gb → CC SoT.

Rules:
- Only verifiable storage_addon purchases (paid tx, unique session_id)
- No duplicates
- Doubtful cases → suspended (no destructive wipe)
- dry-run by default
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("omnia.storage.migrate_extra_to_cc")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _verifiable_gb_by_cc(db) -> Dict[str, Dict[str, Any]]:
    """Map cc_id → {gb, sessions: set, unresolved_sessions: [...]}."""
    txs = await db.payment_transactions.find(
        {
            "kind": "storage_addon",
            "payment_status": "paid",
        },
        {
            "_id": 0,
            "session_id": 1,
            "storage_gb": 1,
            "commercial_customer_id": 1,
            "agency_id": 1,
        },
    ).to_list(length=100_000)

    out: Dict[str, Dict[str, Any]] = {}
    seen_sessions: Set[str] = set()
    unresolved: List[str] = []

    for tx in txs or []:
        sid = (tx.get("session_id") or "").strip()
        if not sid or sid in seen_sessions:
            continue
        seen_sessions.add(sid)
        gb = int(tx.get("storage_gb") or 0)
        if gb <= 0:
            continue
        cc_id = (tx.get("commercial_customer_id") or "").strip() or None
        if not cc_id:
            aid = (tx.get("agency_id") or "").strip() or None
            if aid:
                agency = await db.agencies.find_one(
                    {"id": aid}, {"_id": 0, "commercial_customer_id": 1}
                )
                cc_id = ((agency or {}).get("commercial_customer_id") or "").strip() or None
        if not cc_id:
            unresolved.append(sid)
            continue
        bucket = out.setdefault(cc_id, {"gb": 0, "sessions": []})
        bucket["gb"] += gb
        bucket["sessions"].append(sid)

    return {"by_cc": out, "unresolved_sessions": unresolved}


async def classify_cc(
    db,
    cc_id: str,
    *,
    verifiable: Optional[dict] = None,
) -> dict:
    cc = await db.commercial_customers.find_one(
        {"id": cc_id},
        {"_id": 0, "id": 1, "storage_extra_gb": 1, "storage_migration_status": 1},
    )
    if not cc:
        return {"cc_id": cc_id, "status": "missing"}

    current = (cc.get("storage_migration_status") or "").strip().lower()
    if current == "migrated":
        return {
            "cc_id": cc_id,
            "status": "noop",
            "reason": "already_migrated",
            "storage_extra_gb": int(cc.get("storage_extra_gb") or 0),
        }

    if verifiable is None:
        pack = await _verifiable_gb_by_cc(db)
        verifiable = pack["by_cc"].get(cc_id, {"gb": 0, "sessions": []})

    ver_gb = int(verifiable.get("gb") or 0)
    orgs = await db.agencies.find(
        {"commercial_customer_id": cc_id},
        {"_id": 0, "id": 1, "storage_extra_gb": 1},
    ).to_list(length=5000)
    agency_sum = sum(max(0, int(a.get("storage_extra_gb") or 0)) for a in (orgs or []))

    if ver_gb == 0 and agency_sum == 0:
        return {
            "cc_id": cc_id,
            "status": "noop",
            "reason": "both_zero",
            "verifiable_gb": 0,
            "agency_sum": 0,
        }

    if ver_gb == 0 and agency_sum > 0:
        return {
            "cc_id": cc_id,
            "status": "suspend",
            "reason": "agency_extra_without_verifiable_tx",
            "verifiable_gb": 0,
            "agency_sum": agency_sum,
            "agency_ids": [a["id"] for a in orgs if int(a.get("storage_extra_gb") or 0) > 0],
        }

    if agency_sum > ver_gb:
        return {
            "cc_id": cc_id,
            "status": "suspend",
            "reason": "agency_sum_exceeds_verifiable",
            "verifiable_gb": ver_gb,
            "agency_sum": agency_sum,
            "sessions": verifiable.get("sessions") or [],
        }

    # ver_gb >= agency_sum and ver_gb > 0 → migrate
    return {
        "cc_id": cc_id,
        "status": "migrate",
        "reason": "verifiable_ok" if agency_sum == ver_gb else "verifiable_gt_agency",
        "verifiable_gb": ver_gb,
        "agency_sum": agency_sum,
        "sessions": verifiable.get("sessions") or [],
        "agency_ids": [a["id"] for a in orgs],
    }


async def apply_classification(db, row: dict, *, dry_run: bool = True) -> dict:
    result = dict(row)
    result["dry_run"] = dry_run
    if row.get("status") != "migrate":
        if row.get("status") == "suspend" and not dry_run:
            await db.commercial_customers.update_one(
                {"id": row["cc_id"]},
                {
                    "$set": {
                        "storage_migration_status": "suspended",
                        "storage_migration_reason": row.get("reason"),
                        "updated_at": _now(),
                    }
                },
            )
            result["applied"] = "suspended_flag"
        return result

    if dry_run:
        result["applied"] = False
        return result

    cc_id = row["cc_id"]
    ver_gb = int(row["verifiable_gb"])
    now = _now()
    await db.commercial_customers.update_one(
        {"id": cc_id},
        {
            "$set": {
                "storage_extra_gb": ver_gb,
                "storage_migration_status": "migrated",
                "storage_extra_migrated_at": now,
                "storage_migration_reason": row.get("reason"),
                "updated_at": now,
            }
        },
    )
    for aid in row.get("agency_ids") or []:
        await db.agencies.update_one(
            {"id": aid},
            {"$set": {"storage_extra_gb": 0, "updated_at": now}},
        )
    result["applied"] = True
    return result


async def run_migration(
    db,
    *,
    dry_run: bool = True,
    cc_id: Optional[str] = None,
) -> dict:
    pack = await _verifiable_gb_by_cc(db)
    by_cc = pack["by_cc"]

    if cc_id:
        cc_ids = [cc_id]
    else:
        # All CCs that have agencies with extra or verifiable txs
        cc_ids = set(by_cc.keys())
        agencies = await db.agencies.find(
            {"storage_extra_gb": {"$gt": 0}},
            {"_id": 0, "commercial_customer_id": 1},
        ).to_list(length=100_000)
        for a in agencies or []:
            cid = (a.get("commercial_customer_id") or "").strip()
            if cid:
                cc_ids.add(cid)
        # also all CCs in collection (cheap enough for dogfood)
        all_cc = await db.commercial_customers.find({}, {"_id": 0, "id": 1}).to_list(
            length=100_000
        )
        for c in all_cc or []:
            if c.get("id"):
                cc_ids.add(c["id"])
        cc_ids = sorted(cc_ids)

    rows = []
    for cid in cc_ids:
        classified = await classify_cc(
            db, cid, verifiable=by_cc.get(cid, {"gb": 0, "sessions": []})
        )
        rows.append(await apply_classification(db, classified, dry_run=dry_run))

    summary = {
        "dry_run": dry_run,
        "migrate": sum(1 for r in rows if r.get("status") == "migrate"),
        "suspend": sum(1 for r in rows if r.get("status") == "suspend"),
        "noop": sum(1 for r in rows if r.get("status") == "noop"),
        "unresolved_sessions": pack.get("unresolved_sessions") or [],
        "rows": rows,
    }
    logger.info(
        "storage migration summary dry_run=%s migrate=%s suspend=%s noop=%s",
        dry_run,
        summary["migrate"],
        summary["suspend"],
        summary["noop"],
    )
    return summary
