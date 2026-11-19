"""D-175 · C1 — Isolamento Dogfood fail-closed + hard-gate H4 sealed.

Precisione A: ``OMNIA_H4_PURCHASE_READY=true`` da solo NON sblocca gli acquisti.
Serve anche un marker sealed prodotto solo dopo C5+C6 (mai creato da C1).

Precisione B: acquisti commerciali = solo Main Admin nominato. Super Admin
non ha autorità implicita di purchase (D07 wallet ≠ checkout). Questo modulo
nega purchase a tutti finché H4 non è sealed-ready; C5 enforserà MA-only.

Precisione C: in Dogfood il runtime non può usare DB condiviso ``omnia``
né URI di produzione.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from fastapi import HTTPException

logger = logging.getLogger("omnia.dogfood.perimeter")

# Marker sealed: una sola riga firmata dal ciclo C6 (non da C1).
H4_READY_MARKER_LINE_PREFIX = "H4_PURCHASE_READY_V1="
H4_READY_MARKER_DEFAULT = "dogfood/h4_purchase_ready.sealed"

# DB names forbidden as Dogfood runtime (shared / prod / legacy).
_FORBIDDEN_DB_NAMES = frozenset(
    {
        "omnia",
        "omnia_prod",
        "omnia-production",
        "production",
        "prod",
        "test",
        "admin",
        "local",
        "omnia_local",
    }
)

_PROD_HOST_FRAGMENTS = (
    "api.omniarealestateecosystem.it",
    "www.omniarealestateecosystem.it",
    "omniarealestateecosystem.it",
)

_RAILWAY_MONGO_HINTS = (
    "railway.app",
    "rlwy.net",
    "mongodb.net",  # Atlas prod-like; dogfood uses local/dedicated
)


def is_dogfood_env() -> bool:
    return (os.environ.get("OMNIA_ENV") or "").strip().lower() == "dogfood"


def _split_csv(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    return [p.strip().lower() for p in raw.replace(";", ",").split(",") if p.strip()]


def _host_from_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    if "://" not in u:
        u = "https://" + u
    try:
        return (urlparse(u).hostname or "").lower()
    except Exception:  # noqa: BLE001
        return ""


def _is_loopback_host(host: str) -> bool:
    h = (host or "").lower()
    return h in ("127.0.0.1", "localhost", "::1") or h.endswith(".localhost")


def _db_name() -> str:
    return (os.environ.get("DB_NAME") or "").strip()


def _mongo_url() -> str:
    return (os.environ.get("MONGO_URL") or "").strip()


def check_dogfood_db_isolation() -> dict[str, Any]:
    """Precisione C — runtime Dogfood ≠ prod e ≠ DB condiviso sviluppo."""
    db = _db_name()
    mongo = _mongo_url()
    errors: list[str] = []
    if not db:
        errors.append("db_name_missing")
    elif db.lower() in _FORBIDDEN_DB_NAMES:
        errors.append("db_name_shared_or_forbidden")
    elif not db.lower().startswith("omnia_df_"):
        # Dogfood runtime must be dedicated copy DB (omnia_df_clean_* / cont_* / …)
        errors.append("db_name_not_dogfood_prefix")

    if not mongo:
        errors.append("mongo_url_missing")
    else:
        # Precisione C / fail-closed: Dogfood runtime Mongo host must be loopback.
        # Hint-only denylist (railway/atlas) is insufficient — block any remote host.
        host = ""
        try:
            host = (
                urlparse(mongo if "://" in mongo else f"mongodb://{mongo}").hostname or ""
            ).lower()
        except Exception:  # noqa: BLE001
            host = ""
        if not host:
            errors.append("mongo_url_host_unparseable")
        elif not _is_loopback_host(host):
            errors.append("mongo_url_remote_blocked")
        # Explicit permanent URI must never be runtime
        perm = (os.environ.get("OMNIA_DOGFOOD_PERMANENT_URI") or "").strip()
        if perm and mongo == perm:
            errors.append("mongo_url_is_permanent")
        runtime = (os.environ.get("OMNIA_DOGFOOD_RUNTIME_URI") or "").strip()
        if runtime and mongo != runtime:
            # If runtime URI is declared, MONGO_URL must match it
            errors.append("mongo_url_ne_runtime_uri")

    return {
        "ok": not errors,
        "db_name": db or None,
        "errors": errors,
    }


def check_dogfood_host_allowlists() -> dict[str, Any]:
    api_allow = _split_csv(os.environ.get("OMNIA_DOGFOOD_ALLOWED_API_HOSTS"))
    fe_allow = _split_csv(os.environ.get("OMNIA_DOGFOOD_ALLOWED_FE_HOSTS"))
    errors: list[str] = []
    if not api_allow:
        errors.append("api_allowlist_empty")
    if not fe_allow:
        errors.append("fe_allowlist_empty")

    api_url = (os.environ.get("OMNIA_API_PUBLIC_URL") or "").strip()
    fe_url = (
        os.environ.get("FRONTEND_URL")
        or os.environ.get("FRONTEND_ORIGIN")
        or os.environ.get("REACT_APP_BACKEND_URL")
        or ""
    ).strip()
    # REACT_APP_BACKEND_URL is API; prefer FRONTEND_* for FE check
    fe_candidates = [
        (os.environ.get("FRONTEND_URL") or "").strip(),
        (os.environ.get("FRONTEND_ORIGIN") or "").strip(),
        (os.environ.get("FRONTEND_PUBLIC_URL") or "").strip(),
    ]

    def _host_ok(host: str, allow: list[str]) -> bool:
        if not host:
            return False
        if host in allow:
            return True
        # allow entries may be bare IPs
        return any(host == a or host.endswith("." + a) for a in allow)

    api_host = _host_from_url(api_url) if api_url else ""
    if api_url:
        if any(frag in api_host for frag in _PROD_HOST_FRAGMENTS):
            errors.append("api_host_is_product")
        elif api_allow and not _host_ok(api_host, api_allow):
            errors.append("api_host_not_in_allowlist")

    for raw in fe_candidates:
        if not raw:
            continue
        h = _host_from_url(raw)
        if any(frag in h for frag in _PROD_HOST_FRAGMENTS):
            errors.append("fe_host_is_product")
            break
        if fe_allow and not _host_ok(h, fe_allow):
            errors.append("fe_host_not_in_allowlist")
            break

    tunnel = (os.environ.get("OMNIA_DOGFOOD_TUNNEL_HOST") or "").strip()
    if tunnel:
        th = _host_from_url(tunnel) or tunnel.lower()
        combined = set(api_allow) | set(fe_allow)
        if th not in combined and not _is_loopback_host(th):
            errors.append("tunnel_host_not_in_allowlist")

    return {
        "ok": not errors,
        "api_allowlist": api_allow,
        "fe_allowlist": fe_allow,
        "api_host": api_host or None,
        "fe_url_checked": bool(any(fe_candidates)),
        "errors": errors,
    }


def check_dogfood_stripe_test_only() -> dict[str, Any]:
    errors: list[str] = []
    sk = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    pk = (
        os.environ.get("STRIPE_PUBLISHABLE_KEY")
        or os.environ.get("STRIPE_PUBLIC_KEY")
        or ""
    ).strip()
    if sk.startswith("sk_live_"):
        errors.append("stripe_sk_live")
    if pk.startswith("pk_live_"):
        errors.append("stripe_pk_live")
    # If keys present, must be identifiable as test
    if sk and not sk.startswith("sk_test_"):
        errors.append("stripe_sk_not_test")
    if pk and not pk.startswith("pk_test_"):
        errors.append("stripe_pk_not_test")
    return {"ok": not errors, "errors": errors}


def h4_ready_marker_path() -> Path:
    raw = (os.environ.get("OMNIA_H4_READY_MARKER_PATH") or "").strip()
    if raw:
        return Path(raw)
    root = (os.environ.get("DOGFOOD_ROOT") or "").strip()
    if root:
        return Path(root) / H4_READY_MARKER_DEFAULT
    # Repo-relative default (never created by C1)
    return Path(__file__).resolve().parents[3] / H4_READY_MARKER_DEFAULT


def _marker_is_sealed(path: Path) -> bool:
    """True only if marker file exists and carries sealed C6 payload."""
    try:
        if not path.is_file():
            return False
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(H4_READY_MARKER_LINE_PREFIX):
            token = line[len(H4_READY_MARKER_LINE_PREFIX) :].strip()
            # Non-empty opaque token (≥16) — minted only after C6 verification
            if len(token) >= 16 and re.fullmatch(r"[A-Za-z0-9_\-.=]+", token):
                return True
    return False


def is_h4_purchase_ready() -> bool:
    """Sealed dual-gate. Env flag alone is NEVER enough (Precisione A)."""
    flag = (os.environ.get("OMNIA_H4_PURCHASE_READY") or "").strip().lower() == "true"
    if not flag:
        return False
    return _marker_is_sealed(h4_ready_marker_path())


def guard_h4_purchase_or_raise() -> None:
    """Block credits/storage purchase until sealed ready.

    Precisione B: even after sealed ready, Super Admin purchase authority is
    NOT granted here; C5 will authorize only nominated Main Admin. C1 blocks all.
    """
    if is_h4_purchase_ready():
        # C1 never ships the marker; if somehow present in later cycles, still
        # require C5 MA path — this guard only opens the "not h4_not_ready" door.
        return
    raise HTTPException(
        status_code=503,
        detail={
            "error": "h4_not_ready",
            "code": "h4_not_ready",
            "message": (
                "Acquisto crediti/storage bloccato finché H4 non è certificato "
                "(C5+C6). Impostare OMNIA_H4_PURCHASE_READY=true non basta: "
                "serve il marker sealed post-verifica."
            ),
        },
    )


def purchase_super_admin_denied_by_policy() -> bool:
    """Precisione B — SA non acquista per conto CC (no autorità implicita)."""
    return True


def dogfood_preflight_checks() -> dict[str, Any]:
    """Single preflight aggregate — fail if any critical check fails."""
    if not is_dogfood_env():
        return {
            "ok": True,
            "skipped": True,
            "reason": "OMNIA_ENV_not_dogfood",
            "checks": {},
        }
    checks = {
        "db": check_dogfood_db_isolation(),
        "hosts": check_dogfood_host_allowlists(),
        "stripe": check_dogfood_stripe_test_only(),
        "h4_sealed_gate": {
            "ok": True,  # informational: gate present
            "purchase_ready": is_h4_purchase_ready(),
            "env_flag": (os.environ.get("OMNIA_H4_PURCHASE_READY") or "").strip().lower()
            == "true",
            "marker_path": str(h4_ready_marker_path()),
            "marker_sealed": _marker_is_sealed(h4_ready_marker_path()),
            "note": "env_flag_alone_insufficient",
        },
    }
    failures = []
    for name, c in checks.items():
        if name == "h4_sealed_gate":
            continue
        if not c.get("ok"):
            failures.append({"check": name, "errors": c.get("errors") or []})
    return {
        "ok": not failures,
        "skipped": False,
        "failures": failures,
        "checks": checks,
    }


def assert_dogfood_boot_or_raise() -> None:
    """Call at API boot when OMNIA_ENV=dogfood — refuse start if isolation broken."""
    if not is_dogfood_env():
        return
    report = dogfood_preflight_checks()
    if report.get("ok"):
        logger.info("dogfood perimeter OK db=%s", _db_name())
        return
    logger.error("dogfood perimeter FAIL: %s", report.get("failures"))
    raise RuntimeError(
        "dogfood_perimeter_failed:"
        + ",".join(
            e
            for f in report.get("failures") or []
            for e in (f.get("errors") or [f.get("check")])
        )
    )


def apply_dogfood_provider_holds() -> list[str]:
    """N3 — HOLD paid providers + kill Resend in dogfood (in-memory circuit)."""
    if not is_dogfood_env():
        return []
    from shared.security import circuit as circuit_mod

    # Resend killed; paid providers held. Stripe test stays usable for later cycles
    # but C1 does not mutate Stripe / run purchases.
    held = ["resend", "fal", "gemini", "llm", "openai", "tavily", "openapi"]
    for pid in held:
        circuit_mod.force_hold(pid)
    logger.warning("dogfood provider HOLD applied: %s", ",".join(held))
    return held
