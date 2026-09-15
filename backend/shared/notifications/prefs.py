"""OMNIA — Notification preference helpers (A-021).

Channels: email | push (push reserved for v1.1)
Email types (toggleable): welcome, agency_invite, lead_notification, saved_search_alert
Always-on (cannot disable): password_reset
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

EMAIL_TYPES = (
    "welcome",
    "agency_invite",
    "lead_notification",
    "saved_search_alert",
)
ALWAYS_ON_TYPES = ("password_reset",)
CHANNELS = ("email", "push")
FREQ = ("instant", "daily", "weekly")

DEFAULT_CHANNELS: List[str] = ["email"]
DEFAULT_EMAIL_TYPES: List[str] = list(EMAIL_TYPES)
DEFAULT_SAVED_SEARCH_FREQ = "instant"


def normalize_channels(raw: Optional[Iterable[str]]) -> List[str]:
    out = []
    for c in raw or []:
        if c in CHANNELS and c not in out:
            out.append(c)
    # push allowed in storage but inactive in v1 UI
    return out


def normalize_email_types(raw: Optional[Iterable[str]]) -> List[str]:
    out = []
    for t in raw or []:
        if t in EMAIL_TYPES and t not in out:
            out.append(t)
    return out


def normalize_frequency(raw: Optional[str]) -> str:
    if raw in FREQ:
        return raw  # type: ignore[return-value]
    return DEFAULT_SAVED_SEARCH_FREQ


def prefs_from_user(user: dict) -> Dict[str, Any]:
    channels = normalize_channels(user.get("notification_channels") or DEFAULT_CHANNELS)
    types = user.get("notification_email_types")
    if types is None:
        types = DEFAULT_EMAIL_TYPES
    else:
        types = normalize_email_types(types)
    return {
        "notification_channels": channels,
        "notification_email_types": types,
        "saved_search_frequency_default": normalize_frequency(
            user.get("saved_search_frequency_default")
        ),
        "always_on_email_types": list(ALWAYS_ON_TYPES),
        "push_available": False,  # v1 — UI shows disabled + tooltip
    }


def user_allows_email(user: Optional[dict], email_type: str) -> bool:
    """Return True if this user should receive `email_type`."""
    if not user:
        return False
    if email_type in ALWAYS_ON_TYPES:
        return True
    channels = user.get("notification_channels") or DEFAULT_CHANNELS
    if "email" not in channels:
        return False
    types = user.get("notification_email_types")
    if types is None:
        # legacy users: all marketing/ops types on by default
        return email_type in EMAIL_TYPES
    return email_type in types
