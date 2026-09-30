"""O1 — D-095 fascicolo media · D-100 invite · D-106 active_agency_id (unit)."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from apps.immoweb.media import _is_private_media_path
from shared.auth.tenant import optional_agency_id, require_agency


def test_private_media_fascicolo_blocked():
    assert _is_private_media_path("omnia/fascicolo/prop1/doc1") is True
    assert _is_private_media_path("omnia/modulistica/agency/x.pdf") is True
    assert _is_private_media_path("omnia/properties/prop1/photo.jpg") is False


def test_optional_agency_no_fallback_to_first():
    user = {"agency_ids": ["a1", "a2"], "active_agency_id": None}
    assert optional_agency_id(user) is None
    user2 = {"agency_ids": ["a1", "a2"], "active_agency_id": "a2"}
    assert optional_agency_id(user2) == "a2"
    user3 = {"agency_ids": ["a1"], "active_agency_id": "missing"}
    assert optional_agency_id(user3) is None


def test_require_agency_errors():
    with pytest.raises(HTTPException) as ei:
        require_agency({"agency_ids": ["a1"]})
    assert ei.value.detail == "active_agency_required"

    with pytest.raises(HTTPException) as ei2:
        require_agency({"agency_ids": ["a1"], "active_agency_id": "other"})
    assert ei2.value.detail == "active_agency_invalid"

    assert require_agency({"agency_ids": ["a1"], "active_agency_id": "a1"}) == "a1"
