"""Scelta sito semplice: URL normalizzato + presence."""
import pytest
from fastapi import HTTPException

from apps.immoweb.themes import _normalize_site_url


def test_normalize_adds_https():
    assert _normalize_site_url("www.nicastroimmobiliare.it") == "https://www.nicastroimmobiliare.it"


def test_normalize_strips_slash():
    assert _normalize_site_url("https://example.it/") == "https://example.it"


def test_normalize_rejects_garbage():
    with pytest.raises(HTTPException):
        _normalize_site_url("not a url")
