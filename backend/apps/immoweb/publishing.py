"""OMNIA — Publishing Center router (M2.6a, D-052 + M2.6b, D-053).

M2.6a: multi-portal outbound publishing layer + compliance HARD filter on feed.
M2.6b: adds sync engine (scheduled + manual) + rich compliance dashboard.
Coexists with legacy portals.py (M2.S5 "portal subscriptions" concept, kept intact).

Endpoints under /api/app/publishing:
    GET    /catalog                             list of supported portals
    GET    /connections                         my agency's activations
    POST   /connections                         activate a portal
    PATCH  /connections/{id}                    update creds / toggle
    DELETE /connections/{id}                    deactivate
    GET    /connections/{id}/logs               recent sync logs
    POST   /connections/{id}/sync-now           M2.6b — trigger sync manually
    GET    /connections/{id}/compliance         M2.6b — compliance snapshot for this agency
    POST   /sync/run-all                        M2.6b — admin cron endpoint (super_admin)
"""
import logging
import os
import re
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4
from xml.sax.saxutils import escape as xml_escape

from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import Field, HttpUrl

from shared.db.connection import Database
from shared.auth.dependencies import require_roles
from shared.models.base import OmniaBaseModel
from shared.models.portal import (
    PortalConnectionCreate, PortalConnectionUpdate, AgencyPortalConnection,
    PortalCatalog,
)
from shared.utils.crypto import encrypt_dict
from shared.validators.compliance import (
    validate_property, summarize_agency_compliance, is_publishable as _validator_is_publishable,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/publishing", tags=["publishing"])


CATALOG_SEED = [
    {"slug": "subito", "name": "Subito.it", "category": "freemium", "dialect": "osf_federata",
     "integration_type": "feed_pull", "traffic_score": 5,
     "credential_fields": [{"name": "username", "label": "Username", "type": "text"},
                           {"name": "api_key", "label": "Chiave partner (opz.)", "type": "text"}],
     "notes": "Piu' grande portale generalista italiano."},
    {"slug": "bakeca", "name": "Bakeca.it", "category": "gratuito", "dialect": "osf_federata",
     "integration_type": "feed_pull", "traffic_score": 3,
     "credential_fields": [{"name": "email", "label": "Email account", "type": "email"}],
     "notes": "Gratuito con pubblicita'. Setup semplice."},
    {"slug": "kijiji", "name": "Kijiji.it", "category": "gratuito", "dialect": "osf_federata",
     "integration_type": "feed_pull", "traffic_score": 2,
     "credential_fields": [{"name": "email", "label": "Email account", "type": "email"}], "notes": "Adevinta group."},
    {"slug": "wikicasa", "name": "Wikicasa.it", "category": "freemium", "dialect": "generic_rss",
     "integration_type": "feed_pull", "traffic_score": 4,
     "credential_fields": [{"name": "api_key", "label": "API Key", "type": "text"}],
     "notes": "Free tier fino a ~20 annunci."},
    {"slug": "facebook-marketplace", "name": "Facebook Marketplace", "category": "gratuito",
     "dialect": "facebook_catalog", "integration_type": "api_push", "traffic_score": 4,
     "credential_fields": [{"name": "page_id", "label": "Page ID", "type": "text"},
                           {"name": "access_token", "label": "Access Token", "type": "text"}],
     "notes": "Meta Business API. Copertura enorme."},
    {"slug": "google-business", "name": "Google Business Profile", "category": "gratuito",
     "dialect": "google_merchant", "integration_type": "api_push", "traffic_score": 4,
     "credential_fields": [{"name": "account_id", "label": "Google Business Account ID", "type": "text"}],
     "notes": "Migliora visibilita' su Google Search / Maps."},
    {"slug": "attico", "name": "Attico.it", "category": "freemium", "dialect": "osf_federata",
     "integration_type": "feed_pull", "traffic_score": 2,
     "credential_fields": [{"name": "email", "label": "Email account", "type": "email"}], "notes": "Free tier limitato."},
    {"slug": "case24", "name": "Case24.it", "category": "freemium", "dialect": "osf_federata",
     "integration_type": "feed_pull", "traffic_score": 2,
     "credential_fields": [{"name": "email", "label": "Email account", "type": "email"}],
     "notes": "Portale generalista minore."},
]


async def seed_publishing_catalog() -> None:
    """Idempotent catalog seed. Called from server startup."""
    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    for p in CATALOG_SEED:
        existing = await db.publishing_catalog.find_one({"slug": p["slug"]})
        if existing:
            continue
        await db.publishing_catalog.insert_one(
            {**p, "id": p["slug"], "is_active": True, "geographic_scope": "national",
             "created_at": now, "updated_at": now})
        inserted += 1
    if inserted:
        logger.info("publishing_catalog seeded (%d new entries)", inserted)


from shared.auth.tenant import require_agency_404 as _agency_id


def _public(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k not in ("_id", "credentials_encrypted")}


@router.get("/catalog")
async def catalog(user: dict = Depends(require_roles("agency_admin", "super_admin"))):
    """List active portals visible to the caller.

    Returns:
      - system portals (owner_agency_id absent/None), sorted by traffic_score DESC
      - this agency's custom portals (M2.6d), sorted after system ones
    Other agencies' custom portals are ALWAYS filtered out (tenant isolation).
    """
    db = Database.get()
    aid = _agency_id(user)
    docs = await db.publishing_catalog.find(
        {
            "is_active": True,
            "$or": [
                {"owner_agency_id": {"$in": [None, ""]}},
                {"owner_agency_id": {"$exists": False}},
                {"owner_agency_id": aid},
            ],
        },
        {"_id": 0},
    ).sort([("is_custom", 1), ("traffic_score", -1)]).to_list(500)
    return {"items": docs, "total": len(docs)}


@router.get("/connections")
async def list_connections(user: dict = Depends(require_roles("agency_admin", "super_admin"))):
    db = Database.get()
    aid = _agency_id(user)
    docs = await db.publishing_connections.find({"agency_id": aid}).sort("created_at", -1).to_list(200)
    return {"items": [_public(d) for d in docs], "total": len(docs)}


@router.post("/connections", status_code=201)
async def create_connection(
    payload: PortalConnectionCreate,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    db = Database.get()
    aid = _agency_id(user)
    portal = await db.publishing_catalog.find_one({"slug": payload.portal_slug})
    if not portal:
        raise HTTPException(status_code=404, detail="portal_not_in_catalog")
    existing = await db.publishing_connections.find_one(
        {"agency_id": aid, "portal_slug": payload.portal_slug})
    if existing:
        raise HTTPException(status_code=409, detail="already_connected")

    conn = AgencyPortalConnection(
        agency_id=aid, portal_slug=payload.portal_slug,
        status="active" if payload.credentials else "pending",
        credentials_encrypted=encrypt_dict(payload.credentials) if payload.credentials else None,
        is_all_properties=payload.is_all_properties,
    )
    doc = conn.model_dump()
    await db.publishing_connections.insert_one(doc)
    logger.info("publishing_connection_created agency=%s portal=%s", aid, payload.portal_slug)
    return _public(doc)


@router.patch("/connections/{conn_id}")
async def update_connection(
    conn_id: str, payload: PortalConnectionUpdate,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    db = Database.get()
    aid = _agency_id(user)
    conn = await db.publishing_connections.find_one({"id": conn_id, "agency_id": aid})
    if not conn:
        raise HTTPException(status_code=404, detail="connection_not_found")

    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if payload.credentials is not None:
        update["credentials_encrypted"] = encrypt_dict(payload.credentials)
        update["status"] = "active"
    if payload.is_all_properties is not None:
        update["is_all_properties"] = payload.is_all_properties
    if payload.status in {"active", "disabled"}:
        update["status"] = payload.status

    await db.publishing_connections.update_one({"id": conn_id}, {"$set": update})
    return _public(await db.publishing_connections.find_one({"id": conn_id}))


@router.delete("/connections/{conn_id}")
async def delete_connection(
    conn_id: str,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    db = Database.get()
    aid = _agency_id(user)
    r = await db.publishing_connections.delete_one({"id": conn_id, "agency_id": aid})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="connection_not_found")
    return {"status": "ok", "id": conn_id}


@router.get("/connections/{conn_id}/logs")
async def connection_logs(
    conn_id: str, limit: int = 20,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    db = Database.get()
    aid = _agency_id(user)
    conn = await db.publishing_connections.find_one({"id": conn_id, "agency_id": aid}, {"portal_slug": 1})
    if not conn:
        raise HTTPException(status_code=404, detail="connection_not_found")
    logs = await db.publishing_sync_logs.find(
        {"agency_id": aid, "portal_slug": conn["portal_slug"]}, {"_id": 0}
    ).sort("started_at", -1).limit(min(max(limit, 1), 100)).to_list(100)
    return {"items": logs, "total": len(logs)}


# ---------- COMPLIANCE (HARD, D-052 + D-053) ----------

def is_publishable(prop: dict) -> tuple:
    """Backwards-compatible wrapper around shared.validators.compliance.

    Kept as a module-level export so existing imports (tests, feed generator)
    keep working. All logic lives in shared/validators/compliance.py now.
    """
    return _validator_is_publishable(prop)


# ---------- M2.6b — SYNC ENDPOINTS ----------

@router.post("/connections/{conn_id}/sync-now")
async def sync_now(
    conn_id: str,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Trigger a manual sync for one connection. No retry (snappy response)."""
    db = Database.get()
    aid = _agency_id(user)
    conn = await db.publishing_connections.find_one({"id": conn_id, "agency_id": aid})
    if not conn:
        raise HTTPException(status_code=404, detail="connection_not_found")
    if conn.get("status") == "disabled":
        raise HTTPException(status_code=409, detail="connection_disabled")
    from apps.immoweb.sync_engine import sync_connection_with_retry
    result = await sync_connection_with_retry(conn, trigger="manual")
    return {
        "ok": result.get("ok"),
        "publishable": result.get("publishable_count", 0),
        "blocked": result.get("blocked_count", 0),
        "integration_type": result.get("integration_type"),
        "log": result.get("log"),
    }


@router.get("/connections/{conn_id}/compliance")
async def connection_compliance(
    conn_id: str,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Aggregated compliance snapshot for the agency behind this connection.

    Returns which properties would be blocked / warned if we synced right now.
    Useful to show a "5 immobili non pubblicabili" alert on the dashboard.
    """
    db = Database.get()
    aid = _agency_id(user)
    conn = await db.publishing_connections.find_one({"id": conn_id, "agency_id": aid})
    if not conn:
        raise HTTPException(status_code=404, detail="connection_not_found")
    props = await db.properties.find(
        {"agency_id": aid, "status": "active"}, {"_id": 0}
    ).limit(2000).to_list(2000)
    summary = summarize_agency_compliance(props)
    # Also give the per-property status for the top 20 blocked ones (so the UI
    # can list them with a "vai a correggere" link).
    blocked_details = []
    for p in props:
        r = validate_property(p)
        if not r["publishable"]:
            blocked_details.append({
                "id": p.get("id"),
                "reference": p.get("reference_code"),
                "title": p.get("title") or "",
                "reasons": r["hard_violations"],
            })
            if len(blocked_details) >= 20:
                break
    return {
        "portal_slug": conn["portal_slug"],
        "summary": summary,
        "blocked_details": blocked_details,
    }


@router.post("/sync/run-all")
async def sync_run_all(user: dict = Depends(require_roles("super_admin"))):
    """Admin trigger to run all active syncs immediately (bypasses scheduler)."""
    from apps.immoweb.sync_engine import run_all_active_syncs
    return await run_all_active_syncs(trigger="admin_manual")


# =====================================================================
# M2.6d — Universal Portal Wizard (self-service custom portal setup)
# =====================================================================
#
# Track B agencies often work with regional / franchise / niche portals that
# are NOT in the OMNIA catalog. This block lets them register a custom portal
# in 4 steps without OMNIA intervention:
#
#   1. Name + site URL + category
#   2. Dialect (osf_federata XML | generic_rss) + integration mode
#   3. Endpoint URL (optional, informational for the wizard's copy screen)
#   4. Confirm → creates PortalCatalog entry + auto-creates connection
#
# Custom portals are visible only to the owning agency (tenant isolation via
# `owner_agency_id`). System portals stay untouched.


_SUPPORTED_DIALECTS = {"osf_federata", "generic_rss"}
_SUPPORTED_INTEGRATIONS = {"feed_pull"}  # push_url / api_push arrive in Sprint 2+
_CUSTOM_SLUG_PREFIX = "x-"


def _agency_short(aid: str) -> str:
    """First 8 chars of the agency uuid — enough for slug uniqueness."""
    return (aid or "").replace("-", "")[:8]


def _custom_slug(agency_id: str, user_slug: str) -> str:
    """Build the definitive slug: x-{agency8}-{user_slug}.

    Prevents cross-tenant collisions (two agencies with a "portale-locale"
    still get distinct slugs) while remaining URL-safe.
    """
    base = re.sub(r"[^a-z0-9]+", "-", (user_slug or "").lower()).strip("-")
    if not base:
        raise HTTPException(status_code=422, detail="invalid_slug")
    if base.startswith(_CUSTOM_SLUG_PREFIX):
        base = base[len(_CUSTOM_SLUG_PREFIX):]
    slug = f"{_CUSTOM_SLUG_PREFIX}{_agency_short(agency_id)}-{base}"
    return slug[:80]


class CustomPortalCreate(OmniaBaseModel):
    name: str = Field(min_length=2, max_length=80)
    slug: str = Field(min_length=2, max_length=60)
    dialect: str = Field(default="osf_federata")
    integration_type: str = Field(default="feed_pull")
    category: str = Field(default="freemium")
    site_url: Optional[str] = Field(default=None, max_length=300)
    endpoint_url: Optional[str] = Field(default=None, max_length=300)
    geographic_scope: str = Field(default="local")
    notes: Optional[str] = Field(default=None, max_length=500)


class CustomPortalUpdate(OmniaBaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    dialect: Optional[str] = None
    integration_type: Optional[str] = None
    category: Optional[str] = None
    site_url: Optional[str] = Field(default=None, max_length=300)
    endpoint_url: Optional[str] = Field(default=None, max_length=300)
    geographic_scope: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


def _validate_wizard_choices(dialect: str, integration_type: str) -> None:
    if dialect not in _SUPPORTED_DIALECTS:
        raise HTTPException(status_code=422, detail="unsupported_dialect")
    if integration_type not in _SUPPORTED_INTEGRATIONS:
        raise HTTPException(status_code=422, detail="unsupported_integration_type")


async def _agency_slug(db, aid: str) -> str:
    doc = await db.agencies.find_one({"id": aid}, {"slug": 1, "_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="agency_not_found")
    return doc["slug"]


def _feed_urls(agency_slug: str, dialect: str) -> dict:
    """Return the ready-to-copy feed URLs for the wizard confirmation step."""
    base = os.environ.get("FRONTEND_URL", "").rstrip("/")
    # Public agency feed already exposed by feed_router below.
    path = f"/api/publishing/feed/{agency_slug}.xml"
    return {
        "primary": f"{base}{path}?dialect={dialect}" if base else f"{path}?dialect={dialect}",
        "fallback_generic_rss": f"{base}{path}?dialect=generic_rss" if base else f"{path}?dialect=generic_rss",
        "note": "public_no_auth_cache_30min",
    }


@router.get("/custom-portals")
async def list_custom_portals(
    user: dict = Depends(require_roles("agency_admin", "super_admin", "branch_admin", "group_admin")),
):
    """List custom portals owned by this agency (M2.6d)."""
    db = Database.get()
    aid = _agency_id(user)
    docs = await db.publishing_catalog.find(
        {"owner_agency_id": aid, "is_custom": True}, {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    return {"items": docs, "total": len(docs)}


@router.get("/custom-portals/feed-info")
async def custom_portal_feed_info(
    dialect: str = "osf_federata",
    user: dict = Depends(require_roles("agency_admin", "super_admin", "branch_admin", "group_admin")),
):
    """Return the ready-to-copy feed URL for this agency (wizard confirmation).

    Independent from any specific custom portal — the feed is per-agency.
    """
    if dialect not in _SUPPORTED_DIALECTS:
        raise HTTPException(status_code=422, detail="unsupported_dialect")
    db = Database.get()
    aid = _agency_id(user)
    slug = await _agency_slug(db, aid)
    return {"agency_slug": slug, "dialect": dialect, **_feed_urls(slug, dialect)}


@router.post("/custom-portals", status_code=201)
async def create_custom_portal(
    payload: CustomPortalCreate,
    user: dict = Depends(require_roles("agency_admin", "super_admin", "branch_admin", "group_admin")),
):
    """Create a custom portal + auto-create the agency connection.

    Idempotent-per-name: a second call with the same user-provided slug for the
    same agency returns 409.
    """
    _validate_wizard_choices(payload.dialect, payload.integration_type)
    db = Database.get()
    aid = _agency_id(user)
    full_slug = _custom_slug(aid, payload.slug)

    existing = await db.publishing_catalog.find_one({"slug": full_slug})
    if existing:
        raise HTTPException(status_code=409, detail="slug_already_used")

    now = datetime.now(timezone.utc).isoformat()
    portal = PortalCatalog(
        slug=full_slug,
        name=payload.name.strip(),
        category=payload.category,
        dialect=payload.dialect,
        integration_type=payload.integration_type,
        geographic_scope=payload.geographic_scope,
        credential_fields=[],
        traffic_score=1,
        is_active=True,
        notes=payload.notes,
        owner_agency_id=aid,
        is_custom=True,
        endpoint_url=payload.endpoint_url,
        site_url=payload.site_url,
    )
    doc = portal.model_dump()
    await db.publishing_catalog.insert_one(doc)

    # Auto-create the connection so the agent doesn't have to click again.
    conn = AgencyPortalConnection(
        agency_id=aid,
        portal_slug=full_slug,
        status="active",  # feed_pull → no credentials, always active
        credentials_encrypted=None,
        is_all_properties=True,
    )
    conn_doc = conn.model_dump()
    await db.publishing_connections.insert_one(conn_doc)

    logger.info(
        "custom_portal_created agency=%s slug=%s dialect=%s",
        aid, full_slug, payload.dialect,
    )

    agency_slug_val = await _agency_slug(db, aid)
    return {
        "portal": {k: v for k, v in doc.items() if k != "_id"},
        "connection": {k: v for k, v in conn_doc.items() if k not in ("_id", "credentials_encrypted")},
        "feed": _feed_urls(agency_slug_val, payload.dialect),
    }


@router.patch("/custom-portals/{slug}")
async def update_custom_portal(
    slug: str,
    payload: CustomPortalUpdate,
    user: dict = Depends(require_roles("agency_admin", "super_admin", "branch_admin", "group_admin")),
):
    db = Database.get()
    aid = _agency_id(user)
    portal = await db.publishing_catalog.find_one({"slug": slug, "owner_agency_id": aid, "is_custom": True})
    if not portal:
        raise HTTPException(status_code=404, detail="custom_portal_not_found")

    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    data = payload.model_dump(exclude_unset=True)
    if "dialect" in data or "integration_type" in data:
        _validate_wizard_choices(
            data.get("dialect", portal["dialect"]),
            data.get("integration_type", portal["integration_type"]),
        )
    for k, v in data.items():
        if v is not None:
            update[k] = v

    await db.publishing_catalog.update_one({"slug": slug}, {"$set": update})
    refreshed = await db.publishing_catalog.find_one({"slug": slug}, {"_id": 0})
    return refreshed


@router.delete("/custom-portals/{slug}")
async def delete_custom_portal(
    slug: str,
    user: dict = Depends(require_roles("agency_admin", "super_admin", "branch_admin", "group_admin")),
):
    """Delete a custom portal + its associated connection.

    Deletion of the portal cascades to the connection (same agency, same slug).
    Sync logs are preserved for audit.
    """
    db = Database.get()
    aid = _agency_id(user)
    r = await db.publishing_catalog.delete_one(
        {"slug": slug, "owner_agency_id": aid, "is_custom": True}
    )
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="custom_portal_not_found")
    await db.publishing_connections.delete_many(
        {"agency_id": aid, "portal_slug": slug}
    )
    logger.info("custom_portal_deleted agency=%s slug=%s", aid, slug)
    return {"status": "ok", "slug": slug}


# ---------- FEED GENERATOR (public, no auth) ----------

feed_router = APIRouter(prefix="/publishing/feed", tags=["publishing-feed"])


@feed_router.get("/{agency_slug}.xml")
async def portals_feed(agency_slug: str, dialect: str = "osf_federata") -> Response:
    db = Database.get()
    agency = await db.agencies.find_one({"slug": agency_slug, "is_active": True})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    props = await db.properties.find(
        {"agency_id": agency["id"], "status": "active"}
    ).limit(2000).to_list(2000)
    publishable = [p for p in props if is_publishable(p)[0]]
    xml = _render_generic_rss(publishable, agency) if dialect == "generic_rss" \
        else _render_osf_federata(publishable, agency)
    return Response(content=xml, media_type="application/xml; charset=utf-8",
                    headers={"Cache-Control": "public, max-age=1800"})


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def _render_osf_federata(props: List[dict], agency: dict) -> str:
    now = datetime.now(timezone.utc).isoformat()
    parts = ['<?xml version="1.0" encoding="UTF-8"?>', "<feed>",
             f"  <agency><name>{xml_escape(agency.get('display_name',''))}</name>"
             f"<slug>{xml_escape(agency.get('slug',''))}</slug></agency>",
             f"  <generated_at>{now}</generated_at>",
             f"  <total>{len(props)}</total>", "  <properties>"]
    for p in props:
        photos_xml = "".join(
            f'<photo url="{xml_escape(ph.get("url",""))}" order="{i}"/>'
            for i, ph in enumerate(p.get("photos") or []))
        energy = (p.get("energy") or {}).get("energy_class") or ""
        parts.append(
            f'    <property id="{xml_escape(p["id"])}">'
            f'<reference>{xml_escape(p.get("reference_code") or "")}</reference>'
            f'<title>{xml_escape(p.get("title") or "")}</title>'
            f'<type>{xml_escape(p.get("property_type") or "")}</type>'
            f'<operation>{xml_escape(p.get("operation") or "sale")}</operation>'
            f'<city>{xml_escape(p.get("city") or "")}</city>'
            f'<province>{xml_escape(p.get("province") or "")}</province>'
            f'<price>{p.get("price") or ""}</price>'
            f'<rent_monthly>{p.get("rent_monthly") or ""}</rent_monthly>'
            f'<surface_sqm>{p.get("surface_sqm") or ""}</surface_sqm>'
            f'<rooms>{p.get("rooms") or ""}</rooms>'
            f'<bathrooms>{p.get("bathrooms") or ""}</bathrooms>'
            f'<energy_class>{xml_escape(energy)}</energy_class>'
            f'<description>{xml_escape((p.get("description") or "")[:2000])}</description>'
            f'<photos>{photos_xml}</photos>'
            f'</property>')
    parts.extend(["  </properties>", "</feed>"])
    return "\n".join(parts)


def _render_generic_rss(props: List[dict], agency: dict) -> str:
    now = datetime.now(timezone.utc).isoformat()
    parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0"><channel>',
             f"<title>{xml_escape(agency.get('display_name',''))}</title>",
             f"<link>https://omnia.re/agencies/{xml_escape(agency.get('slug',''))}</link>",
             f"<description>Feed immobili</description>",
             f"<lastBuildDate>{now}</lastBuildDate>"]
    for p in props:
        price = p.get("price") or p.get("rent_monthly") or 0
        parts.append(
            f"<item><guid isPermaLink=\"false\">{xml_escape(p['id'])}</guid>"
            f"<title>{xml_escape(p.get('title') or '')} - {price} EUR</title>"
            f"<link>https://omnia.re/p/{xml_escape(p['id'])}</link>"
            f"<description>{xml_escape((p.get('description') or '')[:500])}</description></item>")
    parts.append("</channel></rss>")
    return "\n".join(parts)
