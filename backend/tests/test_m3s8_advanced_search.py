"""Backend tests for M3.S8 Advanced Search (Sprint 3 · Item #2)."""
import os
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://omnia-crm-docs.preview.emergentagent.com",
).rstrip("/")


class TestAdvancedSearchBasic:
    def test_endpoint_accepts_empty_body(self):
        r = requests.post(f"{BASE_URL}/api/cloud/search/advanced", json={})
        assert r.status_code == 200
        data = r.json()
        assert "items" in data and "total" in data
        assert data["page"] == 1

    def test_multi_city_filter(self):
        r = requests.post(f"{BASE_URL}/api/cloud/search/advanced",
                          json={"cities": ["Roma", "Milano"], "page_size": 5})
        assert r.status_code == 200
        data = r.json()
        assert data["filters_applied"]["cities"] == ["Roma", "Milano"]

    def test_multi_property_types(self):
        r = requests.post(f"{BASE_URL}/api/cloud/search/advanced",
                          json={"property_types": ["appartamento", "villa"]})
        assert r.status_code == 200


class TestAdvancedSearchPolygon:
    def test_polygon_less_than_3_points_ignored(self):
        r = requests.post(f"{BASE_URL}/api/cloud/search/advanced",
                          json={"polygon": [[45.0, 9.0], [45.1, 9.1]]})
        # <3 points: polygon simply not applied, request succeeds
        assert r.status_code == 200
        assert r.json()["filters_applied"]["polygon_points"] == 2

    def test_polygon_over_italy_returns_or_empty(self):
        # Very large polygon covering Milano+Roma
        r = requests.post(f"{BASE_URL}/api/cloud/search/advanced", json={
            "polygon": [[46.0, 8.0], [46.0, 13.0], [40.0, 13.0], [40.0, 8.0]],
        })
        assert r.status_code == 200
        assert r.json()["filters_applied"]["polygon_points"] == 4


class TestAdvancedSearchNearMe:
    def test_near_me_requires_coordinates(self):
        r = requests.post(f"{BASE_URL}/api/cloud/search/advanced",
                          json={"near_me": {"radius_km": 5}})
        assert r.status_code == 422

    def test_near_me_valid_returns(self):
        # Milano center
        r = requests.post(f"{BASE_URL}/api/cloud/search/advanced", json={
            "near_me": {"lat": 45.4642, "lng": 9.19, "radius_km": 3},
            "sort": "distance_asc",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["filters_applied"]["near_me"]["radius_km"] == 3
        # If any items → each must have _distance_km <= 3
        for item in data["items"]:
            if "_distance_km" in item:
                assert item["_distance_km"] <= 3


class TestAdvancedSearchComparePrices:
    def test_compare_prices_returns_stats_when_available(self):
        r = requests.post(f"{BASE_URL}/api/cloud/search/advanced", json={
            "operation": "sale",
            "compare_prices": True,
            "page_size": 5,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["filters_applied"]["compare_prices"] is True
        if data["total"] > 0 and data["price_stats"]:
            ps = data["price_stats"]
            assert ps["type"] in ("sale", "rent")
            assert ps["min"] <= ps["median"] <= ps["max"]
            assert ps["count"] >= 1

    def test_compare_prices_off_returns_null(self):
        r = requests.post(f"{BASE_URL}/api/cloud/search/advanced",
                          json={"compare_prices": False})
        assert r.status_code == 200
        assert r.json()["price_stats"] is None


class TestAdvancedSearchValidation:
    def test_invalid_operation_rejected(self):
        r = requests.post(f"{BASE_URL}/api/cloud/search/advanced",
                          json={"operation": "swap"})
        assert r.status_code == 422

    def test_polygon_over_max_points_rejected(self):
        many = [[45.0 + i * 0.001, 9.0 + i * 0.001] for i in range(150)]
        r = requests.post(f"{BASE_URL}/api/cloud/search/advanced",
                          json={"polygon": many})
        assert r.status_code == 422


class TestPointInPolygonUnit:
    def test_point_inside_square(self):
        from apps.immocloud.public_portal import _point_in_polygon
        square = [[0, 0], [0, 10], [10, 10], [10, 0]]
        assert _point_in_polygon(5, 5, square) is True
        assert _point_in_polygon(15, 5, square) is False

    def test_haversine_zero_distance(self):
        from apps.immocloud.public_portal import _haversine_km
        d = _haversine_km(45.4642, 9.19, 45.4642, 9.19)
        assert d < 0.001  # zero within numeric precision
