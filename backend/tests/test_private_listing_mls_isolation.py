"""Unit: annunci privati B2C restano fuori da MLS / matching CRM."""
from __future__ import annotations

import ast
import inspect
from pathlib import Path


def test_shareable_filters_block_b2c_private():
    from apps.immoweb.mls import _shareable_listing_filters

    f = _shareable_listing_filters()
    assert f["is_private_listing"] == {"$ne": True}
    assert f["agency_id"] == {"$ne": "_private_listings"}


def test_private_create_forces_mls_shared_false():
    from apps.immocloud import private_listings as pl

    src = inspect.getsource(pl.create_private_listing)
    assert '"mls_shared": False' in src or "'mls_shared': False" in src
    assert '"visibility": "private"' in src or "'visibility': 'private'" in src


def test_moderation_approve_keeps_mls_shared_false():
    from apps.immoweb import moderation as mod

    src = inspect.getsource(mod.approve_listing)
    assert '"mls_shared": False' in src or "'mls_shared': False" in src
    assert '"visibility": "public"' in src or "'visibility': 'public'" in src


def test_match_request_uses_shareable_clause():
    """client_requests_service.match_request deve riusare la clause MLS filtrata."""
    path = Path(__file__).resolve().parents[1] / "apps/immoweb/client_requests_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "_shareable_listing_clause":
                found = True
                break
    assert found, "match path must call _shareable_listing_clause()"
