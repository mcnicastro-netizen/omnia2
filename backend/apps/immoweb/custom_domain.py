"""OMNIA — Custom Domain workflow (M2.S6, D-022).

Allows each agency to map its own domain (e.g. www.nicastroimmobiliare.it) to
its public OMNIA themed site. Flow:

  1) Agency POSTs the domain → backend generates a random TXT verification
     token + asks the agency to add 2 DNS records on its registrar (Aruba etc.).
  2) Agency adds the records, calls POST /verify → backend resolves DNS,
     checks both TXT (anti-takeover) and CNAME (or A) → marks `verified`.
  3) Backend hostname middleware (see middleware.py) maps `Host: <domain>` →
     agency slug → serves the themed public site (/api/p/{slug}/).
  4) Admin (super_admin) is emailed and sees a Pending list in a dedicated
     endpoint so they can add the domain manually on the Emergent panel.

Endpoints (mounted under /app/website):
  POST   /domain/request          — start workflow + generate TXT token
  POST   /domain/verify           — verify DNS records + activate
  DELETE /domain                  — remove the custom domain
  GET    /domain                  — read current state (for the UI)
  GET    /domain/admin/pending    — super_admin: list of pending requests
"""
import logging
import os
import re
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user, require_roles
from shared.db.connection import Database

logger = logging.getLogger("omnia.custom_domain")
router = APIRouter(prefix="/website", tags=["website"])


# ============================================================
# Config
# ============================================================

# Sub-domain the agency must CNAME to. This is the "edge" of OMNIA reserved
# to custom-domain hosting. Configured via env so it can differ in
# preview/production.
CNAME_TARGET = os.environ.get("OMNIA_CUSTOM_DOMAIN_CNAME_TARGET",
                              "agencies.omniarealestateecosystem.it")

# The TXT record host = "_omnia-challenge.<domain>"
TXT_RECORD_PREFIX = "_omnia-challenge"

# Reserved suffixes never allowed as custom domain (must not collide with us)
RESERVED_SUFFIXES = (
    "omniarealestateecosystem.it",
    "emergent.host",
    "emergentagent.com",
)

DOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?)+$")


def _normalize_domain(raw: str) -> str:
    d = (raw or "").strip().lower()
    # strip protocol + path
    d = re.sub(r"^https?://", "", d)
    d = d.split("/")[0]
    d = d.strip(".")
    if not DOMAIN_RE.match(d):
        raise HTTPException(status_code=400, detail="invalid_domain")
    if any(d.endswith(s) for s in RESERVED_SUFFIXES):
        raise HTTPException(status_code=400, detail="reserved_domain")
    if len(d) > 120:
        raise HTTPException(status_code=400, detail="domain_too_long")
    return d


async def _agency_for(user: dict) -> dict:
    ag = user.get("agency_ids") or []
    if not ag:
        raise HTTPException(status_code=400, detail="no_agency")
    db = Database.get()
    a = await db.agencies.find_one({"id": ag[0]})
    if not a:
        raise HTTPException(status_code=404, detail="agency_not_found")
    return a


# ============================================================
# Pydantic
# ============================================================

class DomainRequest(BaseModel):
    domain: str = Field(min_length=4, max_length=120)


# ============================================================
# DNS verification (uses dnspython)
# ============================================================

def _resolve_txt(host: str) -> list:
    import dns.resolver
    res = dns.resolver.Resolver()
    res.timeout = 4.0
    res.lifetime = 6.0
    res.nameservers = ["1.1.1.1", "8.8.8.8"]
    answers = res.resolve(host, "TXT")
    out = []
    for r in answers:
        chunks = [bytes(s).decode("utf-8", errors="ignore") for s in r.strings]
        out.append("".join(chunks))
    return out


def _resolve_cname_or_a(host: str) -> list:
    """Return a list of strings: CNAME targets first, then A IPs.
    Used to verify the agency CNAME actually points to our CNAME_TARGET."""
    import dns.resolver
    res = dns.resolver.Resolver()
    res.timeout = 4.0
    res.lifetime = 6.0
    res.nameservers = ["1.1.1.1", "8.8.8.8"]
    out = []
    # Try CNAME first
    try:
        answers = res.resolve(host, "CNAME")
        for r in answers:
            out.append(str(r.target).rstrip(".").lower())
    except Exception:
        pass
    # Resolve A records too (some registrars flatten CNAMEs at apex)
    try:
        answers = res.resolve(host, "A")
        for r in answers:
            out.append(str(r.address))
    except Exception:
        pass
    return out


