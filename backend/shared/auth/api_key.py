"""OMNIA — API Key auth + credit accounting (M2.5.2 Track B).

Public entrypoints accept `Authorization: Bearer omk_<random>` and enforce:
  - key exists, is_active, not revoked
  - agency is active
  - credit balance ≥ cost of the endpoint
Every call is logged to `api_usage_log` for billing audit.
"""
import hashlib
import logging
import secrets
import time
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import HTTPException, Request

from shared.db.connection import Database

logger = logging.getLogger(__name__)

# Plaintext key format: omk_live_<28 base32 chars>
KEY_PREFIX = "omk_live_"

# --- Credit cost catalog (D-047 pricing) ------------------------------------
# 1 credit = €0,03 (aligned to PRICING_OMNIA.md v2)
CREDIT_COSTS: Dict[str, int] = {
    "valuator": 5,          # UNI 10750 valuation
    "mortgages_compare": 1, # in-house mortgage compare
    "legal_ask": 3,         # HAL Legal one-shot question
    "staging_render": 15,   # virtual staging (async, reserved)
    "feed_properties": 0,   # read-only export, free
    "feed_properties_ingest": 0,  # inbound feed from external CRM (D-041, free — value = adoption)
    "leads_export": 0,      # lead export back to Track B CRM (D-041, free)
    "widget_lead": 0,       # widget lead capture — free (funds monetized separately)
    "domain_check": 1,      # RDAP domain ownership check (M2.5.4b, D-054)
    "legal_render": 2,      # PDF template render (M2.5.4c, D-055) — compute cost
}


# --- Plaintext / hash helpers ----------------------------------------------

def generate_plaintext_key() -> str:
    """Return a fresh plaintext API key: `omk_live_<28 base32>`."""
    return KEY_PREFIX + secrets.token_urlsafe(21).replace("-", "").replace("_", "")[:28]


