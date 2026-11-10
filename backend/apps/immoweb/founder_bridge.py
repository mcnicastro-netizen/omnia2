"""Cabina di regia Super Admin — archivi piattaforma (non CRM tenant).

Moduli: ingresso, clienti (agenzie+B2C), fornitori, API keys, listino.
I valori secret non vengono mai restituiti — solo presenza/circuiti.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from shared.auth.dependencies import require_roles
from shared.db.connection import Database

logger = logging.getLogger("omnia.founder_bridge")
router = APIRouter(prefix="/ops", tags=["founder-bridge"])

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k != "_id"}


# -------------------- INGRESSO --------------------


@router.get("/bridge/summary")
async def bridge_summary(user: dict = Depends(require_roles("super_admin"))) -> Dict[str, Any]:
    """KPI cabina: coda, tenant, API, alert, backup."""
    db = Database.get()
    pending = await db.agencies.count_documents({"activation_status": "pending"})
    agencies = await db.agencies.count_documents({})
    active = await db.agencies.count_documents(
        {"$or": [{"activation_status": "active"}, {"activation_status": {"$exists": False}}]}
    )
    b2c = await db.users.count_documents({"account_type": "b2c"})
    keys_active = await db.api_keys.count_documents({"is_active": True})
    keys_total = await db.api_keys.count_documents({})
    unacked = await db.ops_alerts.count_documents({"acked": False})

    bak: Dict[str, Any] = {}
    try:
        from apps.immoweb.backup_job import read_latest_backup_health

        bak = read_latest_backup_health() or {}
    except Exception:  # noqa: BLE001
        logger.exception("backup health for bridge summary")

    return {
        "ok": True,
        "generated_at": _now(),
        "activation_pending": pending,
        "agencies_total": agencies,
        "agencies_active": active,
        "b2c_users": b2c,
        "api_keys_active": keys_active,
        "api_keys_total": keys_total,
        "alerts_unacked": unacked,
        "backup": {
            "status": bak.get("status"),
            "day": bak.get("day"),
            "created_at": bak.get("created_at"),
        },
    }


# -------------------- CLIENTI (agenzie) --------------------


@router.get("/bridge/tenants")
async def bridge_tenants(
    q: str = "",
    status: str = "",
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    db = Database.get()
    flt: Dict[str, Any] = {}
    if status == "pending":
        flt["activation_status"] = "pending"
    elif status == "active":
        flt["$or"] = [
            {"activation_status": "active"},
            {"activation_status": {"$exists": False}},
        ]
    elif status == "suspended":
        flt["activation_status"] = "suspended"

    cur = db.agencies.find(flt, {"_id": 0}).sort("created_at", -1)
    docs = await cur.to_list(length=500)
    qn = (q or "").strip().lower()
    if qn:
        docs = [
            d
            for d in docs
            if qn in (d.get("display_name") or "").lower()
            or qn in (d.get("slug") or "").lower()
            or qn in (d.get("id") or "").lower()
        ]

    owner_ids = [d.get("owner_id") for d in docs if d.get("owner_id")]
    owners: Dict[str, dict] = {}
    if owner_ids:
        ocur = db.users.find(
            {"id": {"$in": owner_ids}},
            {"_id": 0, "id": 1, "email": 1, "name": 1, "phone": 1},
        )
        for o in await ocur.to_list(length=len(owner_ids) + 10):
            owners[o["id"]] = o

    items = []
    for d in docs[:limit]:
        oid = d.get("owner_id")
        owner = owners.get(oid) or {}
        aid = d.get("id")
        n_clients = await db.clients.count_documents({"agency_id": aid, "trashed_at": {"$exists": False}})
        n_props = await db.properties.count_documents(
            {"agency_id": aid, "trashed_at": {"$exists": False}}
        )
        n_keys = await db.api_keys.count_documents({"agency_id": aid, "is_active": True})
        items.append(
            {
                "id": aid,
                "slug": d.get("slug"),
                "display_name": d.get("display_name"),
                "plan": d.get("plan") or d.get("billing_assisted_tier"),
                "activation_status": d.get("activation_status") or "active",
                "is_active": d.get("is_active", True),
                "credits_balance": d.get("credits_balance"),
                "created_at": d.get("created_at"),
                "owner_email": owner.get("email"),
                "owner_name": owner.get("name"),
                "owner_phone": owner.get("phone"),
                "contact": d.get("contact") or {},
                "counts": {
                    "clients": n_clients,
                    "properties": n_props,
                    "api_keys_active": n_keys,
                },
            }
        )
    return {"ok": True, "count": len(items), "items": items, "q": q, "status": status}


@router.get("/bridge/tenants/{agency_id}")
async def bridge_tenant_detail(
    agency_id: str,
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    db = Database.get()
    agency = await db.agencies.find_one({"id": agency_id}, {"_id": 0})
    if not agency:
        raise HTTPException(404, detail="agency_not_found")

    owner = None
    if agency.get("owner_id"):
        owner = await db.users.find_one(
            {"id": agency["owner_id"]},
            {"_id": 0, "password_hash": 0},
        )

    members = await db.users.find(
        {"agency_ids": agency_id},
        {"_id": 0, "password_hash": 0},
    ).to_list(length=100)

    clients = await db.clients.find(
        {"agency_id": agency_id, "trashed_at": {"$exists": False}},
        {"_id": 0},
    ).sort("created_at", -1).to_list(length=100)

    props = await db.properties.find(
        {"agency_id": agency_id, "trashed_at": {"$exists": False}},
        {
            "_id": 0,
            "id": 1,
            "title": 1,
            "status": 1,
            "reference_code": 1,
            "city": 1,
            "price": 1,
            "created_at": 1,
        },
    ).sort("created_at", -1).to_list(length=50)

    keys = await db.api_keys.find(
        {"agency_id": agency_id},
        {"_id": 0, "key_hash": 0},
    ).sort("created_at", -1).to_list(length=50)

    return {
        "ok": True,
        "agency": agency,
        "owner": owner,
        "members": members,
        "clients": clients,
        "properties": props,
        "api_keys": keys,
        "counts": {
            "members": len(members),
            "clients": len(clients),
            "properties": len(props),
            "api_keys": len(keys),
        },
    }


@router.get("/bridge/b2c-users")
async def bridge_b2c_users(
    q: str = "",
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    db = Database.get()
    flt: Dict[str, Any] = {"account_type": "b2c"}
    qn = (q or "").strip()
    if qn:
        safe = re.escape(qn[:80])
        flt["$or"] = [
            {"email": {"$regex": safe, "$options": "i"}},
            {"name": {"$regex": safe, "$options": "i"}},
            {"client_code": {"$regex": safe, "$options": "i"}},
        ]
    docs = (
        await db.users.find(flt, {"_id": 0, "password_hash": 0})
        .sort("created_at", -1)
        .limit(limit)
        .to_list(length=limit)
    )
    return {"ok": True, "count": len(docs), "items": docs, "q": q}


# -------------------- FORNITORI --------------------

_PROVIDER_ENV = [
    ("resend", "RESEND_API_KEY", "Email transazionale"),
    ("fal", "FAL_KEY", "Staging / video AI"),
    ("gemini", "GEMINI_API_KEY", "LLM / HAL / safety"),
    ("stripe", "STRIPE_SECRET_KEY", "Pagamenti"),
    ("openai", "OPENAI_API_KEY", "LLM fallback"),
    ("tavily", "TAVILY_API_KEY", "Web search Legal"),
    ("mongodb", "MONGO_URL", "Database"),
]


@router.get("/bridge/providers")
async def bridge_providers(user: dict = Depends(require_roles("super_admin"))) -> Dict[str, Any]:
    """Stato fornitori esterni: presenza chiave + circuit + kill-switch (mai il valore)."""
    from shared.ops.provider_flags import list_flags

    circuits: Dict[str, Any] = {}
    try:
        from shared.security.circuit import snapshot

        circuits = snapshot() or {}
    except Exception:  # noqa: BLE001
        logger.exception("circuit snapshot")

    flags = {f["id"]: f for f in await list_flags()}

    items = []
    for key, env_name, label in _PROVIDER_ENV:
        raw = (os.environ.get(env_name) or "").strip()
        circ = circuits.get(key) or circuits.get(env_name.lower()) or {}
        fl = flags.get(key) or {}
        items.append(
            {
                "id": key,
                "label": label,
                "env": env_name,
                "configured": bool(raw),
                "hint": f"{raw[:4]}…" if len(raw) > 8 else ("set" if raw else "missing"),
                "circuit_open": bool(circ.get("open")),
                "circuit_failures": circ.get("failures"),
                "last_error": (circ.get("last_error") or "")[:120] or None,
                "killed": bool(fl.get("killed")),
                "held": bool(fl.get("held") or circ.get("held")),
                "kill_note": fl.get("note") or "",
                "kill_updated_at": fl.get("updated_at"),
            }
        )

    stripe_on = (os.environ.get("STRIPE_ENABLED") or "").strip().lower() == "true"
    return {
        "ok": True,
        "generated_at": _now(),
        "stripe_enabled": stripe_on,
        "stripe_mode": os.environ.get("STRIPE_MODE") or "test",
        "items": items,
        "circuits": circuits,
    }


class ProviderKillBody(BaseModel):
    note: str = Field(default="", max_length=500)


@router.post("/bridge/providers/{provider_id}/kill")
async def bridge_provider_kill(
    provider_id: str,
    body: ProviderKillBody = ProviderKillBody(),
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    from shared.ops.provider_flags import set_killed

    try:
        doc = await set_killed(provider_id, killed=True, user=user, note=body.note)
    except ValueError:
        raise HTTPException(404, detail="unknown_provider") from None
    return {"ok": True, "flag": doc}


@router.post("/bridge/providers/{provider_id}/revive")
async def bridge_provider_revive(
    provider_id: str,
    body: ProviderKillBody = ProviderKillBody(),
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    from shared.ops.provider_flags import set_killed

    try:
        doc = await set_killed(provider_id, killed=False, user=user, note=body.note)
    except ValueError:
        raise HTTPException(404, detail="unknown_provider") from None
    return {"ok": True, "flag": doc}


# -------------------- API CLIENTI (piattaforma) --------------------


@router.get("/bridge/api-keys")
async def bridge_api_keys(
    q: str = "",
    active_only: bool = False,
    limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    db = Database.get()
    flt: Dict[str, Any] = {}
    if active_only:
        flt["is_active"] = True
    docs = await db.api_keys.find(flt, {"_id": 0, "key_hash": 0}).sort("created_at", -1).to_list(
        length=limit
    )
    agency_ids = list({d.get("agency_id") for d in docs if d.get("agency_id")})
    names: Dict[str, str] = {}
    if agency_ids:
        for a in await db.agencies.find(
            {"id": {"$in": agency_ids}}, {"_id": 0, "id": 1, "display_name": 1, "slug": 1}
        ).to_list(length=len(agency_ids) + 5):
            names[a["id"]] = a.get("display_name") or a.get("slug") or a["id"]

    qn = (q or "").strip().lower()
    items = []
    for d in docs:
        row = {
            **d,
            "agency_name": names.get(d.get("agency_id") or "", "—"),
        }
        if qn:
            blob = " ".join(
                [
                    str(row.get("name") or ""),
                    str(row.get("key_prefix") or ""),
                    str(row.get("agency_name") or ""),
                    str(row.get("agency_id") or ""),
                ]
            ).lower()
            if qn not in blob:
                continue
        items.append(row)
    return {"ok": True, "count": len(items), "items": items}


@router.post("/bridge/api-keys/{key_id}/revoke")
async def bridge_revoke_key(
    key_id: str,
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    db = Database.get()
    now = _now()
    r = await db.api_keys.update_one(
        {"id": key_id},
        {"$set": {"is_active": False, "revoked_at": now, "updated_at": now, "revoked_by": user.get("id")}},
    )
    if r.matched_count == 0:
        raise HTTPException(404, detail="api_key_not_found")
    logger.warning("bridge revoke api_key id=%s by=%s", key_id, user.get("email"))
    return {"ok": True, "id": key_id, "revoked_at": now}


@router.post("/bridge/api-keys/{key_id}/rotate")
async def bridge_rotate_key(
    key_id: str,
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    """Revoca e riesce una chiave (plaintext una sola volta)."""
    from shared.auth.api_key import generate_plaintext_key, hash_key, prefix_of
    from shared.models.api_key import ApiKeyInDB

    db = Database.get()
    old = await db.api_keys.find_one({"id": key_id})
    if not old:
        raise HTTPException(404, detail="api_key_not_found")
    if not old.get("is_active", True):
        raise HTTPException(400, detail="api_key_already_revoked")

    now = _now()
    await db.api_keys.update_one(
        {"id": key_id},
        {
            "$set": {
                "is_active": False,
                "revoked_at": now,
                "updated_at": now,
                "rotated": True,
                "revoked_by": user.get("id"),
            }
        },
    )
    plaintext = generate_plaintext_key()
    doc = ApiKeyInDB(
        agency_id=old["agency_id"],
        group_id=old.get("group_id"),
        name=f"{old.get('name') or 'key'} (rotated)",
        key_hash=hash_key(plaintext),
        key_prefix=prefix_of(plaintext),
        credits_balance=int(old.get("credits_balance") or 0),
        partner_id=old.get("partner_id"),
        allowed_origins=list(old.get("allowed_origins") or []),
    ).model_dump()
    doc["rotated_from"] = key_id
    doc["issued_by"] = user.get("id")
    await db.api_keys.insert_one(doc)
    logger.warning(
        "bridge rotate api_key old=%s new=%s by=%s", key_id, doc["id"], user.get("email")
    )
    public = {k: v for k, v in doc.items() if k not in ("_id", "key_hash")}
    return {"ok": True, "key": plaintext, "api_key": public}


# -------------------- LISTINO --------------------


class B2CPricePatch(BaseModel):
    price_eur: float = Field(gt=0, le=9999)
    note: str = Field(default="", max_length=500)


@router.get("/bridge/catalog")
async def bridge_catalog(user: dict = Depends(require_roles("super_admin"))) -> Dict[str, Any]:
    from apps.billing.plans import LAUNCH_PLANS, POST_TRACTION_PLANS, CREDIT_PACKAGES, CREDIT_COSTS
    from apps.billing.b2c_products import B2C_ONE_SHOT_PRODUCTS

    db = Database.get()
    overrides = {}
    try:
        docs = await db.pricing_overrides.find({}, {"_id": 0}).to_list(length=500)
        overrides = {d["key"]: d for d in docs if d.get("key")}
    except Exception:  # noqa: BLE001
        overrides = {}

    b2c = []
    for k, p in B2C_ONE_SHOT_PRODUCTS.items():
        ov = overrides.get(k) or {}
        row = dict(p)
        row["price_eur_effective"] = float(ov.get("price_eur") if ov.get("price_eur") is not None else p.get("price_eur") or 0)
        row["override"] = bool(ov.get("price_eur") is not None)
        row["override_note"] = ov.get("note")
        row["override_at"] = ov.get("updated_at")
        b2c.append(row)

    def _b2b_row(phase: str, tier: str, plan) -> dict:
        key = f"b2b_{phase}_{tier}"
        ov = overrides.get(key) or {}
        base = plan.model_dump()
        pm = float(ov.get("price_monthly") if ov.get("price_monthly") is not None else base["price_monthly"])
        py = float(ov.get("price_yearly") if ov.get("price_yearly") is not None else base["price_yearly"])
        cr = int(ov.get("credits_included_monthly") if ov.get("credits_included_monthly") is not None else base["credits_included_monthly"])
        return {
            "tier": tier,
            "phase": phase,
            **base,
            "price_monthly": pm,
            "price_yearly": py,
            "credits_included_monthly": cr,
            "override": bool(ov),
            "override_key": key,
            "override_note": ov.get("note"),
            "stripe_lookup_monthly": f"{tier}_monthly",
            "stripe_lookup_yearly": f"{tier}_yearly",
        }

    plans_launch = [_b2b_row("founders", t, p) for t, p in LAUNCH_PLANS.items()]
    plans_std = [_b2b_row("standard", t, p) for t, p in POST_TRACTION_PLANS.items()]

    return {
        "ok": True,
        "b2b_founders": plans_launch,
        "b2b_standard": plans_std,
        "credit_packages": [p.model_dump() for p in CREDIT_PACKAGES],
        "credit_costs": CREDIT_COSTS,
        "b2c": b2c,
        "note": (
            "Override B2B/B2C in Mongo (pricing_overrides). "
            "Patch B2B può sincronizzare Stripe lookup_key {tier}_monthly/yearly."
        ),
    }


@router.patch("/bridge/catalog/b2c/{product_key}")
async def bridge_patch_b2c_price(
    product_key: str,
    body: B2CPricePatch,
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    from apps.billing.b2c_products import B2C_ONE_SHOT_PRODUCTS

    if product_key not in B2C_ONE_SHOT_PRODUCTS:
        raise HTTPException(404, detail="product_not_found")
    db = Database.get()
    now = _now()
    doc = {
        "key": product_key,
        "price_eur": float(body.price_eur),
        "note": (body.note or "").strip(),
        "updated_at": now,
        "updated_by": user.get("id"),
        "updated_by_email": user.get("email"),
    }
    await db.pricing_overrides.update_one({"key": product_key}, {"$set": doc}, upsert=True)
    logger.warning(
        "b2c price override key=%s price=%s by=%s",
        product_key,
        body.price_eur,
        user.get("email"),
    )
    return {"ok": True, "override": doc}


class B2BPlanPatch(BaseModel):
    price_monthly: Optional[float] = Field(default=None, gt=0, le=99999)
    price_yearly: Optional[float] = Field(default=None, gt=0, le=999999)
    credits_included_monthly: Optional[int] = Field(default=None, ge=0, le=1_000_000)
    note: str = Field(default="", max_length=500)
    sync_stripe: bool = True


@router.patch("/bridge/catalog/b2b/{phase}/{tier}")
async def bridge_patch_b2b_plan(
    phase: str,
    tier: str,
    body: B2BPlanPatch,
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    """Override prezzi piano B2B + sync Stripe lookup_key (best-effort)."""
    from apps.billing.plans import LAUNCH_PLANS, POST_TRACTION_PLANS

    phase_n = (phase or "").strip().lower()
    tier_n = (tier or "").strip().lower()
    catalog = LAUNCH_PLANS if phase_n in ("founders", "launch") else POST_TRACTION_PLANS
    if phase_n not in ("founders", "launch", "standard", "post_traction"):
        raise HTTPException(400, detail="phase_invalid")
    if tier_n not in catalog:
        raise HTTPException(404, detail="tier_not_found")
    plan = catalog[tier_n]
    key = f"b2b_{'founders' if phase_n in ('founders', 'launch') else 'standard'}_{tier_n}"
    db = Database.get()
    now = _now()
    doc = {
        "key": key,
        "phase": "founders" if phase_n in ("founders", "launch") else "standard",
        "tier": tier_n,
        "price_monthly": float(
            body.price_monthly if body.price_monthly is not None else plan.price_monthly
        ),
        "price_yearly": float(
            body.price_yearly if body.price_yearly is not None else plan.price_yearly
        ),
        "credits_included_monthly": int(
            body.credits_included_monthly
            if body.credits_included_monthly is not None
            else plan.credits_included_monthly
        ),
        "note": (body.note or "").strip(),
        "updated_at": now,
        "updated_by": user.get("id"),
        "updated_by_email": user.get("email"),
    }
    await db.pricing_overrides.update_one({"key": key}, {"$set": doc}, upsert=True)

    stripe_report: Dict[str, Any] = {"skipped": True}
    if body.sync_stripe:
        stripe_report = _sync_b2b_stripe_prices(
            tier_n, doc["price_monthly"], doc["price_yearly"]
        )

    logger.warning(
        "b2b plan override key=%s monthly=%s yearly=%s stripe=%s by=%s",
        key,
        doc["price_monthly"],
        doc["price_yearly"],
        stripe_report.get("ok"),
        user.get("email"),
    )
    return {"ok": True, "override": doc, "stripe": stripe_report}


def _sync_b2b_stripe_prices(tier: str, monthly: float, yearly: float) -> Dict[str, Any]:
    """Crea/ruota Price Stripe su lookup {tier}_monthly / {tier}_yearly."""
    if (os.environ.get("STRIPE_ENABLED") or "").strip().lower() != "true":
        return {"ok": False, "skipped": True, "reason": "stripe_disabled"}
    key = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    if not key:
        return {"ok": False, "skipped": True, "reason": "no_stripe_key"}
    try:
        import stripe
        from apps.billing.setup_stripe import _ensure_price, _get_or_create_product

        stripe.api_key = key
        product = _get_or_create_product(f"plan_{tier}", f"OMNIA {tier.title()}")
        m = _ensure_price(product.id, f"{tier}_monthly", monthly, interval="month")
        y = _ensure_price(product.id, f"{tier}_yearly", yearly, interval="year")
        return {
            "ok": True,
            "monthly_price_id": getattr(m, "id", None),
            "yearly_price_id": getattr(y, "id", None),
        }
    except Exception as e:  # noqa: BLE001
        logger.exception("stripe b2b sync failed tier=%s", tier)
        return {"ok": False, "error": str(e)[:200]}


# -------------------- IMPERSONATION CRM --------------------


class ImpersonateBody(BaseModel):
    agency_id: str = Field(min_length=8, max_length=80)


@router.post("/bridge/impersonate")
async def bridge_impersonate(
    body: ImpersonateBody,
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    """Entra nel CRM di un'agenzia in modo esplicito (D-153-safe)."""
    db = Database.get()
    aid = body.agency_id.strip()
    agency = await db.agencies.find_one({"id": aid}, {"_id": 0, "id": 1, "display_name": 1, "slug": 1})
    if not agency:
        raise HTTPException(404, detail="agency_not_found")

    prev_ids = list(user.get("agency_ids") or [])
    prev_active = user.get("active_agency_id")
    stamp = {
        "agency_id": aid,
        "agency_name": agency.get("display_name") or agency.get("slug"),
        "started_at": _now(),
        "previous_agency_ids": prev_ids,
        "previous_active_agency_id": prev_active,
    }
    new_ids = list(dict.fromkeys(prev_ids + [aid]))
    await db.users.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "agency_ids": new_ids,
                "active_agency_id": aid,
                "ops_impersonation": stamp,
                "updated_at": _now(),
            }
        },
    )
    logger.warning(
        "impersonate start by=%s agency=%s slug=%s",
        user.get("email"),
        aid,
        agency.get("slug"),
    )
    return {"ok": True, "impersonation": stamp, "redirect": "/app/dashboard"}


