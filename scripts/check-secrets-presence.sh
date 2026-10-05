#!/usr/bin/env bash
# Report presence of critical env secrets (NAMES + present/missing only).
# Never prints values. Exit 1 if any required secret is missing.
set -euo pipefail

REQUIRED=(RESEND_API_KEY GEMINI_API_KEY)
OPTIONAL=(FAL_KEY TAVILY_API_KEY STRIPE_SECRET_KEY GOOGLE_CLIENT_ID JWT_SECRET)

# Also accept Gemini aliases
has_gemini() {
  [[ -n "${GEMINI_API_KEY:-}" || -n "${GOOGLE_API_KEY:-}" || -n "${EMERGENT_LLM_KEY:-}" ]]
}

echo "[check-secrets] presence report (values never printed)"
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
  if [[ -n "${!k:-}" ]]; then
    echo "  PRESENT  $k (optional)"
  else
    echo "  absent   $k (optional)"
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