def hash_key(plaintext: str) -> str:
    """SHA-256 hex digest — safe to store (irreversible)."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def prefix_of(plaintext: str) -> str:
    """First 12 chars of the plaintext — searchable, safe to display."""
    return plaintext[:12]


# --- Bearer extraction ------------------------------------------------------

def extract_bearer(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    return token or None


# --- Main dependency --------------------------------------------------------

async def require_api_key(request: Request, endpoint_key: str) -> dict:
    """
    FastAPI dependency: validates Bearer API key, checks credits, and returns
    the api_key document (without the hash).

    Charging happens in a separate call to `charge_credits()` after the
    endpoint succeeds — this keeps refunds trivial (we simply skip the charge
    on error).
    """
    token = extract_bearer(request)
    if not token or not token.startswith(KEY_PREFIX):
        raise HTTPException(status_code=401, detail="missing_or_invalid_api_key")

    db = Database.get()
    h = hash_key(token)
    key = await db.api_keys.find_one({"key_hash": h})
    if not key:
        raise HTTPException(status_code=401, detail="invalid_api_key")
    if not key.get("is_active") or key.get("revoked_at"):
        raise HTTPException(status_code=403, detail="api_key_revoked")

    # M2.5.3 — Origin whitelist: if the key declares allowed_origins, enforce them.
    # Some ingresses/proxies rewrite the `Origin` header to internal hostnames,
    # so we also accept a Referer that matches. Any match on either wins.
    allowed = key.get("allowed_origins") or []
    if allowed:
        candidates = []
        origin = request.headers.get("Origin")
        if origin:
            candidates.append(origin.rstrip("/"))
        ref_origin = _origin_from_referer(request.headers.get("Referer", ""))
        if ref_origin:
            candidates.append(ref_origin.rstrip("/"))
        matched = any(_origin_matches(c, allowed) for c in candidates)
        if not matched:
            logger.warning(
                "origin_not_allowed key=%s candidates=%r allowed=%r",
                key["id"], candidates, allowed,
            )
            raise HTTPException(status_code=403, detail="origin_not_allowed")

    # Verify owning agency is still active
    ag = await db.agencies.find_one({"id": key["agency_id"]}, {"_id": 0, "is_active": 1})
    if not ag or not ag.get("is_active", True):
        raise HTTPException(status_code=403, detail="agency_inactive")

    cost = CREDIT_COSTS.get(endpoint_key, 0)
    if cost > 0 and key.get("credits_balance", 0) < cost:
        raise HTTPException(status_code=402, detail="insufficient_credits")

    # attach transient context (used by charge/log after handler)
    request.state.api_key = key
    request.state.api_cost = cost
    request.state.api_endpoint_key = endpoint_key
    request.state.api_started_at = time.monotonic()

    return key


def _origin_from_referer(referer: str) -> Optional[str]:
    """Extract origin (scheme://host[:port]) from a Referer URL."""
    if not referer:
        return None
    try:
        from urllib.parse import urlparse
        u = urlparse(referer)
        if u.scheme and u.netloc:
            return f"{u.scheme}://{u.netloc}"
    except Exception:
        return None
    return None


def _origin_matches(origin: str, allowed: list) -> bool:
    """
    Check origin against whitelist. Patterns:
      - "https://example.com"        exact
      - "https://*.example.com"      wildcard subdomain
      - "*"                          allow all (escape hatch)
    """
    origin = (origin or "").rstrip("/")
    for pat in allowed:
        pat = (pat or "").rstrip("/")
        if pat == "*" or pat == origin:
            return True
        # subdomain wildcard: "https://*.example.com"
        if "://*." in pat:
            scheme, rest = pat.split("://", 1)
            base = rest[2:]  # after "*."
            if origin.startswith(f"{scheme}://") and origin.endswith(base):
                # ensure it's a subdomain, not the base itself
                host_part = origin[len(scheme) + 3:]
                if host_part == base or host_part.endswith("." + base):
                    return True
    return False


def make_key_dep(endpoint_key: str):
    """Sugar: create a Depends-friendly async function bound to an endpoint cost."""
    async def _dep(request: Request) -> dict:
        return await require_api_key(request, endpoint_key)
    return _dep


# --- Post-call accounting ---------------------------------------------------

async def charge_and_log(request: Request, status_code: int = 200,
                         error_code: Optional[str] = None) -> None:
    """
    Debit credits (only on success) and append a usage log row.

    Call this AFTER the business logic has completed successfully, or with
    `error_code` set to record a failed attempt without charging.
    """
    key = getattr(request.state, "api_key", None)
    if not key:
        return  # not an API-key request; nothing to do

    db = Database.get()
    cost = getattr(request.state, "api_cost", 0)
    endpoint = getattr(request.state, "api_endpoint_key", "unknown")
    started = getattr(request.state, "api_started_at", None)
    latency_ms = int((time.monotonic() - started) * 1000) if started else None

    ok = 200 <= status_code < 400 and error_code is None
    now = datetime.now(timezone.utc).isoformat()

    # Debit only on success + non-zero cost (H8 — atomic, never overdraws)
    if ok and cost > 0:
        res = await db.api_keys.update_one(
            {"id": key["id"], "credits_balance": {"$gte": cost}},
            {
                "$inc": {"credits_balance": -cost, "credits_spent": cost},
                "$set": {"last_used_at": now, "updated_at": now},
            },
        )
        if res.modified_count == 0:
            # Concurrent race consumed the balance: drain to zero, never negative.
            logger.warning("credit_debit_clamped key=%s cost=%s", key["id"], cost)
            await db.api_keys.update_one(
                {"id": key["id"]},
                [{"$set": {
                    "credits_spent": {"$add": ["$credits_spent", "$credits_balance"]},
                    "credits_balance": 0,
                    "last_used_at": now,
                    "updated_at": now,
                }}],
            )
    else:
        # touch last_used_at anyway (attempts count)
        await db.api_keys.update_one(
            {"id": key["id"]},
            {"$set": {"last_used_at": now, "updated_at": now}},
        )

    log_doc = {
        "id": secrets.token_hex(12),
        "api_key_id": key["id"],
        "agency_id": key["agency_id"],
        "partner_id": key.get("partner_id"),
        "endpoint": endpoint,
        "credits_charged": cost if ok else 0,
        "status_code": status_code,
        "ok": ok,
        "error_code": error_code,
        "latency_ms": latency_ms,
        "created_at": now,
        "updated_at": now,
    }
    await db.api_usage_log.insert_one(log_doc)
