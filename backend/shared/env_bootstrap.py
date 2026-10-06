"""Load backend/.env without letting it clobber Cloud Agent vault secrets.

Cursor injects My Secrets / Environment Secrets into the process env at boot
(see CLOUD_AGENT_INJECTED_SECRET_NAMES). server.py historically used
load_dotenv(..., override=True) so the committed template
STRIPE_ENABLED=false in backend/.env wiped vault STRIPE_ENABLED=true and
left billing in permanent 503 even when Stripe keys were present.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv

# Keys that must never be overwritten by a local .env when already set in-process
# (Cloud Agent vault, CI, or explicit export).
_VAULT_PROTECTED: frozenset[str] = frozenset(
    {
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "STRIPE_PUBLIC_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_ENABLED",
        "STRIPE_MODE",
        "RESEND_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "EMERGENT_LLM_KEY",
        "FAL_KEY",
        "TAVILY_API_KEY",
        "JWT_SECRET",
        "GOOGLE_CLIENT_ID",
        "ADMIN_EMAIL",
        "ADMIN_PASSWORD",
        "DEMO_ADMIN_PASSWORD",
    }
)


def _injected_names() -> set[str]:
    raw = os.environ.get("CLOUD_AGENT_INJECTED_SECRET_NAMES") or ""
    return {n.strip() for n in raw.split(",") if n.strip()}


def _snapshot_protected() -> dict[str, str]:
    names = _VAULT_PROTECTED | _injected_names()
    out: dict[str, str] = {}
    for key in names:
        val = os.environ.get(key)
        if val is not None and str(val).strip() != "":
            out[key] = val
    return out


def _restore(snapshot: dict[str, str]) -> None:
    for key, val in snapshot.items():
        os.environ[key] = val


def _normalize_stripe_flags() -> None:
    """After restore: keep test sandbox usable; never auto-enable live."""
    sk = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    pk = (
        os.environ.get("STRIPE_PUBLISHABLE_KEY")
        or os.environ.get("STRIPE_PUBLIC_KEY")
        or ""
    ).strip()
    if pk and not (os.environ.get("STRIPE_PUBLISHABLE_KEY") or "").strip():
        os.environ["STRIPE_PUBLISHABLE_KEY"] = pk

    enabled = (os.environ.get("STRIPE_ENABLED") or "").strip().lower()
    if sk.startswith("sk_test_"):
        if enabled != "true":
            # Vault key present but template .env forced false — enable sandbox.
            os.environ["STRIPE_ENABLED"] = "true"
        os.environ["STRIPE_MODE"] = "test"
    elif sk.startswith("sk_live_"):
        # Live keys require an explicit STRIPE_ENABLED=true from vault/ops.
        # Do not auto-enable from a mere secret presence.
        os.environ["STRIPE_MODE"] = "live"


def load_backend_env(
    env_path: Path | str | None = None,
    *,
    override: bool = True,
    extra_protect: Iterable[str] | None = None,
) -> Path:
    """Load dotenv then re-apply process/vault secrets so they win.

    Returns the path that was loaded (or the default backend/.env).
    """
    root = Path(__file__).resolve().parents[1]
    path = Path(env_path) if env_path else root / ".env"
    snapshot = _snapshot_protected()
    if extra_protect:
        for key in extra_protect:
            val = os.environ.get(key)
            if val is not None and str(val).strip() != "":
                snapshot[key] = val
    if path.is_file():
        load_dotenv(path, override=override)
    _restore(snapshot)
    _normalize_stripe_flags()
    return path
