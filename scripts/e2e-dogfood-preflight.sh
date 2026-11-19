#!/usr/bin/env bash
# D-175 C1 — Preflight Dogfood fail-closed (no secret values printed).
# Exit ≠0 if any critical isolation check fails (C1-T26).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== D-175 C1 dogfood preflight =="

if [[ "${OMNIA_ENV:-}" != "dogfood" ]]; then
  echo "SKIP: OMNIA_ENV!=dogfood (got '${OMNIA_ENV:-}'). Isolation suite requires dogfood."
  echo "To run C1 checks: OMNIA_ENV=dogfood … bash scripts/e2e-dogfood-preflight.sh"
  exit 0
fi

export PYTHONPATH="$ROOT/backend:${PYTHONPATH:-}"
PY="${ROOT}/backend/.venv/bin/python3"
if [[ ! -x "$PY" ]]; then
  PY="$(command -v python3)"
fi
"$PY" - <<'PY'
import json
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
from shared.dogfood.perimeter import dogfood_preflight_checks, is_h4_purchase_ready

report = dogfood_preflight_checks()
print(json.dumps({
    "ok": report.get("ok"),
    "failures": report.get("failures"),
    "db_ok": (report.get("checks") or {}).get("db", {}).get("ok"),
    "hosts_ok": (report.get("checks") or {}).get("hosts", {}).get("ok"),
    "stripe_ok": (report.get("checks") or {}).get("stripe", {}).get("ok"),
    "h4_purchase_ready": is_h4_purchase_ready(),
    "h4_env_flag": (os.environ.get("OMNIA_H4_PURCHASE_READY") or "").lower() == "true",
    "note": "env_flag_alone_insufficient",
}, indent=2))
if not report.get("ok"):
    sys.exit(2)
print("OK perimeter checks")
PY

echo
echo "== deploy wrappers must refuse dogfood =="
set +e
out_r=$(bash scripts/railway-deploy.sh 2>&1 | head -5)
ec_r=$?
out_v=$(bash scripts/vercel-deploy.sh 2>&1 | head -5)
ec_v=$?
set -e
echo "railway-deploy exit=$ec_r"
echo "$out_r" | head -3
echo "vercel-deploy exit=$ec_v"
echo "$out_v" | head -3
if [[ "$ec_r" -ne 99 ]] || [[ "$ec_v" -ne 99 ]]; then
  echo "FAIL: deploy scripts must exit 99 in dogfood before CLI"
  exit 3
fi
echo "OK deploy blocked before CLI"

echo
echo "== H4 sealed gate (flag alone must NOT ready) =="
export OMNIA_H4_PURCHASE_READY=true
export OMNIA_H4_READY_MARKER_PATH="${TMPDIR:-/tmp}/omnia-c1-no-marker-$$"
rm -f "$OMNIA_H4_READY_MARKER_PATH"
PYTHONPATH="$ROOT/backend" "$PY" - <<'PY'
import os, sys
sys.path.insert(0, "backend")
from shared.dogfood.perimeter import is_h4_purchase_ready
assert os.environ.get("OMNIA_H4_PURCHASE_READY", "").lower() == "true"
if is_h4_purchase_ready():
    print("FAIL: flag alone unlocked H4")
    sys.exit(4)
print("OK flag-alone insufficient (C1-T15/T16 sealed)")
PY

echo
echo "OK preflight C1 critical path"
