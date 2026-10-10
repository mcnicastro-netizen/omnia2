"""S7 — demo story unica: finestra sandbox + CTA Acquista."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from shared.demo_story import (
    DEMO_AGENCY_ID,
    build_demo_status,
    demo_window_fields,
)


def test_canonical_agency_id():
    assert DEMO_AGENCY_ID == "demo-agency-001"


def test_demo_window_fields_active():
    start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    f = demo_window_fields(trial_days=7, start=start)
    assert f["demo_story"] is True
    assert f["demo_trial_days"] == 7
    assert f["demo_started_at"].startswith("2026-10-01")
    exp = datetime.fromisoformat(f["demo_expires_at"])
    assert exp == start + timedelta(days=7)


def test_demo_window_force_expired():
    f = demo_window_fields(force_expired=True)
    exp = datetime.fromisoformat(f["demo_expires_at"])
    start = datetime.fromisoformat(f["demo_started_at"])
    assert exp < start or exp <= datetime.now(timezone.utc)


def test_status_active_cta_use_sandbox():
    now = datetime.now(timezone.utc)
    agency = {
        "id": DEMO_AGENCY_ID,
        "demo_story": True,
        "demo_trial_days": 7,
        "demo_started_at": now.isoformat(),
        "demo_expires_at": (now + timedelta(days=5)).isoformat(),
    }
    st = build_demo_status(agency, self_serve_enabled=False)
    assert st["is_demo_story"] is True
    assert st["expired"] is False
    assert st["cta"] == "use_sandbox"
    assert st["checkout_available"] is False
    assert st["days_remaining"] >= 5


def test_status_expired_acquista_self_serve_off():
    now = datetime.now(timezone.utc)
    agency = {
        "id": DEMO_AGENCY_ID,
        "demo_story": True,
        "demo_trial_days": 7,
        "demo_started_at": (now - timedelta(days=10)).isoformat(),
        "demo_expires_at": (now - timedelta(days=1)).isoformat(),
    }
    st = build_demo_status(agency, self_serve_enabled=False)
    assert st["expired"] is True
    assert st["cta"] == "acquista_pacchetto"
    assert st["checkout_available"] is False
    assert "self-serve OFF" in st["message"] or "assistito" in st["message"]


def test_status_expired_checkout_when_self_serve_on():
    now = datetime.now(timezone.utc)
    agency = {
        "id": DEMO_AGENCY_ID,
        "demo_story": True,
        "demo_trial_days": 7,
        "demo_started_at": (now - timedelta(days=10)).isoformat(),
        "demo_expires_at": (now - timedelta(hours=1)).isoformat(),
    }
    st = build_demo_status(agency, self_serve_enabled=True)
    assert st["expired"] is True
    assert st["checkout_available"] is True


def test_non_demo_agency():
    st = build_demo_status(
        {"id": "nicastro-agency", "name": "Nicastro"},
        self_serve_enabled=False,
    )
    assert st["is_demo_story"] is False
    assert st["cta"] == "none"
