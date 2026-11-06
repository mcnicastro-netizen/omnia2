"""Unit checks for demo retire helpers (no live mongo required)."""
from apps.immoweb.demo_retire import (
    DEMO_ADMIN_EMAIL,
    DEMO_AGENCY_ID,
    KEEP_GLOBAL,
    purge_agency_shell,
)


def test_demo_ids_stable():
    assert DEMO_AGENCY_ID == "demo-agency-001"
    assert DEMO_ADMIN_EMAIL == "demo.admin@omniaecosystem.it"


def test_keep_global_excludes_crm():
    assert "properties" not in KEEP_GLOBAL
    assert "clients" not in KEEP_GLOBAL
    assert "agencies" not in KEEP_GLOBAL


def test_purge_agency_shell_is_async_callable():
    assert callable(purge_agency_shell)
