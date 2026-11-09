"""Login pubblico non deve 500 se il doc user è incompleto (name/timestamps)."""
from apps.core.auth import _public


def test_public_tolerates_missing_name_and_timestamps():
    payload = _public(
        {
            "id": "u1",
            "email": "a@example.com",
            "role": "agency_admin",
            # no name / created_at / updated_at
        }
    )
    assert payload["name"] == ""
    assert payload["created_at"] is None
    assert payload["updated_at"] is None
    assert payload["role"] == "agency_admin"


def test_public_falls_back_to_full_name():
    payload = _public(
        {
            "id": "u2",
            "email": "b@example.com",
            "role": "agent",
            "full_name": "Mario Rossi",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
    )
    assert payload["name"] == "Mario Rossi"
