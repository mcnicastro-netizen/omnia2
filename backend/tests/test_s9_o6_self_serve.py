"""S9 — O6 PASS: self-serve B2B ON (D-120)."""
from __future__ import annotations

import asyncio
import os

import pytest
from fastapi import HTTPException


def test_self_serve_env_true(monkeypatch):
    monkeypatch.setenv("OMNIA_SELF_SERVE_ENABLED", "true")
    from shared.billing import self_serve as ss

    assert ss.is_self_serve_enabled() is True
    ss.guard_self_serve()  # no raise


def test_self_serve_still_blocks_when_false(monkeypatch):
    monkeypatch.setenv("OMNIA_SELF_SERVE_ENABLED", "false")
    from shared.billing.self_serve import guard_self_serve

    with pytest.raises(HTTPException) as ei:
        guard_self_serve()
    assert ei.value.status_code == 503
    assert ei.value.detail["code"] == "self_serve_blocked"


def test_plans_self_serve_reflects_env(monkeypatch):
    monkeypatch.setenv("OMNIA_SELF_SERVE_ENABLED", "true")
    from apps.billing import routes as br

    out = asyncio.run(br.list_plans())
    assert out["self_serve_enabled"] is True
