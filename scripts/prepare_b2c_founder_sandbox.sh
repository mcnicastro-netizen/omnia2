#!/usr/bin/env bash
# Prepare Cloud/local sandbox so Founder can dogfood B2C as a private seller:
# register → sell listing → HAL improve → Stripe Test (staging / vetrina) → see on portal.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/backend/.env"

echo "[b2c-sandbox] ensuring stack…"
bash "$ROOT/scripts/omnia-stack.sh" ensure

# Auto-approve private listings on submit (sandbox only)
if [[ -f "$ENV_FILE" ]]; then
  if grep -q '^OMNIA_B2C_SANDBOX_AUTO_APPROVE=' "$ENV_FILE"; then
    sed -i 's/^OMNIA_B2C_SANDBOX_AUTO_APPROVE=.*/OMNIA_B2C_SANDBOX_AUTO_APPROVE=true/' "$ENV_FILE"
  else
    printf '\n# B2C Founder sandbox: publish without moderation queue\nOMNIA_B2C_SANDBOX_AUTO_APPROVE=true\n' >> "$ENV_FILE"
  fi
  echo "[b2c-sandbox] OMNIA_B2C_SANDBOX_AUTO_APPROVE=true"
fi

# Nudge uvicorn --reload
touch "$ROOT/backend/server.py" 2>/dev/null || true
sleep 1

URL="$(cat /tmp/omnia-stack/SHARE_URL.txt 2>/dev/null || true)"
API="http://127.0.0.1:43121/api"
stripe="$(curl -s "$API/billing/b2c/catalog" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("stripe_enabled"))' 2>/dev/null || echo '?')"

cat <<EOF

════════════════════════════════════════════════════════
  B2C Founder sandbox — privato (non gestionale)
════════════════════════════════════════════════════════
  Portale:     ${URL:-http://127.0.0.1:43123}
  Registrati:  ${URL:-http://127.0.0.1:43123}/it/cloud/register?intent=sell
  Area Vendi:  ${URL:-http://127.0.0.1:43123}/it/cloud/account/sell
  Cerca casa:  ${URL:-http://127.0.0.1:43123}/it/cloud/search
  Stripe Test: ${stripe}  (carta 4242 4242 4242 4242)
  Auto-approve annunci: ON (OMNIA_B2C_SANDBOX_AUTO_APPROVE)
  Guida:       docs/ops/B2C_FOUNDER_SANDBOX.md
════════════════════════════════════════════════════════

EOF
