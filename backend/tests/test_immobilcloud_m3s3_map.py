"""Backend tests for M3.S3 ImmobilCloud Map + Advanced Filters.

Covers:
  - GET /api/cloud/map (no filters)
  - GET /api/cloud/map?bbox=... (valid + invalid)
  - GET /api/cloud/map advanced filters (operation/price/bedrooms_min/energy_class)
  - GET /api/cloud/search advanced filters (bedrooms_min, bathrooms_min, energy_class)
  - GET /api/cloud/search lat/lng in card items
  - POST /api/app/properties triggers schedule_geocode (warning if Nominatim unreachable)
  - PATCH /api/app/properties/{id} re-triggers geocoding on address change
"""
import os
import time
import uuid

import pytest
import requests

BASE_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or "https://omnia-crm-docs.preview.emergentagent.com"
).rstrip("/")
ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]

# Two deterministic in-bbox points (Roma area) and one out-of-bbox (Milano)
ROMA_LAT, ROMA_LNG = 41.9028, 12.4964        # inside bbox 41.0,12.0,42.5,13.0
ROMA_LAT_2, ROMA_LNG_2 = 41.8500, 12.5200    # inside bbox
MILANO_LAT, MILANO_LNG = 45.4642, 9.1900     # OUTSIDE bbox

TEST_BBOX = "41.0,12.0,42.5,13.0"            # south,west,north,east


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text[:200]}")
    return s


def _build_property_payload(
    title: str,
    *,
    lat=None,
    lng=None,
    bedrooms=2,
    bathrooms=1,
    energy_class="C",
    operation="sale",
    price=250000,
    city="Roma",
    address=None,
    postal_code=None,
):
    payload = {
        "title": title,
        "description": f"M3S3 test {title}",
        "property_type": "appartamento",
        "operation": operation,
        "status": "active",
        "visibility": "public",
        "is_listed_on_immobilcloud": True,
        "city": city,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "rooms": bedrooms + 1,
        "surface_sqm": 90,
        "energy": {"energy_class": energy_class},
        "price": price if operation == "sale" else None,
        "rent_monthly": price if operation == "rent" else None,
    }
    if lat is not None:
        payload["lat"] = lat
    if lng is not None:
        payload["lng"] = lng
    if address:
        payload["address"] = address
    if postal_code:
        payload["postal_code"] = postal_code
    return payload


def _create(session, payload):
    r = session.post(f"{BASE_URL}/api/app/properties", json=payload)
    assert r.status_code == 201, f"create failed: {r.status_code} {r.text[:300]}"
    return r.json()


def _delete(session, pid):
    try:
        session.delete(f"{BASE_URL}/api/app/properties/{pid}")
    except Exception:
        pass


@pytest.fixture(scope="module")
def seeded_properties(admin_session):
    """Create deterministic test properties and clean up at end."""
    created = []

    # 1) Inside bbox, sale, bedrooms=3, bathrooms=2, energy A
    p1 = _create(admin_session, _build_property_payload(
        f"TEST_M3S3_inside_A_{uuid.uuid4().hex[:6]}",
        lat=ROMA_LAT, lng=ROMA_LNG,
        bedrooms=3, bathrooms=2, energy_class="A",
        operation="sale", price=250000,
    ))
    created.append(p1["id"])

    # 2) Inside bbox, rent, bedrooms=1, bathrooms=1, energy C
    p2 = _create(admin_session, _build_property_payload(
        f"TEST_M3S3_inside_rent_{uuid.uuid4().hex[:6]}",
        lat=ROMA_LAT_2, lng=ROMA_LNG_2,
        bedrooms=1, bathrooms=1, energy_class="C",
        operation="rent", price=1200, city="Roma",
    ))
    created.append(p2["id"])

    # 3) OUTSIDE bbox (Milano), sale, bedrooms=2, energy B
    p3 = _create(admin_session, _build_property_payload(
        f"TEST_M3S3_outside_{uuid.uuid4().hex[:6]}",
        lat=MILANO_LAT, lng=MILANO_LNG,
        bedrooms=2, bathrooms=1, energy_class="B",
        operation="sale", price=400000, city="Milano",
    ))
    created.append(p3["id"])

    yield {"inside_A": p1, "inside_rent": p2, "outside": p3}

    for pid in created:
        _delete(admin_session, pid)


# ============================================================
# 1) /api/cloud/map
# ============================================================

