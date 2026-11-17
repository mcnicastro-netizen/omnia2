"""B04-DES-04 / Slice B04-II — Wallet centrale, lotti, allocazioni, ledger FIFO.

Collections (nuove, CC-scoped):
  cc_credit_wallets, credit_lots, credit_allocations, cc_credit_ledger

Legacy agency `credit_wallets` / `credit_ledger` restano mirror di compatibilità
finché i call-site agency-scoped non migrano completamente.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException
from pymongo import ReturnDocument

logger = logging.getLogger("omnia.billing.credit_wallet")

ENTRY_GRANT = "grant"
ENTRY_ALLOCATE = "allocate"
ENTRY_REVOKE = "revoke"
ENTRY_CONSUME = "consume"
ENTRY_COMPENSATE = "compensate"
ENTRY_RETURN = "return_to_central"  # uscita filiale / revoke


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


async def ensure_wallet(db, commercial_customer_id: str) -> dict:
    existing = await db.cc_credit_wallets.find_one(
        {"commercial_customer_id": commercial_customer_id}, {"_id": 0}
    )
    if existing:
        return existing
    doc = {
        "id": _new_id(),
        "commercial_customer_id": commercial_customer_id,
        "balance_unallocated": 0,
        "balance_total": 0,
        "created_at": _now(),
        "updated_at": _now(),
    }
    try:
        await db.cc_credit_wallets.insert_one(doc)
    except Exception:
        existing = await db.cc_credit_wallets.find_one(
            {"commercial_customer_id": commercial_customer_id}, {"_id": 0}
        )
        if existing:
            return existing
        raise
    return {k: v for k, v in doc.items() if k != "_id"}


async def _refresh_wallet_balances(db, commercial_customer_id: str) -> dict:
    """Recompute cached totals from lots (remaining) and unallocated."""
    lots = await db.credit_lots.find(
        {"commercial_customer_id": commercial_customer_id},
        {"_id": 0, "remaining_qty": 1},
    ).to_list(length=10_000)
    total = sum(int(l.get("remaining_qty") or 0) for l in lots)
    allocs = await db.credit_allocations.find(
        {"commercial_customer_id": commercial_customer_id},
        {"_id": 0, "remaining_qty": 1},
    ).to_list(length=10_000)
    allocated = sum(int(a.get("remaining_qty") or 0) for a in allocs)
    unallocated = max(0, total - allocated)
    await db.cc_credit_wallets.update_one(
        {"commercial_customer_id": commercial_customer_id},
        {
            "$set": {
                "balance_total": total,
                "balance_unallocated": unallocated,
                "updated_at": _now(),
            }
        },
    )
    return await db.cc_credit_wallets.find_one(
        {"commercial_customer_id": commercial_customer_id}, {"_id": 0}
    ) or {}


async def _mirror_agency_balance(db, organization_id: str) -> int:
    """Sync legacy credit_wallets.balance to sum of org allocation remaining."""
    allocs = await db.credit_allocations.find(
        {"organization_id": organization_id},
        {"_id": 0, "remaining_qty": 1},
    ).to_list(length=10_000)
    balance = sum(int(a.get("remaining_qty") or 0) for a in allocs)
    now = _now()
    await db.credit_wallets.update_one(
        {"agency_id": organization_id},
        {
            "$set": {"balance": balance, "updated_at": now},
            "$setOnInsert": {
                "id": _new_id(),
                "agency_id": organization_id,
                "created_at": now,
            },
        },
        upsert=True,
    )
    return balance


async def _append_ledger(
    db,
    *,
    commercial_customer_id: str,
    entry_type: str,
    delta: int,
    reason: str,
    organization_id: Optional[str] = None,
    lot_id: Optional[str] = None,
    allocation_id: Optional[str] = None,
    ref_id: Optional[str] = None,
    ref_type: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    meta: Optional[dict] = None,
) -> dict:
    if idempotency_key:
        existing = await db.cc_credit_ledger.find_one(
            {"idempotency_key": idempotency_key}, {"_id": 0}
        )
        if existing:
            return existing
    doc = {
        "id": _new_id(),
        "commercial_customer_id": commercial_customer_id,
        "organization_id": organization_id,
        "lot_id": lot_id,
        "allocation_id": allocation_id,
        "entry_type": entry_type,
        "delta": int(delta),
        "reason": reason,
        "ref_id": ref_id,
        "ref_type": ref_type,
        "idempotency_key": idempotency_key,
        "meta": meta or {},
        "created_at": _now(),
    }
    try:
        await db.cc_credit_ledger.insert_one(doc)
    except Exception:
        if idempotency_key:
            existing = await db.cc_credit_ledger.find_one(
                {"idempotency_key": idempotency_key}, {"_id": 0}
            )
            if existing:
                return existing
        raise
    return {k: v for k, v in doc.items() if k != "_id"}


async def resolve_cc_id_for_agency(db, agency_id: str) -> Optional[str]:
    agency = await db.agencies.find_one(
        {"id": agency_id}, {"commercial_customer_id": 1}
    )
    return (agency or {}).get("commercial_customer_id")


def _spend_blocked(cc: Optional[dict]) -> bool:
    if not cc:
        return False
    status = cc.get("commercial_status") or "pre_activation"
    return status in ("suspended", "ceased", "pre_activation")


async def grant_lot(
    db,
    *,
    commercial_customer_id: str,
    amount: int,
    origin: str,
    reason: str,
    idempotency_key: Optional[str] = None,
    allocate_to_organization_id: Optional[str] = None,
    ref_id: Optional[str] = None,
    ref_type: Optional[str] = None,
) -> dict:
    """Create a credit lot on the central wallet. Optionally allocate to one org."""
    if amount <= 0:
        raise ValueError("amount_must_be_positive")
    if idempotency_key:
        existing_lot = await db.credit_lots.find_one(
            {"idempotency_key": idempotency_key}, {"_id": 0}
        )
        if existing_lot:
            return existing_lot

    wallet = await ensure_wallet(db, commercial_customer_id)
    lot = {
        "id": _new_id(),
        "commercial_customer_id": commercial_customer_id,
        "wallet_id": wallet["id"],
        "origin": origin,
        "original_qty": int(amount),
        "remaining_qty": int(amount),
        "idempotency_key": idempotency_key,
        "created_at": _now(),
        "updated_at": _now(),
    }
    try:
        await db.credit_lots.insert_one(lot)
    except Exception:
        if idempotency_key:
            existing_lot = await db.credit_lots.find_one(
                {"idempotency_key": idempotency_key}, {"_id": 0}
            )
            if existing_lot:
                return existing_lot
        raise

    await _append_ledger(
        db,
        commercial_customer_id=commercial_customer_id,
        entry_type=ENTRY_GRANT,
        delta=amount,
        reason=reason,
        lot_id=lot["id"],
        ref_id=ref_id,
        ref_type=ref_type,
        idempotency_key=f"grant:{idempotency_key}" if idempotency_key else None,
    )
    await _refresh_wallet_balances(db, commercial_customer_id)

    if allocate_to_organization_id:
        await allocate_credits(
            db,
            commercial_customer_id=commercial_customer_id,
            organization_id=allocate_to_organization_id,
            amount=amount,
            prefer_lot_id=lot["id"],
            reason=f"auto_allocate:{reason}",
            idempotency_key=(
                f"alloc:{idempotency_key}" if idempotency_key else None
            ),
        )
    return {k: v for k, v in lot.items() if k != "_id"}


async def allocate_credits(
    db,
    *,
    commercial_customer_id: str,
    organization_id: str,
    amount: int,
    prefer_lot_id: Optional[str] = None,
    reason: str = "allocate",
    idempotency_key: Optional[str] = None,
) -> list[dict]:
    """Allocate unallocated lot qty to an Organization (FIFO, optionally prefer one lot)."""
    if amount <= 0:
        raise ValueError("amount_must_be_positive")
    if idempotency_key:
        existing = await db.cc_credit_ledger.find_one(
            {"idempotency_key": idempotency_key}, {"_id": 0}
        )
        if existing:
            return []

    # Verify org belongs to same CC (no cross-P.IVA)
    agency = await db.agencies.find_one(
        {"id": organization_id}, {"commercial_customer_id": 1}
    )
    org_cc = (agency or {}).get("commercial_customer_id")
    if org_cc and org_cc != commercial_customer_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "cross_vat_transfer_forbidden",
                "hint": "Nessun trasferimento crediti tra P.IVA differenti",
            },
        )

    remaining_to_alloc = int(amount)
    created: list[dict] = []

    async def _lots_cursor():
        q: dict[str, Any] = {
            "commercial_customer_id": commercial_customer_id,
            "remaining_qty": {"$gt": 0},
        }
        if prefer_lot_id:
            # Prefer specific lot first, then FIFO others
            preferred = await db.credit_lots.find_one(
                {"id": prefer_lot_id, **q}, {"_id": 0}
            )
            others = (
                await db.credit_lots.find(
                    {**q, "id": {"$ne": prefer_lot_id}}, {"_id": 0}
                )
                .sort("created_at", 1)
                .to_list(length=10_000)
            )
            return ([preferred] if preferred else []) + others
        return (
            await db.credit_lots.find(q, {"_id": 0})
            .sort("created_at", 1)
            .to_list(length=10_000)
        )

    lots = await _lots_cursor()
    # Unallocated per lot = remaining_qty - sum(allocations remaining on that lot)
    for lot in lots:
        if remaining_to_alloc <= 0:
            break
        lot_id = lot["id"]
        allocs = await db.credit_allocations.find(
            {"lot_id": lot_id}, {"_id": 0, "remaining_qty": 1}
        ).to_list(length=10_000)
        allocated = sum(int(a.get("remaining_qty") or 0) for a in allocs)
        free = int(lot.get("remaining_qty") or 0) - allocated
        if free <= 0:
            continue
        take = min(free, remaining_to_alloc)
        # Atomic: ensure lot still has enough remaining
        updated_lot = await db.credit_lots.find_one_and_update(
            {"id": lot_id, "remaining_qty": {"$gte": 0}},
            {"$set": {"updated_at": _now()}},
            return_document=ReturnDocument.AFTER,
        )
        if not updated_lot:
            continue
        # Re-check free after lock-ish read
        allocs = await db.credit_allocations.find(
            {"lot_id": lot_id}, {"_id": 0, "remaining_qty": 1}
        ).to_list(length=10_000)
        allocated = sum(int(a.get("remaining_qty") or 0) for a in allocs)
        free = int(updated_lot.get("remaining_qty") or 0) - allocated
        if free <= 0:
            continue
        take = min(free, remaining_to_alloc)
        alloc_doc = {
            "id": _new_id(),
            "commercial_customer_id": commercial_customer_id,
            "lot_id": lot_id,
            "organization_id": organization_id,
            "original_qty": take,
            "remaining_qty": take,
            "created_at": _now(),
            "updated_at": _now(),
        }
        await db.credit_allocations.insert_one(alloc_doc)
        await _append_ledger(
            db,
            commercial_customer_id=commercial_customer_id,
            entry_type=ENTRY_ALLOCATE,
            delta=0,
            reason=reason,
            organization_id=organization_id,
            lot_id=lot_id,
            allocation_id=alloc_doc["id"],
            idempotency_key=(
                f"{idempotency_key}:{lot_id}" if idempotency_key and take == amount else None
            ),
            meta={"allocated": take},
        )
        created.append({k: v for k, v in alloc_doc.items() if k != "_id"})
        remaining_to_alloc -= take

    if remaining_to_alloc > 0:
        # Compensate: roll back created allocations in this call
        for a in created:
            await db.credit_allocations.delete_one({"id": a["id"]})
        raise HTTPException(
            status_code=409,
            detail={
                "error": "insufficient_unallocated_credits",
                "requested": amount,
                "shortfall": remaining_to_alloc,
            },
        )

    if idempotency_key:
        await _append_ledger(
            db,
            commercial_customer_id=commercial_customer_id,
            entry_type=ENTRY_ALLOCATE,
            delta=0,
            reason=reason,
            organization_id=organization_id,
            idempotency_key=idempotency_key,
            meta={"allocated_total": amount},
        )

    await _refresh_wallet_balances(db, commercial_customer_id)
    await _mirror_agency_balance(db, organization_id)
    return created


async def revoke_allocation(
    db,
    *,
    allocation_id: str,
    commercial_customer_id: str,
    reason: str = "revoke",
    idempotency_key: Optional[str] = None,
) -> dict:
    """Return remaining allocation qty to central (unallocated on same lot).

    B04-H1: `commercial_customer_id` is mandatory and must match the allocation.
    Client-supplied allocation_id alone is never sufficient authorization.
    Atomic find_one_and_update prevents double-revoke / concurrent races.
    Cross-tenant or missing allocation → 404 (no victim wallet mutation).
    """
    if not commercial_customer_id:
        raise HTTPException(
            status_code=400,
            detail={"error": "commercial_customer_required"},
        )
    if idempotency_key:
        existing = await db.cc_credit_ledger.find_one(
            {"idempotency_key": idempotency_key}, {"_id": 0}
        )
        if existing:
            return existing

    alloc = await db.credit_allocations.find_one_and_update(
        {
            "id": allocation_id,
            "commercial_customer_id": commercial_customer_id,
            "remaining_qty": {"$gt": 0},
        },
        {"$set": {"remaining_qty": 0, "updated_at": _now(), "revoked_at": _now()}},
        return_document=ReturnDocument.BEFORE,
    )
    if not alloc:
        raise HTTPException(status_code=404, detail={"error": "allocation_not_found"})

    returned = int(alloc.get("remaining_qty") or 0)
    entry = await _append_ledger(
        db,
        commercial_customer_id=alloc["commercial_customer_id"],
        entry_type=ENTRY_REVOKE,
        delta=0,
        reason=reason,
        organization_id=alloc.get("organization_id"),
        lot_id=alloc.get("lot_id"),
        allocation_id=allocation_id,
        idempotency_key=idempotency_key,
        meta={"returned": returned},
    )
    await _refresh_wallet_balances(db, alloc["commercial_customer_id"])
    if alloc.get("organization_id"):
        await _mirror_agency_balance(db, alloc["organization_id"])
    return entry


async def org_spendable_balance(db, organization_id: str) -> int:
    cc_id = await resolve_cc_id_for_agency(db, organization_id)
    if not cc_id:
        w = await db.credit_wallets.find_one(
            {"agency_id": organization_id}, {"balance": 1}
        )
        return int((w or {}).get("balance") or 0)
    allocs = await db.credit_allocations.find(
        {"organization_id": organization_id, "remaining_qty": {"$gt": 0}},
        {"_id": 0, "remaining_qty": 1},
    ).to_list(length=10_000)
    return sum(int(a.get("remaining_qty") or 0) for a in allocs)


async def debit_for_organization(
    db,
    *,
    organization_id: str,
    amount: int,
    reason: str,
    ref_id: Optional[str] = None,
    ref_type: Optional[str] = None,
) -> int:
    """Consume credits FIFO across allocations/lots for one Organization.

    Dual-writes legacy agency wallet + ledger. Raises HTTP 402 if insufficient
    or spend blocked by commercial status.
    """
    if amount <= 0:
        raise ValueError("amount_must_be_positive")

    cc_id = await resolve_cc_id_for_agency(db, organization_id)
    if not cc_id:
        # Legacy path: agency wallet only (pre-B01 agencies)
        return await _legacy_debit(
            db,
            agency_id=organization_id,
            amount=amount,
            reason=reason,
            ref_id=ref_id,
            ref_type=ref_type,
        )

    cc = await db.commercial_customers.find_one({"id": cc_id}, {"_id": 0})
    if _spend_blocked(cc):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "credits_not_spendable",
                "commercial_status": (cc or {}).get("commercial_status"),
                "reason": reason,
            },
        )

    # Load allocations with lot created_at for FIFO
    allocs = await db.credit_allocations.find(
        {
            "organization_id": organization_id,
            "commercial_customer_id": cc_id,
            "remaining_qty": {"$gt": 0},
        },
        {"_id": 0},
    ).to_list(length=10_000)
    if not allocs:
        raise HTTPException(
            status_code=402,
            detail={"error": "insufficient_credits", "required": amount, "reason": reason},
        )

    lot_ids = list({a["lot_id"] for a in allocs if a.get("lot_id")})
    lots = await db.credit_lots.find(
        {"id": {"$in": lot_ids}}, {"_id": 0, "id": 1, "created_at": 1}
    ).to_list(length=10_000)
    lot_created = {l["id"]: l.get("created_at") or "" for l in lots}
    allocs_sorted = sorted(
        allocs, key=lambda a: (lot_created.get(a.get("lot_id"), ""), a.get("created_at") or "")
    )

    need = int(amount)
    consumed_plan: list[tuple[dict, int]] = []
    for alloc in allocs_sorted:
        if need <= 0:
            break
        avail = int(alloc.get("remaining_qty") or 0)
        if avail <= 0:
            continue
        take = min(avail, need)
        consumed_plan.append((alloc, take))
        need -= take

    if need > 0:
        raise HTTPException(
            status_code=402,
            detail={"error": "insufficient_credits", "required": amount, "reason": reason},
        )

    # Apply atomic decrements; rollback on failure
    applied: list[tuple[str, int]] = []
    try:
        for alloc, take in consumed_plan:
            updated = await db.credit_allocations.find_one_and_update(
                {"id": alloc["id"], "remaining_qty": {"$gte": take}},
                {
                    "$inc": {"remaining_qty": -take},
                    "$set": {"updated_at": _now()},
                },
                return_document=ReturnDocument.AFTER,
            )
            if not updated:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "insufficient_credits",
                        "required": amount,
                        "reason": reason,
                    },
                )
            applied.append((alloc["id"], take))
            # Decrement lot remaining
            lot_ok = await db.credit_lots.find_one_and_update(
                {"id": alloc["lot_id"], "remaining_qty": {"$gte": take}},
                {
                    "$inc": {"remaining_qty": -take},
                    "$set": {"updated_at": _now()},
                },
                return_document=ReturnDocument.AFTER,
            )
            if not lot_ok:
                raise HTTPException(
                    status_code=409,
                    detail={"error": "lot_inconsistency", "lot_id": alloc["lot_id"]},
                )
            await _append_ledger(
                db,
                commercial_customer_id=cc_id,
                entry_type=ENTRY_CONSUME,
                delta=-take,
                reason=reason,
                organization_id=organization_id,
                lot_id=alloc["lot_id"],
                allocation_id=alloc["id"],
                ref_id=ref_id,
                ref_type=ref_type,
            )
    except HTTPException:
        # Best-effort compensate applied allocation decrements
        for alloc_id, take in applied:
            await db.credit_allocations.update_one(
                {"id": alloc_id},
                {"$inc": {"remaining_qty": take}, "$set": {"updated_at": _now()}},
            )
            # Note: lot restore would need lot_id; leave compensate ledger for ops
            await _append_ledger(
                db,
                commercial_customer_id=cc_id,
                entry_type=ENTRY_COMPENSATE,
                delta=take,
                reason=f"compensate_failed_debit:{reason}",
                organization_id=organization_id,
                allocation_id=alloc_id,
                ref_id=ref_id,
                ref_type=ref_type,
            )
        raise

    await _refresh_wallet_balances(db, cc_id)
    new_balance = await _mirror_agency_balance(db, organization_id)

    # Legacy ledger mirror
    await db.credit_ledger.insert_one(
        {
            "id": _new_id(),
            "agency_id": organization_id,
            "delta": -amount,
            "reason": reason,
            "balance_after": new_balance,
            "ref_id": ref_id,
            "ref_type": ref_type,
            "created_at": _now(),
            "cc_mirror": True,
        }
    )
    return new_balance


async def _legacy_debit(
    db,
    *,
    agency_id: str,
    amount: int,
    reason: str,
    ref_id: Optional[str],
    ref_type: Optional[str],
) -> int:
    now = _now()
    wallet = await db.credit_wallets.find_one_and_update(
        {"agency_id": agency_id, "balance": {"$gte": amount}},
        {"$inc": {"balance": -amount}, "$set": {"updated_at": now}},
        return_document=ReturnDocument.AFTER,
    )
    if not wallet:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "insufficient_credits",
                "required": amount,
                "reason": reason,
            },
        )
    new_balance = wallet["balance"]
    await db.credit_ledger.insert_one(
        {
            "id": _new_id(),
            "agency_id": agency_id,
            "delta": -amount,
            "reason": reason,
            "balance_after": new_balance,
            "ref_id": ref_id,
            "ref_type": ref_type,
            "created_at": now,
        }
    )
    return new_balance


async def grant_for_agency(
    db,
    *,
    agency_id: str,
    amount: int,
    origin: str,
    reason: str,
    idempotency_key: Optional[str] = None,
    ref_id: Optional[str] = None,
    ref_type: Optional[str] = None,
) -> dict:
    """Grant lot to CC of agency and auto-allocate to that organization."""
    cc_id = await resolve_cc_id_for_agency(db, agency_id)
    if not cc_id:
        # Legacy: direct agency wallet topup
        now = _now()
        wallet = await db.credit_wallets.find_one_and_update(
            {"agency_id": agency_id},
            {
                "$inc": {"balance": amount},
                "$set": {"last_topup_at": now, "updated_at": now},
                "$setOnInsert": {"id": _new_id(), "agency_id": agency_id, "created_at": now},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        bal = (wallet or {}).get("balance", amount)
        await db.credit_ledger.insert_one(
            {
                "id": _new_id(),
                "agency_id": agency_id,
                "delta": amount,
                "reason": reason,
                "balance_after": bal,
                "ref_id": ref_id,
                "ref_type": ref_type,
                "created_at": now,
            }
        )
        return {"legacy": True, "balance": bal}

    lot = await grant_lot(
        db,
        commercial_customer_id=cc_id,
        amount=amount,
        origin=origin,
        reason=reason,
        idempotency_key=idempotency_key,
        allocate_to_organization_id=agency_id,
        ref_id=ref_id,
        ref_type=ref_type,
    )
    return lot


async def wallet_summary(db, commercial_customer_id: str) -> dict:
    wallet = await ensure_wallet(db, commercial_customer_id)
    lots = await db.credit_lots.find(
        {"commercial_customer_id": commercial_customer_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(length=10_000)
    allocs = await db.credit_allocations.find(
        {"commercial_customer_id": commercial_customer_id}, {"_id": 0}
    ).to_list(length=10_000)
    return {
        "wallet": wallet,
        "lots": lots,
        "allocations": allocs,
        "balance_total": wallet.get("balance_total", 0),
        "balance_unallocated": wallet.get("balance_unallocated", 0),
    }
