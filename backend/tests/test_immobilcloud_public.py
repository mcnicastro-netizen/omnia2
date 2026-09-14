"""Backend tests for M3.S1 ImmobilCloud B2C public portal."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")


class TestPublicSearch:
    def test_search_returns_active_properties(self):
        r = requests.get(f"{BASE_URL}/api/cloud/search")
        assert r.status_code == 200
        d = r.json()
        assert "items" in d
        assert "total" in d
        assert d["page"] == 1
        assert d["page_size"] == 20
        for item in d["items"]:
            assert "id" in item
            assert "title" in item
            assert "agency" in item
            assert item["agency"]["name"]

    def test_search_filters_by_city(self):
        r = requests.get(f"{BASE_URL}/api/cloud/search?city=Roma")
        assert r.status_code == 200
        for it in r.json()["items"]:
            assert it["city"].lower().startswith("roma")

    def test_search_filters_by_operation(self):
        r = requests.get(f"{BASE_URL}/api/cloud/search?operation=sale")
        assert r.status_code == 200
        for it in r.json()["items"]:
            assert it["operation"] == "sale"

    def test_search_sort_price_asc(self):
        r = requests.get(f"{BASE_URL}/api/cloud/search?sort=price_asc&page_size=5")
        assert r.status_code == 200

    def test_search_pagination_works(self):
        r1 = requests.get(f"{BASE_URL}/api/cloud/search?page=1&page_size=1")
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["page"] == 1
        assert len(d1["items"]) <= 1
        if d1["total"] > 1:
            r2 = requests.get(f"{BASE_URL}/api/cloud/search?page=2&page_size=1")
            assert r2.json()["page"] == 2

    def test_search_invalid_sort_rejected(self):
        r = requests.get(f"{BASE_URL}/api/cloud/search?sort=xxx")
        assert r.status_code == 422


class TestPublicFacets:
    def test_facets_has_cities_and_types(self):
        r = requests.get(f"{BASE_URL}/api/cloud/facets")
        assert r.status_code == 200
        d = r.json()
        assert "total_active" in d
        assert "cities" in d
        assert "property_types" in d
        assert isinstance(d["cities"], list)

    def test_facets_filter_by_operation(self):
        r = requests.get(f"{BASE_URL}/api/cloud/facets?operation=rent")
        assert r.status_code == 200


class TestPublicPropertyDetail:
    def _get_pid(self):
        r = requests.get(f"{BASE_URL}/api/cloud/search?page_size=1")
        items = r.json().get("items") or []
        return items[0]["id"] if items else None

    def test_property_detail_returns_data(self):
        pid = self._get_pid()
        if not pid:
            pytest.skip("no active properties in DB")
        r = requests.get(f"{BASE_URL}/api/cloud/property/{pid}")
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == pid
        assert "agency" in d
        # Sensitive fields must NOT be exposed
        assert "owner" not in d
        assert "seller_client_id" not in d
        assert "commission_pct" not in d
        assert "listing_agent_id" not in d

    def test_unknown_property_returns_404(self):
        r = requests.get(f"{BASE_URL}/api/cloud/property/does-not-exist")
        assert r.status_code == 404


class TestPublicAgency:
    def test_unknown_agency_returns_404(self):
        r = requests.get(f"{BASE_URL}/api/cloud/agency/does-not-exist")
        assert r.status_code == 404


class TestPublicNoAuth:
    def test_search_works_without_auth(self):
        # explicit: no cookies, no auth headers
        s = requests.Session()
        r = s.get(f"{BASE_URL}/api/cloud/search")
        assert r.status_code == 200

    def test_facets_works_without_auth(self):
        s = requests.Session()
        r = s.get(f"{BASE_URL}/api/cloud/facets")
        assert r.status_code == 200
