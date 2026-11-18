"""MC-042 v2 / MC-054 — gate accesso commerciale (cessazione + sospensione giorno 8).

Cessazione: nessun login / nessun accesso autonomo (salvo Super Admin).
Sospensione (opzione B Founder): collaboratori fuori; Main Admin solo billing recovery.
Deroga attiva (MC-056): ripristina operatività finché non scade.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException, Request

logger = logging.getLogger("omnia.billing.commercial_access")

DEROGA_COLL = "commercial_reactivation_derogations"

# Prefissi path (dopo mount /api) ammessi al Main Admin in sospensione
_BILLING_ALLOW_PREFIXES = (
    "/billing/subscription",
    "/billing/plans",
    "/billing/checkout",
    "/billing/portal",
    "/billing/status/",
    "/billing/commercial/main-admin",
    "/auth/me",
    "/auth/logout",
    "/auth/refresh",
    "/notifications",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _parse_iso(raw: Optional[str]) -> Optional[datetime]:
    if not raw or not isinstance(raw, str):
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def normalize_request_path(path: str) -> str:
    p = path or ""
    if p.startswith("/api"):
        p = p[4:] or "/"
    return p


def is_billing_recovery_path(path: str) -> bool:
    p = normalize_request_path(path)
    return any(p == pref.rstrip("/") or p.startswith(pref) for pref in _BILLING_ALLOW_PREFIXES)


async def resolve_cc_for_user(db, user: dict) -> Optional[dict]:
    """CC dell'agency attiva; None se super_admin / senza agency / legacy senza CC."""
    if (user or {}).get("role") == "super_admin":
        return None
    from shared.auth.tenant import optional_agency_id

    agency_id = optional_agency_id(user or {})
    if not agency_id:
        return None
    agency = await db.agencies.find_one(
        {"id": agency_id}, {"commercial_customer_id": 1}
    )
    cc_id = (agency or {}).get("commercial_customer_id")
    if not cc_id:
        return None
    return await db.commercial_customers.find_one({"id": cc_id}, {"_id": 0})


async def find_active_deroga(db, commercial_customer_id: str) -> Optional[dict]:
    if not commercial_customer_id:
        return None
    now = _now()
    rows = await db[DEROGA_COLL].find(
        {
            "commercial_customer_id": commercial_customer_id,
            "status": "active",
        },
        {"_id": 0},
    ).to_list(length=50)
    for d in rows:
        ends = _parse_iso(d.get("ends_at"))
        if ends and ends > now:
            return d
    return None


async def cc_has_active_deroga(db, cc: Optional[dict]) -> bool:
    if not cc:
        return False
    return bool(await find_active_deroga(db, cc.get("id") or ""))


def cc_is_ceased(cc: Optional[dict]) -> bool:
    if not cc:
        return False
    status = cc.get("commercial_status") or ""
    op = cc.get("operational_status") or ""
    return status == "ceased" or op == "closed_readonly"


def cc_is_suspended(cc: Optional[dict]) -> bool:
    if not cc:
        return False
    status = cc.get("commercial_status") or ""
    op = cc.get("operational_status") or ""
    return status == "suspended" or op == "billing_only"


async def assert_user_login_allowed(db, user: dict) -> None:
    """MC-042 v2 — login negato se CC attivo è ceased (password resta in DB, accesso no)."""
    if (user or {}).get("role") == "super_admin":
        return
    cc = await resolve_cc_for_user(db, user)
    if not cc:
        return
    if await cc_has_active_deroga(db, cc):
        return
    if cc_is_ceased(cc):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "commercial_customer_ceased",
                "hint": "Rapporto cessato. Contatta il Super Admin OMNIA via email per documenti.",
            },
        )


