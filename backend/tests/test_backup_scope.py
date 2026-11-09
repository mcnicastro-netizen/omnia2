"""Unit: backup/restore collection scope (D-096 / Onda 8)."""
from __future__ import annotations

from apps.immoweb.backup_job import _COLLECTIONS
from apps.immoweb.backup_scope import (
    AGENCY_COLLECTIONS,
    B2C_COLLECTIONS,
    BACKUP_COLLECTIONS,
    D096_REQUIRED_AGENCY,
    doc_belongs_to_agency,
    extract_agency_docs,
)


def test_backup_job_uses_shared_scope():
    assert _COLLECTIONS == list(BACKUP_COLLECTIONS)


def test_onda8_collections_include_media_linked():
    for name in (
        "modulistica_documents",
        "videos",
        "virtual_staging_jobs",
        "b2c_purchases",
        "favorites",
    ):
        assert name in BACKUP_COLLECTIONS


def test_d096_required_subset():
    for name in D096_REQUIRED_AGENCY:
        assert name in AGENCY_COLLECTIONS


def test_extract_agency_filters_and_keeps_b2c():
    docs = [
        {"id": "a1", "agency_id": "ag-1"},
        {"id": "a2", "agency_id": "ag-2"},
    ]
    out = extract_agency_docs("properties", docs, "ag-1")
    assert [d["id"] for d in out] == ["a1"]

    b2c = [{"id": "p1"}, {"id": "p2"}]
    assert extract_agency_docs("b2c_purchases", b2c, "ag-1") == b2c


def test_users_membership_and_agency_row():
    assert doc_belongs_to_agency(
        "users", {"id": "u1", "agency_ids": ["ag-1"]}, "ag-1"
    )
    assert not doc_belongs_to_agency(
        "users", {"id": "u2", "agency_ids": ["ag-2"]}, "ag-1"
    )
    assert doc_belongs_to_agency("agencies", {"id": "ag-1"}, "ag-1")
    assert not doc_belongs_to_agency("agencies", {"id": "ag-2"}, "ag-1")


def test_videos_only_by_agency_id():
    assert doc_belongs_to_agency(
        "videos", {"id": "v1", "agency_id": "ag-1"}, "ag-1"
    )
    assert not doc_belongs_to_agency(
        "videos", {"id": "v2", "owner_user_id": "u1"}, "ag-1"
    )


def test_b2c_collections_disjoint_names_ok():
    # B2C names must appear in backup dump
    for name in B2C_COLLECTIONS:
        assert name in BACKUP_COLLECTIONS
