"""OMNIA — Public Feed (OSF Standard Feed v1.0) — M2.S5 Layer B, D-028.

Public endpoints (NO auth) for external portals to pull agency property feeds.

Endpoints (mounted at /api/feed/...):
  GET /api/feed/{slug}.xml   → OSF v1.0 XML
  GET /api/feed/{slug}.json  → OSF v1.0 JSON
  GET /api/feed/schema/osf-v1.json  → JSON Schema documentation

The "secret sauce" (D-028):
  - Clean schema (strings, not opaque legacy numeric codes)
  - Dual format (XML + JSON natively)
  - AI-extended namespace (omnia:ai_description, omnia:lead_score_avg)
  - Documented JSON Schema → invites portals to adopt OMNIA as standard
"""
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Response

from shared.db.connection import Database

router = APIRouter(prefix="/feed", tags=["feed"])

OSF_VERSION = "1.0"
OSF_NS = "https://omniarealestateecosystem.it/schema/osf-v1"
OSF_EXT_NS = "https://omniarealestateecosystem.it/schema/osf-v1#ext"


async def _resolve_agency(slug: str) -> Dict[str, Any]:
    """Find an active agency by slug. 404 if missing."""
    db = Database.get()
    agency = await db.agencies.find_one({"slug": slug, "is_active": True}, {"_id": 0})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    return agency


async def _list_active_properties(agency_id: str) -> List[Dict[str, Any]]:
    db = Database.get()
    cursor = db.properties.find(
        {"agency_id": agency_id, "status": "active"},
        {"_id": 0, "owner": 0},  # never leak owner block externally
    ).sort("updated_at", -1)
    return await cursor.to_list(length=5000)


def _property_to_dict(p: Dict[str, Any]) -> Dict[str, Any]:
    """Map a Property document → OSF v1.0 dict."""
    energy = p.get("energy") or {}
    photos = p.get("photos") or []
    # features dict {key: bool} → list of enabled keys
    feats_raw = p.get("features") or {}
    if isinstance(feats_raw, dict):
        feats = [k for k, v in feats_raw.items() if v]
    elif isinstance(feats_raw, list):
        feats = list(feats_raw)
    else:
        feats = []

    return {
        "id": p["id"],
        "reference_code": p.get("reference_code") or None,
        "title": p.get("title"),
        "description": {
            "it": p.get("description"),
            # M2.S5 phase 1 = single language; multilingua estendibile su richiesta cliente (D-028)
        },
        "type": p.get("property_type"),
        "operation": p.get("operation"),
        "status": p.get("status"),
        "price": {
            "amount": p.get("price"),
            "currency": "EUR",
            "negotiable": bool(p.get("price_negotiable")),
        } if p.get("price") is not None else None,
        "rent_monthly": {
            "amount": p.get("rent_monthly"),
            "currency": "EUR",
        } if p.get("rent_monthly") is not None else None,
        "condo_fees": p.get("condo_fees"),
        "surface_sqm": p.get("surface_sqm"),
        "rooms": p.get("rooms"),
        "bedrooms": p.get("bedrooms"),
        "bathrooms": p.get("bathrooms"),
        "floor": p.get("floor"),
        "total_floors": p.get("total_floors"),
        "year_built": p.get("year_built"),
        "furnished": p.get("furnished"),
        "condition": p.get("condition"),
        "location": {
            "city": p.get("city"),
            "province": p.get("province"),
            "postal_code": p.get("postal_code"),
            "zone": p.get("zone"),
            "address": p.get("address") if not p.get("hide_address") else None,
            "address_hidden": bool(p.get("hide_address")),
            "coordinates": None,  # M3 GIS
        },
        "energy": {
            "class": energy.get("energy_class"),
            "value_kwh_m2_year": energy.get("energy_value"),
            "heating": energy.get("heating"),
        },
        "features": feats,
        "photos": {
            "count": len(photos),
            "cover_index": next(
                (i for i, ph in enumerate(photos) if ph.get("is_cover")),
                0 if photos else None,
            ),
            # NOTE: actual binary URLs land in M3 (S3 migration). For now we expose:
            "items": [
                {
                    "order": i,
                    "is_cover": bool(ph.get("is_cover")),
                    "url": f"/api/public/property/{p['id']}/photo/{i}",
                } for i, ph in enumerate(photos)
            ],
        },
        "virtual_tour_url": p.get("virtual_tour_url"),
        "omnia_ext": {
            "is_exclusive": bool(p.get("is_exclusive")),
            "created_at": p.get("created_at"),
            "updated_at": p.get("updated_at"),
        },
    }


