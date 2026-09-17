"""viewer_is_lister: seller mirror vs buyer trust voice."""
from apps.immocloud.public_portal import _viewer_is_lister


def test_lister_b2c_owner():
    user = {"id": "u-1", "account_type": "b2c"}
    p = {"owner_user_id": "u-1", "is_private_listing": True, "agency_id": "_private_listings"}
    assert _viewer_is_lister(user, p) is True
    assert _viewer_is_lister({"id": "other"}, p) is False
    assert _viewer_is_lister(None, p) is False


def test_lister_agency_agent():
    user = {"id": "a-1", "agency_id": "ag-9", "agency_ids": ["ag-9"]}
    p = {"agency_id": "ag-9", "owner_user_id": None}
    assert _viewer_is_lister(user, p) is True
    assert _viewer_is_lister({"id": "x", "agency_id": "other"}, p) is False


def test_private_sentinel_not_matched_by_random_agency():
    user = {"id": "a-1", "agency_id": "_private_listings"}
    p = {"agency_id": "_private_listings", "owner_user_id": "someone-else"}
    assert _viewer_is_lister(user, p) is False
