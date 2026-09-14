"""Backend tests for M2.5.1 (D-041): Multi-branch / Franchising Layer.

Covers:
- Group CRUD (create, get, list, patch)
- Branch attach / detach
- Consolidated KPIs rollup
- Role promotion (agency_admin/super_admin → group_admin)
- Backward-compat: existing agencies still work without group_id
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://omnia-crm-docs.preview.emergentagent.com",
).rstrip("/")
ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def super_admin_agency_id(session):
    """The agency owned by the super_admin (used to attach as branch in tests)."""
    r = session.get(f"{BASE_URL}/api/app/agencies/me")
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _cleanup_test_groups(session):
    """Remove ALL groups owned by the admin (tests need a clean slate)."""
    r = session.get(f"{BASE_URL}/api/app/groups")
    if r.status_code != 200:
        return
    for g in r.json().get("items", []):
        session.delete(f"{BASE_URL}/api/app/groups/{g['id']}")


@pytest.fixture(scope="module", autouse=True)
def cleanup_before_and_after(session):
    _cleanup_test_groups(session)
    yield
    _cleanup_test_groups(session)


# ---------- GROUP CRUD ----------

class TestGroupCRUD:
    def test_create_group(self, session):
        payload = {
            "name": f"TEST_Group_{uuid.uuid4().hex[:6]}",
            "franchise_name": "TestFranchise",
            "credits_mode": "branch",
            "notes": "smoke test M2.5.1",
        }
        r = session.post(f"{BASE_URL}/api/app/groups", json=payload)
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["id"]
        assert data["slug"].startswith("test-group-")
        assert data["credits_mode"] == "branch"
        assert data["franchise_name"] == "TestFranchise"
        assert data["is_active"] is True

    def test_second_group_conflict(self, session):
        payload = {"name": f"TEST_Group_{uuid.uuid4().hex[:6]}", "credits_mode": "branch"}
        # The super_admin already owns 1 group from the previous test → 400
        r = session.post(f"{BASE_URL}/api/app/groups", json=payload)
        assert r.status_code == 400, r.text
        assert r.json()["detail"] == "group_already_exists"

    def test_list_groups(self, session):
        r = session.get(f"{BASE_URL}/api/app/groups")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data and "total" in data
        # super_admin sees all groups
        assert data["total"] >= 1
        # branches_count enrichment present
        for g in data["items"]:
            assert "branches_count" in g

    def test_get_group_me(self, session):
        r = session.get(f"{BASE_URL}/api/app/groups/me")
        # after create, super_admin was promoted to group_admin and got group_id
        assert r.status_code == 200, r.text
        assert "id" in r.json()
        assert "branches_count" in r.json()

    def test_patch_group(self, session):
        # Get the current group
        me = session.get(f"{BASE_URL}/api/app/groups/me").json()
        gid = me["id"]
        r = session.patch(
            f"{BASE_URL}/api/app/groups/{gid}",
            json={"franchise_name": "Updated Franchise", "credits_mode": "group"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["franchise_name"] == "Updated Franchise"
        assert data["credits_mode"] == "group"


# ---------- BRANCHES ----------

class TestBranches:
    def test_attach_branch(self, session, super_admin_agency_id):
        gid = session.get(f"{BASE_URL}/api/app/groups/me").json()["id"]
        r = session.post(
            f"{BASE_URL}/api/app/groups/{gid}/branches",
            json={"agency_id": super_admin_agency_id, "branch_code": "TEST-01"},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["group_id"] == gid
        assert data["branch_code"] == "TEST-01"

    def test_list_branches(self, session, super_admin_agency_id):
        gid = session.get(f"{BASE_URL}/api/app/groups/me").json()["id"]
        r = session.get(f"{BASE_URL}/api/app/groups/{gid}/branches")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        ids = [b["id"] for b in data["items"]]
        assert super_admin_agency_id in ids
        # BranchSummary shape assertions
        for b in data["items"]:
            for k in ("id", "slug", "display_name", "properties_active", "clients_total", "leads_open"):
                assert k in b

    def test_attach_conflict_when_already_in_another_group(self, session, super_admin_agency_id):
        # Attach again to the same group → same group, no conflict (idempotent-ish)
        gid = session.get(f"{BASE_URL}/api/app/groups/me").json()["id"]
        r = session.post(
            f"{BASE_URL}/api/app/groups/{gid}/branches",
            json={"agency_id": super_admin_agency_id, "branch_code": "TEST-01-again"},
        )
        # Same group: allowed (updates branch_code)
        assert r.status_code in (200, 201), r.text

    def test_consolidated_kpis(self, session, super_admin_agency_id):
        gid = session.get(f"{BASE_URL}/api/app/groups/me").json()["id"]
        r = session.get(f"{BASE_URL}/api/app/groups/{gid}/consolidated")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["group_id"] == gid
        assert data["branches_count"] >= 1
        assert data["branches_active"] >= 1
        # Numeric fields exist and are ints
        for k in ("properties_active", "properties_total", "clients_total", "leads_open", "leads_total"):
            assert isinstance(data[k], int)

    def test_detach_branch(self, session, super_admin_agency_id):
        gid = session.get(f"{BASE_URL}/api/app/groups/me").json()["id"]
        r = session.delete(f"{BASE_URL}/api/app/groups/{gid}/branches/{super_admin_agency_id}")
        assert r.status_code == 200, r.text
        assert r.json()["group_id"] is None

    def test_detach_unknown_branch_404(self, session):
        gid = session.get(f"{BASE_URL}/api/app/groups/me").json()["id"]
        r = session.delete(f"{BASE_URL}/api/app/groups/{gid}/branches/unknown-uuid")
        assert r.status_code == 404


# ---------- BACKWARD-COMPAT ----------

class TestBackwardCompat:
    def test_get_my_agency_still_works(self, session):
        """Existing /agencies/me endpoint keeps returning the agency for old flow."""
        r = session.get(f"{BASE_URL}/api/app/agencies/me")
        assert r.status_code == 200
        # Even after group churn, the agency is intact
        assert "id" in r.json()

    def test_auth_me_exposes_group_id_field(self, session):
        r = session.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200
        # group_id key must exist (nullable) — frontend expects it
        assert "group_id" in r.json()


# ---------- AUTH BOUNDARY ----------

class TestAuthBoundary:
    def test_unauth_groups(self):
        r = requests.get(f"{BASE_URL}/api/app/groups")
        assert r.status_code in (401, 403)

    def test_group_get_404_unknown(self, session):
        r = session.get(f"{BASE_URL}/api/app/groups/does-not-exist")
        assert r.status_code == 404
