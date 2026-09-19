"""Cestino: soft-delete property/client, restore, permanent purge."""
import os
import time
import uuid

import pytest
import requests

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:43121").rstrip("/")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")


@pytest.fixture(scope="module")
def session():
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        pytest.skip("ADMIN_EMAIL/PASSWORD not set")
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, r.text
    return s


def test_property_trash_restore_cycle(session):
    suffix = uuid.uuid4().hex[:8]
    create = session.post(
        f"{BASE}/api/app/properties",
        json={
            "title": f"Trash test {suffix}",
            "property_type": "appartamento",
            "operation": "sale",
            "status": "draft",
            "city": "Milano",
            "price": 100000,
            "surface_sqm": 50,
        },
        timeout=30,
    )
    assert create.status_code == 201, create.text
    prop_id = create.json()["id"]

    d = session.delete(f"{BASE}/api/app/properties/{prop_id}", timeout=30)
    assert d.status_code == 200, d.text
    assert d.json().get("trashed") is True

    gone = session.get(f"{BASE}/api/app/properties/{prop_id}", timeout=30)
    assert gone.status_code == 404

    trash = session.get(f"{BASE}/api/app/trash", timeout=30)
    assert trash.status_code == 200, trash.text
    ids = [i["id"] for i in trash.json().get("items", []) if i.get("kind") == "property"]
    assert prop_id in ids

    rest = session.post(f"{BASE}/api/app/trash/property/{prop_id}/restore", timeout=30)
    assert rest.status_code == 200, rest.text

    back = session.get(f"{BASE}/api/app/properties/{prop_id}", timeout=30)
    assert back.status_code == 200, back.text
    assert back.json()["title"].startswith("Trash test")

    # cleanup → trash then purge forever
    session.delete(f"{BASE}/api/app/properties/{prop_id}", timeout=30)
    purged = session.delete(f"{BASE}/api/app/trash/property/{prop_id}", timeout=30)
    assert purged.status_code == 200, purged.text
    assert session.get(f"{BASE}/api/app/properties/{prop_id}", timeout=30).status_code == 404


def test_client_trash_restore_cycle(session):
    suffix = uuid.uuid4().hex[:8]
    create = session.post(
        f"{BASE}/api/app/clients",
        json={"name": f"TrashCli{suffix}", "client_type": "buyer", "status": "new"},
        timeout=30,
    )
    assert create.status_code == 201, create.text
    cid = create.json()["id"]

    d = session.delete(f"{BASE}/api/app/clients/{cid}", timeout=30)
    assert d.status_code == 200, d.text
    assert d.json().get("trashed") is True

    assert session.get(f"{BASE}/api/app/clients/{cid}", timeout=30).status_code == 404

    trash = session.get(f"{BASE}/api/app/trash?kind=client", timeout=30)
    assert trash.status_code == 200
    assert cid in [i["id"] for i in trash.json().get("items", [])]

    assert session.post(f"{BASE}/api/app/trash/client/{cid}/restore", timeout=30).status_code == 200
    assert session.get(f"{BASE}/api/app/clients/{cid}", timeout=30).status_code == 200

    session.delete(f"{BASE}/api/app/clients/{cid}", timeout=30)
    assert session.delete(f"{BASE}/api/app/trash/client/{cid}", timeout=30).status_code == 200
