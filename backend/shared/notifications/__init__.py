"""OMNIA notification prefs package."""
from shared.notifications.prefs import (  # noqa: F401
    prefs_from_user,
    user_allows_email,
    normalize_channels,
    normalize_email_types,
    normalize_frequency,
    EMAIL_TYPES,
    DEFAULT_EMAIL_TYPES,
    DEFAULT_CHANNELS,
)
