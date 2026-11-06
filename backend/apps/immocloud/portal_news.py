"""OMNIA — Portal news box (D-139).

Aggregatore RSS server-side per ImmobilCloud: immobiliare / mutui / arredo.
Fonti gratuite curate, cache oraria, link esterni. Nessuna API a pagamento.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Query

from shared.db.connection import Database

logger = logging.getLogger("omnia.portal_news")

router = APIRouter(tags=["cloud-news"])

CACHE_KEY = "portal_news_v1"
CACHE_TTL_SECONDS = int(os.environ.get("OMNIA_PORTAL_NEWS_CACHE_S") or 3600)
MAX_ITEMS = 8
PER_FEED_CAP = 3
FETCH_TIMEOUT = 12.0

# v1: 3 feed curati (D-139). MutuiOnline/BdI/Idealista RSS non rispondono →
# Google News RSS (gratis) per mutui; Casa24 + Interni per casa/arredo.
FEEDS: List[Dict[str, str]] = [
    {
        "id": "casa24",
        "source": "Casa24 · Il Sole 24 Ore",
        "category": "immobiliare",
        "url": "https://www.ilsole24ore.com/rss/casa.xml",
    },
    {
        "id": "gnews_mutui",
        "source": "Rassegna mutui",
        "category": "mutui",
        "url": "https://news.google.com/rss/search?q=mutui+casa+Italia&hl=it&gl=IT&ceid=IT:it",
    },
    {
        "id": "interni",
        "source": "Interni Magazine",
        "category": "arredo",
        "url": "https://www.internimagazine.it/feed/",
    },
]

_UA = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; OMNIA-NewsBot/1.0; "
        "+https://cloud.omniarealestateecosystem.it)"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

_refresh_lock = asyncio.Lock()
_mem_cache: Optional[Dict[str, Any]] = None


def news_enabled() -> bool:
    raw = (os.environ.get("OMNIA_PORTAL_NEWS") or "1").strip().lower()
    return raw not in {"0", "false", "off", "no"}


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def _text(el: Optional[ET.Element]) -> str:
    if el is None:
        return ""
    if el.text and el.text.strip():
        return el.text.strip()
    return "".join(el.itertext()).strip()


def _parse_date(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    try:
        # Atom often uses ISO-8601
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return None


def _item_id(url: str, title: str) -> str:
    return hashlib.sha1(f"{url}|{title}".encode("utf-8")).hexdigest()[:16]


def _clean_title(title: str, source_label: str) -> str:
    t = _strip_html(title)
    # Google News: "Titolo - Fonte"
    if " - " in t and source_label.startswith("Rassegna"):
        t = t.rsplit(" - ", 1)[0].strip()
    return t[:180]


def _is_http_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False


def parse_feed_xml(content: bytes, feed_meta: Dict[str, str]) -> List[Dict[str, Any]]:
    """Parse RSS 2.0 or Atom. Pure stdlib — no feedparser dependency."""
    root = ET.fromstring(content)
    items: List[Dict[str, Any]] = []

    # RSS
    for node in root.findall(".//item"):
        title = _clean_title(_text(node.find("title")), feed_meta["source"])
        link = _text(node.find("link")) or _text(node.find("guid"))
        if not title or not _is_http_url(link):
            continue
        summary = _strip_html(_text(node.find("description")))[:240]
        published = _parse_date(_text(node.find("pubDate")))
        items.append(
            {
                "id": _item_id(link, title),
                "title": title,
                "url": link,
                "source": feed_meta["source"],
                "category": feed_meta["category"],
                "feed_id": feed_meta["id"],
                "published_at": published,
                "summary": summary or None,
            }
        )

    if items:
        return items

    # Atom
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for node in root.findall(".//a:entry", ns) or root.findall(
        ".//{http://www.w3.org/2005/Atom}entry"
    ):
        title = _clean_title(_text(node.find("{http://www.w3.org/2005/Atom}title")), feed_meta["source"])
        link_el = node.find("{http://www.w3.org/2005/Atom}link[@rel='alternate']")
        if link_el is None:
            link_el = node.find("{http://www.w3.org/2005/Atom}link")
        link = (link_el.get("href") if link_el is not None else "") or ""
        if not title or not _is_http_url(link):
            continue
        summary = _strip_html(
            _text(node.find("{http://www.w3.org/2005/Atom}summary"))
            or _text(node.find("{http://www.w3.org/2005/Atom}content"))
        )[:240]
        published = _parse_date(
            _text(node.find("{http://www.w3.org/2005/Atom}published"))
            or _text(node.find("{http://www.w3.org/2005/Atom}updated"))
        )
        items.append(
            {
                "id": _item_id(link, title),
                "title": title,
                "url": link,
                "source": feed_meta["source"],
                "category": feed_meta["category"],
                "feed_id": feed_meta["id"],
                "published_at": published,
                "summary": summary or None,
            }
        )
    return items


async def _fetch_one(client: httpx.AsyncClient, feed_meta: Dict[str, str]) -> List[Dict[str, Any]]:
    try:
        r = await client.get(feed_meta["url"], headers=_UA)
        if r.status_code != 200 or not r.content:
            logger.warning("portal_news feed %s HTTP %s", feed_meta["id"], r.status_code)
            return []
        return parse_feed_xml(r.content, feed_meta)[: PER_FEED_CAP * 2]
    except Exception as exc:
        logger.warning("portal_news feed %s failed: %s", feed_meta["id"], exc)
        return []


def merge_items(per_feed: List[List[Dict[str, Any]]], limit: int = MAX_ITEMS) -> List[Dict[str, Any]]:
    """Round-robin across feeds (mix categorie), dedupe by URL. Per-feed già per data."""
    # Newest first inside each feed before interleave
    buckets: List[List[Dict[str, Any]]] = []
    for chunk in per_feed:
        if not chunk:
            continue
        ordered = sorted(
            chunk,
            key=lambda it: it.get("published_at") or "",
            reverse=True,
        )[:PER_FEED_CAP]
        buckets.append(list(ordered))

    interleaved: List[Dict[str, Any]] = []
    seen_urls: set = set()
    while buckets and len(interleaved) < limit:
        next_round: List[List[Dict[str, Any]]] = []
        for bucket in buckets:
            item = bucket.pop(0)
            url = item.get("url") or ""
            if url in seen_urls:
                if bucket:
                    next_round.append(bucket)
                continue
            seen_urls.add(url)
            interleaved.append(item)
            if bucket and len(interleaved) < limit:
                next_round.append(bucket)
        buckets = next_round
    return interleaved[:limit]


async def fetch_fresh(limit: int = MAX_ITEMS) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=FETCH_TIMEOUT, follow_redirects=True) as client:
        chunks = await asyncio.gather(*[_fetch_one(client, f) for f in FEEDS])
    items = merge_items(list(chunks), limit=limit)
    now = datetime.now(timezone.utc).isoformat()
    return {
        "enabled": True,
        "items": items,
        "cached_at": now,
        "sources": [{"id": f["id"], "source": f["source"], "category": f["category"]} for f in FEEDS],
        "stale": False,
    }


async def _load_mongo_cache() -> Optional[Dict[str, Any]]:
    try:
        db = Database.get()
        doc = await db.portal_news_cache.find_one({"_id": CACHE_KEY}, {"_id": 0})
        return doc
    except Exception as exc:
        logger.warning("portal_news mongo read failed: %s", exc)
        return None


async def _save_mongo_cache(payload: Dict[str, Any]) -> None:
    try:
        db = Database.get()
        doc = {**payload, "_id": CACHE_KEY, "updated_at": payload.get("cached_at")}
        await db.portal_news_cache.replace_one({"_id": CACHE_KEY}, doc, upsert=True)
    except Exception as exc:
        logger.warning("portal_news mongo write failed: %s", exc)


def _cache_fresh(payload: Optional[Dict[str, Any]]) -> bool:
    if not payload or not payload.get("items"):
        return False
    raw = payload.get("cached_at")
    if not raw:
        return False
    try:
        cached_at = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except Exception:
        return False
    age = datetime.now(timezone.utc) - cached_at.astimezone(timezone.utc)
    return age <= timedelta(seconds=CACHE_TTL_SECONDS)


async def get_news_bundle(limit: int = MAX_ITEMS, category: Optional[str] = None) -> Dict[str, Any]:
    global _mem_cache

    if not news_enabled():
        return {"enabled": False, "items": [], "cached_at": None, "sources": [], "stale": False}

    # 1) memory
    if _cache_fresh(_mem_cache):
        payload = dict(_mem_cache or {})
    else:
        # 2) mongo
        mongo_doc = await _load_mongo_cache()
        if _cache_fresh(mongo_doc):
            _mem_cache = mongo_doc
            payload = dict(mongo_doc or {})
        else:
            # 3) refresh (single-flight)
            async with _refresh_lock:
                if _cache_fresh(_mem_cache):
                    payload = dict(_mem_cache or {})
                else:
                    try:
                        fresh = await fetch_fresh(limit=MAX_ITEMS)
                        if fresh.get("items"):
                            _mem_cache = fresh
                            await _save_mongo_cache(fresh)
                            payload = fresh
                        elif mongo_doc and mongo_doc.get("items"):
                            # keep stale rather than empty
                            payload = {**mongo_doc, "stale": True}
                            _mem_cache = payload
                        elif _mem_cache and _mem_cache.get("items"):
                            payload = {**_mem_cache, "stale": True}
                        else:
                            payload = fresh
                    except Exception as exc:
                        logger.warning("portal_news refresh failed: %s", exc)
                        payload = mongo_doc or _mem_cache or {
                            "enabled": True,
                            "items": [],
                            "cached_at": None,
                            "sources": [],
                            "stale": True,
                        }

    items = list(payload.get("items") or [])
    if category:
        cat = category.strip().lower()
        items = [i for i in items if (i.get("category") or "").lower() == cat]
    items = items[: max(1, min(limit, MAX_ITEMS))]

    return {
        "enabled": True,
        "items": items,
        "cached_at": payload.get("cached_at"),
        "sources": payload.get("sources") or [],
        "stale": bool(payload.get("stale")),
    }


@router.get("/news")
async def portal_news(
    limit: int = Query(8, ge=1, le=8),
    category: Optional[str] = Query(
        None,
        pattern="^(immobiliare|mutui|arredo)$",
        description="Filtro opzionale per categoria",
    ),
):
    """Box news dinamico ImmobilCloud (D-139). Pubblico, cache ~1h."""
    return await get_news_bundle(limit=limit, category=category)
