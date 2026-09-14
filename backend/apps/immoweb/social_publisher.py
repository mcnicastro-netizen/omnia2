"""OMNIA — Social Publisher (M2.6c, Sprint 1 Item #2).

Auto-publish properties on Facebook Pages, Instagram Business and Telegram
channels via the official APIs (Meta Graph v20 + Telegram Bot API).

Design constraints:
- Multi-tenant: each agency stores its own encrypted credentials (AES-GCM via
  shared.utils.crypto.encrypt_dict, no plaintext ever returned).
- On-demand publish (POST /social/publish) — the scheduled sync in
  sync_engine.py stays focused on feed_pull portals; social is push.
- White label (D-041): every channel operates under the agency's own Meta app /
  Telegram bot. OMNIA never posts under its own identity.
- Audit-first: every attempt (success or fail) writes to social_posts.

Collections owned:
- social_channels: agency channels catalog (one row per agency+channel_type)
- social_posts: per-post audit log

Router mounted at /api/app/publishing/social/*
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field

from shared.auth.dependencies import require_roles
from shared.db.connection import Database
from shared.models.base import OmniaBaseModel, TimestampedModel, utcnow_iso
from shared.utils.crypto import decrypt_dict, encrypt_dict

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/publishing/social", tags=["publishing-social"])


# ---------------------------------------------------------------------------
# Constants & catalog
# ---------------------------------------------------------------------------

GRAPH_BASE = "https://graph.facebook.com/v20.0"
TELEGRAM_BASE = "https://api.telegram.org"
HTTP_TIMEOUT = 20.0
CAPTION_MAX = 2000  # safe budget across FB (5000) / IG (2200) / TG (1024)
TELEGRAM_CAPTION_MAX = 1024

ChannelType = Literal["facebook_page", "instagram_business", "telegram"]

SOCIAL_CATALOG: List[Dict[str, Any]] = [
    {
        "channel": "facebook_page",
        "name": "Facebook Page",
        "kind": "meta",
        "credential_fields": [
            {"name": "page_id", "label": "Facebook Page ID", "type": "text"},
            {"name": "access_token", "label": "Page Access Token", "type": "text"},
        ],
        "notes": "Pubblica sulla tua Pagina Facebook. Serve un Page Access Token con permessi pages_manage_posts.",
    },
    {
        "channel": "instagram_business",
        "name": "Instagram Business",
        "kind": "meta",
        "credential_fields": [
            {"name": "ig_user_id", "label": "Instagram Business ID", "type": "text"},
            {"name": "access_token", "label": "Access Token (Page)", "type": "text"},
        ],
        "notes": "Richiede un account IG Business collegato a una Pagina Facebook. Le foto devono essere HTTPS pubbliche.",
    },
    {
        "channel": "telegram",
        "name": "Telegram Channel",
        "kind": "telegram",
        "credential_fields": [
            {"name": "bot_token", "label": "Bot Token", "type": "text"},
            {"name": "chat_id", "label": "Chat ID (@canale o numerico)", "type": "text"},
        ],
        "notes": "Il bot deve essere admin del canale. Ottieni il token da @BotFather in Telegram.",
    },
]


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SocialChannel(TimestampedModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    agency_id: str
    channel: ChannelType
    status: str = Field(default="pending")  # active | pending | disabled | error
    credentials_encrypted: Optional[str] = None
    display_name: Optional[str] = None      # e.g. Facebook page name / IG handle / TG channel title
    last_used_at: Optional[str] = None
    last_error: Optional[str] = None
    posts_ok: int = 0
    posts_failed: int = 0


class SocialPost(TimestampedModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    agency_id: str
    channel: ChannelType
    property_id: Optional[str] = None
    caption: str = ""
    image_url: Optional[str] = None
    listing_url: Optional[str] = None
    status: str = "success"  # success | failed
    external_id: Optional[str] = None
    error: Optional[str] = None


class SocialChannelCreate(OmniaBaseModel):
    channel: ChannelType
    credentials: Dict[str, str] = Field(default_factory=dict)


class SocialChannelUpdate(OmniaBaseModel):
    credentials: Optional[Dict[str, str]] = None
    status: Optional[str] = None


class SocialPublishRequest(OmniaBaseModel):
    property_id: Optional[str] = None
    channels: List[ChannelType] = Field(default_factory=list)
    caption: Optional[str] = None
    image_url: Optional[str] = None
    listing_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

from shared.auth.tenant import require_agency_404 as _agency_id


def _public_channel(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k not in ("_id", "credentials_encrypted")}


def _valid_channel(ch: str) -> None:
    if ch not in {"facebook_page", "instagram_business", "telegram"}:
        raise HTTPException(status_code=422, detail="unsupported_channel")


def _require_creds(payload: Dict[str, str], required: List[str]) -> None:
    missing = [k for k in required if not (payload.get(k) or "").strip()]
    if missing:
        raise HTTPException(status_code=422, detail=f"missing_credentials:{','.join(missing)}")


def _build_default_caption(prop: dict) -> str:
    """Build a compact, italian caption from a property document."""
    if not prop:
        return ""
    lines: List[str] = []
    title = (prop.get("title") or "").strip()
    if title:
        lines.append(title)
    where_parts = [p for p in (prop.get("city"), prop.get("province")) if p]
    if where_parts:
        lines.append("📍 " + ", ".join(where_parts))
    price = prop.get("price") or prop.get("rent_monthly")
    if price:
        try:
            price_int = int(float(price))
            suffix = "€/mese" if prop.get("rent_monthly") and not prop.get("price") else "€"
            lines.append(f"💶 {price_int:,}".replace(",", ".") + f" {suffix}")
        except (TypeError, ValueError):
            pass
    surface = prop.get("surface_sqm")
    rooms = prop.get("rooms")
    specs = []
    if surface:
        specs.append(f"{surface} mq")
    if rooms:
        specs.append(f"{rooms} locali")
    if specs:
        lines.append("📐 " + " · ".join(specs))
    desc = (prop.get("description") or "").strip()
    if desc:
        lines.append("")
        lines.append(desc[:800])
    return "\n".join(lines)


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _classify_meta_error(exc: Exception, payload: Any) -> str:
    """Turn a Meta HTTP error payload into a human message."""
    if isinstance(payload, dict) and "error" in payload:
        err = payload["error"]
        return f"meta_error:{err.get('code','?')}:{err.get('message','unknown')}"
    return f"http_error:{exc}"


# ---------------------------------------------------------------------------
# HTTP adapters (async, one shot — retry left to the caller/UI)
# ---------------------------------------------------------------------------

async def _http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=HTTP_TIMEOUT)


async def meta_get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    async with await _http_client() as client:
        r = await client.get(f"{GRAPH_BASE}{path}", params=params)
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=_classify_meta_error(RuntimeError(r.status_code), data))
    return data


async def meta_post(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    async with await _http_client() as client:
        r = await client.post(f"{GRAPH_BASE}{path}", params=params)
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=_classify_meta_error(RuntimeError(r.status_code), data))
    return data


async def telegram_call(bot_token: str, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    async with await _http_client() as client:
        r = await client.post(f"{TELEGRAM_BASE}/bot{bot_token}/{method}", json=payload)
    try:
        data = r.json()
    except Exception:
        data = {}
    if not data or not data.get("ok"):
        desc = (data or {}).get("description") or f"http_{r.status_code}"
        raise HTTPException(status_code=502, detail=f"telegram_error:{desc}")
    return data.get("result", {})


# --- Validation --------------------------------------------------------------

async def validate_facebook_page(page_id: str, access_token: str) -> Dict[str, Any]:
    data = await meta_get("/me", {"access_token": access_token, "fields": "id,name"})
    if page_id and str(data.get("id")) != str(page_id):
        raise HTTPException(status_code=422, detail="page_id_mismatch")
    return {"ok": True, "id": data.get("id"), "name": data.get("name")}


async def validate_instagram_business(ig_user_id: str, access_token: str) -> Dict[str, Any]:
    data = await meta_get(
        f"/{ig_user_id}",
        {"access_token": access_token, "fields": "id,username"},
    )
    return {"ok": True, "id": data.get("id"), "username": data.get("username")}


async def validate_telegram(bot_token: str, chat_id: str) -> Dict[str, Any]:
    me = await telegram_call(bot_token, "getMe", {})
    return {"ok": True, "bot_username": me.get("username"), "chat_id": chat_id}


# --- Publish -----------------------------------------------------------------

async def publish_facebook_page(
    page_id: str, access_token: str, caption: str, image_url: Optional[str], listing_url: Optional[str]
) -> Dict[str, Any]:
    caption = _truncate(caption or "", 4900)
    if image_url:
        result = await meta_post(
            f"/{page_id}/photos",
            {"url": image_url, "caption": caption, "access_token": access_token},
        )
        return {"external_id": result.get("id") or result.get("post_id"), "raw": result}
    # Text/link post fallback
    params = {"message": caption, "access_token": access_token}
    if listing_url:
        params["link"] = listing_url
    result = await meta_post(f"/{page_id}/feed", params)
    return {"external_id": result.get("id"), "raw": result}


async def publish_instagram_business(
    ig_user_id: str, access_token: str, caption: str, image_url: str
) -> Dict[str, Any]:
    if not image_url:
        raise HTTPException(status_code=422, detail="instagram_requires_image")
    container = await meta_post(
        f"/{ig_user_id}/media",
        {"image_url": image_url, "caption": _truncate(caption or "", 2100), "access_token": access_token},
    )
    creation_id = container.get("id")
    if not creation_id:
        raise HTTPException(status_code=502, detail="instagram_container_missing_id")
    published = await meta_post(
        f"/{ig_user_id}/media_publish",
        {"creation_id": creation_id, "access_token": access_token},
    )
    return {"external_id": published.get("id"), "raw": published, "container_id": creation_id}


async def publish_telegram(
    bot_token: str, chat_id: str, caption: str, image_url: Optional[str]
) -> Dict[str, Any]:
    if image_url:
        result = await telegram_call(bot_token, "sendPhoto", {
            "chat_id": chat_id,
            "photo": image_url,
            "caption": _truncate(caption or "", TELEGRAM_CAPTION_MAX),
        })
    else:
        result = await telegram_call(bot_token, "sendMessage", {
            "chat_id": chat_id,
            "text": _truncate(caption or " ", 4096),
        })
    return {"external_id": str(result.get("message_id")), "raw": result}


# ---------------------------------------------------------------------------
# Router endpoints
# ---------------------------------------------------------------------------

_ROLES = ("agency_admin", "super_admin", "branch_admin", "group_admin")


@router.get("/catalog")
async def social_catalog(user: dict = Depends(require_roles(*_ROLES))):
    """Static catalog of supported channels + credential fields."""
    return {"items": SOCIAL_CATALOG, "total": len(SOCIAL_CATALOG)}


@router.get("/channels")
async def list_channels(user: dict = Depends(require_roles(*_ROLES))):
    db = Database.get()
    aid = _agency_id(user)
    docs = await db.social_channels.find({"agency_id": aid}).sort("created_at", -1).to_list(50)
    return {"items": [_public_channel(d) for d in docs], "total": len(docs)}


@router.post("/channels", status_code=201)
async def create_channel(
    payload: SocialChannelCreate,
    user: dict = Depends(require_roles(*_ROLES)),
):
    _valid_channel(payload.channel)
    db = Database.get()
    aid = _agency_id(user)
    existing = await db.social_channels.find_one({"agency_id": aid, "channel": payload.channel})
    if existing:
        raise HTTPException(status_code=409, detail="channel_already_configured")

    required = {
        "facebook_page": ["page_id", "access_token"],
        "instagram_business": ["ig_user_id", "access_token"],
        "telegram": ["bot_token", "chat_id"],
    }[payload.channel]
    _require_creds(payload.credentials, required)

    ch = SocialChannel(
        agency_id=aid,
        channel=payload.channel,
        status="active",
        credentials_encrypted=encrypt_dict(payload.credentials),
    )
    doc = ch.model_dump()
    await db.social_channels.insert_one(doc)
    logger.info("social_channel_created agency=%s channel=%s", aid, payload.channel)
    return _public_channel(doc)


@router.patch("/channels/{channel_id}")
async def update_channel(
    channel_id: str,
    payload: SocialChannelUpdate,
    user: dict = Depends(require_roles(*_ROLES)),
):
    db = Database.get()
    aid = _agency_id(user)
    ch = await db.social_channels.find_one({"id": channel_id, "agency_id": aid})
    if not ch:
        raise HTTPException(status_code=404, detail="channel_not_found")
    update: Dict[str, Any] = {"updated_at": utcnow_iso()}
    if payload.credentials is not None:
        required = {
            "facebook_page": ["page_id", "access_token"],
            "instagram_business": ["ig_user_id", "access_token"],
            "telegram": ["bot_token", "chat_id"],
        }[ch["channel"]]
        _require_creds(payload.credentials, required)
        update["credentials_encrypted"] = encrypt_dict(payload.credentials)
        update["status"] = "active"
    if payload.status in {"active", "disabled"}:
        update["status"] = payload.status
    await db.social_channels.update_one({"id": channel_id}, {"$set": update})
    refreshed = await db.social_channels.find_one({"id": channel_id})
    return _public_channel(refreshed)


@router.delete("/channels/{channel_id}")
async def delete_channel(
    channel_id: str,
    user: dict = Depends(require_roles(*_ROLES)),
):
    db = Database.get()
    aid = _agency_id(user)
    r = await db.social_channels.delete_one({"id": channel_id, "agency_id": aid})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="channel_not_found")
    return {"status": "ok", "id": channel_id}


@router.post("/channels/{channel_id}/validate")
async def validate_channel(
    channel_id: str,
    user: dict = Depends(require_roles(*_ROLES)),
):
    db = Database.get()
    aid = _agency_id(user)
    ch = await db.social_channels.find_one({"id": channel_id, "agency_id": aid})
    if not ch:
        raise HTTPException(status_code=404, detail="channel_not_found")
    creds = decrypt_dict(ch.get("credentials_encrypted") or "")
    try:
        if ch["channel"] == "facebook_page":
            info = await validate_facebook_page(creds.get("page_id", ""), creds.get("access_token", ""))
        elif ch["channel"] == "instagram_business":
            info = await validate_instagram_business(creds.get("ig_user_id", ""), creds.get("access_token", ""))
        else:
            info = await validate_telegram(creds.get("bot_token", ""), creds.get("chat_id", ""))
    except HTTPException as e:
        await db.social_channels.update_one(
            {"id": channel_id},
            {"$set": {"status": "error", "last_error": str(e.detail), "updated_at": utcnow_iso()}},
        )
        raise
    display = info.get("name") or info.get("username") or info.get("bot_username")
    await db.social_channels.update_one(
        {"id": channel_id},
        {"$set": {"status": "active", "display_name": display, "last_error": None, "updated_at": utcnow_iso()}},
    )
    return info


@router.post("/publish")
async def publish_property(
    payload: SocialPublishRequest,
    user: dict = Depends(require_roles(*_ROLES)),
):
    """Publish a property to selected social channels.

    Property is loaded from Mongo when property_id is given, otherwise the
    caller must provide caption + image_url explicitly (used by dry-run tests).
    Each channel produces a social_posts row (success or failure).
    """
    db = Database.get()
    aid = _agency_id(user)
    if not payload.channels:
        raise HTTPException(status_code=422, detail="channels_required")
    for c in payload.channels:
        _valid_channel(c)

    prop: Dict[str, Any] = {}
    if payload.property_id:
        prop = await db.properties.find_one({"id": payload.property_id, "agency_id": aid}) or {}
        if not prop:
            raise HTTPException(status_code=404, detail="property_not_found")

    caption = payload.caption or _build_default_caption(prop) or ""
    image_url = payload.image_url
    if not image_url and prop.get("photos"):
        image_url = (prop["photos"][0] or {}).get("url")
    listing_url = payload.listing_url

    results: Dict[str, Any] = {}
    for ch_type in payload.channels:
        ch_doc = await db.social_channels.find_one({"agency_id": aid, "channel": ch_type, "status": "active"})
        if not ch_doc:
            results[ch_type] = {"ok": False, "error": "channel_not_configured"}
            await _record_post(db, aid, ch_type, payload.property_id, caption, image_url, listing_url,
                               status="failed", error="channel_not_configured")
            continue

        creds = decrypt_dict(ch_doc.get("credentials_encrypted") or "")
        try:
            if ch_type == "facebook_page":
                out = await publish_facebook_page(
                    creds.get("page_id", ""), creds.get("access_token", ""),
                    caption, image_url, listing_url,
                )
            elif ch_type == "instagram_business":
                out = await publish_instagram_business(
                    creds.get("ig_user_id", ""), creds.get("access_token", ""),
                    caption, image_url or "",
                )
            else:
                out = await publish_telegram(
                    creds.get("bot_token", ""), creds.get("chat_id", ""),
                    caption, image_url,
                )
        except HTTPException as e:
            err_msg = str(e.detail)
            results[ch_type] = {"ok": False, "error": err_msg}
            await _record_post(db, aid, ch_type, payload.property_id, caption, image_url, listing_url,
                               status="failed", error=err_msg)
            await db.social_channels.update_one(
                {"id": ch_doc["id"]},
                {"$set": {"last_error": err_msg, "status": "error", "updated_at": utcnow_iso()},
                 "$inc": {"posts_failed": 1}},
            )
            continue
        except Exception as e:  # network, DNS, etc.
            err_msg = f"unexpected:{e}"
            results[ch_type] = {"ok": False, "error": err_msg}
            await _record_post(db, aid, ch_type, payload.property_id, caption, image_url, listing_url,
                               status="failed", error=err_msg)
            continue

        external_id = out.get("external_id")
        results[ch_type] = {"ok": True, "external_id": external_id}
        await _record_post(db, aid, ch_type, payload.property_id, caption, image_url, listing_url,
                           status="success", external_id=external_id)
        await db.social_channels.update_one(
            {"id": ch_doc["id"]},
            {"$set": {"last_used_at": utcnow_iso(), "last_error": None,
                      "status": "active", "updated_at": utcnow_iso()},
             "$inc": {"posts_ok": 1}},
        )

    return {
        "property_id": payload.property_id,
        "results": results,
        "ok": all(v.get("ok") for v in results.values()) if results else False,
    }


async def _record_post(
    db, agency_id: str, channel: str, property_id: Optional[str], caption: str,
    image_url: Optional[str], listing_url: Optional[str],
    *, status: str, external_id: Optional[str] = None, error: Optional[str] = None,
) -> None:
    post = SocialPost(
        agency_id=agency_id,
        channel=channel,  # type: ignore[arg-type]
        property_id=property_id,
        caption=caption[:2000],
        image_url=image_url,
        listing_url=listing_url,
        status=status,
        external_id=external_id,
        error=error,
    )
    await db.social_posts.insert_one(post.model_dump())


@router.get("/posts")
async def list_posts(
    limit: int = 50,
    channel: Optional[ChannelType] = None,
    user: dict = Depends(require_roles(*_ROLES)),
):
    db = Database.get()
    aid = _agency_id(user)
    query: Dict[str, Any] = {"agency_id": aid}
    if channel:
        _valid_channel(channel)
        query["channel"] = channel
    docs = await db.social_posts.find(query, {"_id": 0}).sort("created_at", -1).limit(min(max(limit, 1), 200)).to_list(200)
    return {"items": docs, "total": len(docs)}
