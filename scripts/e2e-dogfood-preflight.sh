#!/usr/bin/env bash
# Preflight dogfood E2E (no secret values printed).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== stack =="
bash scripts/omnia-stack.sh status 2>&1 | tail -8

echo
echo "== secrets presence =="
bash scripts/check-secrets-presence.sh 2>&1 | sed -n '1,20p'

echo
echo "== stripe gate =="
python3 - <<'PY'
import os
from pathlib import Path
for line in Path("backend/.env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k,v=line.split("=",1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
en = (os.environ.get("STRIPE_ENABLED") or "").lower() == "true"
sk = bool(os.environ.get("STRIPE_SECRET_KEY"))
pk = bool(os.environ.get("STRIPE_PUBLISHABLE_KEY") or os.environ.get("STRIPE_PUBLIC_KEY"))
print(f"STRIPE_ENABLED={en} secret_present={sk} publishable_present={pk}")
if not en or not sk:
    print("BILLING_PATH=assisted (grant_agency_plan.py) — Stripe checkout non disponibile")
else:
    print("BILLING_PATH=stripe_test_ok")
PY

echo
echo "== health =="
curl -sS "http://127.0.0.1:43121/api/health" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('status'), d.get('message',{}).get('db'))"
curl -sS "http://127.0.0.1:43121/api/billing/plans" | python3 -c "import sys,json;d=json.load(sys.stdin);print('plans',[p['tier'] for p in d.get('plans',[])])"

SHARE=$(cat /tmp/omnia-stack/SHARE_URL.txt 2>/dev/null || true)
echo
echo "== URLs =="
echo "public: ${SHARE:-unknown}"
echo "login:  ${SHARE:-http://127.0.0.1:43123}/it/login"
echo "register agency: .../it/register"
echo "cloud private sell: .../it/cloud/account/sell"
echo "cloud register: .../it/cloud/register"
echo
echo "OK preflight done"
