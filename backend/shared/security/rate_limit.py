"""OMNIA — lightweight IP rate limiter (anti-scraping / anti-abuse).

Mongo-backed rolling window. Used on public high-volume endpoints
(ImmobilCloud search/map/contact, API gateway, valuator).
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import HTTPException, Request

from shared.db.connection import Database


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for") or ""
    if forwarded:
        return forwarded.split(",")[0].strip()[:64] or "unknown"
    if request.client and request.client.host:
        return request.client.host[:64]
    return "unknown"


async def enforce_rate_limit(
    *,
    bucket: str,
    key: str,
    max_requests: int,
    window_seconds: int = 3600,
) -> None:
    """Raise 429 if `key` exceeded `max_requests` in the rolling window for `bucket`."""
    db = Database.get()
    now = datetime.now(timezone.utc)
    since = (now - timedelta(seconds=window_seconds)).isoformat()
    ident = f"{bucket}:{key}"
    count = await db.rate_limit_events.count_documents(
        {"identifier": ident, "created_at": {"$gte": since}}
    )
    if count >= max_requests:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "bucket": bucket,
                "retry_after_seconds": window_seconds,
            },
            headers={"Retry-After": str(window_seconds)},
        )
    await db.rate_limit_events.insert_one(
        {
            "identifier": ident,
            "bucket": bucket,
            "key": key,
            "created_at": now.isoformat(),
        }
    )


async def enforce_ip_rate_limit(
    request: Request,
    *,
    bucket: str,
    max_requests: int,
    window_seconds: int = 3600,
) -> str:
    ip = client_ip(request)
    await enforce_rate_limit(
        bucket=bucket, key=ip, max_requests=max_requests, window_seconds=window_seconds
    )
    return ip