@router.post("/bridge/impersonate/exit")
async def bridge_impersonate_exit(
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    """Esce dall'impersonation e ripristina membership precedente (di solito vuota)."""
    db = Database.get()
    full = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not full:
        raise HTTPException(404, detail="user_not_found")
    stamp = full.get("ops_impersonation") or {}
    prev_ids = list(stamp.get("previous_agency_ids") or [])
    prev_active = stamp.get("previous_active_agency_id")
    # Se non c'era stamp, stacca tutto (allinea D-153)
    await db.users.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "agency_ids": prev_ids,
                "active_agency_id": prev_active if prev_active in prev_ids else None,
                "updated_at": _now(),
            },
            "$unset": {"ops_impersonation": ""},
        },
    )
    logger.warning("impersonate exit by=%s was=%s", user.get("email"), stamp.get("agency_id"))
    return {"ok": True, "restored_agency_ids": prev_ids, "redirect": "/app/ops"}


@router.get("/bridge/impersonate/status")
async def bridge_impersonate_status(
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    db = Database.get()
    full = await db.users.find_one({"id": user["id"]}, {"_id": 0, "ops_impersonation": 1})
    return {"ok": True, "impersonation": (full or {}).get("ops_impersonation")}


# -------------------- GDPR ERASE (cabina) --------------------


class EraseUserBody(BaseModel):
    confirm: str = Field(min_length=3, max_length=40)


@router.post("/bridge/users/{user_id}/erase")
async def bridge_erase_user(
    user_id: str,
    body: EraseUserBody,
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    """GDPR erase assistito (stesso motore di POST /auth/me/erase)."""
    if (body.confirm or "").strip() != "CANCELLA_UTENTE":
        raise HTTPException(
            400,
            detail={"error": "confirm_required", "hint": "Passa confirm=CANCELLA_UTENTE"},
        )
    if user_id == user.get("id"):
        raise HTTPException(400, detail="cannot_erase_self_via_ops")
    db = Database.get()
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(404, detail="user_not_found")
    if target.get("role") == "super_admin":
        raise HTTPException(403, detail="cannot_erase_super_admin")
    from shared.privacy.erasure import erase_user_data

    report = await erase_user_data(target)
    logger.warning(
        "ops erase user target=%s by=%s",
        target.get("email"),
        user.get("email"),
    )
    return {"ok": True, "status": "erased", "report": report}


class OffboardAgencyBody(BaseModel):
    confirm: str = Field(min_length=3, max_length=40)
    erase_members: bool = False


@router.post("/bridge/tenants/{agency_id}/offboard")
async def bridge_offboard_agency(
    agency_id: str,
    body: OffboardAgencyBody,
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    """Chiude agenzia: wipe CRM + purge shell (force). Opzionale erase membri."""
    if (body.confirm or "").strip() != "CHIUDI_AGENZIA":
        raise HTTPException(
            400,
            detail={"error": "confirm_required", "hint": "Passa confirm=CHIUDI_AGENZIA"},
        )
    db = Database.get()
    agency = await db.agencies.find_one({"id": agency_id}, {"_id": 0})
    if not agency:
        raise HTTPException(404, detail="agency_not_found")

    from apps.immoweb.demo_retire import purge_agency_shell, wipe_agency_crm_data
    from shared.privacy.erasure import erase_user_data

    wipe = await wipe_agency_crm_data(db, agency_id)
    members = await db.users.find(
        {"agency_ids": agency_id},
        {"_id": 0, "id": 1, "email": 1, "role": 1},
    ).to_list(length=200)
    erased = []
    if body.erase_members:
        for m in members:
            if m.get("role") == "super_admin" or m.get("id") == user.get("id"):
                continue
            full = await db.users.find_one({"id": m["id"]}, {"_id": 0})
            if full:
                await erase_user_data(full)
                erased.append(m.get("id"))

    shell = await purge_agency_shell(db, slug=agency.get("slug") or "", force=True)
    logger.warning(
        "ops offboard agency=%s slug=%s erase_members=%s by=%s",
        agency_id,
        agency.get("slug"),
        len(erased),
        user.get("email"),
    )
    return {
        "ok": True,
        "wipe": wipe,
        "shell": shell,
        "members_erased": erased,
        "members_seen": len(members),
    }
