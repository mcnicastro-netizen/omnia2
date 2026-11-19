"""D-175 C2 — acceptance gates: bootstrap / auth / roles required for PASS."""
from __future__ import annotations

import pytest

from shared.dogfood.c2_acceptance import (
    compute_drill_ok,
    require_admin_credentials,
    require_bootstrap_ok,
    roles_fully_verified,
)


def _base_ok_parts():
    return {
        "after": {"ok": True},
        "dump": {"ok": True},
        "media": {"ok": True},
        "deny_cases": [{"db": "omnia", "blocked": True}],
        "boot": {"ok": True, "returncode": 0},
        "role_checks": {
            "verified": True,
            "checks": [
                {"user": "omnia_df_runtime", "op": "insert", "result": "PASS_ALLOWED"},
                {
                    "user": "omnia_df_runtime",
                    "op": "insert",
                    "expect": "DENIED",
                    "result": "DENIED",
                    "pass": True,
                },
            ],
        },
    }


def test_c2_bootstrap_failed_aborts():
    with pytest.raises(RuntimeError) as ei:
        require_bootstrap_ok({"ok": False, "returncode": 2})
    assert "bootstrap_failed" in str(ei.value)


def test_c2_bootstrap_missing_aborts():
    with pytest.raises(RuntimeError) as ei:
        require_bootstrap_ok({})
    assert "bootstrap_failed" in str(ei.value)


def test_c2_admin_credentials_missing_blocks_unauth_path():
    with pytest.raises(RuntimeError) as ei:
        require_admin_credentials({})
    assert "admin_credentials_missing" in str(ei.value)
    with pytest.raises(RuntimeError):
        require_admin_credentials({"admin": ""})
    with pytest.raises(RuntimeError):
        require_admin_credentials({"admin": "   "})
    assert require_admin_credentials({"admin": "secret"}) == "secret"


def test_c2_wrong_or_missing_role_creds_not_verified():
    """Incomplete privilege verification must never count as PASS."""
    incomplete = {
        "verified": False,
        "checks": [{"name": "creds_missing", "result": "NOT VERIFIED"}],
    }
    assert roles_fully_verified(incomplete) is False
    assert roles_fully_verified({"verified": True, "checks": []}) is False
    assert roles_fully_verified(None) is False
    # Even if verified flag is wrongly True, NOT VERIFIED forces fail
    poisoned = {
        "verified": True,
        "checks": [{"name": "creds_missing", "result": "NOT VERIFIED"}],
    }
    assert roles_fully_verified(poisoned) is False


def test_c2_roles_verified_ok_path():
    ok = {
        "verified": True,
        "checks": [
            {"result": "PASS_ALLOWED"},
            {"result": "DENIED", "pass": True, "expect": "DENIED"},
        ],
    }
    assert roles_fully_verified(ok) is True


def test_c2_roles_malformed_report_rejected():
    """Gate must reject incomplete/malformed privilege reports (not only NOT VERIFIED)."""
    # DENIED without pass:true — ambiguous / failed expectation
    assert (
        roles_fully_verified(
            {
                "verified": True,
                "checks": [{"result": "DENIED", "expect": "DENIED"}],
            }
        )
        is False
    )
    # DENIED with pass:false
    assert (
        roles_fully_verified(
            {
                "verified": True,
                "checks": [{"result": "DENIED", "pass": False}],
            }
        )
        is False
    )
    # Unknown / empty result
    assert (
        roles_fully_verified({"verified": True, "checks": [{"result": "OK"}]})
        is False
    )
    assert roles_fully_verified({"verified": True, "checks": [{}]}) is False
    # Non-dict check entry
    assert roles_fully_verified({"verified": True, "checks": ["PASS_ALLOWED"]}) is False
    # Mix: one good, one malformed → overall fail
    assert (
        roles_fully_verified(
            {
                "verified": True,
                "checks": [
                    {"result": "PASS_ALLOWED"},
                    {"result": "DENIED"},  # missing pass:true
                ],
            }
        )
        is False
    )
    # verified flag alone is insufficient
    assert (
        roles_fully_verified({"verified": True, "checks": [{"result": "PASS_ALLOWED"}]})
        is True
    )


def test_c2_compute_drill_ok_requires_boot_and_roles():
    parts = _base_ok_parts()
    assert compute_drill_ok(**parts) is True

    bad_boot = dict(parts)
    bad_boot["boot"] = {"ok": False, "returncode": 1}
    assert compute_drill_ok(**bad_boot) is False

    bad_roles = dict(parts)
    bad_roles["role_checks"] = {
        "verified": False,
        "checks": [{"name": "creds_missing", "result": "NOT VERIFIED"}],
    }
    assert compute_drill_ok(**bad_roles) is False

    # Restore/media ok but roles incomplete → overall FAIL
    incomplete = dict(parts)
    incomplete["role_checks"] = {
        "verified": True,  # poisoned flag
        "checks": [{"result": "NOT VERIFIED"}],
    }
    assert compute_drill_ok(**incomplete) is False


def test_c2_compute_drill_ok_still_requires_restore_media():
    parts = _base_ok_parts()
    parts["media"] = {"ok": False}
    assert compute_drill_ok(**parts) is False
    parts = _base_ok_parts()
    parts["after"] = {"ok": False}
    assert compute_drill_ok(**parts) is False
