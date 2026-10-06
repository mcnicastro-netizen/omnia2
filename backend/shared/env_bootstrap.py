"""Load backend/.env without letting it clobber Cloud Agent vault secrets.

Cursor injects My Secrets / Environment Secrets into the process env at boot
(see CLOUD_AGENT_INJECTED_SECRET_NAMES). server.py historically used
load_dotenv(..., override=True) so the committed template
STRIPE_ENABLED=false in backend/.env wiped vault STRIPE_ENABLED=true and
left billing in permanent 503 even when Stripe keys were present.

Additional hardening (Oct 2026):
- Prefer any sk_test_/pk_test_ value found in the process env over sk_live_
  (misnamed vault entries or stale .env must not win).
- On Cloud Agent boots, drop Stripe values that appeared *only* from .env
  (warm-disk / previous upsert of live keys).
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

_STRIPE_KEYS: frozenset[str] = frozenset(
    {
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "STRIPE_PUBLIC_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_ENABLED",
        "STRIPE_MODE",
    }
)


def _injected_names() -> set[str]:
    raw = os.environ.get("CLOUD_AGENT_INJECTED_SECRET_NAMES") or ""
    return {n.strip() for n in raw.split(",") if n.strip()}


def _all_vault_names() -> set[str]:
    raw = os.environ.get("CLOUD_AGENT_ALL_SECRET_NAMES") or ""
    return {n.strip() for n in raw.split(",") if n.strip()} | _injected_names()


def _is_cloud_agent() -> bool:
    return bool(_all_vault_names() or os.environ.get("CLOUD_AGENT_INJECTED_SECRET_NAMES"))


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


def prefer_stripe_test_keys() -> dict[str, str]:
    """If any env value is sk_test_/pk_test_, force those into canonical names.

    Returns a small presence report (no secret values) for logs/tests.
    """
    found_sk_test: str | None = None
    found_pk_test: str | None = None
    found_sk_live: str | None = None
    found_pk_live: str | None = None
    sk_source = pk_source = ""

    for key, raw in os.environ.items():
        if raw is None:
            continue
        val = str(raw).strip().strip('"').strip("'")
        if not val:
            continue
        if val.startswith("sk_test_") and found_sk_test is None:
            found_sk_test = val
            sk_source = key
        elif val.startswith("pk_test_") and found_pk_test is None:
            found_pk_test = val
            pk_source = key
        elif val.startswith("sk_live_") and found_sk_live is None:
            found_sk_live = val
        elif val.startswith("pk_live_") and found_pk_live is None:
            found_pk_live = val

    report = {
        "sk_class": "absent",
        "pk_class": "absent",
        "preferred_test": "false",
        "sk_source": "",
        "pk_source": "",
    }

    if found_sk_test:
        os.environ["STRIPE_SECRET_KEY"] = found_sk_test
        os.environ["STRIPE_ENABLED"] = "true"
        os.environ["STRIPE_MODE"] = "test"
        report["sk_class"] = "sk_test"
        report["preferred_test"] = "true"
        report["sk_source"] = sk_source
    elif found_sk_live:
        # Keep canonical live only if no test secret exists anywhere in env.
        if not (os.environ.get("STRIPE_SECRET_KEY") or "").strip():
            os.environ["STRIPE_SECRET_KEY"] = found_sk_live
        report["sk_class"] = "sk_live"

    if found_pk_test:
        os.environ["STRIPE_PUBLISHABLE_KEY"] = found_pk_test
        report["pk_class"] = "pk_test"
        report["preferred_test"] = "true"
        report["pk_source"] = pk_source
    elif found_pk_live:
        if not (os.environ.get("STRIPE_PUBLISHABLE_KEY") or "").strip():
            os.environ["STRIPE_PUBLISHABLE_KEY"] = found_pk_live
        if report["pk_class"] == "absent":
            report["pk_class"] = "pk_live"

    # Recompute classes from canonical after prefer
    sk = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    pk = (os.environ.get("STRIPE_PUBLISHABLE_KEY") or "").strip()
    if sk.startswith("sk_test_"):
        report["sk_class"] = "sk_test"
    elif sk.startswith("sk_live_"):
        report["sk_class"] = "sk_live"
    if pk.startswith("pk_test_"):
        report["pk_class"] = "pk_test"
    elif pk.startswith("pk_live_"):
        report["pk_class"] = "pk_live"
    return report


def _drop_file_only_stripe(snapshot: dict[str, str]) -> None:
    """On Cloud Agent: Stripe must come from vault/process, not warm .env disk."""
    if not _is_cloud_agent():
        return
    for key in _STRIPE_KEYS:
        if key in snapshot:
            continue
        # Appeared only via load_dotenv — discard (stale live upsert risk).
        os.environ.pop(key, None)


def _normalize_stripe_flags() -> None:
    """After restore: keep test sandbox usable; never auto-enable live."""
    prefer_stripe_test_keys()
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
            os.environ["STRIPE_ENABLED"] = "true"
        os.environ["STRIPE_MODE"] = "test"
    elif sk.startswith("sk_live_"):
        # Live keys: do not auto-enable. If ENABLED was only coming from a
        # stale .env=true paired with live, leave Founder-explicit vault value.
        os.environ["STRIPE_MODE"] = "live"


def stripe_key_classes() -> dict[str, str]:
    """Presence-only classification for diagnostics (never returns secret values)."""
    sk = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    pk = (os.environ.get("STRIPE_PUBLISHABLE_KEY") or "").strip()
    def klass(val: str, test_p: str, live_p: str) -> str:
        if not val:
            return "absent"
        if val.startswith(test_p):
            return test_p.rstrip("_")
        if val.startswith(live_p):
            return live_p.rstrip("_")
        return "other"
    return {
        "secret": klass(sk, "sk_test_", "sk_live_"),
        "publishable": klass(pk, "pk_test_", "pk_live_"),
        "enabled": (os.environ.get("STRIPE_ENABLED") or "").strip() or "absent",
        "mode": (os.environ.get("STRIPE_MODE") or "").strip() or "absent",
    }


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
    # Prefer test keys *before* snapshot so vault+aliases are protected together.
    prefer_stripe_test_keys()
    snapshot = _snapshot_protected()
    if extra_protect:
        for key in extra_protect:
            val = os.environ.get(key)
            if val is not None and str(val).strip() != "":
                snapshot[key] = val
    if path.is_file():
        load_dotenv(path, override=override)
    _restore(snapshot)
    _drop_file_only_stripe(snapshot)
    _normalize_stripe_flags()
    return path
