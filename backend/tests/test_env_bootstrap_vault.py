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

    assert (os.environ.get("STRIPE_ENABLED") or "").lower() != "true"
    assert os.environ.get("STRIPE_MODE") == "live"


def test_prefer_test_over_live_even_if_canonical_is_live(tmp_env_file: Path, monkeypatch):
    """Misnamed vault entry with sk_test_ must beat STRIPE_SECRET_KEY=sk_live_."""
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_canonical")
    monkeypatch.setenv("STRIPE_PUBLISHABLE_KEY", "pk_live_canonical")
    monkeypatch.setenv("STRIPE_TEST_SECRET", "sk_test_alias")
    monkeypatch.setenv("STRIPE_TEST_PUBLISHABLE", "pk_test_alias")
    monkeypatch.setenv(
        "CLOUD_AGENT_INJECTED_SECRET_NAMES",
        "STRIPE_SECRET_KEY,STRIPE_PUBLISHABLE_KEY,STRIPE_TEST_SECRET,STRIPE_TEST_PUBLISHABLE",
    )

    from shared.env_bootstrap import load_backend_env

    load_backend_env(tmp_env_file, override=True)

    assert os.environ["STRIPE_SECRET_KEY"] == "sk_test_alias"
    assert os.environ["STRIPE_PUBLISHABLE_KEY"] == "pk_test_alias"
    assert os.environ["STRIPE_ENABLED"] == "true"
    assert os.environ["STRIPE_MODE"] == "test"


def test_cloud_agent_drops_file_only_live_stripe(tmp_path: Path, monkeypatch):
    """Warm .env with live must not populate process when vault has no Stripe."""
    env = tmp_path / ".env"
    env.write_text(
        "STRIPE_ENABLED=true\n"
        "STRIPE_SECRET_KEY=sk_live_from_disk\n"
        "STRIPE_PUBLISHABLE_KEY=pk_live_from_disk\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_PUBLISHABLE_KEY", raising=False)
    monkeypatch.delenv("STRIPE_ENABLED", raising=False)
    monkeypatch.setenv("CLOUD_AGENT_INJECTED_SECRET_NAMES", "RESEND_API_KEY")
    monkeypatch.setenv("RESEND_API_KEY", "re_test")

    from shared.env_bootstrap import load_backend_env

    load_backend_env(env, override=True)

    assert not (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    assert not (os.environ.get("STRIPE_PUBLISHABLE_KEY") or "").strip()
