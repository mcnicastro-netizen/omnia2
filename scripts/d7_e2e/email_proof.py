"""Local T21 no-send proof: L3 status + L4 transport spy (no remote I/O).

L5 (staging/provider dashboard) is intentionally NOT implemented here.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def prove_no_send_local(
    *,
    run_path: Optional[Path] = None,
    template: str = "agency_invite",
    to: str = "d7r2.t21.probe@example.com",
) -> dict[str, Any]:
    """Call real ``send_email`` under hold; assert transport never invoked.

    Covers the single transactional path ``shared.email.client.send_email`` →
    ``resend.Emails.send``. Re-run inventory (T19) if new providers appear.
    """
    # Ensure backend is importable
    import sys
    from pathlib import Path as P

    repo = P(__file__).resolve().parents[2]
    backend = repo / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))

    from shared.security import circuit as circuit_mod
    import shared.email.client as email_client

    transport = MagicMock(name="resend.Emails.send")
    transport.side_effect = RuntimeError("transport_must_not_be_called")

    # Snapshot / restore circuit state for resend
    was_held = circuit_mod.is_held("resend")
    evidence_paths: list[dict[str, Any]] = []

    def _one_attempt(label: str) -> dict[str, Any]:
        transport.reset_mock()
        circuit_mod.force_hold("resend", "d7_t21_no_send_proof")

        async def _run():
            return await email_client.send_email(
                to=to,
                template=template,
                lang="it",
                variables={
                    "agency_name": "D7T21",
                    "inviter_name": "Harness",
                    "role_label": "agent",
                    "accept_url": "https://example.com/accept",
                    "expires_days": 7,
                },
            )

        # Patch transport at the symbol send_email will call
        original = getattr(email_client.resend.Emails, "send", None)
        email_client.resend.Emails.send = transport  # type: ignore[assignment]
        try:
            out = asyncio.run(_run())
        finally:
            if original is not None:
                email_client.resend.Emails.send = original  # type: ignore[assignment]

        status = out.get("status") if isinstance(out, dict) else None
        calls = transport.call_count
        row = {
            "label": label,
            "path": "shared.email.client.send_email",
            "provider_transport": "resend.Emails.send",
            "template": template,
            "status": status,
            "transport_calls": calls,
            "held": circuit_mod.is_held("resend"),
            "ts": _now(),
            "ok": status in ("killed", "blocked") and calls == 0,
        }
        evidence_paths.append(row)
        return row

    try:
        # Attempt 1 — held
        a1 = _one_attempt("held_baseline")

        # Attempt 2 — simulate circuit open+recovery while hold persists
        st = circuit_mod._state("resend")  # noqa: SLF001 — test harness
        st.failures = 5
        st.opened_at = 0.0  # force "open" window elapsed → half-open allowed by circuit_open
        # held must still short-circuit send_email before transport
        a2 = _one_attempt("after_circuit_recovery_window")
        a2["circuit_open_at_probe"] = circuit_mod.circuit_open("resend")

        ok = a1["ok"] and a2["ok"]
        evidence = {
            "level": "L3+L4",
            "l5": "pending_staging_not_executed",
            "ok": ok,
            "attempts": evidence_paths,
            "note": (
                "Transport spy proves resend.Emails.send call_count==0 while "
                "send_email returns killed under force_hold. L5 not claimed."
            ),
            "written_at": _now(),
        }
    finally:
        if not was_held:
            circuit_mod.clear_hold("resend")

    if run_path is not None:
        p = Path(run_path) / "email_send_evidence.json"
        p.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        evidence["path"] = str(p)
    return evidence


def inventory_email_send_paths() -> list[dict[str, str]]:
    """T19 static inventory — single transactional client in this repo."""
    return [
        {
            "module": "backend/shared/email/client.py",
            "function": "send_email",
            "transport": "resend.Emails.send",
            "invite_caller": "backend/apps/immoweb/invites.py:create_invite",
        }
    ]
