"""OpenAPI.it sandbox — single API key (onda D) without OPENAPI_EMAIL."""
from __future__ import annotations

import shared.openapi_catasto as oc


def _clear(monkeypatch):
    for k in (
        "OPENAPI_ENABLED",
        "OPENAPI_API_KEY",
        "OPENAPI_EMAIL",
        "OPENAPI_TOKEN",
        "OPENAPI_MODE",
        "OPENAPI_ENV",
        "OPENAPI_CATASTO_BASE",
        "OPENAPI_OAUTH_BASE",
        "ADMIN_EMAIL",
        "OMNIA_ADMIN_EMAIL",
    ):
        monkeypatch.delenv(k, raising=False)
    oc._token_cache = (None, 0.0)


def test_disabled_without_flag(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("OPENAPI_API_KEY", "k" * 32)
    monkeypatch.setenv("ADMIN_EMAIL", "founder@example.com")
    assert oc.openapi_enabled() is False


def test_single_key_enabled_via_admin_email(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("OPENAPI_ENABLED", "true")
    monkeypatch.setenv("OPENAPI_API_KEY", "k" * 32)
    monkeypatch.setenv("ADMIN_EMAIL", "founder@example.com")
    assert oc.openapi_enabled() is True
    assert oc.auth_mode() == "oauth_single_key"
    assert oc._base() == oc.DEFAULT_SANDBOX_BASE
    assert oc._oauth_base() == oc.DEFAULT_SANDBOX_OAUTH


def test_explicit_openapi_email_is_oauth_mode(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("OPENAPI_ENABLED", "true")
    monkeypatch.setenv("OPENAPI_API_KEY", "k" * 32)
    monkeypatch.setenv("OPENAPI_EMAIL", "console@example.com")
    assert oc.auth_mode() == "oauth"
    assert oc._openapi_email() == "console@example.com"


def test_static_token_wins(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("OPENAPI_ENABLED", "true")
    monkeypatch.setenv("OPENAPI_TOKEN", "bearer-static")
    monkeypatch.setenv("OPENAPI_API_KEY", "k" * 32)
    assert oc.openapi_enabled() is True
    assert oc.auth_mode() == "static_token"


def test_live_mode_uses_prod_hosts(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("OPENAPI_ENABLED", "true")
    monkeypatch.setenv("OPENAPI_API_KEY", "k" * 32)
    monkeypatch.setenv("ADMIN_EMAIL", "founder@example.com")
    monkeypatch.setenv("OPENAPI_MODE", "live")
    assert oc._live_mode() is True
    assert oc._base() == oc.DEFAULT_BASE
    assert oc._oauth_base() == oc.DEFAULT_OAUTH


def test_disabled_without_key_or_email(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("OPENAPI_ENABLED", "true")
    assert oc.openapi_enabled() is False
    monkeypatch.setenv("OPENAPI_API_KEY", "k" * 32)
    # still no email resolvable
    assert oc.openapi_enabled() is False
