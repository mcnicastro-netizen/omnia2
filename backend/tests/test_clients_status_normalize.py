"""GET /clients non deve 500 su status fuori enum stretto."""
from __future__ import annotations

import inspect


def test_client_status_includes_active_hot():
    from shared.models.client import ClientStatus

    # typing.get_args su Literal
    args = getattr(ClientStatus, "__args__", ())
    assert "active" in args
    assert "hot" in args
    assert "new" in args


def test_list_clients_normalizes_status():
    from apps.immoweb import clients

    src = inspect.getsource(clients.list_clients)
    assert "_normalize_client_list_item" in src
    assert clients._normalize_client_list_item({"status": "won", "name": "x"})["status"] == "closed_won"
    assert clients._normalize_client_list_item({"status": "active", "name": "x"})["status"] == "active"
    assert clients._normalize_client_list_item({"status": "weird", "name": "x"})["status"] == "new"
