"""T22 staging procedure contract — PREPARED ONLY, not executed against remote Mongo.

This module documents the repeatable dual-run isolation check for a future
authorized staging mandate. Importing or calling ``dry_run_checklist`` never
connects to MongoDB remote.
"""
from __future__ import annotations

from typing import Any

# Contract keys required by local test_T22_staging_contract_shape
STAGING_T22_CONTRACT: dict[str, Any] = {
    "executed": False,
    "preflight_db": "Verify MONGO_URL/DB_NAME are staging dedicated; refuse prod names",
    "run_ids_disjoint": "Generate two validate_run_id values A≠B",
    "snapshot_before": "Dump ids for SEED_TAGGED∪MLS∪deals∪SIDE_EFFECT where d7_run_id∈{A,B}",
    "inventory_a": "created_ids.json for run A including memberships+notifications",
    "inventory_b": "created_ids.json for run B including memberships+notifications",
    "memberships": "Register membership ids by user_id+organization_id exact",
    "notifications": "Register by meta.invite_id and/or meta.accepted_user_id",
    "cleanup_a_only": "cleanup_run(A) — delete only inventory ids or exact d7_run_id=A",
    "compare_b": "SHA-256 canonical snapshot B before == after",
    "residual_a": "post_cleanup_verify(A) ok; no A tags left",
    "cleanup_a_idempotent": "Second cleanup_run(A) deleted_count 0; B unchanged",
    "evidence_json": "Write t22_staging_evidence.json with snaps + classifications",
    "pass_fail_blocked": (
        "PASS: A CLEAN + B intact + residual 0; "
        "FAIL: B mutated or A residual; "
        "BLOCKED: uncertain/unattributable side-effects"
    ),
    "destructive_queries": "Only {'id':{'$in':[...]}} or {d7_run_id: exact_run}",
    "unattributable_policy": "Never delete; mark uncertain; block CLEAN",
}


def dry_run_checklist() -> dict[str, Any]:
    """Return the procedure checklist without performing remote I/O."""
    return {
        "status": "PREPARED_NOT_EXECUTED",
        "contract": dict(STAGING_T22_CONTRACT),
        "note": "Requires explicit Founder authorization for staging Mongo write",
    }
