"""OMNIA — Domain Ownership Checker (M2.5.4b, D-054 / D-051).

Public lead-magnet endpoint that lets ANY Italian real estate agency verify
in seconds whether their domain is registered under their own name or under
a third-party provider (hosting, web agency, gestionale). This is the first
public deliverable of the "Domain Sovereignty Kit" (D-051).

STRICT RULE (D-051): never name specific competitors. All heuristics use
generic keyword patterns; if we detect a match the user just sees a
category like "il tuo attuale fornitore" — never a brand name.

Endpoints (in this module):
    POST /api/domain/check           public, IP-rate-limited (10/hour/IP)
    POST /api/domain/lead            public, capture lead attached to a check

The v1 API-key equivalent (paid, 1 credit) lives in `apps/v1/gateway.py`.
The widget iframe HTML lives in `apps/v1/assets/domain-check.html`.
"""
from __future__ import annotations
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field, field_validator

from shared.db.connection import Database
from shared.utils.rdap import rdap_lookup, normalize_domain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/domain", tags=["domain-checker"])


# ------------------ Configuration ------------------

# Generic keyword patterns that suggest the registrant is a *provider* rather
# than the end agency itself. These are intentionally category-level — no
# brand names anywhere (D-051).
_PROVIDER_HINT_KEYWORDS = [
    "hosting", "hostname", "hostmaster",
    "web agency", "webagency", "web design", "web factory", "digital agency",
    "gestionale", "immobiliare software", "real estate software",
    "servizi web", "servizi informatici", "informatica", "internet services",
    "domain services", "domain registration", "domini",
    "solutions", "software solutions",
    "editrice", "editoria", "media agency",
    "srl unipersonale", "unipersonale s.r.l.",  # very common provider signal for tiny web shops
]

# Highly-generic tokens that mean the RDAP record is redacted (GDPR / privacy proxy)
_REDACTED_HINTS = [
    "redacted for privacy", "gdpr masked", "not disclosed", "withheld",
    "data protected", "domain administrator", "privacy service",
    "privacy protection", "not disclosed - visit",
]

# Rate limit: max checks per IP per rolling window
_RATE_LIMIT_MAX = 30
_RATE_LIMIT_WINDOW_SEC = 3600  # 1 hour


# ------------------ Models ------------------

class DomainCheckRequest(BaseModel):
    domain: str = Field(min_length=3, max_length=253)
    agency_name: Optional[str] = Field(default=None, max_length=200,
                                        description="Optional: user's own agency name to compare against registrant.")

    @field_validator("domain")
    @classmethod
    def _clean(cls, v: str) -> str:
        return v.strip().lower()


class DomainLeadRequest(BaseModel):
    check_id: str = Field(min_length=8, max_length=64)
    email: EmailStr
    name: str = Field(min_length=2, max_length=120)
    agency: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=40)
    consent: bool = Field(default=False)
    source: str = Field(default="landing", max_length=40)


# ------------------ Heuristics ------------------

def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _registrant_looks_like_provider(registrant: Optional[str]) -> bool:
    """True if the registrant *name* pattern-matches a provider signature.

    Deliberately keyword-based, NOT brand-based. If a well-known
    Italian real-estate-software vendor slips into `registrant`, we still
    want to flag it — but we do so by matching category keywords (which
    all these vendors happen to contain in their legal names, e.g.
    "software", "informatica", "web agency", "hosting"), never their brand.
    """
    if not registrant:
        return False
    r = registrant.lower()
    for kw in _PROVIDER_HINT_KEYWORDS:
        if kw in r:
            return True
    return False


def _is_redacted(registrant: Optional[str]) -> bool:
    if not registrant:
        return True
    r = registrant.lower()
    return any(h in r for h in _REDACTED_HINTS)


def _domain_matches_registrant(domain: str, registrant: Optional[str],
                                agency_name: Optional[str]) -> bool:
    """Fuzzy check: does the registrant look like the agency itself?

    Compares the "brand token" of the domain (2nd-level, no TLD) against a
    normalized version of the registrant name and, if provided, the agency
    name from the form. We stay conservative: any partial substring wins
    (agency owners often use their surname).
    """
    if not registrant:
        return False
    domain_brand = _slug(domain.rsplit(".", 2)[0].split(".")[-1])
    reg_slug = _slug(registrant)
    if not domain_brand:
        return False
    if len(domain_brand) >= 4 and domain_brand in reg_slug:
        return True
    if agency_name:
        agency_slug = _slug(agency_name)
        if agency_slug and (agency_slug in reg_slug or reg_slug in agency_slug):
            return True
    return False


