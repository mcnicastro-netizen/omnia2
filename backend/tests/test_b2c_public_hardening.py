"""B2C ImmobilCloud public hardening — D01/D02/D03/D04 regression tests."""
from __future__ import annotations

import base64
import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shared.db.public_visibility import (
    brand_photo_filter,
    portal_photo_filter,
    public_agency_card,
    strip_internal_property_fields,
)
from shared.utils.privacy_gate import apply_privacy_view
from apps.immocloud.portal_common import _to_card, _public_photo_url


TINY_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a"
    "HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy"
    "MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIA"
    "AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAn/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEB"
    "AQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA8A/9k="
)


def test_d01_to_card_strips_agency_id():
    card = _to_card(
        {
            "id": "p1",
            "agency_id": "ag-secret",
            "title": "Villa",
            "photos": [],
            "reference_code": "OM-L-ABC123",
        },
        {"id": "ag-secret", "display_name": "Casa Roma", "slug": "casa-roma", "logo_url": "/x.png"},
    )
    assert "agency_id" not in card
    assert card["agency"]["name"] == "Casa Roma"
    assert card["agency"]["slug"] == "casa-roma"
    assert "id" not in card["agency"]
    assert card["reference_code"] == "OM-L-ABC123"


def test_d01_public_agency_card_no_internal_id():
    out = public_agency_card(
        {"id": "ag1", "display_name": "A", "slug": "a", "email": "a@x.it", "phone": "06"}
    )
    assert out is not None
    assert "id" not in out
    assert out["email"] == "a@x.it"
    assert out["phone"] == "06"


def test_d01_strip_internal_property_fields():
    cleaned = strip_internal_property_fields(
        {
            "id": "p1",
            "agency_id": "ag1",
            "title": "T",
            "reference_code": "R1",
            "owner_user_id": "u1",
            "commission_pct": 3,
        }
    )
    assert "agency_id" not in cleaned
    assert "owner_user_id" not in cleaned
    assert cleaned["reference_code"] == "R1"
    assert cleaned["title"] == "T"


def test_d02_photo_filters_differ_portal_vs_brand():
    portal = portal_photo_filter("p1")
    brand = brand_photo_filter("agA", "p1")
    # Flatten $and for assertions
    def flat(f):
        out = {}
        for part in f.get("$and") or [f]:
            if isinstance(part, dict):
                out.update({k: v for k, v in part.items() if k != "$or"})
        return out

    fp, fb = flat(portal), flat(brand)
    assert fp["id"] == "p1"
    assert fp["visibility"] == "public"
    assert fp["is_listed_on_immobilcloud"] == {"$ne": False}
    assert fb["agency_id"] == "agA"
    assert "is_listed_on_immobilcloud" not in fb
    assert "privacy_level" not in fb


def test_d02_photo_url_includes_surface():
    assert "surface=portal" in _public_photo_url("p1", 0, surface="portal")


def test_d04_reference_code_visible_l1_l2():
    prop = {
        "id": "p1",
        "title": "T",
        "reference_code": "OM-L-XYZ",
        "address": "Via Segreta 1",
        "price": 100000,
        "lat": 45.46,
        "lng": 9.19,
    }
    l1 = apply_privacy_view(prop, "L1")
    l2 = apply_privacy_view(prop, "L2")
    assert l1.get("reference_code") == "OM-L-XYZ"
    assert l2.get("reference_code") == "OM-L-XYZ"
    assert "address" not in l1 or l1.get("address") is None


@pytest.mark.asyncio
async def test_d02_serve_photo_portal_denies_private():
    from apps.immoweb import site as site_mod

    db = MagicMock()
    db.properties.find_one = AsyncMock(return_value=None)
    with patch.object(site_mod.Database, "get", return_value=db):
        with pytest.raises(Exception) as ei:
            await site_mod.serve_property_photo("p-priv", 0, surface="portal")
        assert getattr(ei.value, "status_code", None) == 404 or "property_not_found" in str(
            ei.value
        )
    # Ensure portal filter was used (visibility public)
    called_flt = db.properties.find_one.await_args.args[0]
    flat = {}
    for part in called_flt.get("$and") or [called_flt]:
        if isinstance(part, dict):
            flat.update({k: v for k, v in part.items() if k != "$or"})
    assert flat.get("visibility") == "public"
    assert flat.get("id") == "p-priv"


@pytest.mark.asyncio
async def test_d02_serve_photo_brand_requires_slug():
    from apps.immoweb import site as site_mod
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as ei:
        await site_mod.serve_property_photo("p1", 0, surface="brand", agency_slug=None)
    assert ei.value.status_code == 400


@pytest.mark.asyncio
async def test_d02_serve_photo_portal_allows_public():
    from apps.immoweb import site as site_mod

    db = MagicMock()
    db.properties.find_one = AsyncMock(
        return_value={
            "id": "p-pub",
            "photos": [{"url": "data:image/jpeg;base64," + base64.b64encode(TINY_JPEG).decode(), "is_cover": True}],
        }
    )
    with patch.object(site_mod.Database, "get", return_value=db):
        resp = await site_mod.serve_property_photo("p-pub", 0, surface="portal")
    assert resp.status_code == 200
    assert b"JFIF" in resp.body or len(resp.body) > 10
    assert "must-revalidate" in resp.headers.get("cache-control", "")


def test_d03_contact_return_opaque_in_source():
    src = inspect.getsource(
        __import__("apps.immocloud.portal_contact", fromlist=["public_property_contact"])
    )
    # Agency path and private path must return only ok
    assert 'return {"ok": True}' in src
    assert 'return {"ok": True, "lead_id"' not in src
    assert 'return {"ok": True, "inquiry_id"' not in src


@pytest.mark.asyncio
async def test_d03_contact_agency_creates_lead_but_opaque_response():
    from apps.immocloud import portal_contact as pc
    from apps.immocloud.portal_contact import PropertyContactPayload

    prop = {
        "id": "p1",
        "agency_id": "agA",
        "title": "Casa",
        "is_private_listing": False,
    }
    db = MagicMock()
    db.properties.find_one = AsyncMock(side_effect=[prop, {"listing_agent_id": None}])
    db.clients.find_one = AsyncMock(return_value=None)
    db.clients.insert_one = AsyncMock()
    db.clients.update_one = AsyncMock()
    db.leads.insert_one = AsyncMock()
    db.agencies.find_one = AsyncMock(return_value={"email": "a@ex.com", "lang": "it"})
    db.properties.update_one = AsyncMock()

    payload = PropertyContactPayload(
        name="Test",
        email="buyer@example.com",
        message="Vorrei informazioni sull'immobile",
        gdpr_consent=True,
    )
    req = MagicMock()
    req.headers = {}
    req.client = MagicMock(host="127.0.0.1")

    with patch.object(pc.Database, "get", return_value=db), patch(
        "shared.security.rate_limit.enforce_ip_rate_limit", new=AsyncMock()
    ), patch.object(pc, "_schedule_lead_email"), patch(
        "apps.immoweb.client_requests_service.ensure_from_immobilcloud",
        new=AsyncMock(),
    ), patch(
        "shared.notifications.center.resolve_lead_recipients", new=AsyncMock(return_value=[])
    ), patch(
        "shared.notifications.center.notify_users", new=AsyncMock()
    ), patch(
        "shared.privacy.consent_log.log_consent", new=AsyncMock()
    ):
        out = await pc.public_property_contact("p1", payload, req)

    assert out == {"ok": True}
    assert "lead_id" not in out
    assert "client_id" not in out
    assert db.leads.insert_one.await_count == 1
    assert db.clients.insert_one.await_count == 1
