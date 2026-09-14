"""OMNIA — Backend i18n helper for messages / errors / emails."""
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

SUPPORTED_LANGS = ("it", "en", "es")
DEFAULT_LANG = "it"
LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"

# Cache: { "it": {...}, "en": {...}, "es": {...} }
_translations: Dict[str, Dict[str, str]] = {}


def _load_locales() -> None:
    """Load JSON locales into memory (called once at startup)."""
    global _translations
    for lang in SUPPORTED_LANGS:
        file_path = LOCALES_DIR / f"{lang}.json"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                _translations[lang] = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Locale file missing: {file_path}")
            _translations[lang] = {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            _translations[lang] = {}


def t(key: str, lang: Optional[str] = None, **vars) -> str:
    """Translate a key. Supports interpolation: t('hello', name='Mario').
    Falls back to DEFAULT_LANG, then to the key itself.
    """
    if not _translations:
        _load_locales()
    lang = lang or DEFAULT_LANG
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    text = _translations.get(lang, {}).get(key)
    if not text:
        text = _translations.get(DEFAULT_LANG, {}).get(key, key)
    if vars:
        try:
            text = text.format(**vars)
        except (KeyError, IndexError):
            pass
    return text


def normalize_lang(lang_header: Optional[str]) -> str:
    """Parse Accept-Language header → first supported lang or default."""
    if not lang_header:
        return DEFAULT_LANG
    # naive parser: 'it-IT,it;q=0.9,en;q=0.8' -> ['it', 'it', 'en']
    for token in lang_header.replace(" ", "").split(","):
        code = token.split(";")[0].split("-")[0].lower()
        if code in SUPPORTED_LANGS:
            return code
    return DEFAULT_LANG
