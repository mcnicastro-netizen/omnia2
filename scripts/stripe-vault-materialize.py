#!/usr/bin/env python3
"""Materialize Stripe (+ vault) secrets into backend/.env for Cloud Agent boot.

- Prefers sk_test_/pk_test_ anywhere in process env over sk_live_
- Wipes prior STRIPE_* lines (stale warm-disk)
- Writes only non-empty process values
- Prints presence/classes only (never secret values)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from shared.env_bootstrap import (  # noqa: E402
    prefer_stripe_test_keys,
    stripe_key_classes,
)

UPSERT_KEYS = (
    "RESEND_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "EMERGENT_LLM_KEY",
    "FAL_KEY",
    "TAVILY_API_KEY",
    "JWT_SECRET",
    "GOOGLE_CLIENT_ID",
    "STRIPE_SECRET_KEY",
    "STRIPE_PUBLISHABLE_KEY",
    "STRIPE_PUBLIC_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_ENABLED",
    "STRIPE_MODE",
)


def wipe_stripe_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if (
            stripped.startswith("STRIPE_")
            or stripped.startswith("#STRIPE_")
            or stripped.startswith("# STRIPE_")
            or "Stripe (from Cloud Agent" in line
            or "Stripe (sandbox)" in line
        ):
            continue
        out.append(line)
    out.append("# --- Stripe (from Cloud Agent vault at boot; do not commit values) ---")
    return out


def upsert(lines: list[str], key: str, val: str) -> list[str]:
    prefix = f"{key}="
    out: list[str] = []
    found = False
    for line in lines:
        stripped = line.lstrip()
        if (
            stripped.startswith(prefix)
            or stripped.startswith("#" + prefix)
            or stripped.startswith("# " + prefix)
        ):
            if not found:
                out.append(f"{key}={val}")
                found = True
            continue
        out.append(line)
    if not found:
        out.append(f"{key}={val}")
    return out


def main() -> int:
    env_path = Path(sys.argv[1]) if len(sys.argv) > 1 else BACKEND / ".env"
    # Wait loop for late vault inject
    names = (
        os.environ.get("CLOUD_AGENT_ALL_SECRET_NAMES", "")
        + ","
        + os.environ.get("CLOUD_AGENT_INJECTED_SECRET_NAMES", "")
    )
    if "STRIPE_SECRET_KEY" in names and not (os.environ.get("STRIPE_SECRET_KEY") or "").strip():
        import time

        for _ in range(20):
            if (os.environ.get("STRIPE_SECRET_KEY") or "").strip():
                break
            time.sleep(0.25)

    rep = prefer_stripe_test_keys()
    sk = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    if sk.startswith("sk_test_"):
        os.environ["STRIPE_ENABLED"] = "true"
        os.environ["STRIPE_MODE"] = "test"
    elif sk.startswith("sk_live_"):
        os.environ["STRIPE_MODE"] = "live"

    lines: list[str] = []
    if env_path.is_file():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    lines = wipe_stripe_lines(lines)

    for key in UPSERT_KEYS:
        val = os.environ.get(key)
        if val is None or str(val).strip() == "":
            continue
        lines = upsert(lines, key, str(val))

    # If no Stripe secret materialized, keep explicit disabled flag in file
    if not (os.environ.get("STRIPE_SECRET_KEY") or "").strip():
        lines = upsert(lines, "STRIPE_ENABLED", "false")

    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    klass = stripe_key_classes()
    print(
        "[stripe-vault-materialize] "
        f"secret={klass['secret']} publishable={klass['publishable']} "
        f"enabled={klass['enabled']} mode={klass['mode']} "
        f"preferred_test={rep.get('preferred_test')}"
    )
    if klass["secret"] == "sk_live":
        print(
            "[stripe-vault-materialize] WARN: process env has sk_live_ "
            "(Cursor vault inject). Sandbox needs sk_test_.",
            file=sys.stderr,
        )
        return 2
    if klass["secret"] == "sk_test" and klass["publishable"] == "pk_live":
        print(
            "[stripe-vault-materialize] WARN: mixed test secret + live publishable",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
