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
    _tenant_db = None

    @classmethod
    def connect(cls) -> AsyncIOMotorDatabase:
        if cls._db is None:
            mongo_url = os.environ["MONGO_URL"]
            db_name = os.environ["DB_NAME"]
            cls._client = AsyncIOMotorClient(mongo_url)
            cls._db = cls._client[db_name]
            from shared.db.tenant_guard import TenantAwareDatabase
            cls._tenant_db = TenantAwareDatabase(cls._db)
            logger.info(f"Connected to MongoDB: {db_name}")
        return cls._db

    @classmethod
    def get_raw(cls) -> AsyncIOMotorDatabase:
        """Underlying Motor DB without tenant injection (jobs, cross-tenant, auth)."""
        if cls._db is None:
            cls.connect()
        return cls._db  # type: ignore[return-value]

    @classmethod
    def get(cls):
        """Tenant-aware DB proxy (auto agency_id on tenant collections when context set)."""
        if cls._db is None:
            cls.connect()
        return cls._tenant_db if cls._tenant_db is not None else cls._db

    @classmethod
    async def close(cls) -> None:
        if cls._client is not None:
            cls._client.close()
            cls._client = None
            cls._db = None
            cls._tenant_db = None

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

    # A-017 — in-app notification inbox (per-user, newest first)
    try:
        await db["notifications"].create_index([("user_id", 1), ("created_at", -1)])
        await db["notifications"].create_index([("user_id", 1), ("read", 1), ("created_at", -1)])
    except Exception as e:
        logger.warning(f"notifications indexes skipped: {e}")

    # GDPR consent audit
    try:
        await db["consent_events"].create_index([("email", 1), ("created_at", -1)])
        await db["consent_events"].create_index([("user_id", 1), ("created_at", -1)])
        await db["consent_events"].create_index([("action", 1), ("created_at", -1)])
        # P-041 — TTL on BSON expire_at (set at insert)
        await db["consent_events"].create_index(
            [("expire_at", 1)], expireAfterSeconds=0, name="consent_expire_at_ttl"
        )
    except Exception as e:
        logger.warning(f"consent_events indexes skipped: {e}")

    # P-041 — retention TTL for Legal audit + B2C purchase ledger
    try:
        await db["al_legal_audit"].create_index(
            [("expire_at", 1)], expireAfterSeconds=0, name="al_legal_expire_at_ttl"
        )
        await db["al_legal_audit"].create_index([("user_id", 1), ("ts", -1)])
    except Exception as e:
        logger.warning(f"al_legal_audit TTL index skipped: {e}")
    try:
        await db["b2c_purchases"].create_index(
            [("expire_at", 1)], expireAfterSeconds=0, name="b2c_purchases_expire_at_ttl"
        )
        await db["b2c_purchases"].create_index([("user_id", 1), ("created_at", -1)])
    except Exception as e:
        logger.warning(f"b2c_purchases TTL index skipped: {e}")

    # Cross-tenant collections (no agency_id filter, but indexed by lookup field)
    try:
        await db["users"].create_index([("email", 1)], unique=True)
        await db["users"].create_index([("id", 1)], unique=True)
        await db["agencies"].create_index([("slug", 1)], unique=True)
        await db["agencies"].create_index([("owner_id", 1)])
        await db["agencies"].create_index([("commercial_customer_id", 1)])
        await db["agency_invites"].create_index([("token", 1)], unique=True)
        await db["agency_invites"].create_index([("agency_id", 1), ("status", 1)])
        await db["agency_invites"].create_index([("agency_id", 1), ("email", 1)])
        await db["mls_network"].create_index([("agency_a", 1), ("agency_b", 1)])
        await db["login_attempts"].create_index([("identifier", 1)])
        await db["password_reset_tokens"].create_index([("token", 1)], unique=True)
        await db["password_reset_tokens"].create_index(
            [("expires_at", 1)], expireAfterSeconds=0
        )
        await db["refresh_tokens"].create_index([("jti", 1)], unique=True)
        await db["refresh_tokens"].create_index([("user_id", 1)])
        # B01 — CommercialCustomer unique by country + normalized VAT
        await db["commercial_customers"].create_index([("id", 1)], unique=True)
        await db["commercial_customers"].create_index(
            [("country_code", 1), ("vat_number_normalized", 1)], unique=True
        )
        # B04-I — at most one Stripe Customer per CommercialCustomer
        await db["commercial_customers"].create_index(
            [("stripe_customer_id", 1)],
            unique=True,
            sparse=True,
            name="commercial_customers_stripe_customer_unique",
        )
        # B04-H2 — Main Admin binding (non-unique: D02 multi-CC)
        await db["commercial_customers"].create_index(
            [("main_admin_user_id", 1)],
            sparse=True,
            name="commercial_customers_main_admin_user",
        )
        await db["commercial_main_admin_events"].create_index([("id", 1)], unique=True)
        await db["commercial_main_admin_events"].create_index(
            [("commercial_customer_id", 1), ("created_at", 1)]
        )
        await db["commercial_main_admin_transfers"].create_index([("id", 1)], unique=True)
        await db["commercial_main_admin_transfers"].create_index(
            [("commercial_customer_id", 1), ("status", 1)]
        )
        await db["plan_catalog_versions"].create_index([("id", 1)], unique=True)
        await db["subscriptions"].create_index([("commercial_customer_id", 1)])
        # B04-II — central wallet / lots / allocations / ledger
        await db["cc_credit_wallets"].create_index(
            [("commercial_customer_id", 1)], unique=True
        )
        await db["credit_lots"].create_index([("id", 1)], unique=True)
        await db["credit_lots"].create_index(
            [("commercial_customer_id", 1), ("created_at", 1)]
        )
        await db["credit_lots"].create_index(
            [("idempotency_key", 1)],
            unique=True,
            sparse=True,
        )
        await db["credit_allocations"].create_index([("id", 1)], unique=True)
        await db["credit_allocations"].create_index(
            [("organization_id", 1), ("remaining_qty", 1)]
        )
        await db["credit_allocations"].create_index(
            [("commercial_customer_id", 1), ("lot_id", 1)]
        )
        await db["cc_credit_ledger"].create_index([("id", 1)], unique=True)
        await db["cc_credit_ledger"].create_index(
            [("commercial_customer_id", 1), ("created_at", 1)]
        )
        await db["cc_credit_ledger"].create_index(
            [("idempotency_key", 1)],
            unique=True,
            sparse=True,
        )
        # B01 — at most one active membership per user
        await db["memberships"].create_index([("id", 1)], unique=True)
        await db["memberships"].create_index([("user_id", 1), ("organization_id", 1)])
        await db["memberships"].create_index(
            [("user_id", 1)],
            unique=True,
            partialFilterExpression={"membership_status": "active"},
            name="memberships_one_active_per_user",
        )
        await db["email_verification_tokens"].create_index([("token", 1)], unique=True)
        await db["email_verification_tokens"].create_index(
            [("expires_at", 1)], expireAfterSeconds=0
        )
        # D-175 — MLS collab / visit feedback / chat / deals (non-destructive)
        await db["mls_collaborations"].create_index([("id", 1)], unique=True)
        await db["mls_collaborations"].create_index(
            [("property_id", 1), ("owner_agency_id", 1), ("partner_agency_id", 1), ("status", 1)]
        )
        await db["mls_visits"].create_index([("id", 1)], unique=True)
        await db["mls_visits"].create_index([("collaboration_id", 1), ("created_at", -1)])
        await db["mls_visit_feedback"].create_index([("id", 1)], unique=True)
        await db["mls_visit_feedback"].create_index(
            [("visit_id", 1), ("from_agency_id", 1)],
            unique=True,
            name="mls_visit_feedback_one_per_agency",
        )
        await db["mls_chat_threads"].create_index([("id", 1)], unique=True)
        await db["mls_chat_threads"].create_index(
            [("scope_key", 1), ("status", 1)],
            name="mls_chat_threads_scope_status",
        )
        await db["mls_document_requests"].create_index([("id", 1)], unique=True)
        await db["mls_document_requests"].create_index(
            [("collaboration_id", 1), ("status", 1)]
        )
        await db["deals"].create_index([("id", 1)], unique=True)
        await db["deals"].create_index([("agency_id", 1), ("updated_at", -1)])
        await db["deals"].create_index([("collaboration_id", 1)])
        await db["mls_rating_dispute_audit"].create_index([("feedback_id", 1), ("at", -1)])
        await db["subscriptions"].create_index(
            [("stripe_subscription_id", 1)], sparse=True
        )
    except Exception as e:
        logger.warning(f"Cross-tenant index creation skipped: {e}")

    logger.info("MongoDB indexes ensured.")
