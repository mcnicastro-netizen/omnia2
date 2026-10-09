#!/usr/bin/env bash
# D-086 / D-088 — per-boot Cloud Agent start: system deps + Mongo + stack + seed.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p "$ROOT/.mongo-data" /tmp/omnia-stack

if [[ ! -f "$ROOT/backend/.env" && -f "$ROOT/backend/.env.example" ]]; then
  cp "$ROOT/backend/.env.example" "$ROOT/backend/.env"
fi
if [[ ! -f "$ROOT/frontend/.env" && -f "$ROOT/frontend/.env.example" ]]; then
  cp "$ROOT/frontend/.env.example" "$ROOT/frontend/.env"
fi

append_if_missing() {
  local file="$1" key="$2" val="$3"
  [[ -f "$file" ]] || return 0
  if ! grep -qE "^${key}=" "$file"; then
    printf '%s=%s\n' "$key" "$val" >>"$file"
  fi
}
append_if_missing "$ROOT/backend/.env" "ADMIN_EMAIL" "mcnicastro@gmail.com"
append_if_missing "$ROOT/backend/.env" "ADMIN_PASSWORD" "OmniaFounder2026!"
append_if_missing "$ROOT/backend/.env" "DEMO_ADMIN_PASSWORD" "OmniaDemo2026!"

# Vault → .env (Stripe test prefer + OPENAPI_* + AI mail keys; never echo values)
if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  set +e
  "$ROOT/backend/.venv/bin/python" "$ROOT/scripts/stripe-vault-materialize.py" "$ROOT/backend/.env"
  _stripe_mat=$?
  set -e
  if [[ "$_stripe_mat" -eq 2 ]]; then
    echo "[cloud-agent-start] Stripe materialize: live/mixed keys (sandbox not auto-enabled)" >&2
  fi
else
  echo "[cloud-agent-start] WARN: backend venv missing — skip stripe vault materialize" >&2
fi

# If install was skipped / snapshot lacked mongod, recover here before exit 1.
bash "$ROOT/scripts/ensure-system-deps.sh"

if ! command -v mongod >/dev/null 2>&1; then
  echo "[cloud-agent-start] ERROR: mongod not in PATH after ensure-system-deps" >&2
  exit 1
fi

if ! pgrep -x mongod >/dev/null 2>&1; then
  echo "[cloud-agent-start] starting mongod"
  mongod \
    --dbpath "$ROOT/.mongo-data" \
    --bind_ip 127.0.0.1 \
    --port 27017 \
    --logpath /tmp/mongod.log \
    --fork
fi

mongo_ready=0
for _i in $(seq 1 40); do
  if python3 - <<'PY' 2>/dev/null
import socket
s = socket.create_connection(("127.0.0.1", 27017), 1)
s.close()
PY
  then
    mongo_ready=1
    break
  fi
  sleep 0.25
done
if [[ "$mongo_ready" != 1 ]]; then
  echo "[cloud-agent-start] ERROR: mongod did not accept connections" >&2
  tail -n 40 /tmp/mongod.log >&2 || true
  exit 1
fi

bash "$ROOT/scripts/omnia-stack.sh" ensure

# Re-sync public URLs + webhook after ensure (tunnel may have just come up)
if [[ -x "$ROOT/backend/.venv/bin/python" && -f /tmp/omnia-stack/SHARE_URL.txt ]]; then
  set +e
  "$ROOT/backend/.venv/bin/python" "$ROOT/scripts/sync-public-base-url.py" \
    --share-file /tmp/omnia-stack/SHARE_URL.txt --env "$ROOT/backend/.env" || true
  "$ROOT/backend/.venv/bin/python" "$ROOT/scripts/sync-stripe-webhook-url.py" \
    --share-file /tmp/omnia-stack/SHARE_URL.txt || true
  set -e
fi

# Integrity: report secret presence (names only). Non-fatal.
# NEVER backfill STRIPE_* from .env into process (stale live risk).
if [[ -f "$ROOT/scripts/check-secrets-presence.sh" ]]; then
  set +e
  if [[ -f "$ROOT/backend/.env" ]]; then
    while IFS= read -r line; do
      case "$line" in
        RESEND_API_KEY=*|GEMINI_API_KEY=*|GOOGLE_API_KEY=*|EMERGENT_LLM_KEY=*|FAL_KEY=*|TAVILY_API_KEY=*|GOOGLE_CLIENT_ID=*|JWT_SECRET=*|OPENAPI_*)
          key="${line%%=*}"
          val="${line#*=}"
          if [[ -z "${!key:-}" ]]; then
            export "$key=$val"
          fi
          ;;
      esac
    done < "$ROOT/backend/.env"
  fi
  bash "$ROOT/scripts/check-secrets-presence.sh" || true
  set -e
fi

if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  echo "[cloud-agent-start] seed demo gestionale"
  "$ROOT/backend/.venv/bin/python" "$ROOT/backend/scripts/seed_demo_gestionale.py" \
    || echo "[cloud-agent-start] seed demo skipped/failed (non-fatal)" >&2
  echo "[cloud-agent-start] seed Nicastroimmobiliare (cliente-1)"
  "$ROOT/backend/.venv/bin/python" "$ROOT/backend/scripts/seed_nicastro_agency.py" \
    || echo "[cloud-agent-start] seed nicastro skipped/failed (non-fatal)" >&2
fi

echo "[cloud-agent-start] done"
