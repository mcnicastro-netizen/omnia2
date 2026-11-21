"""T4 — Main Admin / branch deny / invite accept / membership / no real email."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .artifacts import write_json
from .classify import aggregate, blocked, expect_predicate, expect_status
from .email_gate import run_email_gate
from .http_client import StagingClient
from .inventory import CreatedInventory
from .mongo_util import connect_staging_db, scoped_filter


def run_t4(run_id: str, run_path: Path, seed_meta: dict, password: str) -> dict[str, Any]:
    I = seed_meta["ids"]
    steps: list[dict] = []
    inv = CreatedInventory(run_path, run_id)
    db = connect_staging_db()
    email_send_evidence: dict[str, Any] | None = None
    invite_email = seed_meta["emails"]["invitee"]

    # Seed already created CC/org; confirm binding
    cc = db.commercial_customers.find_one({"id": I["cc"], **scoped_filter(run_id)})
    steps.append(
        expect_predicate(
            "T4.seed_cc",
            bool(cc) and cc.get("main_admin_user_id") == I["user_a"],
            detail={"cc_id": I["cc"], "main_admin": (cc or {}).get("main_admin_user_id")},
            reason="cc_or_main_admin_missing",
        )
    )

    a = StagingClient()
    st, _ = a.login(seed_meta["emails"]["admin_a"], password)
    steps.append(expect_status("T4.login_ma", st, {200}))

    st, ma = a.request("GET", "/api/billing/commercial/main-admin")
    r = expect_status("T4.get_main_admin", st, {200}, body=ma)
    steps.append(r)
    ma_ok = (
        isinstance(ma, dict)
        and ma.get("main_admin_user_id") == I["user_a"]
        and ma.get("commercial_customer_id") == I["cc"]
    )
    steps.append(
        expect_predicate(
            "T4.get_main_admin_binding",
            ma_ok,
            status=st,
            detail=ma if isinstance(ma, dict) else None,
            reason="main_admin_binding_mismatch",
        )
    )

    # Branch admin — same CC, not Main Admin → 403 forbidden
    b = StagingClient()
    st, _ = b.login(seed_meta["emails"]["admin_b"], password)
    steps.append(expect_status("T4.branch_login", st, {200}))
    st, me = b.request("GET", "/api/auth/me")
    steps.append(expect_status("T4.branch_me", st, {200}, body=me))
    steps.append(
        expect_predicate(
            "T4.branch_me_agency",
            isinstance(me, dict) and me.get("active_agency_id") == I["ag_b"],
            status=st,
            detail=me if isinstance(me, dict) else None,
            reason="branch_wrong_agency",
        )
    )
    st, denied = b.request("GET", "/api/billing/commercial/main-admin")
    steps.append(expect_status("T4.branch_denied_ma", st, {403}, body=denied))
    steps.append(
        expect_predicate(
            "T4.branch_denied_detail",
            _detail_error(denied) == "forbidden",
            status=st,
            detail=denied if isinstance(denied, dict) else None,
            reason="branch_deny_not_forbidden",
        )
    )

    # D5 — email gate BEFORE create invite (fail-closed; held-only, not open)
    gate = run_email_gate(client=a)
    steps.extend(gate["steps"])
    if gate["classification"] != "PASS":
        steps.append(blocked("T4.create_invite", "email_gate_blocked_before_invite"))
        steps.append(blocked("T4.accept", "email_gate_blocked_before_invite"))
        steps.append(blocked("T4.membership", "email_gate_blocked_before_invite"))
        return _finish(run_path, steps, email_send_evidence, invite_email, inv, gate)

    # D3 — invitee must not pre-exist (synthetic run-scoped email)
    preexisting = db.users.find_one({"email": invite_email}, {"_id": 0, "id": 1, "email": 1})
    if preexisting:
        steps.append(
            blocked(
                "T4.preexisting_invitee",
                "invitee_email_already_exists",
                detail={"user_id": preexisting.get("id")},
            )
        )
        steps.append(blocked("T4.create_invite", "preexisting_invitee_blocked"))
        steps.append(blocked("T4.accept", "preexisting_invitee_blocked"))
        return _finish(run_path, steps, email_send_evidence, invite_email, inv, gate)
    steps.append(expect_predicate("T4.preexisting_invitee", True, detail={"absent": True}))

    intent_inv = inv.open_intent(
        step="T4.create_invite",
        collection="agency_invites",
        correlation={"email": invite_email, "agency_id": I["ag_active"]},
    )
    st, inv_resp = a.request(
        "POST",
        "/api/app/agencies/me/invites",
        {"email": invite_email, "role": "agent", "name_hint": "D7R2 Invitee"},
    )
    r = expect_status("T4.create_invite", st, {200, 201}, body=inv_resp)
    steps.append(r)
    invite_id = inv_resp.get("id") if isinstance(inv_resp, dict) else None
    if invite_id:
        inv.confirm_intent(intent_inv, invite_id, http_status=st, source="T4.create_invite")
        db.agency_invites.update_one(
            {"id": invite_id},
            {"$set": {**scoped_filter(run_id)}},
        )
    else:
        if st in (200, 201):
            inv.mark_orphan_suspected(intent_inv, http_status=st)
        else:
            inv.fail_intent(intent_inv, http_status=st, reason="create_invite_failed")

    # Token recovery: only by run-scoped tag or exact invite_id — NEVER bare email retag (D3)
    doc = None
    if invite_id:
        doc = db.agency_invites.find_one({"id": invite_id}, {"_id": 0})
    if not doc:
        doc = db.agency_invites.find_one(
            {"email": invite_email, **scoped_filter(run_id)},
            {"_id": 0},
        )
    has_token = bool(doc and doc.get("token"))
    if not doc:
        steps.append(blocked("T4.invite_db", "invite_document_missing"))
        steps.append(blocked("T4.accept", "no_invite_token"))
        steps.append(blocked("T4.membership", "no_invite_token"))
    elif not has_token:
        steps.append(blocked("T4.invite_db", "invite_token_absent"))
        steps.append(blocked("T4.accept", "no_invite_token"))
        steps.append(blocked("T4.membership", "no_invite_token"))
    else:
        steps.append(
            expect_predicate(
                "T4.invite_db",
                True,
                detail={
                    "present": True,
                    "status": doc.get("status"),
                    "has_token": True,
                    "agency_id": doc.get("agency_id"),
                },
            )
        )
        # Re-check preexistence immediately before accept (TOCTOU guard)
        if db.users.find_one({"email": invite_email}, {"_id": 1}):
            steps.append(blocked("T4.accept", "invitee_appeared_before_accept"))
            return _finish(run_path, steps, email_send_evidence, invite_email, inv, gate)

        invitee_password = "D7R2-Inv-" + secrets.token_urlsafe(10)
        x = StagingClient()
        x.health()
        st, acc = x.request(
            "POST",
            "/api/app/invites/accept",
            {
                "token": doc["token"],
                "name": "D7R2 Invitee",
                "password": invitee_password,
            },
        )
        steps.append(expect_status("T4.accept", st, {200, 201}, body=acc))
        user = db.users.find_one(
            {"email": invite_email},
            {"_id": 0, "id": 1, "agency_ids": 1, "role": 1, "email": 1, "active_agency_id": 1},
        )
        if user:
            db.users.update_one(
                {"id": user["id"]},
                {"$set": {**scoped_filter(run_id)}},
            )
            if user.get("id"):
                inv.register(
                    "users",
                    user["id"],
                    source="T4.accept",
                    created_by_run=True,
                )
            # D2 — memberships created by accept (exact attribution only)
            mem_ids: list[str] = []
            for m in db.memberships.find(
                {
                    "user_id": user["id"],
                    "organization_id": I["ag_active"],
                },
                {"_id": 0, "id": 1, "membership_status": 1},
            ):
                if m.get("id"):
                    mem_ids.append(m["id"])
                    inv.register("memberships", m["id"], source="T4.accept_membership")
            if not mem_ids:
                # Side-effect expected but not inventoriable → block CLEAN
                inv._append_uncertain(
                    {
                        "intent_id": None,
                        "collection": "memberships",
                        "candidate_ids": [],
                        "correlation": {
                            "user_id": user["id"],
                            "organization_id": I["ag_active"],
                        },
                        "reason": "membership_not_found_after_accept",
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }
                )
            # D2 — notifications: invite_id OR accepted_user_id (product meta)
            seen_n: set[str] = set()
            notif_queries = [
                {"type": "invite_accepted", "meta.invite_id": doc.get("id")},
                {"type": "invite_accepted", "meta.accepted_user_id": user["id"]},
            ]
            for q in notif_queries:
                for n in db.notifications.find(q, {"_id": 0, "id": 1}):
                    nid = n.get("id")
                    if nid and nid not in seen_n:
                        seen_n.add(nid)
                        inv.register(
                            "notifications", nid, source="T4.accept_notification"
                        )
        member_ok = bool(user and I["ag_active"] in (user.get("agency_ids") or []))
        steps.append(
            expect_predicate(
                "T4.membership",
                member_ok,
                detail=user,
                reason="invitee_not_on_agency",
            )
        )
        steps.append(
            expect_predicate(
                "T4.membership_role",
                bool(user) and user.get("role") == "agent",
                detail={"role": (user or {}).get("role")},
                reason="invitee_role_not_agent",
            )
        )

    # FIX4 — ACTIVE independent tenant iso against CC under test
    iso = StagingClient()
    st, _ = iso.login(seed_meta["emails"]["admin_iso"], password)
    steps.append(expect_status("T4.iso_active_login", st, {200}))
    st, iso_me = iso.request("GET", "/api/auth/me")
    steps.append(expect_status("T4.iso_active_me", st, {200}, body=iso_me))
    steps.append(
        expect_predicate(
            "T4.iso_active_agency",
            isinstance(iso_me, dict)
            and iso_me.get("active_agency_id") == I["ag_iso"]
            and iso_me.get("is_active") is not False,
            status=st,
            detail=iso_me if isinstance(iso_me, dict) else None,
            reason="iso_not_active_independent",
        )
    )
    st, denied2 = iso.request(
        "GET",
        f"/api/billing/commercial/main-admin?commercial_customer_id={I['cc']}",
    )
    steps.append(expect_status("T4.iso_active_denied", st, {403}, body=denied2))
    steps.append(
        expect_predicate(
            "T4.iso_active_denied_detail",
            _detail_error(denied2) == "forbidden",
            status=st,
            detail=denied2 if isinstance(denied2, dict) else None,
            reason="iso_deny_not_forbidden_detail",
        )
    )

    return _finish(run_path, steps, email_send_evidence, invite_email, inv, gate)


def _detail_error(body: Any) -> str | None:
    if not isinstance(body, dict):
        return None
    d = body.get("detail")
    if isinstance(d, dict):
        return d.get("error")
    if isinstance(d, str):
        return d
    return body.get("error")


def _finish(
    run_path: Path,
    steps: list[dict],
    email_send_evidence: dict | None,
    invite_email: str,
    inv: CreatedInventory,
    gate: dict | None,
) -> dict[str, Any]:
    out = {
        "classification": aggregate(steps),
        "steps": steps,
        # D6 — never a constant False; null until T21 evidence attached
        "email_send_evidence": email_send_evidence,
        "email_gate": (gate or {}).get("assessment"),
        "invite_email": invite_email,
        "inventory": inv.as_dict(),
        "harness": "scripts/d7_e2e",
        "forensic_note": (
            "Historical A6 used invitee3 + inline harness; this harness is the SoT going forward."
        ),
        "note": (
            "PASS requires every T4.* PASS; email gate must prove mock|blocked|held "
            "before invite; CLEAN email requires separate T21 L3+L4 evidence; "
            "iso uses ACTIVE third tenant + 403 forbidden on target CC"
        ),
    }
    write_json(run_path / "t4_api.json", out)
    write_json(
        run_path / "t4_classification.json",
        {
            "classification": out["classification"],
            "step_results": [s["result"] for s in steps],
            "email_gate_mode": ((gate or {}).get("assessment") or {}).get("mode"),
        },
    )
    return out
