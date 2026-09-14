"""OMNIA — Resend email client + transactional templates.

If RESEND_API_KEY is not configured we fall back to logging the email
(useful in dev environments without internet access to Resend).
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional

import resend

logger = logging.getLogger(__name__)

SENDER = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _configure_resend() -> bool:
    key = os.environ.get("RESEND_API_KEY")
    if not key:
        return False
    resend.api_key = key
    return True


def _read_template(name: str, lang: str) -> str:
    """Read template file: e.g. 'welcome' + 'it' → welcome.it.html"""
    if lang not in ("it", "en", "es"):
        lang = "it"
    path = TEMPLATES_DIR / f"{name}.{lang}.html"
    if not path.exists():
        path = TEMPLATES_DIR / f"{name}.it.html"
    return path.read_text(encoding="utf-8")


def _render(tpl: str, vars: dict) -> str:
    for key, value in vars.items():
        tpl = tpl.replace("{{" + key + "}}", str(value))
    return tpl


SUBJECTS = {
    "welcome": {
        "it": "Benvenuto in OMNIA",
        "en": "Welcome to OMNIA",
        "es": "Bienvenido a OMNIA",
    },
    "password_reset": {
        "it": "Reimposta la tua password OMNIA",
        "en": "Reset your OMNIA password",
        "es": "Restablece tu contraseña OMNIA",
    },
    "agency_invite": {
        "it": "Sei stato invitato a unirti a {{agency_name}} su OMNIA",
        "en": "You have been invited to join {{agency_name}} on OMNIA",
        "es": "Has sido invitado a unirte a {{agency_name}} en OMNIA",
    },
    "lead_notification": {
        "it": "🔔 Nuovo lead da ImmobilCloud — {{property_title}}",
        "en": "🔔 New lead from ImmobilCloud — {{property_title}}",
        "es": "🔔 Nuevo lead desde ImmobilCloud — {{property_title}}",
    },
    "saved_search_alert": {
        "it": "🔔 {{match_count}} nuovi immobili per la tua ricerca \"{{search_name}}\"",
        "en": "🔔 {{match_count}} new listings for your search \"{{search_name}}\"",
        "es": "🔔 {{match_count}} nuevos inmuebles para tu búsqueda \"{{search_name}}\"",
    },
}


async def send_email(
    to: str,
    template: str,
    lang: str = "it",
    variables: Optional[dict] = None,
) -> dict:
    """Send a localized transactional email via Resend."""
    variables = dict(variables or {})
    # Inject default assets for branded emails (D-060, logo asset in FE public/)
    variables.setdefault(
        "logo_url",
        os.environ.get("OMNIA_LOGO_URL", "https://omniarealestateecosystem.it/omnia-mark.png"),
    )
    variables.setdefault(
        "public_base",
        os.environ.get("OMNIA_PUBLIC_URL", "https://omniarealestateecosystem.it"),
    )
    subject_raw = SUBJECTS.get(template, {}).get(lang) or SUBJECTS.get(template, {}).get("it") or "OMNIA"
    subject = _render(subject_raw, variables)
    html = _render(_read_template(template, lang), variables)

    if not _configure_resend():
        logger.warning(
            "[EMAIL MOCK] to=%s template=%s lang=%s subject=%s vars=%s",
            to, template, lang, subject, variables,
        )
        return {"id": "mock", "status": "mock"}

    params = {
        "from": SENDER,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(
            "[EMAIL OK] to=%s template=%s lang=%s id=%s",
            to, template, lang, result.get("id"),
        )
        return {"id": result.get("id"), "status": "sent"}
    except Exception as e:
        logger.error("[EMAIL ERROR] to=%s template=%s err=%s", to, template, e)
        return {"id": None, "status": "error", "error": str(e)}
