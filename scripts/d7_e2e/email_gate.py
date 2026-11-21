"""Fail-closed email no-send gate for T4 invite (harness-only; no product changes).

Observable signals only (never print secrets):

1. Health ``message.circuits.resend.held`` → ``killed`` (NOT ``open`` — D5)
2. Absence of ``RESEND_API_KEY`` in observed process/api vars → ``mock``
3. ``OMNIA_ENV=dogfood`` with empty ``OMNIA_EMAIL_ALLOWLIST`` → ``blocked``

Gate PASS is a *precondition* only. CLEAN email still requires T21 L3+L4 proof.
HTTP invite response is NOT used as proof of no-send.
"""
from __future__ import annotations

import os
from typing import Any, Optional

from . import config
from .classify import blocked, expect_predicate
from .http_client import StagingClient
from .mongo_util import fetch_api_service_variables


ALLOWED_NO_SEND_MODES = frozenset({"mock", "blocked", "killed"})


def _key_present(vars_map: dict, name: str) -> bool:
    val = vars_map.get(name)
    return bool(val) and str(val).strip() != ""


def assess_email_no_send(
    *,
    api_vars: Optional[dict] = None,
    health_body: Any = None,
) -> dict[str, Any]:
    """Pure assessment. Never includes secret values in the returned dict.

    ``circuit_open`` alone must NOT yield mode=killed (recovery half-open).
    Only ``held`` counts as durable kill for gate PASS.
    """
    api_vars = dict(api_vars or {})
    reasons: list[str] = []
    mode: Optional[str] = None

    circuits = {}
    if isinstance(health_body, dict):
        msg = health_body.get("message")
        if isinstance(msg, dict):
            circuits = msg.get("circuits") or {}
        circuits = circuits or health_body.get("circuits") or {}
    resend_circuit = circuits.get("resend") if isinstance(circuits, dict) else None
    held = False
    open_only = False
    if isinstance(resend_circuit, dict):
        held = bool(resend_circuit.get("held"))
        open_only = bool(resend_circuit.get("open")) and not held
    if held:
        mode = "killed"
        reasons.append("health_circuits_resend_held")
    elif open_only:
        reasons.append("health_circuits_resend_open_not_durable")

    has_resend_key = _key_present(api_vars, "RESEND_API_KEY")
    omnia_env = str(api_vars.get("OMNIA_ENV") or "").strip().lower()
    raw_allow = str(api_vars.get("OMNIA_EMAIL_ALLOWLIST") or "").strip()
    allow_empty = raw_allow == ""

    if mode is None and not has_resend_key:
        mode = "mock"
        reasons.append("resend_api_key_absent")

    if mode is None and omnia_env == "dogfood" and allow_empty:
        mode = "blocked"
        reasons.append("dogfood_empty_allowlist")

    if mode is None and omnia_env == "dogfood" and not allow_empty:
        reasons.append("dogfood_allowlist_nonempty_may_send")

    if mode is None and has_resend_key:
        reasons.append("resend_api_key_present_outbound_possible")

    signals = {
        "resend_key_present": has_resend_key,
        "omnia_env": omnia_env or None,
        "allowlist_empty": allow_empty,
        "resend_circuit_held": held,
        "resend_circuit_open": open_only or (
            isinstance(resend_circuit, dict) and bool(resend_circuit.get("open"))
        ),
        # legacy alias — true only when held (not open-only)
        "resend_circuit_held_or_open": held,
    }

    if mode is None:
        return {
            "ok": False,
            "mode": None,
            "classification": "BLOCKED",
            "reasons": reasons or ["no_send_not_demonstrable"],
            "signals": signals,
        }

    return {
        "ok": True,
        "mode": mode,
        "classification": "PASS",
        "reasons": reasons,
        "signals": signals,
    }


def run_email_gate(
    *,
    client: Optional[StagingClient] = None,
    api_vars: Optional[dict] = None,
    skip_network: bool = False,
) -> dict[str, Any]:
    """Execute gate. With skip_network=True, only ``api_vars``/injected health used.

    When network is enabled (Package C runtime), fetches Railway API vars and
    health. Never mutates; never prints secrets.
    """
    steps = []
    health_body = None
    vars_injected = api_vars is not None
    vars_map = dict(api_vars or {})

    if not skip_network:
        tok = os.environ.get("RAILWAY_API_TOKEN") or os.environ.get("RAILWAY_TOKEN")
        # Fetch Railway only when caller did not inject api_vars (None).
        # Empty dict {} means "explicitly no vars" — do not hit remote.
        if not tok and not vars_injected:
            step = blocked(
                "T4.email_gate_vars",
                "missing_RAILWAY_API_TOKEN_and_no_injected_vars",
            )
            return {
                "classification": "BLOCKED",
                "steps": [step],
                "assessment": assess_email_no_send(api_vars={}, health_body=None),
            }
        if tok and not vars_injected:
            try:
                vars_map = fetch_api_service_variables(tok)
            except Exception as e:
                step = blocked(
                    "T4.email_gate_vars",
                    "railway_vars_fetch_failed",
                    detail=str(e)[:200],
                )
                return {
                    "classification": "BLOCKED",
                    "steps": [step],
                    "assessment": None,
                }
        # Health probe only when we intend network mode with a client
        c = client or StagingClient(api_base=config.STAGING_API_URL, origin=config.STAGING_FE_URL)
        try:
            st, health_body = c.health()
            steps.append(
                expect_predicate(
                    "T4.email_gate_health",
                    st == 200,
                    status=st,
                    reason="health_not_200",
                )
            )
        except Exception as e:
            steps.append(
                blocked("T4.email_gate_health", "health_fetch_failed", detail=str(e)[:200])
            )
            return {
                "classification": "BLOCKED",
                "steps": steps,
                "assessment": None,
            }

    assessment = assess_email_no_send(api_vars=vars_map, health_body=health_body)
    steps.append(
        expect_predicate(
            "T4.email_gate_no_send",
            bool(assessment.get("ok"))
            and assessment.get("mode") in ALLOWED_NO_SEND_MODES,
            reason="email_no_send_not_demonstrable",
            detail={
                "mode": assessment.get("mode"),
                "reasons": assessment.get("reasons"),
                "signals": assessment.get("signals"),
            },
        )
        if assessment.get("ok")
        else blocked(
            "T4.email_gate_no_send",
            "email_no_send_not_demonstrable",
            detail={
                "mode": assessment.get("mode"),
                "reasons": assessment.get("reasons"),
                "signals": assessment.get("signals"),
            },
        )
    )

    from .classify import aggregate

    return {
        "classification": aggregate(steps),
        "steps": steps,
        "assessment": assessment,
    }
