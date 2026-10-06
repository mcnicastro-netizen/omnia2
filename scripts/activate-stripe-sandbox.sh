#!/usr/bin/env bash
# Activate Stripe TEST sandbox on a running Cloud Agent pod.
# Never prints secret values. Exit 0 only when plans enabled with sk_test_.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
API="${API_ORIGIN:-http://127.0.0.1:43121}"
PY="${ROOT}/backend/.venv/bin/python"
[[ -x "$PY" ]] || PY=python3

echo "[activate-stripe-sandbox] materialize vault → .env"
set +e
"$PY" "$ROOT/scripts/stripe-vault-materialize.py" "$ROOT/backend/.env"
mat=$?
set -e
if [[ "$mat" -eq 2 ]]; then
  echo "[activate-stripe-sandbox] FAIL: Cursor vault still injects sk_live_/pk_live_ (or mixed)."
  echo "  Code path is ready for sk_test_; vault values are live. Not a .env template issue."
  exit 2
fi

# Export from .env into this shell ONLY for Stripe after materialize (test only)
eval "$("$PY" - "$ROOT/backend/.env" <<'PY'
import os, sys
from pathlib import Path
from dotenv import dotenv_values
p = Path(sys.argv[1])
vals = dotenv_values(p) if p.is_file() else {}
sk = (vals.get("STRIPE_SECRET_KEY") or os.environ.get("STRIPE_SECRET_KEY") or "").strip()
if not sk.startswith("sk_test_"):
    raise SystemExit("no sk_test in materialized env")
for k in ("STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY", "STRIPE_ENABLED", "STRIPE_MODE", "STRIPE_WEBHOOK_SECRET"):
    v = (vals.get(k) or os.environ.get(k) or "").strip()
    if not v:
        continue
    esc = v.replace("'", "'\"'\"'")
    print(f"export {k}='{esc}'")
PY
)"

echo "[activate-stripe-sandbox] setup_stripe catalog"
cd "$ROOT/backend"
"$PY" -m apps.billing.setup_stripe

echo "[activate-stripe-sandbox] restart API to pick env"
bash "$ROOT/scripts/omnia-stack.sh" ensure

echo "[activate-stripe-sandbox] GET /api/billing/plans"
"$PY" - <<PY
import json, os, urllib.request
url = "${API}/api/billing/plans"
with urllib.request.urlopen(url, timeout=10) as r:
    data = json.load(r)
enabled = bool(data.get("enabled"))
pk = (data.get("publishable_key") or "")
mode = data.get("mode")
pk_class = "pk_test" if pk.startswith("pk_test_") else ("pk_live" if pk.startswith("pk_live_") else ("absent" if not pk else "other"))
print(json.dumps({"enabled": enabled, "mode": mode, "publishable_class": pk_class}, indent=2))
if not enabled or pk_class == "pk_live":
    raise SystemExit(3)
print("[activate-stripe-sandbox] OK — sandbox billing enabled (test keys)")
PY
