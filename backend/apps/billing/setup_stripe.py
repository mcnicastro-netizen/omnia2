"""OMNIA — Stripe catalog setup (idempotent).

Reads plans + credit packages from apps.billing.plans and creates matching
Stripe Products + Prices using stable lookup_keys.

Usage:
    python -m apps.billing.setup_stripe

Idempotency: guaranteed. Re-running never duplicates products or prices.
"""
import os
import sys
import logging

# ensure /app/backend is on path when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env"))

import stripe

from apps.billing.plans import LAUNCH_PLANS, CREDIT_PACKAGES

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("stripe_setup")

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")


def _get_or_create_product(emergent_product_id: str, name: str, tax_code: str = "txcd_10103001") -> "stripe.Product":
    for p in stripe.Product.list(active=True, limit=100).auto_paging_iter():
        if p.to_dict().get("metadata", {}).get("emergent_product_id") == emergent_product_id:
            logger.info("Product exists: %s (%s)", emergent_product_id, p.id)
            return p
    prod = stripe.Product.create(
        name=name,
        tax_code=tax_code,
        metadata={"managed_by": "omnia", "emergent_product_id": emergent_product_id},
    )
    logger.info("Product created: %s (%s)", emergent_product_id, prod.id)
    return prod


def _ensure_price(product_id: str, lookup_key: str, amount_eur: float,
                  currency: str = "eur", interval: str = None):
    amount_cents = int(round(amount_eur * 100))
    existing = stripe.Price.list(lookup_keys=[lookup_key], active=True, limit=1).data
    if existing:
        p = existing[0]
        if p.unit_amount != amount_cents or p.currency != currency:
            stripe.Price.modify(p.id, active=False)
            logger.info("Deactivated stale price %s (lookup=%s)", p.id, lookup_key)
            existing = []
        else:
            logger.info("Price ok: %s (%s)", lookup_key, p.id)
            return p
    kwargs = dict(
        product=product_id, unit_amount=amount_cents, currency=currency,
        lookup_key=lookup_key, transfer_lookup_key=True,
        metadata={"managed_by": "omnia"},
    )
    if interval:
        kwargs["recurring"] = {"interval": interval}
    price = stripe.Price.create(**kwargs)
    logger.info("Price created: %s (%s) €%.2f/%s", lookup_key, price.id, amount_eur, interval or "one-off")
    return price


def main():
    if not stripe.api_key:
        logger.error("STRIPE_SECRET_KEY not set. Aborting.")
        sys.exit(1)

    logger.info("Setting up subscription plans...")
    for tier, plan in LAUNCH_PLANS.items():
        prod = _get_or_create_product(f"plan_{tier}", f"OMNIA {plan.name}")
        _ensure_price(prod.id, f"{tier}_monthly", plan.price_monthly, "eur", "month")
        _ensure_price(prod.id, f"{tier}_yearly", plan.price_yearly, "eur", "year")

    logger.info("Setting up credit packages...")
    for pkg in CREDIT_PACKAGES:
        prod = _get_or_create_product(f"credit_{pkg.key}", f"OMNIA Crediti {pkg.credits}")
        _ensure_price(prod.id, pkg.key, pkg.price_eur, "eur")

    logger.info("Stripe catalog setup complete. Use lookup_key at checkout, e.g. 'starter_monthly', 'pkg_200'.")


if __name__ == "__main__":
    main()
