#!/usr/bin/env bash
# Report presence of critical env secrets (NAMES + present/missing only).
# Never prints values. Exit 1 if any required secret is missing.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${OMNIA_ENV_FILE:-$ROOT/backend/.env}"

REQUIRED=(RESEND_API_KEY GEMINI_API_KEY JWT_SECRET)
# Dogfood portal group — required when STRIPE_ENABLED=true or OPENAPI_ENABLED=true
OPTIONAL=(
  FAL_KEY TAVILY_API_KEY GOOGLE_CLIENT_ID
  STRIPE_SECRET_KEY STRIPE_PUBLISHABLE_KEY STRIPE_ENABLED STRIPE_WEBHOOK_SECRET
  OPENAPI_ENABLED OPENAPI_EMAIL OPENAPI_API_KEY OPENAPI_TOKEN
  OPENAPI_CATASTO_BASE OPENAPI_OAUTH_BASE
  FRONTEND_BASE_URL FRONTEND_URL OMNIA_PUBLIC_URL
)

# Load backend/.env for shell↔uvicorn parity (P-006). Vault/process env wins over file.
load_dotenv_file() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  echo "  ENVFILE  loading $f (keys only fill if unset in process)"
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      local key="${BASH_REMATCH[1]}"
      local val="${BASH_REMATCH[2]}"
      if [[ "$val" =~ ^\"(.*)\"$ ]]; then val="${BASH_REMATCH[1]}"; fi
      if [[ "$val" =~ ^\'(.*)\'$ ]]; then val="${BASH_REMATCH[1]}"; fi
      if [[ -z "${!key:-}" ]]; then
        export "${key}=${val}"
      fi
    fi
  done <"$f"
}

has_gemini() {
  [[ -n "${GEMINI_API_KEY:-}" || -n "${GOOGLE_API_KEY:-}" || -n "${EMERGENT_LLM_KEY:-}" ]]
}

echo "[check-secrets] presence report (values never printed)"
load_dotenv_file "$ENV_FILE"

if [[ -n "${CLOUD_AGENT_INJECTED_SECRET_NAMES:-}" ]]; then
  echo "  INJECTED  CLOUD_AGENT_INJECTED_SECRET_NAMES=${CLOUD_AGENT_INJECTED_SECRET_NAMES}"
else
  echo "  INJECTED  (no CLOUD_AGENT_INJECTED_SECRET_NAMES — not a Cloud Agent boot, or vault empty at start)"
fi
if [[ -n "${CLOUD_AGENT_ALL_SECRET_NAMES:-}" ]]; then
  echo "  VAULT     CLOUD_AGENT_ALL_SECRET_NAMES=${CLOUD_AGENT_ALL_SECRET_NAMES}"
fi

missing=0

for k in "${REQUIRED[@]}"; do
  if [[ "$k" == "GEMINI_API_KEY" ]]; then
    if has_gemini; then
      echo "  PRESENT  GEMINI_API_KEY (or alias)"
    else
      echo "  MISSING  GEMINI_API_KEY (or GOOGLE_API_KEY / EMERGENT_LLM_KEY)"
      missing=1
    fi
    continue
  fi
  if [[ -n "${!k:-}" ]]; then
    echo "  PRESENT  $k"
  else
    echo "  MISSING  $k"
    missing=1
  fi
done

# Conditional dogfood requirements
if [[ "${STRIPE_ENABLED:-}" == "true" ]]; then
  if [[ -z "${STRIPE_SECRET_KEY:-}" ]]; then
    echo "  MISSING  STRIPE_SECRET_KEY (required because STRIPE_ENABLED=true)"
    missing=1
  elif [[ "${STRIPE_SECRET_KEY}" == sk_test_* ]]; then
    echo "  PRESENT  STRIPE_SECRET_KEY (dogfood, class=sk_test)"
  elif [[ "${STRIPE_SECRET_KEY}" == sk_live_* ]]; then
    echo "  WARN     STRIPE_SECRET_KEY class=sk_live (Cloud dogfood wants sk_test_)"
  else
    echo "  PRESENT  STRIPE_SECRET_KEY (dogfood, class=other)"
  fi
  if [[ -z "${STRIPE_WEBHOOK_SECRET:-}" ]]; then
    echo "  WARN     STRIPE_WEBHOOK_SECRET absent (webhook verify will 503)"
  else
    echo "  PRESENT  STRIPE_WEBHOOK_SECRET (dogfood)"
  fi
fi

if [[ "${OPENAPI_ENABLED:-}" == "true" || "${OPENAPI_ENABLED:-}" == "1" ]]; then
  if [[ -z "${OPENAPI_TOKEN:-}" ]]; then
    if [[ -z "${OPENAPI_EMAIL:-}" || -z "${OPENAPI_API_KEY:-}" ]]; then
      echo "  MISSING  OPENAPI_EMAIL+OPENAPI_API_KEY (or OPENAPI_TOKEN) — Visura PDF off"
      missing=1
    else
      echo "  PRESENT  OPENAPI_EMAIL + OPENAPI_API_KEY (dogfood Visura)"
    fi
  else
    echo "  PRESENT  OPENAPI_TOKEN (dogfood Visura)"
  fi
fi

for k in "${OPTIONAL[@]}"; do
  if [[ "$k" == "STRIPE_ENABLED" || "$k" == "OPENAPI_ENABLED" ]]; then
    if [[ -n "${!k:-}" ]]; then
      echo "  PRESENT  ${k}=${!k}"
    else
      echo "  absent   ${k} (optional)"
    fi
    continue
  fi
  if [[ "$k" == "OPENAPI_ENABLED" ]]; then
    if [[ -n "${OPENAPI_ENABLED:-}" ]]; then
      echo "  PRESENT  OPENAPI_ENABLED=${OPENAPI_ENABLED}"
    else
      echo "  absent   OPENAPI_ENABLED (optional)"
    fi
    continue
  fi
  # Skip keys already handled in conditional blocks
  if [[ "$k" == "STRIPE_SECRET_KEY" || "$k" == "STRIPE_WEBHOOK_SECRET" ]]; then
    if [[ "${STRIPE_ENABLED:-}" == "true" ]]; then
      continue
    fi
  fi
  if [[ "$k" == "OPENAPI_EMAIL" || "$k" == "OPENAPI_API_KEY" || "$k" == "OPENAPI_TOKEN" ]]; then
    if [[ "${OPENAPI_ENABLED:-}" == "true" || "${OPENAPI_ENABLED:-}" == "1" ]]; then
      continue
    fi
  fi
  if [[ -n "${!k:-}" ]]; then
    if [[ "$k" == "STRIPE_SECRET_KEY" ]]; then
      case "${STRIPE_SECRET_KEY}" in
        sk_test_*) echo "  PRESENT  STRIPE_SECRET_KEY (optional, class=sk_test)" ;;
        sk_live_*) echo "  PRESENT  STRIPE_SECRET_KEY (optional, class=sk_live)" ;;
        *) echo "  PRESENT  STRIPE_SECRET_KEY (optional, class=other)" ;;
      esac
    elif [[ "$k" == "STRIPE_PUBLISHABLE_KEY" ]]; then
      case "${STRIPE_PUBLISHABLE_KEY}" in
        pk_test_*) echo "  PRESENT  STRIPE_PUBLISHABLE_KEY (optional, class=pk_test)" ;;
        pk_live_*) echo "  PRESENT  STRIPE_PUBLISHABLE_KEY (optional, class=pk_live)" ;;
        *) echo "  PRESENT  STRIPE_PUBLISHABLE_KEY (optional, class=other)" ;;
      esac
    elif [[ "$k" == "OPENAPI_API_KEY" ]]; then
      echo "  PRESENT  OPENAPI_API_KEY (optional, len=${#OPENAPI_API_KEY})"
    elif [[ "$k" == "FRONTEND_BASE_URL" || "$k" == "FRONTEND_URL" || "$k" == "OMNIA_PUBLIC_URL" ]]; then
      val="${!k}"
      # Prefer .env / SHARE_URL if process still has stale localhost from parent shell
      if [[ "$val" == http://127.0.0.1:* || "$val" == http://localhost:* ]]; then
        if [[ -f "$ENV_FILE" ]]; then
          file_val="$(grep -E "^${k}=" "$ENV_FILE" | tail -n1 | cut -d= -f2- || true)"
          if [[ "$file_val" =~ ^https://[a-z0-9-]+\.trycloudflare\.com/?$ ]]; then
            val="$file_val"
            export "${k}=$val"
          fi
        fi
        if [[ -f /tmp/omnia-stack/SHARE_URL.txt ]]; then
          share_val="$(tr -d '[:space:]' </tmp/omnia-stack/SHARE_URL.txt || true)"
          if [[ "$share_val" =~ ^https://[a-z0-9-]+\.trycloudflare\.com$ ]]; then
            val="$share_val"
          fi
        fi
      fi
      if [[ "$val" == http://127.0.0.1:* || "$val" == http://localhost:* ]]; then
        echo "  WARN     $k is localhost ($val) — email links break on tunnel (P-019; sync-public-base-url should fix)"
      elif [[ "$val" =~ ^https://[a-z0-9-]+\.trycloudflare\.com/?$ ]]; then
        echo "  PRESENT  $k (tunnel)"
      else
        echo "  PRESENT  $k"
      fi
    else
      echo "  PRESENT  $k (optional)"
    fi
  else
    echo "  absent   $k (optional)"
  fi
done

# Vault completeness hint (P-018)
if [[ -n "${CLOUD_AGENT_ALL_SECRET_NAMES:-}" ]]; then
  for need in STRIPE_SECRET_KEY STRIPE_PUBLISHABLE_KEY STRIPE_WEBHOOK_SECRET OPENAPI_ENABLED OPENAPI_EMAIL OPENAPI_API_KEY; do
    if [[ ",${CLOUD_AGENT_ALL_SECRET_NAMES}," != *",${need},"* ]]; then
      echo "  WARN     vault missing name $need (runtime may use disk .env only — fragile on new env)"
    fi
  done
fi

if [[ -n "${STRIPE_SECRET_KEY:-}" && "${STRIPE_ENABLED:-}" != "true" ]]; then
  echo "  WARN     STRIPE_SECRET_KEY present but STRIPE_ENABLED!=true — billing stays 503"
  echo "           Fix: vault STRIPE_ENABLED=true OR rely on cloud-agent-start auto-enable for sk_test_"
fi

# D-123 Railway API + D-074 Vercel FE (optional until go-live)
echo "  --- Railway API (D-123; not required for dogfood) ---"
for k in RAILWAY_TOKEN RAILWAY_PROJECT_ID OMNIA_API_PUBLIC_URL; do
  if [[ -n "${!k:-}" ]]; then
    echo "  PRESENT  $k"
  else
    echo "  WAIT     $k (see docs/ops/RAILWAY_DEPLOY.md)"
  fi
done
echo "  --- Vercel FE (D-074; after API URL) ---"
for k in VERCEL_TOKEN VERCEL_ORG_ID VERCEL_PROJECT_ID CLOUDFLARE_API_TOKEN CLOUDFLARE_ZONE_ID; do
  if [[ -n "${!k:-}" ]]; then
    echo "  PRESENT  $k"
  else
    echo "  WAIT     $k (see docs/ops/VERCEL_DEPLOY.md)"
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo "[check-secrets] FAIL — required secrets missing."
  echo "  SoT keys = password manager + provider consoles (see memory/INTEGRITY_AND_SECRETS.md)."
  echo "  Cursor vault is a copy; empty vault usually means wrong/new environment, not deleted keys."
  exit 1
fi
echo "[check-secrets] OK — required secrets present in this process env."
exit 0