class TestCloudMapEndpoint:
    def test_map_returns_items_and_count(self, seeded_properties):
        r = requests.get(f"{BASE_URL}/api/cloud/map")
        assert r.status_code == 200
        d = r.json()
        assert "items" in d and "count" in d
        assert d["count"] == len(d["items"])
        assert d["count"] >= 3  # at least the 3 we seeded

        # Every item must have lat/lng + required fields
        for it in d["items"]:
            assert it.get("lat") is not None
            assert it.get("lng") is not None
            assert "id" in it
            assert "price" in it or "rent_monthly" in it
            assert "operation" in it
            assert "property_type" in it
            assert "city" in it

    def test_map_bbox_filters_in_and_out(self, seeded_properties):
        r = requests.get(f"{BASE_URL}/api/cloud/map?bbox={TEST_BBOX}")
        assert r.status_code == 200
        d = r.json()
        ids = {it["id"] for it in d["items"]}

        assert seeded_properties["inside_A"]["id"] in ids, "in-bbox property must be returned"
        assert seeded_properties["inside_rent"]["id"] in ids, "second in-bbox property must be returned"
        assert seeded_properties["outside"]["id"] not in ids, "Milano property must be excluded by bbox"

        # All returned coords must be within bbox
        for it in d["items"]:
            assert 41.0 <= it["lat"] <= 42.5
            assert 12.0 <= it["lng"] <= 13.0

    def test_map_bbox_invalid_returns_400(self):
        r = requests.get(f"{BASE_URL}/api/cloud/map?bbox=invalid")
        assert r.status_code == 400
        assert "invalid_bbox" in r.text or r.json().get("detail") == "invalid_bbox_format"

    def test_map_bbox_invalid_partial_returns_400(self):
        r = requests.get(f"{BASE_URL}/api/cloud/map?bbox=41.0,12.0,42.5")  # only 3 parts
        assert r.status_code == 400

    def test_map_filter_operation_and_price_range(self, seeded_properties):
        # operation=sale + price 100k..500k should include inside_A (250k) and outside (400k)
        r = requests.get(
            f"{BASE_URL}/api/cloud/map?operation=sale&price_min=100000&price_max=500000"
        )
        assert r.status_code == 200
        d = r.json()
        ids = {it["id"] for it in d["items"]}
        assert seeded_properties["inside_A"]["id"] in ids
        # The rent property must NOT appear (operation=sale filter)
        assert seeded_properties["inside_rent"]["id"] not in ids
        for it in d["items"]:
            assert it["operation"] == "sale"
            if it.get("price") is not None:
                assert 100000 <= it["price"] <= 500000

    def test_map_filter_bedrooms_min_and_energy_class(self, seeded_properties):
        r = requests.get(f"{BASE_URL}/api/cloud/map?bedrooms_min=2&energy_class=A")
        assert r.status_code == 200
        d = r.json()
        ids = {it["id"] for it in d["items"]}
        # inside_A has bedrooms=3 AND energy=A — must be included
        assert seeded_properties["inside_A"]["id"] in ids
        # inside_rent has bedrooms=1 — excluded
        assert seeded_properties["inside_rent"]["id"] not in ids
        # outside has energy=B — excluded
        assert seeded_properties["outside"]["id"] not in ids

    def test_map_invalid_energy_class_returns_422(self):
        r = requests.get(f"{BASE_URL}/api/cloud/map?energy_class=Z")
        assert r.status_code == 422


# ============================================================
# 2) /api/cloud/search advanced filters
# ============================================================