def _verify_dns(domain: str, token: str) -> dict:
    """Return {ok: bool, txt: [...], cname_a: [...], errors: [...]}."""
    errors = []
    try:
        txts = _resolve_txt(f"{TXT_RECORD_PREFIX}.{domain}")
    except Exception as e:
        txts = []
        errors.append(f"txt_lookup_failed: {type(e).__name__}: {e}")

    expected_txt = f"omnia-verify={token}"
    txt_ok = any(t.strip() == expected_txt for t in txts)
    if not txt_ok:
        errors.append("txt_record_not_found_or_mismatch")

    try:
        cname_a = _resolve_cname_or_a(domain)
    except Exception as e:
        cname_a = []
        errors.append(f"cname_lookup_failed: {type(e).__name__}: {e}")

    target_lower = CNAME_TARGET.lower()
    cname_ok = any(c.lower() == target_lower for c in cname_a)
    # Allow A records if they resolve to the same IP family as our target
    if not cname_ok:
        try:
            import dns.resolver
            res = dns.resolver.Resolver()
            res.nameservers = ["1.1.1.1", "8.8.8.8"]
            target_ips = {str(r.address) for r in res.resolve(CNAME_TARGET, "A")}
            cname_ok = any(c in target_ips for c in cname_a)
        except Exception:
            pass

    if not cname_ok:
        errors.append("cname_record_not_pointing_to_target")

    return {
        "ok": txt_ok and cname_ok,
        "txt_records": txts,
        "txt_expected": expected_txt,
        "cname_resolved": cname_a,
        "cname_expected": CNAME_TARGET,
        "errors": errors,
    }


# ============================================================
# Email notify (best-effort, never blocks)
# ============================================================

async def _notify_super_admin_new_request(agency: dict, domain: str) -> None:
    try:
        from shared.emails.sender import send_html_email  # type: ignore
    except Exception:
        try:
            from apps.core.emails import send_html_email  # type: ignore
        except Exception:
            return
    super_admin = os.environ.get("SUPER_ADMIN_EMAIL")
    if not super_admin:
        return
    body = (
        f"<p>L'agenzia <strong>{agency.get('display_name')}</strong> "
        f"(slug: <code>{agency.get('slug')}</code>) ha richiesto il custom domain "
        f"<strong>{domain}</strong>.</p>"
        f"<p>Per attivarlo:</p>"
        f"<ol>"
        f"<li>Attendi che l'agenzia abbia configurato i DNS (TXT + CNAME).</li>"
        f"<li>Verifica la richiesta nel pannello Super Admin OMNIA.</li>"
        f"<li>Aggiungi il dominio nel pannello <strong>Emergent</strong> "
        f"(Settings → Custom Domains) per attivare l'SSL Let's Encrypt.</li>"
        f"</ol>"
        f"<p><a href='https://omniarealestateecosystem.it/it/admin/domains'>"
        f"Apri pannello richieste pendenti</a></p>"
    )
    try:
        await send_html_email(
            to=super_admin,
            subject=f"[OMNIA] Nuova richiesta custom domain: {domain}",
            html=body,
        )
    except Exception as e:
        logger.warning("super_admin notify failed: %s", e)


# ============================================================
# 1) Request: agency submits its domain, gets the DNS instructions
# ============================================================

