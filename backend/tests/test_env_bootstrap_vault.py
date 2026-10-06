"""Tests: Cloud Agent vault secrets must win over backend/.env template."""
from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "STRIPE_ENABLED=false\n"
        "STRIPE_MODE=test\n"
        "JWT_SECRET=from-file\n"
        "# STRIPE_SECRET_KEY=\n",
        encoding="utf-8",
    )
    return p


def test_vault_stripe_enabled_survives_dotenv_override(tmp_env_file: Path, monkeypatch):
    monkeypatch.setenv("STRIPE_ENABLED", "true")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_abc123")
    monkeypatch.setenv("STRIPE_PUBLISHABLE_KEY", "pk_test_abc123")
    monkeypatch.setenv(
        "CLOUD_AGENT_INJECTED_SECRET_NAMES",
        "STRIPE_ENABLED,STRIPE_SECRET_KEY,STRIPE_PUBLISHABLE_KEY",
    )
    monkeypatch.setenv("JWT_SECRET", "from-vault")

    from shared.env_bootstrap import load_backend_env

    load_backend_env(tmp_env_file, override=True)

    assert os.environ["STRIPE_ENABLED"] == "true"
    assert os.environ["STRIPE_SECRET_KEY"] == "sk_test_abc123"
    assert os.environ["STRIPE_PUBLISHABLE_KEY"] == "pk_test_abc123"
    assert os.environ["JWT_SECRET"] == "from-vault"


def test_sk_test_auto_enables_when_template_false(tmp_env_file: Path, monkeypatch):
    # Simulate: vault injected only the key; .env forces ENABLED=false
    monkeypatch.delenv("STRIPE_ENABLED", raising=False)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_onlykey")
    monkeypatch.setenv(
        "CLOUD_AGENT_INJECTED_SECRET_NAMES",
        "STRIPE_SECRET_KEY",
    )

    from shared.env_bootstrap import load_backend_env

    load_backend_env(tmp_env_file, override=True)

    assert os.environ["STRIPE_ENABLED"] == "true"
    assert os.environ.get("STRIPE_MODE") == "test"


def test_sk_live_does_not_auto_enable(tmp_env_file: Path, monkeypatch):
    monkeypatch.delenv("STRIPE_ENABLED", raising=False)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_danger")
    monkeypatch.setenv("CLOUD_AGENT_INJECTED_SECRET_NAMES", "STRIPE_SECRET_KEY")

    from shared.env_bootstrap import load_backend_env

    load_backend_env(tmp_env_file, override=True)

    # Template left false; live must stay off without explicit vault enable
    assert (os.environ.get("STRIPE_ENABLED") or "").lower() != "true"
    assert os.environ.get("STRIPE_MODE") == "live"