async def enforce_commercial_access(db, user: dict, request: Optional[Request] = None) -> None:
    """Gate su ogni request autenticata (get_current_user)."""
    if (user or {}).get("role") == "super_admin":
        return
    cc = await resolve_cc_for_user(db, user)
    if not cc:
        return
    if await cc_has_active_deroga(db, cc):
        return

    if cc_is_ceased(cc):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "commercial_customer_ceased",
                "hint": "Rapporto cessato. Contatta il Super Admin OMNIA via email.",
            },
        )

    if not cc_is_suspended(cc):
        return

    # MC-054 opzione B — sospensione
    path = ""
    if request is not None:
        path = request.url.path or ""

    is_ma = cc.get("main_admin_user_id") == user.get("id")
    if not is_ma:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "commercial_customer_suspended",
                "hint": "Accesso collaboratori sospeso per mancato pagamento. Contatta il Main Admin.",
            },
        )
    if request is not None and not is_billing_recovery_path(path):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "commercial_customer_suspended_billing_only",
                "hint": "In sospensione il Main Admin può solo pagamento, metodo e fatture.",
            },
        )


async def grant_reactivation_deroga(
    db,
    *,
    commercial_customer_id: str,
    actor: dict,
    reason: str,
    amount_due: float,
    duration_hours: int,
) -> dict:
    """MC-056/057 — deroga eccezionale Super Admin."""
    if (actor or {}).get("role") != "super_admin":
        raise HTTPException(status_code=403, detail={"error": "forbidden"})
    reason = (reason or "").strip()
    if len(reason) < 8:
        raise HTTPException(status_code=400, detail={"error": "extraordinary_reason_required"})
    if duration_hours <= 0 or duration_hours > 24 * 90:
        raise HTTPException(status_code=400, detail={"error": "invalid_duration_hours"})
    cc = await db.commercial_customers.find_one({"id": commercial_customer_id}, {"_id": 0})
    if not cc:
        raise HTTPException(status_code=404, detail={"error": "commercial_customer_not_found"})
    if cc_is_ceased(cc):
        raise HTTPException(status_code=400, detail={"error": "cannot_derogate_ceased"})

    starts = _now()
    from datetime import timedelta

    ends = starts + timedelta(hours=int(duration_hours))
    # Chiudi eventuali deroghe attive precedenti su questo CC
    await db[DEROGA_COLL].update_many(
        {"commercial_customer_id": commercial_customer_id, "status": "active"},
        {"$set": {"status": "superseded", "resolved_at": _now_iso()}},
    )
    doc = {
        "id": str(uuid4()),
        "commercial_customer_id": commercial_customer_id,
        "actor_user_id": actor.get("id"),
        "actor_email": actor.get("email"),
        "reason": reason,
        "amount_due": float(amount_due),
        "duration_hours": int(duration_hours),
        "starts_at": starts.isoformat(),
        "ends_at": ends.isoformat(),
        "status": "active",
        "outcome": "granted",
        "created_at": _now_iso(),
        "resolved_at": None,
    }
    await db[DEROGA_COLL].insert_one(doc)

    # Email cliente (Main Admin) — best effort (MC-058)
    try:
        ma_id = cc.get("main_admin_user_id")
        if ma_id:
            ma = await db.users.find_one({"id": ma_id}, {"email": 1})
            to_email = (ma or {}).get("email")
            if to_email:
                from shared.email import send_email

                await send_email(
                    to=to_email,
                    template="agency_pending",
                    subject="OMNIA — riattivazione eccezionale concessa",
                    variables={
                        "agency_name": cc.get("legal_name") or "CommercialCustomer",
                        "amount_due": str(amount_due),
                        "ends_at": ends.isoformat(),
                        "duration_hours": str(duration_hours),
                    },
                )
    except Exception as exc:  # noqa: BLE001
        logger.warning("deroga email failed cc=%s: %s", commercial_customer_id, exc)

    return {k: v for k, v in doc.items() if k != "_id"}


