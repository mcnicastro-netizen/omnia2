"""D-175 C1 — Dogfood perimeter (fail-closed isolation + sealed H4 gate)."""

from shared.dogfood.perimeter import (
    assert_dogfood_boot_or_raise,
    dogfood_preflight_checks,
    is_dogfood_env,
    is_h4_purchase_ready,
    guard_h4_purchase_or_raise,
    apply_dogfood_provider_holds,
)

__all__ = [
    "assert_dogfood_boot_or_raise",
    "dogfood_preflight_checks",
    "is_dogfood_env",
    "is_h4_purchase_ready",
    "guard_h4_purchase_or_raise",
    "apply_dogfood_provider_holds",
]
