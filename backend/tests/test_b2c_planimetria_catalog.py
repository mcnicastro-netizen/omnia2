"""Smoke catalog + product registration for B2C planimetria (€12)."""
from apps.billing.b2c_products import (
    B2C_ONE_SHOT_PRODUCTS,
    get_b2c_product,
    is_b2c_coming_soon,
)


def test_planimetria_in_one_shot_catalog():
    p = get_b2c_product("b2c_planimetria_catastale")
    assert p is not None
    assert p["price_eur"] == 12.0
    assert p["stripe_lookup_key"] == "b2c_planimetria_catastale"
    assert not is_b2c_coming_soon("b2c_planimetria_catastale")
    assert "b2c_planimetria_catastale" in B2C_ONE_SHOT_PRODUCTS


def test_openapi_planimetria_helpers_importable():
    from shared.openapi_catasto import (
        request_elaborato_planimetrico,
        get_elaborato_planimetrico_status,
        download_elaborato_planimetrico_document,
    )
    assert callable(request_elaborato_planimetrico)
    assert callable(get_elaborato_planimetrico_status)
    assert callable(download_elaborato_planimetrico_document)
