"""OMNIA — Web Push (VAPID) for B2C ImmobilCloud alerts.

Closes the Idealista/Immobiliare gap on browser push without a native app.
Subscriptions live in Mongo `push_subscriptions`.

Env:
  VAPID_PRIVATE_KEY  — PEM private key
  VAPID_PUBLIC_KEY   — URL-safe applicationServerKey (for PushManager.subscribe)
  VAPID_CLAIMS_EMAIL — mailto:… (default ops@…)
"""
from __future__ import annotations

import base64
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger("omnia.web_push")

_VAPID_CACHE_FILE = Path(__file__).resolve().parents[2] / ".vapid_local.json"


def vapid_public_key() -> str:
    return (os.environ.get("VAPID_PUBLIC_KEY") or "").strip()


def vapid_private_key() -> str:
    return (os.environ.get("VAPID_PRIVATE_KEY") or "").strip()


def vapid_mailto() -> str:
    raw = (os.environ.get("VAPID_CLAIMS_EMAIL") or "mailto:ops@omniarealestateecosystem.it").strip()
    return raw if raw.startswith("mailto:") else f"mailto:{raw}"


def is_push_configured() -> bool:
    return bool(vapid_public_key() and vapid_private_key())


def _app_server_key_from_vapid(v) -> str:
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    raw = v.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def ensure_vapid_keys() -> Dict[str, Any]:
    """Load or generate VAPID keys (process env + local cache file)."""
    if is_push_configured():
        return {"configured": True, "public_key": vapid_public_key()}

    if _VAPID_CACHE_FILE.exists():
        try:
            data = json.loads(_VAPID_CACHE_FILE.read_text())
            if data.get("public_key") and data.get("private_key"):
                os.environ["VAPID_PUBLIC_KEY"] = data["public_key"]
                os.environ["VAPID_PRIVATE_KEY"] = data["private_key"]
                return {"configured": True, "public_key": data["public_key"], "from_cache": True}
        except Exception as e:
            logger.warning("vapid cache read failed: %s", e)

    try:
        from py_vapid import Vapid
        v = Vapid()
        v.generate_keys()
        priv = v.private_pem()
        if isinstance(priv, bytes):
            priv = priv.decode("utf-8")
        pub = _app_server_key_from_vapid(v)
        os.environ["VAPID_PRIVATE_KEY"] = priv
        os.environ["VAPID_PUBLIC_KEY"] = pub
        try:
            _VAPID_CACHE_FILE.write_text(json.dumps({
                "public_key": pub,
                "private_key": priv,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }))
        except Exception as e:
            logger.warning("vapid cache write failed: %s", e)
        logger.info("VAPID keys ready (local cache %s)", _VAPID_CACHE_FILE.name)
        return {"configured": True, "public_key": pub, "generated": True}
    except Exception as e:
        logger.warning("VAPID key generation failed: %s", e)
        return {"configured": False, "error": str(e)}


async def save_subscription(*, user_id: str, subscription: dict, user_agent: str = "") -> str:
    from shared.db.connection import Database
    db = Database.get()
    endpoint = (subscription or {}).get("endpoint")
    if not endpoint or not (subscription or {}).get("keys"):
        raise ValueError("invalid_subscription")
    now = datetime.now(timezone.utc).isoformat()
    existing = await db.push_subscriptions.find_one({"user_id": user_id, "endpoint": endpoint})
    if existing:
        await db.push_subscriptions.update_one(
            {"id": existing["id"]},
            {"$set": {"subscription": subscription, "user_agent": user_agent, "updated_at": now}},
        )
        return existing["id"]
    doc_id = uuid4().hex
    await db.push_subscriptions.insert_one({
        "id": doc_id,
        "user_id": user_id,
        "endpoint": endpoint,
        "subscription": subscription,
        "user_agent": (user_agent or "")[:300],
        "created_at": now,
        "updated_at": now,
    })
    return doc_id


async def delete_subscription(*, user_id: str, endpoint: Optional[str] = None) -> int:
    from shared.db.connection import Database
    db = Database.get()
    flt: Dict[str, Any] = {"user_id": user_id}
    if endpoint:
        flt["endpoint"] = endpoint
    r = await db.push_subscriptions.delete_many(flt)
    return int(r.deleted_count or 0)


async def send_push_to_user(
    user_id: str,
    *,
    title: str,
    body: str,
    url: str = "/it/cloud/account",
) -> int:
    if not is_push_configured():
        ensure_vapid_keys()
    if not is_push_configured():
        return 0
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        logger.warning("pywebpush not installed")
        return 0

    from shared.db.connection import Database
    db = Database.get()
    subs = await db.push_subscriptions.find({"user_id": user_id}, {"_id": 0}).to_list(length=20)
    if not subs:
        return 0

    payload = json.dumps({
        "title": (title or "")[:80],
        "body": (body or "")[:160],
        "url": url,
    }, ensure_ascii=False)
    ok = 0
    for row in subs:
        try:
            webpush(
                subscription_info=row["subscription"],
                data=payload,
                vapid_private_key=vapid_private_key(),
                vapid_claims={"sub": vapid_mailto()},
            )
            ok += 1
        except WebPushException as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            logger.info("webpush fail user=%s status=%s: %s", user_id, status, e)
            if status in (404, 410):
                await db.push_subscriptions.delete_one({"id": row["id"]})
        except Exception as e:
            logger.warning("webpush error user=%s: %s", user_id, e)
    return ok
