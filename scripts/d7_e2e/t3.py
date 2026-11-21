"""T3 — Deal / chat / mini-dossier with explicit per-step PASS/FAIL (5xx → FAIL)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import write_json
from .classify import aggregate, expect_predicate, expect_status
from .http_client import StagingClient
from .inventory import CreatedInventory


def run_t3(run_id: str, run_path: Path, seed_meta: dict, password: str) -> dict[str, Any]:
    I = seed_meta["ids"]
    steps: list[dict] = []
    inv = CreatedInventory(run_path, run_id)
    cid = did = tid = vid = None

    # --- B requests collab ---
    b = StagingClient()
    st, _ = b.login(seed_meta["emails"]["admin_b"], password)
    steps.append(expect_status("T3.login_b", st, {200}))

    collab_msg = f"D7R2 collab {run_id}"
    intent_collab = inv.open_intent(
        step="T3.create_collab",
        collection="mls_collaborations",
        correlation={
            "message": collab_msg,
            "property_id": I["prop"],
            "partner_agency_id": I["ag_b"],
        },
    )
    st, collab = b.request(
        "POST",
        "/api/app/collaborations",
        {
            "property_id": I["prop"],
            "partner_agency_id": I["ag_b"],
            "message": collab_msg,
        },
    )
    r = expect_status("T3.create_collab", st, {200, 201}, body=collab)
    steps.append(r)
    cid = collab.get("id") if isinstance(collab, dict) else None
    if cid:
        inv.confirm_intent(intent_collab, cid, http_status=st, source="T3.create_collab")
    else:
        if st in (200, 201):
            inv.mark_orphan_suspected(intent_collab, http_status=st)
        else:
            inv.fail_intent(intent_collab, http_status=st, reason="create_collab_failed")
    if r["result"] != "PASS" or not cid:
        steps.append(
            expect_predicate("T3.create_collab_id", False, reason="missing_collaboration_id")
        )
        return _finish(run_path, steps, {"collaboration_id": cid}, inv)

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
    visit_notes = f"D7R2 visit {run_id}"
    intent_visit = inv.open_intent(
        step="T3.create_visit",
        collection="mls_visits",
        correlation={"collaboration_id": cid, "notes": visit_notes},
    )
    st, visit = b.request(
        "POST",
        "/api/app/visits",
        {
            "collaboration_id": cid,
            "proposed_slots": ["2026-12-15T10:00:00+00:00"],
            "notes": visit_notes,
        },
    )
    r = expect_status("T3.create_visit", st, {200, 201}, body=visit)
    steps.append(r)
    vid = visit.get("id") if isinstance(visit, dict) else None
    if vid:
        inv.confirm_intent(intent_visit, vid, http_status=st, source="T3.create_visit")
    else:
        inv.mark_orphan_suspected(intent_visit, http_status=st) if st in (200, 201) else inv.fail_intent(
            intent_visit, http_status=st, reason="create_visit_failed"
        )
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
        fb_text = f"D7R2 mini-dossier {run_id}"
        intent_fb = inv.open_intent(
            step="T3.mini_dossier",
            collection="mls_visit_feedback",
            correlation={"visit_id": vid, "feedback_text": fb_text},
        )
        st, fb = b.request(
            "POST",
            "/api/app/visit-feedback",
            {
                "visit_id": vid,
                "rating": 5,
                "feedback_text": fb_text,
            },
        )
        r = expect_status("T3.mini_dossier", st, {200, 201}, body=fb)
        steps.append(r)
        fbid = fb.get("id") if isinstance(fb, dict) else None
        if fbid:
            inv.confirm_intent(intent_fb, fbid, http_status=st, source="T3.mini_dossier")
        else:
            inv.mark_orphan_suspected(intent_fb, http_status=st) if st in (200, 201) else inv.fail_intent(
                intent_fb, http_status=st, reason="feedback_failed"
            )
        steps.append(
            expect_predicate(
                "T3.mini_dossier_id",
                bool(fbid),
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
    deal_notes = f"D7R2 deal {run_id}"
    intent_deal = inv.open_intent(
        step="T3.open_deal",
        collection="deals",
        correlation={
            "property_id": I["prop"],
            "client_id": I["client"],
            "collaboration_id": cid,
            "notes": deal_notes,
        },
    )
    st, deal = a.request(
        "POST",
        "/api/app/deals",
        {
            "property_id": I["prop"],
            "client_id": I["client"],
            "collaboration_id": cid,
            "notes": deal_notes,
        },
    )
    r = expect_status("T3.open_deal", st, {200, 201}, body=deal)
    steps.append(r)
    did = deal.get("id") if isinstance(deal, dict) else None
    if did:
        inv.confirm_intent(intent_deal, did, http_status=st, source="T3.open_deal")
    else:
        inv.mark_orphan_suspected(intent_deal, http_status=st) if st in (200, 201) else inv.fail_intent(
            intent_deal, http_status=st, reason="open_deal_failed"
        )
    steps.append(expect_predicate("T3.open_deal_id", bool(did), reason="missing_deal_id"))

    # --- Chat ---
    payload = {"collaboration_id": cid}
    if did:
        payload["deal_id"] = did
    intent_thread = inv.open_intent(
        step="T3.open_chat",
        collection="mls_chat_threads",
        correlation={"collaboration_id": cid, **({"deal_id": did} if did else {})},
    )
    st, thread = a.request("POST", "/api/app/collab-chat/threads", payload)
    r = expect_status("T3.open_chat", st, {200, 201}, body=thread)
    steps.append(r)
    tid = thread.get("id") if isinstance(thread, dict) else None
    if tid:
        inv.confirm_intent(intent_thread, tid, http_status=st, source="T3.open_chat")
    else:
        inv.mark_orphan_suspected(intent_thread, http_status=st) if st in (200, 201) else inv.fail_intent(
            intent_thread, http_status=st, reason="open_chat_failed"
        )
    steps.append(expect_predicate("T3.open_chat_id", bool(tid), reason="missing_thread_id"))

    if tid:
        chat_body = f"D7R2 chat {run_id} — no external send"
        intent_msg = inv.open_intent(
            step="T3.post_chat",
            collection="mls_chat_messages",
            correlation={"thread_id": tid, "body": chat_body},
        )
        st, msg = a.request(
            "POST",
            f"/api/app/collab-chat/threads/{tid}/messages",
            {"body": chat_body},
        )
        steps.append(expect_status("T3.post_chat", st, {200, 201}, body=msg))
        mid = msg.get("id") if isinstance(msg, dict) else None
        if mid:
            inv.confirm_intent(intent_msg, mid, http_status=st, source="T3.post_chat")
        else:
            inv.mark_orphan_suspected(intent_msg, http_status=st) if st in (200, 201) else inv.fail_intent(
                intent_msg, http_status=st, reason="post_chat_failed"
            )

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
        bodies = []
        if isinstance(items, list):
            for it in items:
                if isinstance(it, dict):
                    bodies.append(str(it.get("body") or it.get("text") or ""))
        steps.append(
            expect_predicate(
                "T3.list_chat_b_run_id_body",
                any(run_id in b for b in bodies),
                detail={"matched": any(run_id in b for b in bodies)},
                reason="chat_body_missing_run_id",
            )
        )

        # Isolation — ACTIVE independent tenant (not inactive agency)
        x = StagingClient()
        st, _ = x.login(seed_meta["emails"]["admin_iso"], password)
        steps.append(expect_status("T3.iso_login_active_third", st, {200}))
        st, me = x.request("GET", "/api/auth/me")
        steps.append(expect_status("T3.iso_me", st, {200}, body=me))
        steps.append(
            expect_predicate(
                "T3.iso_me_active_agency",
                isinstance(me, dict)
                and me.get("active_agency_id") == I["ag_iso"]
                and me.get("is_active") is not False,
                status=st,
                detail=me if isinstance(me, dict) else None,
                reason="iso_tenant_not_active_or_wrong_agency",
            )
        )
        st, denied = x.request("GET", f"/api/app/collab-chat/threads/{tid}/messages")
        steps.append(expect_status("T3.iso_other", st, {401, 403}, body=denied))
        detail_ok = True
        if isinstance(denied, dict):
            # Prefer semantic deny (chat_forbidden) when present
            d = denied.get("detail")
            if d is not None:
                detail_ok = d == "chat_forbidden" or (
                    isinstance(d, dict) and d.get("error") in ("chat_forbidden", "forbidden")
                ) or isinstance(d, str)
        steps.append(
            expect_predicate(
                "T3.iso_other_detail",
                detail_ok,
                status=st,
                detail=denied if isinstance(denied, dict) else None,
                reason="iso_deny_detail_unexpected",
            )
        )
    else:
        for s in (
            "T3.post_chat",
            "T3.list_chat_b",
            "T3.list_chat_b_count",
            "T3.list_chat_b_run_id_body",
            "T3.iso_login_active_third",
            "T3.iso_me",
            "T3.iso_me_active_agency",
            "T3.iso_other",
            "T3.iso_other_detail",
        ):
            steps.append({"step": s, "result": "FAIL", "reason": "skipped_missing_thread"})

    # --- Revoke + proposal after revoke ---
    if did and cid:
        st, rev = a.request(
            "POST", f"/api/app/collaborations/{cid}/respond", {"action": "revoke"}
        )
        r = expect_status("T3.revoke", st, {200}, body=rev)
        steps.append(r)
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

    return _finish(
        run_path,
        steps,
        {"collaboration_id": cid, "deal_id": did, "thread_id": tid, "visit_id": vid},
        inv,
    )


def _finish(
    run_path: Path, steps: list[dict], ids_out: dict, inv: CreatedInventory
) -> dict[str, Any]:
    out = {
        "classification": aggregate(steps),
        "steps": steps,
        "ids": ids_out,
        "inventory": inv.as_dict(),
        "harness": "scripts/d7_e2e",
        "note": "PASS requires every T3.* step PASS; 5xx always FAIL; iso uses ACTIVE third tenant",
    }
    write_json(run_path / "t3_api.json", out)
    write_json(
        run_path / "t3_classification.json",
        {"classification": out["classification"], "step_results": [s["result"] for s in steps]},
    )
    return out
