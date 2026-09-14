"""
OMNIA — Shared MongoDB connection with tenant context
Provides:
- AsyncIOMotorClient singleton
- Tenant context (agency_id injected via middleware/JWT later)
- Helpers for tenant-aware queries
"""
import os
import logging
from contextvars import ContextVar
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Tenant context — set per request in M1.S3 (via JWT middleware)
# For now defaults to None; routes can read/set it
_current_agency_id: ContextVar[Optional[str]] = ContextVar("current_agency_id", default=None)
_current_lang: ContextVar[str] = ContextVar("current_lang", default="it")


def get_current_agency_id() -> Optional[str]:
    """Return current request's agency_id (set by JWT middleware in M1.S3)."""
    return _current_agency_id.get()


def set_current_agency_id(agency_id: Optional[str]) -> None:
    _current_agency_id.set(agency_id)


def get_current_lang() -> str:
    """Return current request's language code (it/en/es)."""
    return _current_lang.get()


def set_current_lang(lang: str) -> None:
    if lang not in ("it", "en", "es"):
        lang = "it"
    _current_lang.set(lang)


class Database:
    """MongoDB singleton wrapper with tenant-aware helpers."""

    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    def connect(cls) -> AsyncIOMotorDatabase:
        if cls._db is None:
            mongo_url = os.environ["MONGO_URL"]
            db_name = os.environ["DB_NAME"]
            cls._client = AsyncIOMotorClient(mongo_url)
            cls._db = cls._client[db_name]
            logger.info(f"Connected to MongoDB: {db_name}")
        return cls._db

    @classmethod
    def get(cls) -> AsyncIOMotorDatabase:
        if cls._db is None:
            return cls.connect()
        return cls._db

    @classmethod
    async def close(cls) -> None:
        if cls._client is not None:
            cls._client.close()
            cls._client = None
            cls._db = None

    @classmethod
    def tenant_filter(cls, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build a query filter that auto-includes agency_id from context.
        Use this on ALL tenant-aware collection queries.
        """
        agency_id = get_current_agency_id()
        base: Dict[str, Any] = {}
        if agency_id is not None:
            base["agency_id"] = agency_id
        if extra:
            base.update(extra)
        return base


async def ensure_indexes() -> None:
    """Create core indexes for tenant-aware collections.
    Called at app startup. Safe to call multiple times (idempotent).
    """
    db = Database.get()

    # Tenant-aware collections: compound index on agency_id + commonly-queried field
    tenant_indexes = {
        "properties": [("agency_id", 1), ("status", 1), ("created_at", -1)],
        "clients": [("agency_id", 1), ("email", 1)],
        "client_requests": [("agency_id", 1), ("status", 1)],
        "matches": [("agency_id", 1), ("score", -1)],
        "leads": [("agency_id", 1), ("created_at", -1)],
        "credit_transactions": [("agency_id", 1), ("created_at", -1)],
    }
    for coll_name, idx_fields in tenant_indexes.items():
        try:
            await db[coll_name].create_index(idx_fields)
        except Exception as e:
            logger.warning(f"Index creation skipped for {coll_name}: {e}")

    # Extra index on properties for seller lookup (M2.S3.5, D-026)
    try:
        await db["properties"].create_index([("agency_id", 1), ("seller_client_id", 1)])
    except Exception as e:
        logger.warning(f"properties.seller_client_id index skipped: {e}")

    # Lead score cache: TTL index on cached_at — entries expire after 24h
    try:
        await db["lead_score_cache"].create_index(
            [("agency_id", 1), ("property_id", 1), ("client_id", 1)], unique=True
        )
        await db["lead_score_cache"].create_index(
            "cached_at", expireAfterSeconds=86400  # 24h
        )
    except Exception as e:
        logger.warning(f"lead_score_cache indexes skipped: {e}")

    # Cross-tenant collections (no agency_id filter, but indexed by lookup field)
    try:
        await db["users"].create_index([("email", 1)], unique=True)
        await db["users"].create_index([("id", 1)], unique=True)
        await db["agencies"].create_index([("slug", 1)], unique=True)
        await db["agencies"].create_index([("owner_id", 1)])
        await db["agency_invites"].create_index([("token", 1)], unique=True)
        await db["agency_invites"].create_index([("agency_id", 1), ("status", 1)])
        await db["agency_invites"].create_index([("agency_id", 1), ("email", 1)])
        await db["mls_network"].create_index([("agency_a", 1), ("agency_b", 1)])
        await db["login_attempts"].create_index([("identifier", 1)])
        await db["password_reset_tokens"].create_index([("token", 1)], unique=True)
        await db["password_reset_tokens"].create_index(
            [("expires_at", 1)], expireAfterSeconds=0
        )
    except Exception as e:
        logger.warning(f"Cross-tenant index creation skipped: {e}")

    logger.info("MongoDB indexes ensured.")
