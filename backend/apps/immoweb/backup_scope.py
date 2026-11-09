"""OMNIA — Backup/restore collection scope (D-096 / D-113 / Onda 8).

Single source of truth for which Mongo collections enter the daily bak
and how agency-first extract filters documents.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

# Agency-scoped CRM / SaaS (filter by agency_id / membership).
AGENCY_COLLECTIONS: Sequence[str] = (
    "agencies",
    "users",
    "properties",
    "clients",
    "client_requests",
    "activities",
    "leads",
    "subscriptions",
    "credit_wallets",
    "credit_ledger",
    "api_keys",
    "groups",
    "publishing_connections",
    "modulistica_documents",
    "videos",
    "virtual_staging_jobs",
)

# Portale B2C / privacy / UGC — dump globale (P-046); restore replaces whole coll.
B2C_COLLECTIONS: Sequence[str] = (
    "b2c_purchases",
    "b2c_visura_orders",
    "consent_events",
    "favorites",
    "saved_searches",
    "al_legal_audit",
    "listing_inquiries",
)

# Ordered union for daily bak JSONL dump.
BACKUP_COLLECTIONS: Sequence[str] = tuple(
    dict.fromkeys([*AGENCY_COLLECTIONS, *B2C_COLLECTIONS])
)

# Minimum set required for D-096 success criteria (agency + media-linked).
D096_REQUIRED_AGENCY: Sequence[str] = (
    "agencies",
    "users",
    "properties",
    "clients",
    "client_requests",
    "activities",
)


def doc_belongs_to_agency(coll: str, doc: Dict[str, Any], agency_id: str) -> bool:
    """Return True if doc should be included in an agency-first extract."""
    if coll in B2C_COLLECTIONS:
        return True
    if coll == "agencies":
        return doc.get("id") == agency_id
    if coll == "users":
        return agency_id in (doc.get("agency_ids") or []) or doc.get("account_type") == "b2c"
    if doc.get("agency_id") == agency_id:
        return True
    # Private UGC listings live in properties without agency_id — included in
    # agency-first extract when restoring a portal-capable sandbox (legacy O3b).
    if coll == "properties" and doc.get("is_private_listing") and doc.get("owner_user_id"):
        return True
    return False


def extract_agency_docs(
    coll: str,
    docs: Iterable[Dict[str, Any]],
    agency_id: str,
) -> List[Dict[str, Any]]:
    """Filter bak documents for one agency (B2C collections pass through)."""
    return [d for d in docs if doc_belongs_to_agency(coll, d, agency_id)]
