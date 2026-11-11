"""Link pubblici per email (login gestionale con next sicuro)."""
from __future__ import annotations

from urllib.parse import quote

from shared.public_base import get_public_base_url


def gestionale_enter_urls(lang: str = "it") -> dict:
    """URL per email di attivazione CRM.

    ``enter_url`` → login B2B con ``from=app`` + ``next`` dashboard
    (evita 403 se c'è già una sessione cloud/client aperta).
    """
    lang = (lang or "it")[:2]
    if lang not in ("it", "en", "es"):
        lang = "it"
    base = get_public_base_url().rstrip("/")
    dash_path = f"/{lang}/app/dashboard"
    login_url = f"{base}/{lang}/login"
    enter_url = f"{login_url}?from=app&next={quote(dash_path, safe='')}"
    return {
        "login_url": login_url,
        "dashboard_url": f"{base}{dash_path}",
        "enter_url": enter_url,
        "dashboard_path": dash_path,
    }
