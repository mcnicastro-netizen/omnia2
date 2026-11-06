"""D-145 — demo seed off on Railway by default."""
import os

from apps.core.seed import should_seed_demo_agency


def test_should_seed_demo_explicit_true(monkeypatch):
    monkeypatch.setenv("OMNIA_SEED_DEMO_AGENCY", "true")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    assert should_seed_demo_agency() is True


def test_should_seed_demo_explicit_false(monkeypatch):
    monkeypatch.setenv("OMNIA_SEED_DEMO_AGENCY", "0")
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    monkeypatch.delenv("RAILWAY_SERVICE_NAME", raising=False)
    monkeypatch.delenv("RAILWAY_PROJECT_ID", raising=False)
    assert should_seed_demo_agency() is False


def test_should_seed_demo_railway_default_off(monkeypatch):
    monkeypatch.delenv("OMNIA_SEED_DEMO_AGENCY", raising=False)
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    assert should_seed_demo_agency() is False


def test_should_seed_demo_local_default_on(monkeypatch):
    monkeypatch.delenv("OMNIA_SEED_DEMO_AGENCY", raising=False)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    monkeypatch.delenv("RAILWAY_SERVICE_NAME", raising=False)
    monkeypatch.delenv("RAILWAY_PROJECT_ID", raising=False)
    assert should_seed_demo_agency() is True
