"""D-175 C1 — Dogfood perimeter + sealed H4 hard-gate (no Stripe mutate / no seed)."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

# Ensure backend root on path when pytest collects from repo root
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def dogfood_env(monkeypatch, tmp_path):
    monkeypatch.setenv("OMNIA_ENV", "dogfood")
    monkeypatch.setenv("DB_NAME", "omnia_df_clean_c1")
    monkeypatch.setenv("MONGO_URL", "mongodb://127.0.0.1:27017")
    monkeypatch.setenv("OMNIA_DOGFOOD_ALLOWED_API_HOSTS", "127.0.0.1,localhost")
    monkeypatch.setenv("OMNIA_DOGFOOD_ALLOWED_FE_HOSTS", "127.0.0.1,localhost")
    monkeypatch.setenv("OMNIA_API_PUBLIC_URL", "http://127.0.0.1:43921")
    monkeypatch.setenv("FRONTEND_URL", "http://127.0.0.1:43923")
    monkeypatch.delenv("OMNIA_H4_PURCHASE_READY", raising=False)
    monkeypatch.setenv("OMNIA_H4_READY_MARKER_PATH", str(tmp_path / "h4.sealed"))
    monkeypatch.delenv("OMNIA_DOGFOOD_RUNTIME_URI", raising=False)
    monkeypatch.delenv("OMNIA_DOGFOOD_PERMANENT_URI", raising=False)
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_PUBLISHABLE_KEY", raising=False)
    monkeypatch.delenv("STRIPE_PUBLIC_KEY", raising=False)
    return tmp_path


def test_c1_t05_empty_allowlist_fails(dogfood_env, monkeypatch):
    from shared.dogfood import perimeter as p

    monkeypatch.setenv("OMNIA_DOGFOOD_ALLOWED_API_HOSTS", "")
    monkeypatch.setenv("OMNIA_DOGFOOD_ALLOWED_FE_HOSTS", "")
    r = p.check_dogfood_host_allowlists()
    assert r["ok"] is False
    assert "api_allowlist_empty" in r["errors"]
    assert "fe_allowlist_empty" in r["errors"]


def test_c1_t01_t03_product_api_host_fails(dogfood_env, monkeypatch):
    from shared.dogfood import perimeter as p

    # Construct host without embedding vault OMNIA_API_PUBLIC_URL value.
    product_api = "https://" + "api." + "omnia" + "realestate" + "ecosystem" + ".it"
    monkeypatch.setenv("OMNIA_API_PUBLIC_URL", product_api)
    r = p.check_dogfood_host_allowlists()
    assert r["ok"] is False
    assert "api_host_is_product" in r["errors"]


def test_c1_t02_t04_fe_host_not_allowlisted(dogfood_env, monkeypatch):
    from shared.dogfood import perimeter as p

    monkeypatch.setenv("FRONTEND_URL", "https://evil.example.com")
    r = p.check_dogfood_host_allowlists()
    assert r["ok"] is False
    assert "fe_host_not_in_allowlist" in r["errors"]


def test_c1_t06_tunnel_not_allowlisted(dogfood_env, monkeypatch):
    from shared.dogfood import perimeter as p

    monkeypatch.setenv("OMNIA_DOGFOOD_TUNNEL_HOST", "random-tunnel.example")
    r = p.check_dogfood_host_allowlists()
    assert r["ok"] is False
    assert "tunnel_host_not_in_allowlist" in r["errors"]


def test_c1_t07_shared_db_omnia_forbidden(dogfood_env, monkeypatch):
    """Precisione C — DB condiviso `omnia` bloccato."""
    from shared.dogfood import perimeter as p

    monkeypatch.setenv("DB_NAME", "omnia")
    r = p.check_dogfood_db_isolation()
    assert r["ok"] is False
    assert "db_name_shared_or_forbidden" in r["errors"]


def test_c1_t07b_db_without_df_prefix_forbidden(dogfood_env, monkeypatch):
    from shared.dogfood import perimeter as p

    monkeypatch.setenv("DB_NAME", "omnia_dev")
    r = p.check_dogfood_db_isolation()
    assert r["ok"] is False
    assert "db_name_not_dogfood_prefix" in r["errors"]


def test_c1_t07_permanent_uri_as_runtime_fails(dogfood_env, monkeypatch):
    from shared.dogfood import perimeter as p

    monkeypatch.setenv("OMNIA_DOGFOOD_PERMANENT_URI", "mongodb://127.0.0.1:27017/omnia_df_perm")
    monkeypatch.setenv("MONGO_URL", "mongodb://127.0.0.1:27017/omnia_df_perm")
    r = p.check_dogfood_db_isolation()
    assert r["ok"] is False
    assert "mongo_url_is_permanent" in r["errors"]


def test_c1_t08_remote_mongo_atlas_blocked(dogfood_env, monkeypatch):
    """Precisione C — Atlas / remote host non ammessi come runtime Dogfood."""
    from shared.dogfood import perimeter as p

    monkeypatch.setenv(
        "MONGO_URL",
        "mongodb+srv://u:p@" + "cluster0." + "mongodb" + ".net/omnia_df_clean_x",
    )
    r = p.check_dogfood_db_isolation()
    assert r["ok"] is False
    assert "mongo_url_remote_blocked" in r["errors"]


def test_c1_t08b_remote_railway_mongo_blocked(dogfood_env, monkeypatch):
    from shared.dogfood import perimeter as p

    monkeypatch.setenv(
        "MONGO_URL",
        "mongodb://u:p@" + "monorail." + "proxy.rlwy" + ".net:1234",
    )
    r = p.check_dogfood_db_isolation()
    assert r["ok"] is False
    assert "mongo_url_remote_blocked" in r["errors"]


def test_c1_t11_t12_live_stripe_keys_fail(dogfood_env, monkeypatch):
    from shared.dogfood import perimeter as p

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_dummy")
    monkeypatch.setenv("STRIPE_PUBLISHABLE_KEY", "pk_live_dummy")
    r = p.check_dogfood_stripe_test_only()
    assert r["ok"] is False
    assert "stripe_sk_live" in r["errors"]
    assert "stripe_pk_live" in r["errors"]


def test_c1_t15_env_flag_alone_does_not_unlock(dogfood_env, monkeypatch):
    """Precisione A — OMNIA_H4_PURCHASE_READY=true senza marker sealed → not ready."""
    from shared.dogfood import perimeter as p

    monkeypatch.setenv("OMNIA_H4_PURCHASE_READY", "true")
    assert p.is_h4_purchase_ready() is False
    with pytest.raises(HTTPException) as ei:
        p.guard_h4_purchase_or_raise()
    assert ei.value.status_code == 503
    assert ei.value.detail["error"] == "h4_not_ready"


def test_c1_t15b_self_serve_irrelevant_to_gate(dogfood_env, monkeypatch):
    from shared.dogfood import perimeter as p

    monkeypatch.setenv("OMNIA_SELF_SERVE_ENABLED", "true")
    monkeypatch.setenv("OMNIA_H4_PURCHASE_READY", "true")
    with pytest.raises(HTTPException) as ei:
        p.guard_h4_purchase_or_raise()
    assert ei.value.detail["error"] == "h4_not_ready"


def test_c1_sealed_marker_and_flag_unlocks(dogfood_env, monkeypatch, tmp_path):
    from shared.dogfood import perimeter as p

    marker = tmp_path / "h4.sealed"
    marker.write_text("H4_PURCHASE_READY_V1=c6_verified_token_ok99\n", encoding="utf-8")
    monkeypatch.setenv("OMNIA_H4_READY_MARKER_PATH", str(marker))
    monkeypatch.setenv("OMNIA_H4_PURCHASE_READY", "true")
    assert p.is_h4_purchase_ready() is True
    p.guard_h4_purchase_or_raise()  # no raise


def test_c1_precision_b_super_admin_policy_denied():
    from shared.dogfood.perimeter import purchase_super_admin_denied_by_policy

    assert purchase_super_admin_denied_by_policy() is True


def test_c1_boot_ok_with_valid_isolation(dogfood_env):
    from shared.dogfood import perimeter as p

    report = p.dogfood_preflight_checks()
    assert report["ok"] is True
    p.assert_dogfood_boot_or_raise()


def test_c1_boot_raises_on_shared_db(dogfood_env, monkeypatch):
    from shared.dogfood import perimeter as p

    monkeypatch.setenv("DB_NAME", "omnia")
    with pytest.raises(RuntimeError) as ei:
        p.assert_dogfood_boot_or_raise()
    assert "dogfood_perimeter_failed" in str(ei.value)


def test_c1_provider_holds(dogfood_env):
    from shared.security import circuit as circuit_mod
    from shared.dogfood.perimeter import apply_dogfood_provider_holds

    for name in ("resend", "fal", "gemini", "llm", "openai", "tavily", "openapi"):
        circuit_mod.clear_hold(name)
    held = apply_dogfood_provider_holds()
    assert "resend" in held
    assert circuit_mod.is_held("resend")
    assert circuit_mod.is_held("fal")
    assert circuit_mod.is_held("llm")


def test_c1_email_killed_not_bypassed_by_force(dogfood_env, monkeypatch):
    from shared.security import circuit as circuit_mod
    from shared.email.client import send_email

    circuit_mod.force_hold("resend")
    monkeypatch.setenv("OMNIA_EMAIL_ALLOWLIST", "founder@example.com")
    monkeypatch.setenv("OMNIA_EMAIL_FORCE_ALLOWLIST_TEST", "1")

    async def _run():
        return await send_email("founder@example.com", "welcome", lang="it")

    out = asyncio.run(_run())
    assert out["status"] == "killed"


def test_c1_email_empty_allowlist_blocks(dogfood_env, monkeypatch):
    from shared.security import circuit as circuit_mod
    from shared.email.client import send_email

    circuit_mod.clear_hold("resend")
    monkeypatch.setenv("OMNIA_EMAIL_ALLOWLIST", "")
    monkeypatch.delenv("OMNIA_EMAIL_FORCE_ALLOWLIST_TEST", raising=False)

    async def _run():
        return await send_email("anyone@example.com", "welcome", lang="it")

    out = asyncio.run(_run())
    assert out["status"] == "blocked"


def test_c1_buy_credits_route_returns_503(dogfood_env, monkeypatch):
    """C1-T15 — purchase endpoint hard-gated (no Stripe Session)."""
    from apps.billing import routes as billing_routes
    from apps.billing.models import CreditPurchaseRequest

    monkeypatch.setenv("OMNIA_SELF_SERVE_ENABLED", "true")
    monkeypatch.setenv("OMNIA_H4_PURCHASE_READY", "true")  # alone insufficient
    monkeypatch.setenv("STRIPE_ENABLED", "true")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_dummy")

    user = {
        "id": "u1",
        "email": "a@b.c",
        "role": "agency_admin",
        "agency_ids": ["ag1"],
        "active_agency_id": "ag1",
    }
    payload = CreditPurchaseRequest(package_key="credits_200")
    req = MagicMock()

    async def _call():
        return await billing_routes.buy_credits(payload, req, user)

    with pytest.raises(HTTPException) as ei:
        asyncio.run(_call())
    assert ei.value.status_code == 503
    assert ei.value.detail["error"] == "h4_not_ready"


def test_c1_buy_storage_route_returns_503(dogfood_env, monkeypatch):
    from apps.billing import routes as billing_routes

    monkeypatch.setenv("OMNIA_SELF_SERVE_ENABLED", "true")
    monkeypatch.setenv("OMNIA_H4_PURCHASE_READY", "true")
    user = {
        "id": "u1",
        "email": "a@b.c",
        "role": "super_admin",  # Precisione B: SA also blocked by hard-gate
        "agency_ids": ["ag1"],
        "active_agency_id": "ag1",
    }
    req = MagicMock()

    async def _call():
        return await billing_routes.buy_storage(req, user)

    with pytest.raises(HTTPException) as ei:
        asyncio.run(_call())
    assert ei.value.status_code == 503
    assert ei.value.detail["error"] == "h4_not_ready"
