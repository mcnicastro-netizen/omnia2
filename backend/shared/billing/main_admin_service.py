"""B04-H2 — Main Admin commerciale sul CommercialCustomer (D01–D12).

Autorità per-CC (non ruolo globale). Membership non richiesta.
Wallet centrale: solo Main Admin idoneo; Super Admin mutate solo straordinario (D07).
"""
from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException
from pymongo import ReturnDocument

logger = logging.getLogger("omnia.billing.main_admin")

TRANSFER_TTL_HOURS = 48
EVENT_COLL = "commercial_main_admin_events"
TRANSFER_COLL = "commercial_main_admin_transfers"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def append_main_admin_event(
    db,
    *,
    commercial_customer_id: str,
    event_type: str,
    actor_user_id: Optional[str],
    outcome: str = "success",
    previous_main_admin_user_id: Optional[str] = None,
    new_main_admin_user_id: Optional[str] = None,
    reason: Optional[str] = None,
    meta: Optional[dict] = None,
) -> dict:
    doc = {
        "id": str(uuid4()),
        "commercial_customer_id": commercial_customer_id,
        "event_type": event_type,
        "actor_user_id": actor_user_id,
        "previous_main_admin_user_id": previous_main_admin_user_id,
        "new_main_admin_user_id": new_main_admin_user_id,
        "reason": reason,
        "outcome": outcome,
        "meta": meta or {},
        "created_at": _now_iso(),
    }
    await db[EVENT_COLL].insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


def user_is_eligible_main_admin(user: Optional[dict]) -> bool:
    """D04/D11/D12 — idoneità account (non Membership).

    Deny-by-default: `is_active` assente/null/False → non idoneo.
    Serve esplicitamente `is_active is True` e `email_verified is True`.
    """
    if not user:
        return False
    if user.get("is_active") is not True:
        return False
    if user.get("email_verified") is not True:
        return False
    return True


async def load_user(db, user_id: str) -> Optional[dict]:
    if not user_id:
        return None
    return await db.users.find_one(
        {"id": user_id},
        {"_id": 0, "password_hash": 0},
    )


async def get_commercial_customer(db, cc_id: str) -> Optional[dict]:
    return await db.commercial_customers.find_one({"id": cc_id}, {"_id": 0})


def cc_allows_wallet_mutation(cc: dict) -> bool:
    """D05/D12 — cessazione e stati non operativi: no mutate wallet."""
    return cc_is_wallet_operable(cc)


def cc_allows_wallet_admin_read(cc: dict) -> bool:
    """MC-042 — consultazione operativa wallet vietata se CC non operativo.

    Whitelist residua (chiusura/fatturazione) non passa da questo gate:
    vive su endpoint documenti dedicati, non su wallet_summary/saldi.
    """
    return cc_is_wallet_operable(cc)


def cc_is_wallet_operable(cc: Optional[dict]) -> bool:
    """True solo se il CC consente accesso operativo al wallet (read o mutate).

    Non-operabile (MC-042 / D05): ``ceased`` oppure
    ``operational_status`` in ``none`` / ``closed_readonly``.
    """
    if not cc:
        return False
    status = cc.get("commercial_status") or "pre_activation"
    if status == "ceased":
        return False
    op = cc.get("operational_status")
    if op in ("none", "closed_readonly"):
        return False
    return True


async def assert_cc_wallet_operable(
    db,
    commercial_customer_id: str,
    *,
    actor_user_id: Optional[str] = None,
    operation: str = "wallet_access",
) -> dict:
    """MC-042 — deny-by-default su CC non operativo per qualsiasi accesso wallet operativo."""
    cc = await get_commercial_customer(db, commercial_customer_id)
    if not cc:
        raise HTTPException(status_code=404, detail={"error": "commercial_customer_not_found"})
    if not cc_is_wallet_operable(cc):
        await append_main_admin_event(
            db,
            commercial_customer_id=commercial_customer_id,
            event_type="deny_attempt",
            actor_user_id=actor_user_id,
            outcome="denied",
            reason="cc_not_operable",
            meta={"operation": operation},
        )
        raise HTTPException(status_code=403, detail={"error": "cc_not_operable"})
    return cc