async def _notify_deroga_event(
    db, *, deroga: dict, kind: str, subject: str
) -> None:
    """Best-effort email cliente (+ ops note in log)."""
    try:
        from shared.email import send_email

        cc_id = deroga.get("commercial_customer_id")
        cc = await db.commercial_customers.find_one({"id": cc_id}, {"_id": 0}) if cc_id else None
        to_email = None
        if cc and cc.get("main_admin_user_id"):
            ma = await db.users.find_one(
                {"id": cc["main_admin_user_id"]}, {"email": 1}
            )
            to_email = (ma or {}).get("email")
        if to_email:
            await send_email(
                to=to_email,
                template="agency_pending",
                subject=subject,
                variables={
                    "agency_name": (cc or {}).get("legal_name") or "CommercialCustomer",
                    "amount_due": str(deroga.get("amount_due") or ""),
                    "ends_at": str(deroga.get("ends_at") or ""),
                    "kind": kind,
                },
            )
        logger.info(
            "deroga notify kind=%s cc=%s actor=%s",
            kind,
            cc_id,
            deroga.get("actor_email"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("deroga notify failed kind=%s: %s", kind, exc)


async def expire_due_deroghe(db) -> dict:
    """MC-057/058 — a scadenza senza saldo: chiudi deroga (cliente resta/torna sospeso)."""
    now = _now()
    rows = await db[DEROGA_COLL].find({"status": "active"}, {"_id": 0}).to_list(
        length=10_000
    )
    expired = 0
    for d in rows:
        ends = _parse_iso(d.get("ends_at"))
        if not ends or ends > now:
            continue
        await db[DEROGA_COLL].update_one(
            {"id": d["id"], "status": "active"},
            {
                "$set": {
                    "status": "expired",
                    "outcome": "expired_unpaid",
                    "resolved_at": _now_iso(),
                }
            },
        )
        expired += 1
        cc_id = d.get("commercial_customer_id")
        if cc_id:
            await db.commercial_customers.update_one(
                {"id": cc_id, "commercial_status": {"$ne": "ceased"}},
                {
                    "$set": {
                        "commercial_status": "suspended",
                        "operational_status": "billing_only",
                        "updated_at": _now_iso(),
                    }
                },
            )
        await _notify_deroga_event(
            db,
            deroga=d,
            kind="expired_unpaid",
            subject="OMNIA — deroga scaduta, accesso di nuovo sospeso",
        )
    return {"scanned": len(rows), "expired": expired}


async def remind_deroghe_expiring_soon(db, *, within_hours: int = 48) -> dict:
    """MC-058 — promemoria Super Admin ~48h prima della scadenza."""
    from datetime import timedelta

    now = _now()
    horizon = now + timedelta(hours=int(within_hours))
    rows = await db[DEROGA_COLL].find({"status": "active"}, {"_id": 0}).to_list(
        length=10_000
    )
    reminded = 0
    for d in rows:
        if d.get("ops_reminder_sent_at"):
            continue
        ends = _parse_iso(d.get("ends_at"))
        if not ends or ends > horizon or ends <= now:
            continue
        ops_email = d.get("actor_email")
        if ops_email:
            try:
                from shared.email import send_email

                await send_email(
                    to=ops_email,
                    template="agency_pending",
                    subject="OMNIA — deroga in scadenza entro 48h",
                    variables={
                        "agency_name": d.get("commercial_customer_id") or "",
                        "ends_at": d.get("ends_at") or "",
                        "amount_due": str(d.get("amount_due") or ""),
                    },
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("deroga ops reminder failed: %s", exc)
        await db[DEROGA_COLL].update_one(
            {"id": d["id"]},
            {"$set": {"ops_reminder_sent_at": _now_iso()}},
        )
        reminded += 1
    return {"scanned": len(rows), "reminded": reminded}


async def set_commercial_status(
    db,
    commercial_customer_id: str,
    *,
    commercial_status: str,
    actor_user_id: Optional[str] = None,
    reason: str = "",
) -> dict:
    """Imposta commercial_status + operational envelope (ops / job giorno 8)."""
    from shared.models.commercial_customer import operational_status_for

    cc = await db.commercial_customers.find_one(
        {"id": commercial_customer_id}, {"_id": 0}
    )
    if not cc:
        raise HTTPException(status_code=404, detail={"error": "commercial_customer_not_found"})
    op = operational_status_for(commercial_status)  # type: ignore[arg-type]
    fields: dict[str, Any] = {
        "commercial_status": commercial_status,
        "operational_status": op,
        "updated_at": _now_iso(),
    }
    if commercial_status == "ceased":
        fields["ceased_at"] = _now_iso()
    if commercial_status == "suspended":
        fields["suspended_at"] = _now_iso()
    if reason:
        fields["status_reason"] = reason[:500]
    if actor_user_id:
        fields["status_changed_by"] = actor_user_id
    await db.commercial_customers.update_one(
        {"id": commercial_customer_id}, {"$set": fields}
    )
    return {**(cc or {}), **fields}


async def apply_day8_suspensions(db, *, grace_days: int = 8) -> dict:
    """MC-054 — dopo N giorni in past_due → suspended / billing_only.

    Usa ``subscriptions.status == past_due`` e ``payment_failed_at`` (o updated_at).
    """
    from datetime import timedelta

    cutoff = _now() - timedelta(days=int(grace_days))
    subs = await db.subscriptions.find(
        {"status": "past_due"},
        {"_id": 0},
    ).to_list(length=10_000)
    applied = 0
    scanned = 0
    for sub in subs:
        scanned += 1
        failed_at = _parse_iso(sub.get("payment_failed_at")) or _parse_iso(
            sub.get("updated_at")
        )
        if not failed_at or failed_at > cutoff:
            continue
        agency_id = sub.get("agency_id")
        cc_id = sub.get("commercial_customer_id")
        if not cc_id and agency_id:
            agency = await db.agencies.find_one(
                {"id": agency_id}, {"commercial_customer_id": 1}
            )
            cc_id = (agency or {}).get("commercial_customer_id")
        if not cc_id:
            continue
        cc = await db.commercial_customers.find_one({"id": cc_id}, {"_id": 0})
        if not cc or cc_is_ceased(cc):
            continue
        if (cc.get("commercial_status") or "") == "suspended":
            continue
        await set_commercial_status(
            db,
            cc_id,
            commercial_status="suspended",
            reason=f"day{grace_days}_past_due",
        )
        applied += 1
    return {"scanned": scanned, "applied": applied, "grace_days": grace_days}


async def reactivate_cc_on_full_payment(db, commercial_customer_id: str) -> dict:
    """MC-055 — saldo pieno / invoice.paid → riattivazione automatica."""
    if not commercial_customer_id:
        return {"ok": False, "skipped": "no_cc"}
    cc = await db.commercial_customers.find_one(
        {"id": commercial_customer_id}, {"_id": 0}
    )
    if not cc:
        return {"ok": False, "skipped": "cc_not_found"}
    if cc_is_ceased(cc):
        return {"ok": False, "skipped": "ceased"}
    status = cc.get("commercial_status") or ""
    if status not in ("suspended", "grace", "cancel_pending"):
        # already active-like
        if status == "active":
            return {"ok": True, "skipped": "already_active"}
    await db.commercial_customers.update_one(
        {"id": commercial_customer_id},
        {
            "$set": {
                "commercial_status": "active",
                "operational_status": "full",
                "updated_at": _now_iso(),
            }
        },
    )
    await db[DEROGA_COLL].update_many(
        {"commercial_customer_id": commercial_customer_id, "status": "active"},
        {
            "$set": {
                "status": "closed_paid",
                "outcome": "reactivated_on_payment",
                "resolved_at": _now_iso(),
            }
        },
    )
    return {"ok": True, "commercial_customer_id": commercial_customer_id}
