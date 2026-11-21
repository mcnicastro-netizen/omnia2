"""T4 — Main Admin / branch deny / invite accept / membership / no real email."""
from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any

from .artifacts import write_json
from .classify import aggregate, blocked, expect_predicate, expect_status
from .http_client import StagingClient
from .mongo_util import connect_staging_db, scoped_filter


def run_t4(run_id: str, run_path: Path, seed_meta: dict, password: str) -> dict[str, Any]:
    I = seed_meta["ids"]
    steps: list[dict] = []
    db = connect_staging_db()

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

    # Branch admin
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
    steps.append(expect_status("T4.branch_denied_ma", st, {401, 403}, body=denied))

    # Invite
    invite_email = seed_meta["emails"]["invitee"]
    st, inv = a.request(
        "POST",
        "/api/app/agencies/me/invites",
        {"email": invite_email, "role": "agent", "name_hint": "D7R2 Invitee"},
    )
    r = expect_status("T4.create_invite", st, {200, 201}, body=inv)
    steps.append(r)
    # Detect real email send signals in response (without logging secrets)
    email_sent = False
    if isinstance(inv, dict):
        for k, v in inv.items():
            if "email" in k.lower() and v in (True, "sent", "delivered", "ok"):
                email_sent = True
    steps.append(
        expect_predicate(
            "T4.no_real_email_response",
            not email_sent,
            detail={"email_real_send_detected": email_sent},
            reason="email_send_signal_in_api_response",
        )
    )

    # Controlled token recovery from staging DB only
    doc = db.agency_invites.find_one(
        {"email": invite_email, **scoped_filter(run_id)},
        {"_id": 0},
    )
    # Some APIs may not stamp d7_run_id on invite — also allow agency_id match for this run
    if not doc:
        doc = db.agency_invites.find_one(
            {"email": invite_email, "agency_id": I["ag_active"]},
            {"_id": 0},
        )
        # Tag invite for scoped cleanup if found
        if doc and doc.get("id"):
            db.agency_invites.update_one(
                {"id": doc["id"]},
                {"$set": {**scoped_filter(run_id)}},
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
            {"_id": 0, "agency_ids": 1, "role": 1, "email": 1, "active_agency_id": 1},
        )
        # Tag invitee for cleanup
        if user:
            db.users.update_one(
                {"email": invite_email},
                {"$set": {**scoped_filter(run_id)}},
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

    # Non-member / inactive agency user
    c = StagingClient()
    st, _ = c.login(seed_meta["emails"]["admin_inactive"], password)
    steps.append(expect_status("T4.iso_non_member_login", st, {200}))
    st, denied2 = c.request("GET", "/api/billing/commercial/main-admin")
    steps.append(
        expect_status("T4.iso_non_member", st, {400, 401, 403, 404}, body=denied2)
    )

    out = {
        "classification": aggregate(steps),
        "steps": steps,
        "email_real_send_detected": email_sent,
        "invite_email": invite_email,
        "harness": "scripts/d7_e2e",
        "forensic_note": (
            "Historical A6 used invitee3 + inline harness; this harness is the SoT going forward."
        ),
        "note": "PASS requires every T4.* PASS; BLOCKED if invite token unavailable without external email",
    }
    write_json(run_path / "t4_api.json", out)
    write_json(
        run_path / "t4_classification.json",
        {
            "classification": out["classification"],
            "step_results": [s["result"] for s in steps],
            "email_real_send_detected": email_sent,
        },
    )
    return out
