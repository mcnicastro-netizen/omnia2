"""D-175 C6 / S2 — Migrate legacy agencies.storage_extra_gb → CC SoT.

Rules:
- Only verifiable storage_addon purchases (paid tx, unique coherent session_id)
- No duplicates; discordant duplicate session_id → anomaly (suspend)
- tx.CC vs agency.CC mismatch → suspend (do not credit tx CC)
- Before zeroing agency extra: permanent snapshot per org
- Doubtful cases → suspended (no destructive wipe)
- dry-run by default; apply idempotent (already migrated → noop)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("omnia.storage.migrate_extra_to_cc")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


async def _verifiable_gb_by_cc(db) -> Dict[str, Any]:
    """Build per-CC verifiable GB with anomaly detection.

    Returns:
      by_cc: cc_id → {gb, sessions, agency_snapshots hint}
      unresolved_sessions, discordant_sessions, cc_agency_mismatch_sessions
    """
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
    seen: Dict[str, dict] = {}  # session_id → first fingerprint
    unresolved: List[str] = []
    discordant: List[dict] = []
    mismatch: List[dict] = []
    suspended_cc: Set[str] = set()

    for tx in txs or []:
        sid = (tx.get("session_id") or "").strip()
        if not sid:
            continue
        gb = int(tx.get("storage_gb") or 0)
        if gb <= 0:
            continue

        tx_cc = (tx.get("commercial_customer_id") or "").strip() or None
        aid = (tx.get("agency_id") or "").strip() or None
        agency_cc = None
        if aid:
            agency = await db.agencies.find_one(
                {"id": aid}, {"_id": 0, "commercial_customer_id": 1}
            )
            agency_cc = ((agency or {}).get("commercial_customer_id") or "").strip() or None

        # tx CC vs agency CC mismatch → suspend both CCs involved
        if tx_cc and agency_cc and tx_cc != agency_cc:
            mismatch.append(
                {
                    "session_id": sid,
                    "tx_commercial_customer_id": tx_cc,
                    "agency_id": aid,
                    "agency_commercial_customer_id": agency_cc,
                    "storage_gb": gb,
                }
            )
            suspended_cc.add(tx_cc)
            suspended_cc.add(agency_cc)
            continue

        cc_id = tx_cc or agency_cc
        if not cc_id:
            unresolved.append(sid)
            continue

        fingerprint = {
            "commercial_customer_id": cc_id,
            "storage_gb": gb,
            "agency_id": aid,
        }
        if sid in seen:
            prev = seen[sid]
            if (
                prev["commercial_customer_id"] != fingerprint["commercial_customer_id"]
                or prev["storage_gb"] != fingerprint["storage_gb"]
            ):
                discordant.append(
                    {
                        "session_id": sid,
                        "first": prev,
                        "other": fingerprint,
                    }
                )
                suspended_cc.add(prev["commercial_customer_id"])
                suspended_cc.add(fingerprint["commercial_customer_id"])
            # duplicate coherent → ignore silently (dedupe)
            continue

        seen[sid] = fingerprint
        if cc_id in suspended_cc:
            # still record session but CC will be forced suspend
            pass
        bucket = out.setdefault(cc_id, {"gb": 0, "sessions": []})
        bucket["gb"] += gb
        bucket["sessions"].append(sid)

    # Remove verifiable buckets for CCs that must suspend due to anomalies
    for cid in list(suspended_cc):
        out.pop(cid, None)

    return {
        "by_cc": out,
        "unresolved_sessions": unresolved,
        "discordant_sessions": discordant,
        "cc_agency_mismatch_sessions": mismatch,
        "force_suspend_cc_ids": sorted(suspended_cc),
    }


async def classify_cc(
    db,
    cc_id: str,
    *,
    verifiable: Optional[dict] = None,
    force_suspend: bool = False,
    force_reason: Optional[str] = None,
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

    orgs = await db.agencies.find(
        {"commercial_customer_id": cc_id},
        {"_id": 0, "id": 1, "storage_extra_gb": 1},
    ).to_list(length=5000)
    agency_rows = [
        {
            "agency_id": a["id"],
            "previous_storage_extra_gb": max(0, int(a.get("storage_extra_gb") or 0)),
        }
        for a in (orgs or [])
    ]
    agency_sum = sum(r["previous_storage_extra_gb"] for r in agency_rows)

    if force_suspend:
        return {
            "cc_id": cc_id,
            "status": "suspend",
            "reason": force_reason or "anomaly_force_suspend",
            "verifiable_gb": int((verifiable or {}).get("gb") or 0),
            "agency_sum": agency_sum,
            "agency_snapshots": agency_rows,
            "sessions": (verifiable or {}).get("sessions") or [],
        }

    if verifiable is None:
        pack = await _verifiable_gb_by_cc(db)
        verifiable = pack["by_cc"].get(cc_id, {"gb": 0, "sessions": []})

    ver_gb = int(verifiable.get("gb") or 0)

    if ver_gb == 0 and agency_sum == 0:
        return {
            "cc_id": cc_id,
            "status": "noop",
            "reason": "both_zero",
            "verifiable_gb": 0,
            "agency_sum": 0,
            "agency_snapshots": agency_rows,
        }

    if ver_gb == 0 and agency_sum > 0:
        return {
            "cc_id": cc_id,
            "status": "suspend",
            "reason": "agency_extra_without_verifiable_tx",
            "verifiable_gb": 0,
            "agency_sum": agency_sum,
            "agency_snapshots": agency_rows,
            "agency_ids": [r["agency_id"] for r in agency_rows if r["previous_storage_extra_gb"] > 0],
        }

    if agency_sum > ver_gb:
        return {
            "cc_id": cc_id,
            "status": "suspend",
            "reason": "agency_sum_exceeds_verifiable",
            "verifiable_gb": ver_gb,
            "agency_sum": agency_sum,
            "agency_snapshots": agency_rows,
            "sessions": verifiable.get("sessions") or [],
        }

    return {
        "cc_id": cc_id,
        "status": "migrate",
        "reason": "verifiable_ok" if agency_sum == ver_gb else "verifiable_gt_agency",
        "verifiable_gb": ver_gb,
        "agency_sum": agency_sum,
        "agency_snapshots": agency_rows,
        "sessions": verifiable.get("sessions") or [],
        "agency_ids": [r["agency_id"] for r in agency_rows],
    }


async def _persist_snapshots(
    db,
    *,
    cc_id: str,
    row: dict,
    outcome: str,
    now: str,
) -> None:
    """Permanent per-org legacy snapshot before any destructive write."""
    coll = db.storage_migration_snapshots
    for snap in row.get("agency_snapshots") or []:
        doc = {
            "id": _new_id(),
            "commercial_customer_id": cc_id,
            "agency_id": snap["agency_id"],
            "previous_storage_extra_gb": snap["previous_storage_extra_gb"],
            "verified_session_ids": list(row.get("sessions") or []),
            "transferred_gb": int(row.get("verifiable_gb") or 0)
            if outcome == "migrated"
            else 0,
            "outcome": outcome,
            "reason": row.get("reason"),
            "migrated_at": now,
            "created_at": now,
        }
        existing = await coll.find_one(
            {
                "commercial_customer_id": cc_id,
                "agency_id": snap["agency_id"],
                "outcome": outcome,
                "previous_storage_extra_gb": snap["previous_storage_extra_gb"],
            },
            {"_id": 0, "id": 1},
        )
        if existing:
            continue
        await coll.insert_one(doc)


async def apply_classification(db, row: dict, *, dry_run: bool = True) -> dict:
    result = dict(row)
    result["dry_run"] = dry_run
    status = row.get("status")

    if status == "noop":
        result["applied"] = False
        return result

    if status == "suspend":
        if dry_run:
            result["applied"] = False
            return result
        now = _now()
        await _persist_snapshots(
            db, cc_id=row["cc_id"], row=row, outcome="suspended", now=now
        )
        await db.commercial_customers.update_one(
            {"id": row["cc_id"]},
            {
                "$set": {
                    "storage_migration_status": "suspended",
                    "storage_migration_reason": row.get("reason"),
                    "updated_at": now,
                }
            },
        )
        result["applied"] = "suspended_flag"
        return result

    if status != "migrate":
        return result

    if dry_run:
        result["applied"] = False
        return result

    cc_id = row["cc_id"]
    ver_gb = int(row["verifiable_gb"])
    now = _now()

    # Snapshots FIRST — permanent legacy photo before zeroing
    await _persist_snapshots(db, cc_id=cc_id, row=row, outcome="migrated", now=now)

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
    force_ids = set(pack.get("force_suspend_cc_ids") or [])

    if cc_id:
        cc_ids = [cc_id]
    else:
        cc_ids = set(by_cc.keys()) | force_ids
        agencies = await db.agencies.find(
            {"storage_extra_gb": {"$gt": 0}},
            {"_id": 0, "commercial_customer_id": 1},
        ).to_list(length=100_000)
        for a in agencies or []:
            cid = (a.get("commercial_customer_id") or "").strip()
            if cid:
                cc_ids.add(cid)
        all_cc = await db.commercial_customers.find({}, {"_id": 0, "id": 1}).to_list(
            length=100_000
        )
        for c in all_cc or []:
            if c.get("id"):
                cc_ids.add(c["id"])
        cc_ids = sorted(cc_ids)

    rows = []
    for cid in cc_ids:
        force = cid in force_ids
        reason = None
        if force:
            reason = "tx_agency_cc_mismatch_or_discordant_session"
        classified = await classify_cc(
            db,
            cid,
            verifiable=by_cc.get(cid, {"gb": 0, "sessions": []}),
            force_suspend=force,
            force_reason=reason,
        )
        rows.append(await apply_classification(db, classified, dry_run=dry_run))

    summary = {
        "dry_run": dry_run,
        "migrate": sum(1 for r in rows if r.get("status") == "migrate"),
        "suspend": sum(1 for r in rows if r.get("status") == "suspend"),
        "noop": sum(1 for r in rows if r.get("status") == "noop"),
        "unresolved_sessions": pack.get("unresolved_sessions") or [],
        "discordant_sessions": pack.get("discordant_sessions") or [],
        "cc_agency_mismatch_sessions": pack.get("cc_agency_mismatch_sessions") or [],
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
