"""Unit: B2C listing publish SKUs (slot dal 3° + add-on)."""
from __future__ import annotations

from apps.billing.b2c_listing_publish import (
    BASE_PHOTO_LIMIT,
    FREE_TIER_MAX_ACTIVE,
    HARD_PHOTO_CAP,
    PHOTO_PACK_EXTRA,
    listing_requires_premium_sku,
    photo_limit_for,
    slot_fields_from_purchase,
)
from apps.billing.b2c_products import (
    is_b2c_listing_addon_product,
    is_b2c_listing_slot_product,
    list_listing_publish_products,
)


def test_free_tier_is_two():
    assert FREE_TIER_MAX_ACTIVE == 2


def test_catalog_has_four_publish_skus():
    keys = {p["key"] for p in list_listing_publish_products()}
    assert keys == {
        "b2c_listing_extra_90",
        "b2c_listing_premium",
        "b2c_hide_address",
        "b2c_photo_pack",
    }


def test_slot_and_addon_helpers():
    assert is_b2c_listing_slot_product("b2c_listing_extra_90")
    assert is_b2c_listing_slot_product("b2c_listing_premium")
    assert not is_b2c_listing_slot_product("b2c_vetrina_30")
    assert is_b2c_listing_addon_product("b2c_hide_address")
    assert is_b2c_listing_addon_product("b2c_photo_pack")
    assert not is_b2c_listing_addon_product("b2c_listing_extra_90")


def test_premium_threshold():
    assert listing_requires_premium_sku({"price": 1_000_001}) is True
    assert listing_requires_premium_sku({"price": 900_000}) is False
    assert listing_requires_premium_sku({"rent_monthly": 2_501}) is True
    assert listing_requires_premium_sku({"rent_monthly": 2_000}) is False


def test_photo_limits():
    assert photo_limit_for({}) == BASE_PHOTO_LIMIT
    assert photo_limit_for({"photo_pack_extra": PHOTO_PACK_EXTRA}) == HARD_PHOTO_CAP


def test_slot_fields_from_purchase():
    fields = slot_fields_from_purchase({
        "product_key": "b2c_listing_extra_90",
        "stripe_session_id": "cs_test_1",
    })
    assert fields["listing_publish_tier"] == "standard"
    assert fields["listing_slot_product_key"] == "b2c_listing_extra_90"
    assert fields["listing_paid_until"]


def test_prices_match_listino():
    from apps.billing.b2c_products import B2C_ONE_SHOT_PRODUCTS
    assert B2C_ONE_SHOT_PRODUCTS["b2c_listing_extra_90"]["price_eur"] == 14.90
    assert B2C_ONE_SHOT_PRODUCTS["b2c_listing_premium"]["price_eur"] == 19.90
    assert B2C_ONE_SHOT_PRODUCTS["b2c_hide_address"]["price_eur"] == 5.90
    assert B2C_ONE_SHOT_PRODUCTS["b2c_photo_pack"]["price_eur"] == 3.90
