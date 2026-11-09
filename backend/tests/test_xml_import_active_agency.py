"""D-106 — XML import deve usare active_agency_id, mai agency_ids[0]."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from apps.immoweb.xml_import import _agency_id_of


def test_xml_import_agency_uses_active_not_first():
    user = {
        "id": "u1",
        "agency_ids": ["wrong-first", "nicastro-agency-001"],
        "active_agency_id": "nicastro-agency-001",
    }
    assert _agency_id_of(user) == "nicastro-agency-001"


def test_xml_import_agency_rejects_missing_active():
    with pytest.raises(HTTPException) as ei:
        _agency_id_of({"id": "u1", "agency_ids": ["a1"], "active_agency_id": None})
    assert ei.value.status_code == 404
    assert ei.value.detail == "active_agency_required"


def test_xml_import_agency_rejects_invalid_active():
    with pytest.raises(HTTPException) as ei:
        _agency_id_of({"id": "u1", "agency_ids": ["a1"], "active_agency_id": "other"})
    assert ei.value.status_code == 404
    assert ei.value.detail == "active_agency_invalid"
