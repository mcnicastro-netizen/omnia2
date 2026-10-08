#!/usr/bin/env python3
"""Point Stripe test webhook endpoint at current public tunnel (sandbox only).

Idempotent: create or update an OMNIA Cloud Agent endpoint to
  {public_url}/api/billing/webhook
Never prints secret values. No-op if not sk_test_ or no public URL.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

ENDPOINT_DESC = "OMNIA Cloud Agent portal (auto-sync)"
EVENTS = ("checkout.session.completed", "customer.subscription.updated", "customer.subscription.deleted")


def _public_url(arg: str | None, share_file: str) -> str:
    url = (arg or "").strip().rstrip("/")
    if not url and Path(share_file).is_file():
        url = Path(share_file).read_text(encoding="utf-8").strip().rstrip("/")
    if not url or not re.match(r"^https://[a-z0-9-]+\.trycloudflare\.com$", url):
        return ""
    return url


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--share-file", default="/tmp/omnia-stack/SHARE_URL.txt")
    args = ap.parse_args()

    def _read_env_file_key(key: str) -> str:
        path = BACKEND / ".env"
        if not path.is_file():
            return ""
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
        return ""

    # Prefer process/vault; fall back to disk .env (Cloud Agent may drop file-only
    # Stripe until Founder reinjects vault — P-018). Never accept sk_live_.
    sk = (os.environ.get("STRIPE_SECRET_KEY") or "").strip() or _read_env_file_key("STRIPE_SECRET_KEY")
    enabled = (os.environ.get("STRIPE_ENABLED") or "").strip() or _read_env_file_key("STRIPE_ENABLED")
    if not sk.startswith("sk_test_"):
        print("[sync-stripe-webhook] SKIP need sk_test_ (process or .env)")
        return 0
    if enabled.strip().lower() != "true":
        # Auto-enable sandbox when we clearly have sk_test_
        enabled = "true"
        os.environ["STRIPE_ENABLED"] = "true"
    os.environ["STRIPE_SECRET_KEY"] = sk

    base = _public_url(args.url, args.share_file)
    if not base:
        print("[sync-stripe-webhook] SKIP no public tunnel url")
        return 0
    target = f"{base}/api/billing/webhook"

    try:
        import stripe
    except ImportError:
        print("[sync-stripe-webhook] SKIP stripe package missing")
        return 0

    stripe.api_key = sk
    try:
        existing = stripe.WebhookEndpoint.list(limit=100).data
    except Exception as e:
        print(f"[sync-stripe-webhook] list failed: {type(e).__name__}")
        return 1

    ours = [ep for ep in existing if (ep.get("description") or "") == ENDPOINT_DESC]
    # also match by path if description missing from older manual endpoints
    by_url = [ep for ep in existing if (ep.get("url") or "").endswith("/api/billing/webhook")]

    ep = ours[0] if ours else (by_url[0] if by_url else None)
    try:
        if ep is None:
            created = stripe.WebhookEndpoint.create(
                url=target,
                enabled_events=list(EVENTS),
                description=ENDPOINT_DESC,
                api_version=None,
            )
            secret = created.get("secret") or ""
            if secret:
                # Persist whsec into .env for local verify (vault still SoT long-term)
                env_path = BACKEND / ".env"
                lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.is_file() else []
                out, found = [], False
                for line in lines:
                    if line.lstrip().startswith("STRIPE_WEBHOOK_SECRET="):
                        if not found:
                            out.append(f"STRIPE_WEBHOOK_SECRET={secret}")
                            found = True
                        continue
                    out.append(line)
                if not found:
                    out.append(f"STRIPE_WEBHOOK_SECRET={secret}")
                env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
                os.environ["STRIPE_WEBHOOK_SECRET"] = secret
                print("[sync-stripe-webhook] CREATED endpoint + wrote STRIPE_WEBHOOK_SECRET (len only)")
                print(f"  url_class=trycloudflare secret_len={len(secret)}")
            else:
                print("[sync-stripe-webhook] CREATED endpoint (no secret returned — set whsec in vault)")
            return 0

        current = (ep.get("url") or "").rstrip("/")
        if current == target:
            print("[sync-stripe-webhook] OK already pointed at current tunnel")
            return 0

        stripe.WebhookEndpoint.modify(ep["id"], url=target, description=ENDPOINT_DESC)
        print("[sync-stripe-webhook] UPDATED endpoint url → current tunnel")
        return 0
    except Exception as e:
        print(f"[sync-stripe-webhook] mutate failed: {type(e).__name__}: {str(e)[:120]}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
