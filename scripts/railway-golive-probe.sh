#!/usr/bin/env bash
# Diagnose Railway go-live blockers (token type + trial/plan).
# Exit 0 = ready for deploy; 2 = Founder action required; 1 = repo/prep fail.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="${HOME}/.railway/bin:${PATH}"

echo "=== railway-golive-probe ==="
bash "$ROOT/scripts/railway-prep-check.sh"

API_TOKEN="${RAILWAY_API_TOKEN:-}"
PROJ_TOKEN="${RAILWAY_TOKEN:-}"
BEARER="${API_TOKEN:-$PROJ_TOKEN}"

if [[ -z "$BEARER" ]]; then
  echo "BLOCKED: serve RAILWAY_API_TOKEN (Account Token) — bootstrap progetto."
  echo "Crea: https://railway.app/account/tokens → vault omnia2 → RAILWAY_API_TOKEN"
  echo "Poi nuovo agent → «vai Railway»"
  exit 2
fi

gql() {
  curl -sS -H "Authorization: Bearer $BEARER" \
    https://backboard.railway.app/graphql/v2 \
    -H 'Content-Type: application/json' \
    --data-binary "$1"
}

echo "--- GraphQL projects ---"
PROJ_JSON="$(gql '{"query":"{ projects { edges { node { id name subscriptionType services { edges { node { id name } } } } } } }"}')"
echo "$PROJ_JSON" | head -c 2500; echo

if echo "$PROJ_JSON" | grep -qiE 'Not Authorized|Unauthenticated|Unauthorized'; then
  echo "BLOCKED: token GraphQL non autorizzato. Rigenera Account Token → RAILWAY_API_TOKEN."
  exit 2
fi

FIRST_PROJECT="$(python3 - <<'PY' "$PROJ_JSON"
import json,sys
try:
    d=json.loads(sys.argv[1])
    edges=(d.get("data") or {}).get("projects",{}).get("edges") or []
    print(edges[0]["node"]["id"] if edges else "")
except Exception:
    print("")
PY
)"

echo "--- plan / trial probe ---"
if [[ -n "$FIRST_PROJECT" ]]; then
  MUT_JSON="$(gql "{\"query\":\"mutation(\$input: ServiceCreateInput!) { serviceCreate(input: \$input) { id } }\",\"variables\":{\"input\":{\"projectId\":\"$FIRST_PROJECT\",\"name\":\"omnia-probe-tmp\"}}}")"
else
  MUT_JSON="$(gql '{"query":"mutation { projectCreate(input: { name: \"omnia-probe-tmp\" }) { id } }"}')"
fi
echo "$MUT_JSON" | head -c 2000; echo

TRIAL_BLOCKED=0
if echo "$MUT_JSON" | grep -qi 'trial has expired'; then
  echo "BLOCKED: trial Railway scaduto — seleziona un piano (Hobby \$5/mese+)."
  echo "  Dashboard: https://railway.app → Workspace → Upgrade / Billing"
  echo "Poi: Account Token fresco → vault RAILWAY_API_TOKEN (togli/rinomina RAILWAY_TOKEN se confonde) → «vai Railway»"
  TRIAL_BLOCKED=1
elif echo "$MUT_JSON" | grep -qi '"serviceCreate"\|"projectCreate"'; then
  # Mutation succeeded — delete probe artifact if we got an id
  PROBE_ID="$(python3 - <<'PY' "$MUT_JSON"
import json,sys
try:
    d=json.loads(sys.argv[1])
    data=d.get("data") or {}
    n=data.get("serviceCreate") or data.get("projectCreate") or {}
    print(n.get("id") or "")
except Exception:
    print("")
PY
)"
  if [[ -n "$PROBE_ID" ]]; then
    echo "INFO probe created id=$PROBE_ID — cleanup best-effort"
    gql "{\"query\":\"mutation { serviceDelete(id: \\\"$PROBE_ID\\\") }\"}" >/dev/null 2>&1 || true
    gql "{\"query\":\"mutation { projectDelete(id: \\\"$PROBE_ID\\\") }\"}" >/dev/null 2>&1 || true
  fi
fi

echo "--- CLI auth ---"
CLI_OK=0
if ! command -v railway >/dev/null 2>&1; then
  echo "WAIT railway CLI non in PATH (deploy script la installa in ~/.railway/bin)"
else
  if [[ -n "$API_TOKEN" && -z "${PROJ_TOKEN:-}" ]]; then
    if RAILWAY_API_TOKEN="$API_TOKEN" railway whoami >/dev/null 2>&1; then
      echo "OK  CLI via RAILWAY_API_TOKEN"
      CLI_OK=1
    else
      echo "FAIL CLI whoami con RAILWAY_API_TOKEN"
      echo "     Vault: metti l'Account Token in RAILWAY_API_TOKEN (non in RAILWAY_TOKEN)."
      echo "     Docs: RAILWAY_TOKEN=project · RAILWAY_API_TOKEN=account/workspace"
    fi
  elif [[ -n "$PROJ_TOKEN" && -z "${API_TOKEN:-}" ]]; then
    echo "INFO solo RAILWAY_TOKEN: deve essere Project Token + progetto già creato"
    if [[ -n "${RAILWAY_PROJECT_ID:-}" ]]; then
      echo "OK  RAILWAY_PROJECT_ID set — ok per railway up"
      CLI_OK=1
    else
      echo "FAIL manca RAILWAY_PROJECT_ID — per bootstrap: RAILWAY_API_TOKEN (Account)"
    fi
  elif [[ -n "$API_TOKEN" && -n "$PROJ_TOKEN" ]]; then
    echo "WARN entrambe settate: CLI privilegia RAILWAY_TOKEN (project)."
    echo "     Per «vai Railway» bootstrap: lascia solo RAILWAY_API_TOKEN nel vault."
    if RAILWAY_TOKEN= RAILWAY_API_TOKEN="$API_TOKEN" railway whoami >/dev/null 2>&1; then
      echo "OK  CLI via RAILWAY_API_TOKEN (ignorando project token)"
      CLI_OK=1
    else
      echo "FAIL CLI whoami anche con solo API token"
    fi
  fi
fi

echo "---"
if [[ "$TRIAL_BLOCKED" -eq 1 ]]; then
  echo "ESITO=BLOCKED — upgrade piano Railway"
  exit 2
fi
if [[ "$CLI_OK" -eq 1 ]]; then
  echo "ESITO=READY — bash scripts/railway-deploy.sh"
  exit 0
fi
echo "ESITO=BLOCKED — token CLI / vault (vedi sopra)"
exit 2