async def assert_agency_wallet_operable(
    db,
    agency_id: str,
    *,
    actor_user_id: Optional[str] = None,
    operation: str = "wallet_access",
) -> dict:
    """MC-042 — resolve CC da Organization e applica gate wallet.

    Deny-by-default: Organization assente, senza ``commercial_customer_id``,
    o con CC non risolvibile → nessun accesso operativo implicito.
    """
    if not (agency_id or "").strip():
        raise HTTPException(
            status_code=403,
            detail={"error": "commercial_customer_required"},
        )
    agency = await db.agencies.find_one(
        {"id": agency_id}, {"commercial_customer_id": 1}
    )
    if not agency:
        raise HTTPException(
            status_code=403,
            detail={"error": "commercial_customer_required"},
        )
    cc_id = (agency.get("commercial_customer_id") or "").strip() or None
    if not cc_id:
        await append_main_admin_event(
            db,
            commercial_customer_id="unlinked",
            event_type="deny_attempt",
            actor_user_id=actor_user_id,
            outcome="denied",
            reason="commercial_customer_required",
            meta={"operation": operation, "organization_id": agency_id},
        )
        raise HTTPException(
            status_code=403,
            detail={"error": "commercial_customer_required"},
        )
    return await assert_cc_wallet_operable(
        db,
        cc_id,
        actor_user_id=actor_user_id,
        operation=operation,
    )


async def assert_is_main_admin_of(
    db,
    user: dict,
    commercial_customer_id: str,
    *,
    for_mutation: bool = False,
    require_wallet_operable: Optional[bool] = None,
) -> dict:
    """Deny-by-default Main Admin check. Returns CC doc.

    ``require_wallet_operable``: se omesso, True quando ``for_mutation`` (D12),
    altrimenti False (identità Main Admin anche su CC ceased — conservazione
    nomine). I path wallet passano ``require_wallet_operable=True`` anche in read (MC-042).
    """
    cc = await get_commercial_customer(db, commercial_customer_id)
    if not cc:
        raise HTTPException(status_code=404, detail={"error": "commercial_customer_not_found"})

    check_operable = (
        for_mutation if require_wallet_operable is None else require_wallet_operable
    )
    if check_operable and not cc_is_wallet_operable(cc):
        await append_main_admin_event(
            db,
            commercial_customer_id=commercial_customer_id,
            event_type="deny_attempt",
            actor_user_id=user.get("id"),
            outcome="denied",
            reason="cc_not_operable",
        )
        raise HTTPException(status_code=403, detail={"error": "cc_not_operable"})

    ma = cc.get("main_admin_user_id")
    if not ma:
        await append_main_admin_event(
            db,
            commercial_customer_id=commercial_customer_id,
            event_type="deny_attempt",
            actor_user_id=user.get("id"),
            outcome="denied",
            reason="main_admin_unassigned",
        )
        raise HTTPException(status_code=403, detail={"error": "main_admin_unassigned"})

    if user.get("id") != ma:
        await append_main_admin_event(
            db,
            commercial_customer_id=commercial_customer_id,
            event_type="deny_attempt",
            actor_user_id=user.get("id"),
            outcome="denied",
            reason="not_main_admin",
        )
        raise HTTPException(status_code=403, detail={"error": "not_main_admin"})

    if not user_is_eligible_main_admin(user):
        await append_main_admin_event(
            db,
            commercial_customer_id=commercial_customer_id,
            event_type="runtime_block",
            actor_user_id=user.get("id"),
            outcome="denied",
            reason="account_not_eligible",
        )
        raise HTTPException(status_code=403, detail={"error": "account_not_eligible"})

    return cc


async def assert_super_admin_emergency_mutate(
    db,
    user: dict,
    commercial_customer_id: str,
    *,
    reason: str,
    organization_id: Optional[str] = None,
    amount: Optional[int] = None,
    operation: str = "wallet_mutate",
) -> dict:
    """D07 — Super Admin solo straordinario, motivato, auditato."""
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail={"error": "forbidden"})
    reason = (reason or "").strip()
    if len(reason) < 8:
        raise HTTPException(
            status_code=400,
            detail={"error": "extraordinary_reason_required"},
        )
    cc = await get_commercial_customer(db, commercial_customer_id)
    if not cc:
        raise HTTPException(status_code=404, detail={"error": "commercial_customer_not_found"})
    if not cc_allows_wallet_mutation(cc):
        raise HTTPException(status_code=403, detail={"error": "cc_not_operable"})
    await append_main_admin_event(
        db,
        commercial_customer_id=commercial_customer_id,
        event_type="super_admin_emergency",
        actor_user_id=user.get("id"),
        outcome="success",
        reason=reason,
        meta={
            "operation": operation,
            "organization_id": organization_id,
            "amount": amount,
        },
    )
    return cc


