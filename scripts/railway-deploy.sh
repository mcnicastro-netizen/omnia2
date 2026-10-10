#!/usr/bin/env bash
# Deploy OMNIA API to Railway.
# Bootstrap: RAILWAY_API_TOKEN (Account Token). Redeploy: RAILWAY_TOKEN (Project Token) + RAILWAY_PROJECT_ID.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="${HOME}/.railway/bin:${PATH}"

echo "=== railway-deploy ==="
bash "$ROOT/scripts/railway-golive-probe.sh"

cd "$ROOT"

if ! command -v railway >/dev/null 2>&1; then
  echo "Installing Railway CLI…"
  curl -fsSL https://railway.app/install.sh | sh
  export PATH="${HOME}/.railway/bin:${PATH}"
fi

# Prefer account token for init; project token alone only if project already linked/id set.
if [[ -n "${RAILWAY_API_TOKEN:-}" ]]; then
  # Avoid project-token override when both present
  if [[ -n "${RAILWAY_TOKEN:-}" && -z "${RAILWAY_PROJECT_ID:-}" ]]; then
    echo "INFO: unset RAILWAY_TOKEN for bootstrap (CLI would ignore account token)"
    unset RAILWAY_TOKEN
  fi
  export RAILWAY_API_TOKEN
elif [[ -n "${RAILWAY_TOKEN:-}" ]]; then
  export RAILWAY_TOKEN
else
  echo "BLOCKED: missing RAILWAY_API_TOKEN (or RAILWAY_TOKEN + RAILWAY_PROJECT_ID)."
  exit 2
fi

if [[ -n "${RAILWAY_PROJECT_ID:-}" ]]; then
  echo "Linking project ${RAILWAY_PROJECT_ID}…"
  railway link -p "$RAILWAY_PROJECT_ID" \
    ${RAILWAY_ENVIRONMENT_ID:+-e "$RAILWAY_ENVIRONMENT_ID"} \
    ${RAILWAY_SERVICE_ID:+-s "$RAILWAY_SERVICE_ID"} || true
else
  echo "No RAILWAY_PROJECT_ID — creating/linking omnia-api…"
  railway init --name omnia-api --json || railway link || true
  echo "Adding MongoDB plugin…"
  railway add -d mongo || true
fi

echo "Setting core variables (from vault / local env — values not printed)…"
# shellcheck disable=SC1091
set -a
# Prefer process env; optionally fill gaps from backend/.env without overriding vault
if [[ -f "$ROOT/backend/.env" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      k="${BASH_REMATCH[1]}"; v="${BASH_REMATCH[2]}"
      [[ -z "${!k:-}" ]] && export "$k=$v"
    fi
  done <"$ROOT/backend/.env"
fi
set +a

VARS=(
  DB_NAME=omnia
  COOKIE_SECURE=true
  STORAGE_BACKEND=local
  CORS_ORIGINS="${CORS_ORIGINS:-https://www.omniarealestateecosystem.it,https://app.omniarealestateecosystem.it,https://cloud.omniarealestateecosystem.it}"
  FRONTEND_URL="${FRONTEND_URL:-https://www.omniarealestateecosystem.it}"
  FRONTEND_BASE_URL="${FRONTEND_BASE_URL:-https://www.omniarealestateecosystem.it}"
  OMNIA_PUBLIC_URL="${OMNIA_PUBLIC_URL:-https://www.omniarealestateecosystem.it}"
  SENDER_EMAIL="${SENDER_EMAIL:-OMNIA <info@omniarealestateecosystem.it>}"
  OMNIA_SELF_SERVE_ENABLED="${OMNIA_SELF_SERVE_ENABLED:-true}"
)

# Secrets / keys — only if present in env
for k in JWT_SECRET GEMINI_API_KEY RESEND_API_KEY ADMIN_EMAIL ADMIN_PASSWORD DEMO_ADMIN_PASSWORD \
  STRIPE_ENABLED STRIPE_SECRET_KEY STRIPE_PUBLISHABLE_KEY STRIPE_WEBHOOK_SECRET \
  FAL_KEY TAVILY_API_KEY GOOGLE_CLIENT_ID; do
  if [[ -n "${!k:-}" ]]; then
    VARS+=("${k}=${!k}")
  fi
done

# Mongo: prefer Railway plugin reference if not set; leave for Founder UI if missing
if [[ -n "${MONGO_URL:-}" ]]; then
  VARS+=("MONGO_URL=${MONGO_URL}")
else
  echo "WAIT MONGO_URL not in env — set in Railway UI to \${{MongoDB.MONGO_URL}} (plugin name may vary)"
fi

railway variables --set "$(printf '%s ' "${VARS[@]}")" 2>/dev/null \
  || for pair in "${VARS[@]}"; do
       railway variables --set "$pair" >/dev/null || true
     done

echo "Deploying (Dockerfile.railway)…"
railway up --ci -d -y || railway up --detach -y

echo "DONE — next:"
echo "  1) Confirm MongoDB plugin + MONGO_URL"
echo "  2) Generate domain → smoke /api/health"
echo "  3) Set PUBLIC_BASE_URL + vault OMNIA_API_PUBLIC_URL"
echo "  4) Cloudflare CNAME api → Railway"
echo "  5) «vai Vercel»"