class TestSearchAdvancedFilters:
    def test_search_bedrooms_min(self, seeded_properties):
        r = requests.get(f"{BASE_URL}/api/cloud/search?bedrooms_min=3&page_size=60")
        assert r.status_code == 200
        items = r.json()["items"]
        for it in items:
            assert (it.get("bedrooms") or 0) >= 3
        ids = {it["id"] for it in items}
        assert seeded_properties["inside_A"]["id"] in ids
        assert seeded_properties["inside_rent"]["id"] not in ids

    def test_search_bathrooms_min(self, seeded_properties):
        r = requests.get(f"{BASE_URL}/api/cloud/search?bathrooms_min=2&page_size=60")
        assert r.status_code == 200
        items = r.json()["items"]
        for it in items:
            assert (it.get("bathrooms") or 0) >= 2
        ids = {it["id"] for it in items}
        assert seeded_properties["inside_A"]["id"] in ids

    def test_search_energy_class_valid(self, seeded_properties):
        r = requests.get(f"{BASE_URL}/api/cloud/search?energy_class=A&page_size=60")
        assert r.status_code == 200
        items = r.json()["items"]
        for it in items:
            assert it.get("energy_class") == "A"
        ids = {it["id"] for it in items}
        assert seeded_properties["inside_A"]["id"] in ids

    def test_search_energy_class_invalid_returns_422(self):
        r = requests.get(f"{BASE_URL}/api/cloud/search?energy_class=Z")
        assert r.status_code == 422

    def test_search_returns_lat_lng_in_cards(self, seeded_properties):
        r = requests.get(f"{BASE_URL}/api/cloud/search?page_size=60")
        assert r.status_code == 200
        items = r.json()["items"]
        # find one of our seeded properties
        target = next(
            (it for it in items if it["id"] == seeded_properties["inside_A"]["id"]),
            None,
        )
        assert target is not None, "seeded property must appear in search"
        assert target.get("lat") == ROMA_LAT
        assert target.get("lng") == ROMA_LNG


# ============================================================
# 3) Geocoding fire-and-forget
# ============================================================

class TestGeocodingTrigger:
    def test_create_without_coords_schedules_geocode(self, admin_session):
        """Property created with valid address but no lat/lng should eventually
        get coordinates populated via Nominatim (best-effort, tolerant)."""
        payload = _build_property_payload(
            f"TEST_M3S3_geo_create_{uuid.uuid4().hex[:6]}",
            address="Via del Corso 1",
            city="Roma",
            postal_code="00186",
            bedrooms=2, bathrooms=1, energy_class="C",
        )
        # Ensure no lat/lng in payload
        payload.pop("lat", None)
        payload.pop("lng", None)

        created = _create(admin_session, payload)
        pid = created["id"]
        try:
            assert created.get("lat") in (None, 0) or created.get("lat") is None
            assert created.get("lng") in (None, 0) or created.get("lng") is None

            # Poll up to ~12s for geocoding to complete (Nominatim rate limit 1 req/s)
            populated = False
            for _ in range(12):
                time.sleep(1)
                r = admin_session.get(f"{BASE_URL}/api/app/properties/{pid}")
                if r.status_code == 200:
                    d = r.json()
                    if d.get("lat") is not None and d.get("lng") is not None:
                        populated = True
                        # Sanity: Italy lat range ~ 35..48, lng ~ 6..19
                        assert 35.0 <= d["lat"] <= 48.0
                        assert 6.0 <= d["lng"] <= 19.0
                        break
            if not populated:
                pytest.skip("Nominatim did not respond in time (external API; tolerated)")
        finally:
            _delete(admin_session, pid)

    def test_patch_address_reschedules_geocode(self, admin_session):
        """PATCH that changes address fields should re-trigger geocoding."""
        # Create without coords
        payload = _build_property_payload(
            f"TEST_M3S3_geo_patch_{uuid.uuid4().hex[:6]}",
            address="Piazza San Marco",
            city="Venezia",
            postal_code="30124",
            bedrooms=2, bathrooms=1, energy_class="B",
        )
        payload.pop("lat", None)
        payload.pop("lng", None)
        created = _create(admin_session, payload)
        pid = created["id"]
        try:
            # PATCH to change city -> Firenze
            r = admin_session.patch(
                f"{BASE_URL}/api/app/properties/{pid}",
                json={"city": "Firenze", "address": "Piazza del Duomo", "postal_code": "50122"},
            )
            assert r.status_code == 200, f"patch failed: {r.text[:200]}"

            # Tolerant poll
            for _ in range(12):
                time.sleep(1)
                rr = admin_session.get(f"{BASE_URL}/api/app/properties/{pid}")
                if rr.status_code == 200:
                    d = rr.json()
                    if d.get("lat") is not None and d.get("lng") is not None:
                        # Firenze is roughly lat 43.77, lng 11.25 (with Venezia ~45.43)
                        # Just sanity check it's in Italy.
                        assert 35.0 <= d["lat"] <= 48.0
                        assert 6.0 <= d["lng"] <= 19.0
                        return
            pytest.skip("Nominatim did not respond in time (external API; tolerated)")
        finally:
            _delete(admin_session, pid)
