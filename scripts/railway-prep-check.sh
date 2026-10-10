#!/usr/bin/env bash
# Pre-check: repo ready for Railway API deploy (no token required).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fail=0
ok() { echo "OK  $*"; }
bad() { echo "FAIL $*"; fail=1; }

echo "=== railway-prep-check ==="

[[ -f "$ROOT/railway.toml" ]] && ok "railway.toml" || bad "missing railway.toml"
[[ -f "$ROOT/Dockerfile.railway" ]] && ok "Dockerfile.railway (root)" || bad "missing Dockerfile.railway"
[[ -f "$ROOT/backend/server.py" ]] && ok "backend/server.py" || bad "missing server.py"
[[ -f "$ROOT/backend/requirements.txt" ]] && ok "requirements.txt" || bad "missing requirements"
[[ -f "$ROOT/docs/ops/RAILWAY_DEPLOY.md" ]] && ok "RAILWAY_DEPLOY.md" || bad "missing runbook"

grep -q 'dockerfilePath = "Dockerfile.railway"' "$ROOT/railway.toml" && ok "railway.toml → Dockerfile.railway" || bad "toml dockerfile path"
grep -q '/api/health' "$ROOT/railway.toml" && ok "healthcheck /api/health" || bad "healthcheck path"
grep -q 'uvicorn server:app' "$ROOT/Dockerfile.railway" && ok "CMD uvicorn server:app" || bad "CMD"
grep -q 'COPY backend/' "$ROOT/Dockerfile.railway" && ok "build context copies backend/" || bad "COPY backend missing"

echo "--- vault (presence only) ---"
for k in RAILWAY_API_TOKEN RAILWAY_TOKEN RAILWAY_PROJECT_ID OMNIA_API_PUBLIC_URL; do
  if [[ -n "${!k:-}" ]]; then ok "env $k is set"; else echo "WAIT $k not set (ok for prep)"; fi
done

echo "---"
if [[ "$fail" -eq 0 ]]; then
  echo "ESITO=PASS — dopo RAILWAY_API_TOKEN in vault → «vai Railway»"
  exit 0
fi
echo "ESITO=FAIL"
exit 1
