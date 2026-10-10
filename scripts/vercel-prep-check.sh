#!/usr/bin/env bash
# Pre-check: repo ready for Vercel FE deploy (no token required).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FE="$ROOT/frontend"
fail=0

ok() { echo "OK  $*"; }
bad() { echo "FAIL $*"; fail=1; }

echo "=== vercel-prep-check ==="

[[ -f "$FE/vercel.json" ]] && ok "frontend/vercel.json" || bad "missing vercel.json"
[[ -f "$FE/package.json" ]] && ok "frontend/package.json" || bad "missing package.json"
[[ -f "$FE/yarn.lock" ]] && ok "frontend/yarn.lock" || bad "missing yarn.lock"
[[ -f "$FE/.env.example" ]] && ok "frontend/.env.example" || bad "missing .env.example"
[[ -f "$ROOT/docs/ops/VERCEL_DEPLOY.md" ]] && ok "docs/ops/VERCEL_DEPLOY.md" || bad "missing VERCEL_DEPLOY.md"
[[ -f "$ROOT/memory/DNS_SETUP_GUIDE.md" ]] && ok "DNS_SETUP_GUIDE.md" || bad "missing DNS guide"

# vercel.json essentials
if grep -q '"outputDirectory": "build"' "$FE/vercel.json" \
  && grep -q 'yarn build\|craco build\|npm run build' "$FE/vercel.json" "$FE/package.json"; then
  ok "build → build/ configured"
else
  bad "build/outputDirectory mismatch"
fi

# CRA uses REACT_APP_BACKEND_URL
if grep -q 'REACT_APP_BACKEND_URL' "$FE/src/shared/lib/api.js"; then
  ok "api.js reads REACT_APP_BACKEND_URL (empty=same-origin; prod needs absolute)"
else
  bad "api.js missing REACT_APP_BACKEND_URL"
fi

# Token presence (informational — not required for prep PASS)
echo "--- vault (presence only) ---"
for k in VERCEL_TOKEN VERCEL_ORG_ID VERCEL_PROJECT_ID OMNIA_API_PUBLIC_URL CLOUDFLARE_API_TOKEN CLOUDFLARE_ZONE_ID; do
  if [[ -n "${!k:-}" ]]; then
    ok "env $k is set"
  else
    echo "WAIT $k not set (ok for prep; required for E2E deploy)"
  fi
done

echo "---"
if [[ "$fail" -eq 0 ]]; then
  echo "ESITO=PASS — repo ready; after pause add vault secrets then «vai Vercel»"
  exit 0
fi
echo "ESITO=FAIL"
exit 1
