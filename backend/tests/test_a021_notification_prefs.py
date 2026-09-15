"""A-021 notification preferences API smoke (sync requests style)."""
import os
import requests
import pytest

BASE = os.environ.get("OMNIA_TEST_BASE", "http://127.0.0.1:43121")
EMAIL = os.environ.get("OMNIA_TEST_EMAIL", "mcnicastro@gmail.com")
PASSWORD = os.environ.get("OMNIA_TEST_PASSWORD", "OmniaFounder2026!")


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"login failed: {r.status_code}")
    return s


def test_notification_preferences_get_patch(session):
    r = session.get(f"{BASE}/api/auth/me/notification-preferences", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert "notification_channels" in body
    assert "notification_email_types" in body
    assert "password_reset" in body.get("always_on_email_types", [])

    r2 = session.patch(
        f"{BASE}/api/auth/me/notification-preferences",
        json={
            "notification_channels": ["email"],
            "notification_email_types": ["lead_notification", "welcome"],
            "saved_search_frequency_default": "weekly",
        },
        timeout=15,
    )
    assert r2.status_code == 200, r2.text
    b2 = r2.json()
    assert set(b2["notification_email_types"]) == {"lead_notification", "welcome"}
    assert b2["saved_search_frequency_default"] == "weekly"

    me = session.get(f"{BASE}/api/auth/me", timeout=15)
    assert me.status_code == 200
    assert set(me.json().get("notification_email_types") or []) == {"lead_notification", "welcome"}

    # restore defaults for other tests / founder account
    session.patch(
        f"{BASE}/api/auth/me/notification-preferences",
        json={
            "notification_channels": ["email"],
            "notification_email_types": [
                "welcome", "agency_invite", "lead_notification", "saved_search_alert",
            ],
            "saved_search_frequency_default": "instant",
        },
        timeout=15,
    )