async def resolve_wallet_cc_id(
    db,
    user: dict,
    *,
    agency_id: Optional[str] = None,
    commercial_customer_id: Optional[str] = None,
) -> str:
    """Resolve CC for wallet admin (D02 multi-CC).

    Explicit ``commercial_customer_id`` wins so a Main Admin of multiple CC
    is not trapped by the active agency mapping. Authorization remains on
    the resolved CC via ``assert_is_main_admin_of`` / D07 (no ambient trust).
    Fallback: agency→CC when no explicit id is provided.
    """
    cc_id = (commercial_customer_id or "").strip() or None
    if cc_id:
        return cc_id
    if agency_id:
        from shared.billing.credit_wallet_service import resolve_cc_id_for_agency

        from_agency = await resolve_cc_id_for_agency(db, agency_id)
        if from_agency:
            return from_agency
    raise HTTPException(
        status_code=400,
        detail={"error": "commercial_customer_context_required"},
    )


async def nominate_main_admin(
    db,
    *,
    commercial_customer_id: str,
    new_user_id: str,
    actor: dict,
    reason: str = "ops_nominate",
    force: bool = False,
) -> dict:
    """D01 — solo Super Admin Ops.

    Se un Main Admin è già presente e diverso dal target, richiede ``force=True``
    (sostituzione Ops esplicita + audit ``ops_replace``). Nessun overwrite silenzioso.
    """
    if actor.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail={"error": "forbidden"})
    target = await load_user(db, new_user_id)
    if not target or not user_is_eligible_main_admin(target):
        raise HTTPException(status_code=400, detail={"error": "target_not_eligible"})
    cc = await get_commercial_customer(db, commercial_customer_id)
    if not cc:
        raise HTTPException(status_code=404, detail={"error": "commercial_customer_not_found"})

    prev = cc.get("main_admin_user_id")
    if prev and prev != new_user_id and not force:
        raise HTTPException(
            status_code=409,
            detail={"error": "main_admin_already_assigned", "hint": "pass force=true for ops replace"},
        )
    if force and prev and prev != new_user_id:
        reason_stripped = (reason or "").strip()
        if len(reason_stripped) < 8:
            raise HTTPException(
                status_code=400,
                detail={"error": "force_reason_required"},
            )
        reason = reason_stripped

    now = _now_iso()
    updated = await db.commercial_customers.find_one_and_update(
        {"id": commercial_customer_id},
        {
            "$set": {
                "main_admin_user_id": new_user_id,
                "main_admin_appointed_at": now,
                "main_admin_appointed_by": actor["id"],
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    await append_main_admin_event(
        db,
        commercial_customer_id=commercial_customer_id,
        event_type="nominate" if not prev or prev == new_user_id else "ops_replace",
        actor_user_id=actor["id"],
        previous_main_admin_user_id=prev,
        new_main_admin_user_id=new_user_id,
        reason=reason,
        meta={"force": bool(force)} if force else {},
    )
    # Cancel pending transfers on nominate / force replace
    await db[TRANSFER_COLL].update_many(
        {"commercial_customer_id": commercial_customer_id, "status": "pending"},
        {"$set": {"status": "cancelled", "resolved_at": now}},
    )
    return {k: v for k, v in (updated or {}).items() if k != "_id"}


async def revoke_main_admin(
    db,
    *,
    commercial_customer_id: str,
    actor: dict,
    reason: str = "ops_revoke",
) -> dict:
    if actor.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail={"error": "forbidden"})
    cc = await get_commercial_customer(db, commercial_customer_id)
    if not cc:
        raise HTTPException(status_code=404, detail={"error": "commercial_customer_not_found"})
    prev = cc.get("main_admin_user_id")
    now = _now_iso()
    updated = await db.commercial_customers.find_one_and_update(
        {"id": commercial_customer_id},
        {
            "$set": {
                "main_admin_user_id": None,
                "main_admin_appointed_at": None,
                "main_admin_appointed_by": None,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    await append_main_admin_event(
        db,
        commercial_customer_id=commercial_customer_id,
        event_type="revoke",
        actor_user_id=actor["id"],
        previous_main_admin_user_id=prev,
        new_main_admin_user_id=None,
        reason=reason,
    )
    await db[TRANSFER_COLL].update_many(
        {"commercial_customer_id": commercial_customer_id, "status": "pending"},
        {"$set": {"status": "cancelled", "resolved_at": now}},
    )
    return {k: v for k, v in (updated or {}).items() if k != "_id"}


async def _expire_if_needed(db, transfer: dict) -> dict:
    if transfer.get("status") != "pending":
        return transfer
    exp = transfer.get("expires_at")
    if not exp:
        return transfer
    try:
        exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
    except ValueError:
        return transfer
    if _now() < exp_dt:
        return transfer
    updated = await db[TRANSFER_COLL].find_one_and_update(
        {"id": transfer["id"], "status": "pending"},
        {"$set": {"status": "expired", "resolved_at": _now_iso()}},
        return_document=ReturnDocument.AFTER,
    )
    if updated:
        await append_main_admin_event(
            db,
            commercial_customer_id=transfer["commercial_customer_id"],
            event_type="transfer_expired",
            actor_user_id=None,
            outcome="success",
            meta={"transfer_id": transfer["id"]},
        )
        return {k: v for k, v in updated.items() if k != "_id"}
    return transfer


async def propose_transfer(
    db,
    *,
    commercial_customer_id: str,
    to_user_id: str,
    actor: dict,
    reason: str = "transfer_propose",
) -> dict:
    """Propose transfer — returns public fields + raw_token once (never logged)."""
    cc = await get_commercial_customer(db, commercial_customer_id)
    if not cc:
        raise HTTPException(status_code=404, detail={"error": "commercial_customer_not_found"})
    if not cc_allows_wallet_mutation(cc):
        raise HTTPException(status_code=403, detail={"error": "cc_not_operable"})

    is_ops = actor.get("role") == "super_admin"
    is_ma = cc.get("main_admin_user_id") == actor.get("id") and user_is_eligible_main_admin(actor)
    if not (is_ops or is_ma):
        raise HTTPException(status_code=403, detail={"error": "forbidden"})
    # D11 — if current MA not eligible and actor is that MA, block; ops can still nominate
    if is_ma and not user_is_eligible_main_admin(actor):
        raise HTTPException(status_code=403, detail={"error": "account_not_eligible"})

    target = await load_user(db, to_user_id)
    if not target or not user_is_eligible_main_admin(target):
        raise HTTPException(status_code=400, detail={"error": "target_not_eligible"})
    if to_user_id == cc.get("main_admin_user_id"):
        raise HTTPException(status_code=400, detail={"error": "already_main_admin"})

    existing = await db[TRANSFER_COLL].find_one(
        {"commercial_customer_id": commercial_customer_id, "status": "pending"}
    )
    if existing:
        existing = await _expire_if_needed(db, existing)
    if existing and existing.get("status") == "pending":
        raise HTTPException(status_code=409, detail={"error": "transfer_already_pending"})

    raw = secrets.token_urlsafe(32)
    exp = _now() + timedelta(hours=TRANSFER_TTL_HOURS)
    doc = {
        "id": str(uuid4()),
        "commercial_customer_id": commercial_customer_id,
        "from_user_id": cc.get("main_admin_user_id"),
        "to_user_id": to_user_id,
        "status": "pending",
        "token_hash": _hash_token(raw),
        "expires_at": exp.isoformat(),
        "created_by": actor["id"],
        "created_at": _now_iso(),
        "resolved_at": None,
        "reason": reason,
    }
    await db[TRANSFER_COLL].insert_one(doc)
    await append_main_admin_event(
        db,
        commercial_customer_id=commercial_customer_id,
        event_type="propose_transfer",
        actor_user_id=actor["id"],
        previous_main_admin_user_id=cc.get("main_admin_user_id"),
        new_main_admin_user_id=to_user_id,
        reason=reason,
        meta={"transfer_id": doc["id"], "expires_at": doc["expires_at"]},
    )

    # D08 — Cabina obbligatoria sullo stesso db della proposta (non best-effort).
    # create_notification() globale ingoia errori: qui inseriamo e propaghiamo.
    cabina_outcome = "failed"
    try:
        notif_coll = getattr(db, "notifications", None)
        if notif_coll is None:
            notif_coll = db["notifications"]
        notif = {
            "id": str(uuid4()),
            "user_id": to_user_id,
            "agency_id": None,
            "type": "main_admin_transfer",
            "title": "Proposta Main Admin commerciale",
            "body": "Hai una proposta di Main Admin. Accettala dalla Cabina entro 48 ore.",
            "link": "/app/billing/main-admin-transfer",
            "meta": {
                "transfer_id": doc["id"],
                "commercial_customer_id": commercial_customer_id,
                # Token solo in-app (Cabina/inbox); mai in email né nei log eventi
                "accept_token": raw,
            },
            "read": False,
            "created_at": _now_iso(),
            "read_at": None,
        }
        await notif_coll.insert_one(notif)
        cabina_outcome = "sent"
    except Exception as e:  # noqa: BLE001
        logger.warning("cabina notify failed transfer=%s: %s", doc["id"], e)
        now_fail = _now_iso()
        await db[TRANSFER_COLL].update_one(
            {"id": doc["id"], "status": "pending"},
            {
                "$set": {
                    "status": "cancelled",
                    "resolved_at": now_fail,
                    "cancel_reason": "cabina_notify_failed",
                }
            },
        )
        await append_main_admin_event(
            db,
            commercial_customer_id=commercial_customer_id,
            event_type="transfer_notify",
            actor_user_id=actor["id"],
            outcome="failed",
            reason="cabina_notify_failed",
            meta={
                "transfer_id": doc["id"],
                "cabina_outcome": "failed",
                "error": type(e).__name__,
            },
        )
        raise HTTPException(
            status_code=503,
            detail={"error": "cabina_notify_failed", "transfer_id": doc["id"]},
        )

    # Email Resend — best-effort (D08)
    email_outcome = "skipped"
    try:
        from shared.email import send_email

        to_email = target.get("email")
        if to_email:
            await send_email(
                to=to_email,
                template="agency_pending",
                subject="OMNIA — proposta Main Admin commerciale",
                variables={"agency_name": "CommercialCustomer"},
            )
            email_outcome = "sent"
        else:
            email_outcome = "no_email"
    except Exception as e:  # noqa: BLE001
        email_outcome = f"failed:{type(e).__name__}"
        logger.warning("transfer email best-effort failed: %s", e)

    await append_main_admin_event(
        db,
        commercial_customer_id=commercial_customer_id,
        event_type="transfer_notify",
        actor_user_id=actor["id"],
        outcome="success",
        meta={
            "transfer_id": doc["id"],
            "cabina_outcome": cabina_outcome,
            "email_outcome": email_outcome,
        },
    )

    public = {k: v for k, v in doc.items() if k not in ("_id", "token_hash")}
    # Return raw token only to proposer (accept path); never log it
    public["accept_token"] = raw
    public["cabina_outcome"] = cabina_outcome
    public["email_outcome"] = email_outcome
    return public


async def accept_transfer(
    db,
    *,
    transfer_id: str,
    token: str,
    actor: dict,
) -> dict:
    transfer = await db[TRANSFER_COLL].find_one({"id": transfer_id}, {"_id": 0})
    if not transfer:
        raise HTTPException(status_code=404, detail={"error": "transfer_not_found"})
    transfer = await _expire_if_needed(db, transfer)
    if transfer.get("status") != "pending":
        raise HTTPException(status_code=409, detail={"error": "transfer_not_pending"})
    if actor.get("id") != transfer.get("to_user_id"):
        raise HTTPException(status_code=403, detail={"error": "forbidden"})
    if not user_is_eligible_main_admin(actor):
        raise HTTPException(status_code=403, detail={"error": "account_not_eligible"})
    if _hash_token(token or "") != transfer.get("token_hash"):
        await append_main_admin_event(
            db,
            commercial_customer_id=transfer["commercial_customer_id"],
            event_type="deny_attempt",
            actor_user_id=actor.get("id"),
            outcome="denied",
            reason="invalid_transfer_token",
            meta={"transfer_id": transfer_id},
        )
        raise HTTPException(status_code=403, detail={"error": "invalid_transfer_token"})

    cc_id = transfer["commercial_customer_id"]
    cc = await get_commercial_customer(db, cc_id)
    if not cc or not cc_allows_wallet_mutation(cc):
        raise HTTPException(status_code=403, detail={"error": "cc_not_operable"})
    # Current holder must still match proposal from_user (or null→ops path)
    if cc.get("main_admin_user_id") != transfer.get("from_user_id"):
        raise HTTPException(status_code=409, detail={"error": "main_admin_changed"})

    now = _now_iso()
    prev = cc.get("main_admin_user_id")
    expected_from = transfer.get("from_user_id")

    # D10 — binding first (no transfer "accepted" without coherent CC binding).
    # Filter on current holder prevents concurrent overwrite.
    bound = await db.commercial_customers.find_one_and_update(
        {
            "id": cc_id,
            "main_admin_user_id": expected_from,
        },
        {
            "$set": {
                "main_admin_user_id": actor["id"],
                "main_admin_appointed_at": now,
                "main_admin_appointed_by": actor["id"],
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if not bound:
        raise HTTPException(status_code=409, detail={"error": "main_admin_changed"})

    claimed = await db[TRANSFER_COLL].find_one_and_update(
        {"id": transfer_id, "status": "pending"},
        {"$set": {"status": "accepted", "resolved_at": now}},
        return_document=ReturnDocument.BEFORE,
    )
    if not claimed:
        # Compensate: restore previous holder if we still own the binding.
        await db.commercial_customers.find_one_and_update(
            {"id": cc_id, "main_admin_user_id": actor["id"]},
            {
                "$set": {
                    "main_admin_user_id": expected_from,
                    "main_admin_appointed_at": cc.get("main_admin_appointed_at"),
                    "main_admin_appointed_by": cc.get("main_admin_appointed_by"),
                    "updated_at": now,
                }
            },
        )
        await append_main_admin_event(
            db,
            commercial_customer_id=cc_id,
            event_type="accept_transfer",
            actor_user_id=actor.get("id"),
            outcome="failed",
            reason="transfer_claim_lost_after_bind",
            previous_main_admin_user_id=prev,
            new_main_admin_user_id=actor.get("id"),
            meta={"transfer_id": transfer_id, "compensated": True},
        )
        raise HTTPException(status_code=409, detail={"error": "transfer_not_pending"})

    await append_main_admin_event(
        db,
        commercial_customer_id=cc_id,
        event_type="accept_transfer",
        actor_user_id=actor["id"],
        previous_main_admin_user_id=prev,
        new_main_admin_user_id=actor["id"],
        meta={"transfer_id": transfer_id},
    )
    return {"ok": True, "commercial_customer_id": cc_id, "main_admin_user_id": actor["id"]}


async def cancel_transfer(
    db,
    *,
    transfer_id: str,
    actor: dict,
) -> dict:
    transfer = await db[TRANSFER_COLL].find_one({"id": transfer_id}, {"_id": 0})
    if not transfer:
        raise HTTPException(status_code=404, detail={"error": "transfer_not_found"})
    cc = await get_commercial_customer(db, transfer["commercial_customer_id"])
    is_ops = actor.get("role") == "super_admin"
    is_ma = bool(cc) and cc.get("main_admin_user_id") == actor.get("id")
    if not (is_ops or is_ma):
        raise HTTPException(status_code=403, detail={"error": "forbidden"})
    updated = await db[TRANSFER_COLL].find_one_and_update(
        {"id": transfer_id, "status": "pending"},
        {"$set": {"status": "cancelled", "resolved_at": _now_iso()}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"error": "transfer_not_pending"})
    await append_main_admin_event(
        db,
        commercial_customer_id=transfer["commercial_customer_id"],
        event_type="cancel_transfer",
        actor_user_id=actor.get("id"),
        meta={"transfer_id": transfer_id},
    )
    return {"ok": True, "transfer_id": transfer_id, "status": "cancelled"}
