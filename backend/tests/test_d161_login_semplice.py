"""D-161 — Attiva default senza API=password; invite richiede password."""
from __future__ import annotations

import inspect


def test_activate_agency_default_no_login_credential():
    from apps.immoweb.founder_ops import ActivateAgencyBody

    body = ActivateAgencyBody(agency_id="ag1")
    assert body.issue_login_credential is False


def test_accept_invite_requires_password_for_new_user():
    from apps.immoweb import invites as mod

    src = inspect.getsource(mod.accept_invite)
    assert "issue_login_api_credential" not in src
    assert "password_required" in src
