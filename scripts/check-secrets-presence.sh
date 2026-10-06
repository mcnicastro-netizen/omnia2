#!/usr/bin/env bash
# Report presence of critical env secrets (NAMES + present/missing only).
# Never prints values. Exit 1 if any required secret is missing.
set -euo pipefail

REQUIRED=(RESEND_API_KEY GEMINI_API_KEY)
OPTIONAL=(FAL_KEY TAVILY_API_KEY STRIPE_SECRET_KEY STRIPE_PUBLISHABLE_KEY STRIPE_ENABLED STRIPE_WEBHOOK_SECRET GOOGLE_CLIENT_ID JWT_SECRET)

# Also accept Gemini aliases
has_gemini() {
  [[ -n "${GEMINI_API_KEY:-}" || -n "${GOOGLE_API_KEY:-}" || -n "${EMERGENT_LLM_KEY:-}" ]]
}

echo "[check-secrets] presence report (values never printed)"

# Cursor inject list — explains “I see secrets in UI but agent says missing”
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

for k in "${OPTIONAL[@]}"; do
  if [[ "$k" == "STRIPE_ENABLED" ]]; then
    if [[ -n "${STRIPE_ENABLED:-}" ]]; then
      echo "  PRESENT  STRIPE_ENABLED=${STRIPE_ENABLED}"
    else
      echo "  absent   STRIPE_ENABLED (optional)"
    fi
    continue
  fi
  if [[ -n "${!k:-}" ]]; then
    # Presence + safe prefix class for Stripe keys (never full value)
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
    else
      echo "  PRESENT  $k (optional)"
    fi
  else
    echo "  absent   $k (optional)"
  fi
done

# Diagnose classic trap: vault has Stripe but template .env forced disabled
if [[ -n "${STRIPE_SECRET_KEY:-}" && "${STRIPE_ENABLED:-}" != "true" ]]; then
  echo "  WARN     STRIPE_SECRET_KEY present but STRIPE_ENABLED!=true — billing stays 503"
  echo "           Fix: vault STRIPE_ENABLED=true OR rely on cloud-agent-start auto-enable for sk_test_"
fi

if [[ "$missing" -ne 0 ]]; then
  echo "[check-secrets] FAIL — required secrets missing."
  echo "  SoT keys = password manager + provider consoles (see memory/INTEGRITY_AND_SECRETS.md)."
  echo "  Cursor vault is a copy; empty vault usually means wrong/new environment, not deleted keys."
  exit 1
fi
echo "[check-secrets] OK — required secrets present in this process env."
exit 0
