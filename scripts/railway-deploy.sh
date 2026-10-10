#!/usr/bin/env bash
# Deploy OMNIA API to Railway (requires RAILWAY_TOKEN).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== railway-deploy ==="
bash "$ROOT/scripts/railway-prep-check.sh"

if [[ -z "${RAILWAY_TOKEN:-}" ]]; then
  echo "BLOCKED: RAILWAY_TOKEN missing."
  echo "Founder: Railway → Account → Tokens → vault omnia2 → reboot agent → «vai Railway»."
  exit 2
fi

export RAILWAY_TOKEN
cd "$ROOT"

if ! command -v railway >/dev/null 2>&1; then
  echo "Installing Railway CLI…"
  npm install -g @railway/cli >/dev/null 2>&1 \
    || curl -fsSL https://railway.app/install.sh | sh
  export PATH="$HOME/.railway/bin:$PATH"
fi

ARGS=(up --detach)
if [[ -n "${RAILWAY_PROJECT_ID:-}" ]]; then
  railway link --project "$RAILWAY_PROJECT_ID" || true
fi

echo "Deploying (Dockerfile.railway)…"
railway up --ci || railway "${ARGS[@]}"

echo "DONE — next:"
echo "  1) Ensure MongoDB plugin + MONGO_URL linked"
echo "  2) Generate domain → smoke /api/health"
echo "  3) Set OMNIA_API_PUBLIC_URL in vault"
echo "  4) Cloudflare CNAME api → Railway"
echo "  5) «vai Vercel»"