# ---------------- JSON endpoint ----------------

@router.get("/{slug}.json")
async def feed_json(slug: str):
    agency = await _resolve_agency(slug)
    properties = await _list_active_properties(agency["id"])
    body = {
        "feed": {
            "schema": f"{OSF_NS}",
            "version": OSF_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "agency": {
                "id": agency["id"],
                "slug": agency["slug"],
                "name": agency.get("display_name"),
            },
            "properties": [_property_to_dict(p) for p in properties],
            "count": len(properties),
        }
    }
    return body


# ---------------- XML endpoint ----------------

def _set(parent: ET.Element, tag: str, value: Any, attrs: Optional[Dict[str, str]] = None) -> Optional[ET.Element]:
    if value is None or value == "":
        return None
    el = ET.SubElement(parent, tag, attrs or {})
    el.text = str(value)
    return el


def _build_xml(agency: Dict[str, Any], properties: List[Dict[str, Any]]) -> bytes:
    root = ET.Element(
        "feed",
        {
            "xmlns": OSF_NS,
            "xmlns:omnia": OSF_EXT_NS,
            "version": OSF_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    ag_el = ET.SubElement(root, "agency")
    _set(ag_el, "id", agency["id"])
    _set(ag_el, "slug", agency["slug"])
    _set(ag_el, "name", agency.get("display_name"))

    props_el = ET.SubElement(root, "properties", {"count": str(len(properties))})
    for p in properties:
        d = _property_to_dict(p)
        prop_el = ET.SubElement(props_el, "property", {"id": d["id"]})
        _set(prop_el, "reference_code", d["reference_code"])
        _set(prop_el, "title", d["title"])
        if d["description"].get("it"):
            _set(prop_el, "description", d["description"]["it"], {"lang": "it"})
        _set(prop_el, "type", d["type"])
        _set(prop_el, "operation", d["operation"])
        _set(prop_el, "status", d["status"])
        if d["price"]:
            _set(prop_el, "price", d["price"]["amount"],
                 {"currency": d["price"]["currency"], "negotiable": str(d["price"]["negotiable"]).lower()})
        if d["rent_monthly"]:
            _set(prop_el, "rent_monthly", d["rent_monthly"]["amount"], {"currency": "EUR"})
        _set(prop_el, "condo_fees", d["condo_fees"])
        _set(prop_el, "surface_sqm", d["surface_sqm"])
        _set(prop_el, "rooms", d["rooms"])
        _set(prop_el, "bedrooms", d["bedrooms"])
        _set(prop_el, "bathrooms", d["bathrooms"])
        _set(prop_el, "floor", d["floor"])
        _set(prop_el, "total_floors", d["total_floors"])
        _set(prop_el, "year_built", d["year_built"])
        _set(prop_el, "furnished", d["furnished"])
        _set(prop_el, "condition", d["condition"])

        loc = ET.SubElement(prop_el, "location")
        _set(loc, "city", d["location"]["city"])
        _set(loc, "province", d["location"]["province"])
        _set(loc, "postal_code", d["location"]["postal_code"])
        _set(loc, "zone", d["location"]["zone"])
        if d["location"]["address"]:
            _set(loc, "address", d["location"]["address"])
        _set(loc, "address_hidden", str(d["location"]["address_hidden"]).lower())

        en = ET.SubElement(prop_el, "energy")
        _set(en, "class", d["energy"]["class"])
        _set(en, "value_kwh_m2_year", d["energy"]["value_kwh_m2_year"])
        _set(en, "heating", d["energy"]["heating"])

        if d["features"]:
            feats_el = ET.SubElement(prop_el, "features")
            for f in d["features"]:
                _set(feats_el, "feature", f)

        if d["photos"]["count"] > 0:
            ph_el = ET.SubElement(
                prop_el, "photos",
                {"count": str(d["photos"]["count"]),
                 "cover_index": str(d["photos"]["cover_index"])},
            )
            for ph in d["photos"]["items"]:
                _set(ph_el, "photo", None, {
                    "order": str(ph["order"]),
                    "is_cover": str(ph["is_cover"]).lower(),
                    "url": ph["url"],
                })
                # Empty element with attrs
                ph_el[-1].text = ""

        if d.get("virtual_tour_url"):
            _set(prop_el, "virtual_tour_url", d["virtual_tour_url"])
        # AI-extended namespace
        _set(prop_el, "omnia:is_exclusive", str(d["omnia_ext"]["is_exclusive"]).lower())
        _set(prop_el, "omnia:created_at", d["omnia_ext"]["created_at"])
        _set(prop_el, "omnia:updated_at", d["omnia_ext"]["updated_at"])

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


@router.get("/{slug}.xml")
async def feed_xml(slug: str):
    agency = await _resolve_agency(slug)
    properties = await _list_active_properties(agency["id"])
    xml_bytes = _build_xml(agency, properties)
    return Response(content=xml_bytes, media_type="application/xml; charset=utf-8")


# ---------------- Schema documentation ----------------

@router.get("/schema/osf-v1.json")
async def osf_schema():
    """Public JSON Schema for OSF v1.0 — invites portals to adopt as standard."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OSF_NS}/schema/osf-v1.json",
        "title": "OMNIA Standard Feed v1.0",
        "description": "Open standard feed for real estate property listings, AI-extended.",
        "version": OSF_VERSION,
        "type": "object",
        "properties": {
            "feed": {
                "type": "object",
                "required": ["version", "agency", "properties"],
                "properties": {
                    "version": {"const": "1.0"},
                    "generated_at": {"type": "string", "format": "date-time"},
                    "agency": {
                        "type": "object",
                        "required": ["id", "slug", "name"],
                        "properties": {
                            "id": {"type": "string"},
                            "slug": {"type": "string"},
                            "name": {"type": "string"},
                        },
                    },
                    "properties": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/property"},
                    },
                    "count": {"type": "integer", "minimum": 0},
                },
            }
        },
        "$defs": {
            "property": {
                "type": "object",
                "required": ["id", "title", "type", "operation", "status"],
                "properties": {
                    "id": {"type": "string"},
                    "reference_code": {"type": ["string", "null"]},
                    "title": {"type": "string"},
                    "type": {"type": "string", "description": "appartamento|villa|loft|attico|… (strings, NOT numeric codes)"},
                    "operation": {"type": "string", "enum": ["sale", "rent", "rent_to_buy", "auction"]},
                    "status": {"type": "string", "enum": ["draft", "active", "reserved", "sold", "rented", "withdrawn"]},
                    "price": {"type": ["object", "null"]},
                    "surface_sqm": {"type": ["number", "null"]},
                    "rooms": {"type": ["integer", "null"]},
                    "location": {"type": "object"},
                    "energy": {"type": "object"},
                    "features": {"type": "array", "items": {"type": "string"}},
                    "photos": {"type": "object"},
                    "omnia_ext": {"type": "object", "description": "OMNIA-extended fields (AI-friendly)"},
                },
            }
        },
    }
