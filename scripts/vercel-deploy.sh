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

# Normalize: Founder may paste KEY=value or host-only
API_URL="${OMNIA_API_PUBLIC_URL}"
API_URL="${API_URL#OMNIA_API_PUBLIC_URL=}"
API_URL="${API_URL%/}"
API_URL="${API_URL%/api}"
if [[ "$API_URL" != https://* ]]; then
  if [[ "$API_URL" == api.omniarealestateecosystem.it* ]]; then
    API_URL="https://${API_URL}"
  else
    echo "BLOCKED: OMNIA_API_PUBLIC_URL must be https://… (got non-https)."
    exit 2
  fi
fi

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

# Build locally first (catch CRA errors before upload).
# Do NOT blank REACT_APP_BACKEND_URL here — package.json "build" respects the export
# (Cloud preview same-origin uses: REACT_APP_BACKEND_URL= yarn build:same-origin / omnia-stack).
yarn build

# Guard: production FE must call absolute API, not Vercel same-origin /api (SPA HTML → crash).
MAIN_JS="$(ls -1 "$FE"/build/static/js/main.*.js 2>/dev/null | head -1 || true)"
if [[ -z "$MAIN_JS" ]] || ! grep -q "$API_URL" "$MAIN_JS"; then
  echo "BLOCKED: built bundle missing REACT_APP_BACKEND_URL=$API_URL"
  echo "Check frontend/package.json build script is not forcing REACT_APP_BACKEND_URL= empty."
  exit 3
fi
if grep -q 'baseURL:"/api"' "$MAIN_JS"; then
  echo "BLOCKED: bundle still has same-origin baseURL /api (prod would break cloud search)."
  exit 3
fi
echo "OK  bundle embeds API host"

echo "Deploying to Vercel…"
npx --yes vercel@latest deploy --prebuilt "${ARGS[@]}" 2>/dev/null \
  || npx --yes vercel@latest --prod "${ARGS[@]}"

echo "DONE — next: attach custom domains in Vercel + update Cloudflare (DNS_SETUP_GUIDE §4)."
echo "Log tip: save deployment URL; smoke www + /it/login + /it/cloud/search."
