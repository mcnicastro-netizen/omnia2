"""Roll-forward of curated price snapshot to current month (FOI + regional trend)."""
from __future__ import annotations

from datetime import date

from apps.immocloud.data.coefficients import compute_regional_adjustment, foi_revaluation
from apps.immocloud.data.italy_real_estate_prices_2025 import (
    PRICE_DATASET_AS_OF,
    PRICE_DATASET_BASE_YEAR,
    PRICE_DATASET_LABEL,
    format_updated_data_source,
    months_since_price_dataset,
)


def test_months_since_snapshot_from_q1_2025():
    assert months_since_price_dataset(date(2025, 3, 31)) == 0
    assert months_since_price_dataset(date(2025, 9, 30)) == 6
    assert months_since_price_dataset(date(2026, 9, 18)) == 18


def test_foi_defaults_to_current_year():
    assert foi_revaluation(2026) == 1.0
    assert foi_revaluation(PRICE_DATASET_BASE_YEAR, 2026) == foi_revaluation(PRICE_DATASET_BASE_YEAR)


def test_format_source_mentions_update_month_not_stale_label_alone():
    s = format_updated_data_source(
        "Borsino/OMI Milano 2025-Q1",
        foi=1.015,
        months=18,
        as_of=date(2026, 9, 18),
    )
    assert "2025-Q1" in s
    assert "aggiornato a 2026-09" in s
    assert "FOI×1.015" in s
    assert "Dataset 2025" not in s


def test_lombardia_roll_forward_moves_prices_up_from_snapshot():
    """With positive YoY + FOI 2025→2026, updated €/m² > raw snapshot."""
    months = months_since_price_dataset(date(2026, 9, 18))
    foi = foi_revaluation(PRICE_DATASET_BASE_YEAR, 2026)
    pct, _ = compute_regional_adjustment("lombardia", months_since_omi=months)
    mult = foi * (1 + pct)
    assert mult > 1.0
    assert PRICE_DATASET_AS_OF.year == 2025
    assert "2025-Q1" in PRICE_DATASET_LABEL
