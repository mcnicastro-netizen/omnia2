#!/usr/bin/env bash
# Deploy frontend to Vercel production (requires vault tokens).
# Usage: bash scripts/vercel-deploy.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FE="$ROOT/frontend"

echo "=== vercel-deploy ==="
bash "$ROOT/scripts/vercel-prep-check.sh"

if [[ -z "${VERCEL_TOKEN:-}" ]]; then
  echo "BLOCKED: VERCEL_TOKEN missing in env/vault."
  echo "Founder: add token to Cursor env omnia2 Secrets, reboot agent, «vai Vercel»."
  exit 2
fi

if [[ -z "${OMNIA_API_PUBLIC_URL:-}" ]]; then
  echo "BLOCKED: OMNIA_API_PUBLIC_URL missing (e.g. https://api.omniarealestateecosystem.it)."
  echo "FE build needs absolute REACT_APP_BACKEND_URL for production."
  exit 2
fi

API_URL="${OMNIA_API_PUBLIC_URL%/}"
# strip trailing /api if Founder pasted full API root with /api
API_URL="${API_URL%/api}"

export REACT_APP_BACKEND_URL="$API_URL"
echo "REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL"

cd "$FE"
if [[ ! -d node_modules ]]; then
  yarn install --frozen-lockfile
fi

# Ensure vercel CLI
if ! command -v vercel >/dev/null 2>&1; then
  echo "Installing vercel CLI (npx)…"
fi

ARGS=(--token "$VERCEL_TOKEN" --yes --prod)
if [[ -n "${VERCEL_ORG_ID:-}" ]]; then
  export VERCEL_ORG_ID
fi
if [[ -n "${VERCEL_PROJECT_ID:-}" ]]; then
  export VERCEL_PROJECT_ID
fi

# Build locally first (catch CRA errors before upload)
yarn build

echo "Deploying to Vercel…"
npx --yes vercel@latest deploy --prebuilt "${ARGS[@]}" 2>/dev/null \
  || npx --yes vercel@latest --prod "${ARGS[@]}"

echo "DONE — next: attach custom domains in Vercel + update Cloudflare (DNS_SETUP_GUIDE §4)."
echo "Log tip: save deployment URL; smoke www + /it/login."
