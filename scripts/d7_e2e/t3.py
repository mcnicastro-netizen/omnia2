"""T3 — Deal / chat / mini-dossier with explicit per-step PASS/FAIL (5xx → FAIL)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import write_json
from .classify import aggregate, expect_predicate, expect_status
from .http_client import StagingClient


def run_t3(run_id: str, run_path: Path, seed_meta: dict, password: str) -> dict[str, Any]:
    I = seed_meta["ids"]
    steps: list[dict] = []

    # --- B requests collab ---
    b = StagingClient()
    st, _ = b.login(seed_meta["emails"]["admin_b"], password)
    steps.append(expect_status("T3.login_b", st, {200}))

    st, collab = b.request(
        "POST",
        "/api/app/collaborations",
        {
            "property_id": I["prop"],
            "partner_agency_id": I["ag_b"],
            "message": f"D7R2 collab {run_id}",
        },
    )
    r = expect_status("T3.create_collab", st, {200, 201}, body=collab)
    steps.append(r)
    cid = collab.get("id") if isinstance(collab, dict) else None
    if r["result"] != "PASS" or not cid:
        steps.append(
            expect_predicate("T3.create_collab_id", False, reason="missing_collaboration_id")
        )
        return _finish(run_path, steps, {"collaboration_id": cid})

    # --- A accepts ---
    a = StagingClient()
    st, _ = a.login(seed_meta["emails"]["admin_a"], password)
    steps.append(expect_status("T3.login_a", st, {200}))
    st, resp = a.request(
        "POST", f"/api/app/collaborations/{cid}/respond", {"action": "accept"}
    )
    r = expect_status("T3.accept_collab", st, {200}, body=resp)
    steps.append(r)
    active_ok = isinstance(resp, dict) and resp.get("status") == "active"
    steps.append(
        expect_predicate(
            "T3.accept_collab_status_active",
            active_ok,
            status=st,
            detail=resp if isinstance(resp, dict) else None,
            reason="collaboration_not_active",
        )
    )

    # --- Visit create + complete (mandatory for PASS) ---
    st, visit = b.request(
        "POST",
        "/api/app/visits",
        {
            "collaboration_id": cid,
            "proposed_slots": ["2026-12-15T10:00:00+00:00"],
            "notes": f"D7R2 visit {run_id}",
        },
    )
    r = expect_status("T3.create_visit", st, {200, 201}, body=visit)
    steps.append(r)
    vid = visit.get("id") if isinstance(visit, dict) else None
    steps.append(
        expect_predicate("T3.create_visit_id", bool(vid), reason="missing_visit_id")
    )
    if vid:
        st, visit2 = a.request(
            "PATCH",
            f"/api/app/visits/{vid}",
            {"status": "completed", "agreed_slot": "2026-12-15T10:00:00+00:00"},
        )
        r = expect_status("T3.complete_visit", st, {200}, body=visit2)
        steps.append(r)
        completed = isinstance(visit2, dict) and visit2.get("status") == "completed"
        steps.append(
            expect_predicate(
                "T3.complete_visit_status",
                completed,
                status=st,
                detail=visit2 if isinstance(visit2, dict) else None,
                reason="visit_not_completed",
            )
        )
        st, fb = b.request(
            "POST",
            "/api/app/visit-feedback",
            {
                "visit_id": vid,
                "rating": 5,
                "feedback_text": f"D7R2 mini-dossier {run_id}",
            },
        )
        r = expect_status("T3.mini_dossier", st, {200, 201}, body=fb)
        steps.append(r)
        steps.append(
            expect_predicate(
                "T3.mini_dossier_id",
                isinstance(fb, dict) and bool(fb.get("id")),
                reason="missing_feedback_id",
            )
        )
    else:
        for s in (
            "T3.complete_visit",
            "T3.complete_visit_status",
            "T3.mini_dossier",
            "T3.mini_dossier_id",
        ):
            steps.append({"step": s, "result": "FAIL", "reason": "skipped_missing_visit"})

    # --- Deal ---
    st, deal = a.request(
        "POST",
        "/api/app/deals",
        {
            "property_id": I["prop"],
            "client_id": I["client"],
            "collaboration_id": cid,
            "notes": f"D7R2 deal {run_id}",
        },
    )
    r = expect_status("T3.open_deal", st, {200, 201}, body=deal)
    steps.append(r)
    did = deal.get("id") if isinstance(deal, dict) else None
    steps.append(expect_predicate("T3.open_deal_id", bool(did), reason="missing_deal_id"))

    # --- Chat ---
    payload = {"collaboration_id": cid}
    if did:
        payload["deal_id"] = did
    st, thread = a.request("POST", "/api/app/collab-chat/threads", payload)
    r = expect_status("T3.open_chat", st, {200, 201}, body=thread)
    steps.append(r)
    tid = thread.get("id") if isinstance(thread, dict) else None
    steps.append(expect_predicate("T3.open_chat_id", bool(tid), reason="missing_thread_id"))

    if tid:
        st, msg = a.request(
            "POST",
            f"/api/app/collab-chat/threads/{tid}/messages",
            {"body": f"D7R2 chat {run_id} — no external send"},
        )
        steps.append(expect_status("T3.post_chat", st, {200, 201}, body=msg))

        st, msgs = b.request("GET", f"/api/app/collab-chat/threads/{tid}/messages")
        steps.append(expect_status("T3.list_chat_b", st, {200}, body=msgs))
        items = msgs.get("items") if isinstance(msgs, dict) else None
        if items is None and isinstance(msgs, list):
            items = msgs
        count = len(items) if isinstance(items, list) else 0
        steps.append(
            expect_predicate(
                "T3.list_chat_b_count",
                count >= 1,
                status=st,
                detail={"count": count},
                reason="chat_empty_for_partner_b",
            )
        )

        # Isolation — other tenant must be denied; 5xx or 200 → FAIL
        x = StagingClient()
        st, _ = x.login(seed_meta["emails"]["admin_inactive"], password)
        steps.append(expect_status("T3.iso_login_other", st, {200}))
        st, denied = x.request("GET", f"/api/app/collab-chat/threads/{tid}/messages")
        steps.append(expect_status("T3.iso_other", st, {401, 403}, body=denied))
    else:
        for s in (
            "T3.post_chat",
            "T3.list_chat_b",
            "T3.list_chat_b_count",
            "T3.iso_login_other",
            "T3.iso_other",
        ):
            steps.append({"step": s, "result": "FAIL", "reason": "skipped_missing_thread"})

    # --- Revoke + proposal after revoke ---
    if did and cid:
        st, rev = a.request(
            "POST", f"/api/app/collaborations/{cid}/respond", {"action": "revoke"}
        )
        r = expect_status("T3.revoke", st, {200}, body=rev)
        steps.append(r)
        revoked = isinstance(rev, dict) and rev.get("status") in ("revoked", "inactive")
        # accept either explicit revoked or documented equivalent
        if isinstance(rev, dict) and rev.get("status") == "revoked":
            revoked = True
        steps.append(
            expect_predicate(
                "T3.revoke_status",
                isinstance(rev, dict) and rev.get("status") == "revoked",
                status=st,
                detail=rev if isinstance(rev, dict) else None,
                reason="collaboration_not_revoked",
            )
        )
        st, prop = a.request(
            "POST",
            f"/api/app/deals/{did}/proposals",
            {"amount": 240000, "notes": f"after revoke {run_id}"},
        )
        # Expect client error, never 2xx/5xx
        steps.append(expect_status("T3.proposal_after_revoke", st, {400, 403, 409}, body=prop))
    else:
        steps.append({"step": "T3.revoke", "result": "FAIL", "reason": "skipped_missing_deal_or_collab"})
        steps.append(
            {
                "step": "T3.revoke_status",
                "result": "FAIL",
                "reason": "skipped_missing_deal_or_collab",
            }
        )
        steps.append(
            {
                "step": "T3.proposal_after_revoke",
                "result": "FAIL",
                "reason": "skipped_missing_deal_or_collab",
            }
        )

    return _finish(run_path, steps, {"collaboration_id": cid, "deal_id": did, "thread_id": tid})


def _finish(run_path: Path, steps: list[dict], ids_out: dict) -> dict[str, Any]:
    out = {
        "classification": aggregate(steps),
        "steps": steps,
        "ids": ids_out,
        "harness": "scripts/d7_e2e",
        "note": "PASS requires every T3.* step PASS; 5xx always FAIL",
    }
    write_json(run_path / "t3_api.json", out)
    write_json(
        run_path / "t3_classification.json",
        {"classification": out["classification"], "step_results": [s["result"] for s in steps]},
    )
    return out
