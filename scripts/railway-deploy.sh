#!/usr/bin/env bash
# Deploy OMNIA API to Railway.
# Vault name (canonical): RAILWAY_TOKEN = Account token from railway.app/account/tokens
# CLI quirk: Account tokens must be exported as RAILWAY_API_TOKEN, and RAILWAY_TOKEN
# must be unset — otherwise the CLI treats RAILWAY_TOKEN as a *project* token → Unauthorized.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== railway-deploy ==="
bash "$ROOT/scripts/railway-prep-check.sh"

if [[ -z "${RAILWAY_TOKEN:-}" && -z "${RAILWAY_API_TOKEN:-}" ]]; then
  echo "BLOCKED: RAILWAY_TOKEN missing."
  echo "Founder: Railway → Account → Tokens → vault omnia2 as RAILWAY_TOKEN → reboot agent → «vai Railway»."
  exit 2
fi

# Prefer vault RAILWAY_TOKEN; fall back to already-set RAILWAY_API_TOKEN.
ACCOUNT_TOKEN="${RAILWAY_TOKEN:-${RAILWAY_API_TOKEN}}"
unset RAILWAY_TOKEN
export RAILWAY_API_TOKEN="$ACCOUNT_TOKEN"
export PATH="${HOME}/.railway/bin:${PATH}"

cd "$ROOT"

if ! command -v railway >/dev/null 2>&1; then
  echo "Installing Railway CLI…"
  npm install -g @railway/cli >/dev/null 2>&1 \
    || curl -fsSL https://railway.app/install.sh | sh
  export PATH="$HOME/.railway/bin:$PATH"
fi

if ! railway whoami >/dev/null 2>&1; then
  echo "BLOCKED: Railway auth failed (account token invalid or revoked)."
  echo "Founder: create a fresh Account token → vault RAILWAY_TOKEN → new agent → «vai Railway»."
  exit 3
fi
echo "OK  railway whoami"

if [[ -n "${RAILWAY_PROJECT_ID:-}" ]]; then
  railway link --project "$RAILWAY_PROJECT_ID" --environment production || true
else
  # Create project if directory not linked yet
  if [[ ! -f "$ROOT/.railway/config.json" ]] && [[ ! -d "$ROOT/.railway" || -z "$(ls -A "$ROOT/.railway" 2>/dev/null || true)" ]]; then
    echo "Creating Railway project omnia-api…"
    railway init --name omnia-api --json
  fi
fi

# Ensure API service exists
if ! railway service list --json 2>/dev/null | grep -q '"name"'; then
  echo "Adding service omnia-api…"
  railway add --service omnia-api --json || true
fi
railway service link omnia-api 2>/dev/null || railway service link 2>/dev/null || true

# Mongo plugin (idempotent-ish: ignore if already present)
if ! railway service list --json 2>/dev/null | grep -qiE 'mongo|Mongo'; then
  echo "Adding MongoDB plugin…"
  railway add --database mongo --json
fi

echo "Deploying (Dockerfile.railway)…"
railway up --ci --yes --service omnia-api || railway up --detach --yes --service omnia-api

echo "DONE — next:"
echo "  1) Link MONGO_URL on API service (reference to Mongo plugin)"
echo "  2) Set service variables + Generate domain → smoke /api/health"
echo "  3) Set OMNIA_API_PUBLIC_URL in vault Environment"
echo "  4) Cloudflare CNAME api → Railway"
echo "  5) «vai Vercel»"