def _expires_soon(iso: Optional[str], threshold_days: int = 90) -> Optional[int]:
    """Return days-until-expiration if within threshold, else None."""
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days = (dt - now).days
        return days if 0 <= days <= threshold_days else None
    except Exception:
        return None


def _analyze(rdap: Dict[str, Any], agency_name: Optional[str]) -> Dict[str, Any]:
    """Turn the RDAP result into an interpretive report for the UI."""
    domain = rdap["domain"]

    if rdap.get("not_found"):
        return {
            "status": "not_registered",
            "severity": "info",
            "headline": "Il dominio non risulta registrato",
            "explanation": (
                "Questo dominio è ancora libero. Se lo vuoi assicurare al tuo nome, "
                "registralo direttamente su un registrar (Aruba, Register.it, OVH, ecc.) "
                "prima che qualcuno lo prenoti."
            ),
            "actions": ["register_domain", "learn_domain_vault"],
            "flags": {"is_free": True},
        }

    if rdap.get("error"):
        return {
            "status": "unknown",
            "severity": "info",
            "headline": "Non siamo riusciti a leggere i dati del dominio",
            "explanation": (
                "Il registro non ha risposto in tempo o il dominio è di un TLD che "
                "non supporta ancora RDAP. Riprova più tardi o contattaci per un check manuale."
            ),
            "actions": ["retry", "contact_support"],
            "flags": {"rdap_error": True},
        }

    registrant = rdap.get("registrant")
    redacted = _is_redacted(registrant)
    provider_hint = _registrant_looks_like_provider(registrant)
    matches_agency = _domain_matches_registrant(domain, registrant, agency_name)
    exp_days = _expires_soon(rdap.get("expires_at"))
    flags = {
        "registrant_present": bool(registrant),
        "registrant_redacted": redacted,
        "registrant_looks_like_provider": provider_hint,
        "registrant_matches_agency": matches_agency,
        "expires_soon_days": exp_days,
        "has_nameservers": bool(rdap.get("nameservers")),
    }

    # Case 1: registrant matches agency name → GOOD
    if matches_agency and not provider_hint:
        return {
            "status": "owner_ok",
            "severity": "good",
            "headline": "Il dominio risulta a tuo nome",
            "explanation": (
                "Il registrante coincide con il tuo nome / la tua agenzia. "
                "Sei il proprietario ufficiale del dominio e puoi trasferirlo "
                "in qualsiasi momento a un registrar diverso."
            ),
            "actions": ["monitor_expiry"] + (["renew_soon"] if exp_days else []),
            "flags": flags,
        }

    # Case 2: registrant looks like a provider → LIKELY HOSTAGE
    if provider_hint:
        return {
            "status": "likely_hostage",
            "severity": "critical",
            "headline": "Il dominio potrebbe essere in mano al tuo attuale fornitore",
            "explanation": (
                "Il nome del registrante contiene indicatori tipici di un fornitore "
                "terzo (parole come «hosting», «web agency», «software», «servizi», ecc.), "
                "non il nome di un'agenzia immobiliare. Questo significa che se un domani "
                "cambi gestionale il dominio potrebbe restare al fornitore attuale. "
                "Scarica il nostro kit legale per recuperarne la titolarità."
            ),
            "actions": ["download_legal_kit", "contact_support", "learn_domain_vault"],
            "flags": flags,
        }

    # Case 3: redacted / privacy — inconclusive but suspicious
    if redacted:
        return {
            "status": "redacted",
            "severity": "warning",
            "headline": "I dati del registrante sono nascosti (privacy)",
            "explanation": (
                "Il registro non pubblica il nome del titolare (protezione GDPR o "
                "servizio di privacy proxy). Questo NON è di per sé un problema — "
                "ma non ci permette di confermare chi è il proprietario. Puoi verificarlo "
                "aprendo un ticket al tuo registrar chiedendo esplicitamente «di chi risulta "
                "intestato il dominio come Registrante ufficiale?»."
            ),
            "actions": ["open_registrar_ticket", "download_legal_kit"],
            "flags": flags,
        }

    # Case 4: has a registrant but no clear match either way — ambiguous
    return {
        "status": "ambiguous",
        "severity": "warning",
        "headline": "Il registrante non corrisponde in modo evidente alla tua agenzia",
        "explanation": (
            "Il dominio è registrato a nome di «" + (registrant or "—") + "», che non "
            "coincide chiaramente né con il nome dominio né con quello che ci hai indicato. "
            "Potrebbe essere corretto (studio associato, holding, familiare) oppure indicare "
            "che il dominio è intestato a un fornitore. Verifica con calma."
        ),
        "actions": ["open_registrar_ticket", "download_legal_kit"],
        "flags": flags,
    }