@router.post("/domain/request")
async def request_custom_domain(
    payload: DomainRequest,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    domain = _normalize_domain(payload.domain)
    db = Database.get()
    agency = await _agency_for(user)

    # Reject if another agency already claimed it
    other = await db.agencies.find_one({
        "website.custom_domain": domain,
        "id": {"$ne": agency["id"]},
    })
    if other:
        raise HTTPException(status_code=409, detail="domain_already_claimed")

    # If already verified for this agency, just return current state
    cur = (agency.get("website") or {}).get("custom_domain")
    cur_status = (agency.get("website") or {}).get("custom_domain_status")
    if cur == domain and cur_status == "verified":
        return _payload(agency, domain, cur_status, regenerated=False)

    # (Re)generate token + persist
    token = secrets.token_urlsafe(24)
    now = datetime.now(timezone.utc).isoformat()
    update = {
        "website.custom_domain": domain,
        "website.custom_domain_status": "pending",
        "website.custom_domain_token": token,
        "website.custom_domain_requested_at": now,
        "website.custom_domain_verified_at": None,
        "website.custom_domain_last_error": None,
        "updated_at": now,
    }
    await db.agencies.update_one({"id": agency["id"]}, {"$set": update})
    updated = await db.agencies.find_one({"id": agency["id"]})

    # Fire-and-forget admin notify (does not block the API response)
    try:
        await _notify_super_admin_new_request(updated, domain)
    except Exception:
        pass

    return _payload(updated, domain, "pending", regenerated=True)


def _payload(agency: dict, domain: str, status: str, regenerated: bool) -> dict:
    website = agency.get("website") or {}
    token = website.get("custom_domain_token") or ""
    return {
        "domain": domain,
        "status": status,
        "regenerated": regenerated,
        "dns_instructions": {
            "txt_record": {
                "host": f"{TXT_RECORD_PREFIX}.{domain}",
                "type": "TXT",
                "value": f"omnia-verify={token}",
            },
            "cname_record": {
                "host": domain,
                "type": "CNAME",
                "value": CNAME_TARGET,
            },
            "apex_alternative": (
                "Se il tuo dominio è un apex (es. nicastroimmobiliare.it senza www), "
                "alcuni registrar non supportano CNAME su apex: usa ALIAS/ANAME, "
                "oppure aggiungi un CNAME sul sottodominio www."
            ),
        },
        "verified_at": website.get("custom_domain_verified_at"),
        "requested_at": website.get("custom_domain_requested_at"),
        "last_error": website.get("custom_domain_last_error"),
    }


# ============================================================
# 2) Verify: agency triggers DNS check
# ============================================================

@router.post("/domain/verify")
async def verify_custom_domain(
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    agency = await _agency_for(user)
    website = agency.get("website") or {}
    domain = website.get("custom_domain")
    token = website.get("custom_domain_token")
    if not domain or not token:
        raise HTTPException(status_code=400, detail="no_domain_requested")

    result = _verify_dns(domain, token)
    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()
    if result["ok"]:
        await db.agencies.update_one(
            {"id": agency["id"]},
            {"$set": {
                "website.custom_domain_status": "verified",
                "website.custom_domain_verified_at": now,
                "website.custom_domain_last_error": None,
                "updated_at": now,
            }},
        )
        status = "verified"
        last_error = None
    else:
        last_error = "; ".join(result["errors"])[:280]
        await db.agencies.update_one(
            {"id": agency["id"]},
            {"$set": {
                "website.custom_domain_status": "error",
                "website.custom_domain_last_error": last_error,
                "updated_at": now,
            }},
        )
        status = "error"

    return {
        "domain": domain,
        "status": status,
        "ok": result["ok"],
        "checks": {
            "txt_expected": result["txt_expected"],
            "txt_records_found": result["txt_records"],
            "cname_expected": result["cname_expected"],
            "cname_resolved": result["cname_resolved"],
        },
        "errors": result["errors"],
        "verified_at": now if result["ok"] else None,
        "last_error": last_error,
        "next_step_for_admin": (
            "Aggiungi questo dominio nel pannello Emergent (Settings → Custom Domains) "
            "per attivare l'SSL Let's Encrypt automatico."
            if result["ok"] else None
        ),
    }


# ============================================================
# 3) GET current state
# ============================================================

@router.get("/domain")
async def get_custom_domain(user: dict = Depends(get_current_user)):
    agency = await _agency_for(user)
    website = agency.get("website") or {}
    domain = website.get("custom_domain")
    if not domain:
        return {
            "domain": None,
            "status": None,
            "cname_target": CNAME_TARGET,
            "txt_prefix": TXT_RECORD_PREFIX,
        }
    return _payload(agency, domain, website.get("custom_domain_status") or "pending", regenerated=False)


# ============================================================
# 4) DELETE — remove custom domain
# ============================================================

@router.delete("/domain")
async def delete_custom_domain(
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    agency = await _agency_for(user)
    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()
    await db.agencies.update_one(
        {"id": agency["id"]},
        {"$set": {
            "website.custom_domain": None,
            "website.custom_domain_status": None,
            "website.custom_domain_token": None,
            "website.custom_domain_verified_at": None,
            "website.custom_domain_requested_at": None,
            "website.custom_domain_last_error": None,
            "updated_at": now,
        }},
    )
    return {"ok": True, "deleted": True}


# ============================================================
# 5) SUPER ADMIN — list pending requests
# ============================================================

@router.get("/domain/admin/pending")
async def admin_pending_requests(
    _: dict = Depends(require_roles("super_admin")),
):
    db = Database.get()
    cursor = db.agencies.find(
        {"website.custom_domain_status": {"$in": ["pending", "verified", "error"]}},
        {
            "_id": 0,
            "id": 1, "slug": 1, "display_name": 1,
            "website.custom_domain": 1,
            "website.custom_domain_status": 1,
            "website.custom_domain_requested_at": 1,
            "website.custom_domain_verified_at": 1,
            "website.custom_domain_last_error": 1,
        },
    )
    items = []
    async for a in cursor:
        w = a.get("website") or {}
        items.append({
            "agency_id": a["id"],
            "agency_slug": a.get("slug"),
            "agency_name": a.get("display_name"),
            "domain": w.get("custom_domain"),
            "status": w.get("custom_domain_status"),
            "requested_at": w.get("custom_domain_requested_at"),
            "verified_at": w.get("custom_domain_verified_at"),
            "last_error": w.get("custom_domain_last_error"),
        })
    items.sort(key=lambda r: r.get("requested_at") or "", reverse=True)
    by_status = {
        "pending": sum(1 for i in items if i["status"] == "pending"),
        "verified": sum(1 for i in items if i["status"] == "verified"),
        "error": sum(1 for i in items if i["status"] == "error"),
    }
    return {"items": items, "counts": by_status, "total": len(items)}