# ------------------ Rate limit helper ------------------

async def _check_rate_limit(ip: str) -> None:
    """Raise 429 if the IP exceeded the rolling window quota."""
    if not ip:
        return
    db = Database.get()
    since = datetime.now(timezone.utc).timestamp() - _RATE_LIMIT_WINDOW_SEC
    count = await db.domain_checks.count_documents({
        "client_ip": ip,
        "created_ts": {"$gte": since},
    })
    if count >= _RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="rate_limit_exceeded")


# ------------------ Endpoints ------------------

async def run_check(domain_raw: str, agency_name: Optional[str],
                    source: str, client_ip: Optional[str]) -> Dict[str, Any]:
    """Shared internal logic. Used both by the public and the v1 API endpoints."""
    domain = normalize_domain(domain_raw)
    if not domain:
        raise HTTPException(status_code=400, detail="invalid_domain")
    rdap = await rdap_lookup(domain)
    verdict = _analyze(rdap, agency_name)
    check_id = str(uuid4())
    now = datetime.now(timezone.utc)

    db = Database.get()
    doc = {
        "id": check_id,
        "domain": domain,
        "agency_name": agency_name,
        "source": source,
        "client_ip": client_ip,
        "rdap": {
            "registrant": rdap.get("registrant"),
            "registrar": rdap.get("registrar"),
            "nameservers": rdap.get("nameservers"),
            "created_at": rdap.get("created_at"),
            "expires_at": rdap.get("expires_at"),
            "last_changed": rdap.get("last_changed"),
            "not_found": rdap.get("not_found", False),
            "error": rdap.get("error"),
            "raw_source": rdap.get("raw_source"),
        },
        "verdict": verdict,
        "created_at": now.isoformat(),
        "created_ts": now.timestamp(),
    }
    await db.domain_checks.insert_one(doc)
    doc.pop("_id", None)
    doc.pop("client_ip", None)  # never leak IP to caller
    return doc


@router.post("/check")
async def public_domain_check(payload: DomainCheckRequest, request: Request) -> Dict[str, Any]:
    """Public, IP-rate-limited domain check. Landing-page endpoint."""
    ip = request.client.host if request.client else ""
    ip = (request.headers.get("x-forwarded-for") or ip or "").split(",")[0].strip()
    await _check_rate_limit(ip)
    return await run_check(payload.domain, payload.agency_name, "landing", ip)


@router.post("/lead", status_code=201)
async def public_domain_lead(payload: DomainLeadRequest, request: Request) -> Dict[str, Any]:
    """Attach a lead (name/email) to a previous check. GDPR consent required."""
    if not payload.consent:
        raise HTTPException(status_code=400, detail="consent_required")
    db = Database.get()
    check = await db.domain_checks.find_one({"id": payload.check_id}, {"_id": 0})
    if not check:
        raise HTTPException(status_code=404, detail="check_not_found")

    now = datetime.now(timezone.utc)
    lead_doc = {
        "id": str(uuid4()),
        "check_id": payload.check_id,
        "domain": check["domain"],
        "verdict_status": check.get("verdict", {}).get("status"),
        "name": payload.name.strip(),
        "email": payload.email.lower(),
        "agency": (payload.agency or "").strip() or None,
        "phone": (payload.phone or "").strip() or None,
        "source": payload.source,
        "consent_at": now.isoformat(),
        "created_at": now.isoformat(),
        "status": "new",
    }
    await db.domain_leads.insert_one(lead_doc)
    lead_doc.pop("_id", None)
    return {"ok": True, "id": lead_doc["id"], "message": "Lead ricevuto — ti scriviamo entro 24h."}
