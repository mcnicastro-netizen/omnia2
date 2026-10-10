#!/usr/bin/env bash
# D-086 / D-088 — per-boot Cloud Agent start: system deps + Mongo + stack + seed.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p /tmp/omnia-stack

# Prefer repo dbpath; fall back when install left it root-owned (no passwordless sudo).
MONGO_DBPATH="$ROOT/.mongo-data"
mkdir -p "$MONGO_DBPATH" 2>/dev/null || true
if ! touch "$MONGO_DBPATH/.omnia_write_test" 2>/dev/null; then
  MONGO_DBPATH="/tmp/omnia-mongo-data"
  mkdir -p "$MONGO_DBPATH"
  echo "[cloud-agent-start] WARN: $ROOT/.mongo-data not writable — using $MONGO_DBPATH" >&2
else
  rm -f "$MONGO_DBPATH/.omnia_write_test"
fi

ENV_FILE="$ROOT/backend/.env"
if [[ ! -f "$ENV_FILE" && -f "$ROOT/backend/.env.example" ]]; then
  if cp "$ROOT/backend/.env.example" "$ENV_FILE" 2>/dev/null; then
    :
  else
    ENV_FILE="/tmp/omnia-backend.env"
    cp "$ROOT/backend/.env.example" "$ENV_FILE"
    echo "[cloud-agent-start] WARN: cannot create backend/.env — using $ENV_FILE" >&2
  fi
elif [[ -f "$ENV_FILE" && ! -w "$ENV_FILE" ]]; then
  # Build install as root can leave .env unwritable for ubuntu.
  cp "$ENV_FILE" /tmp/omnia-backend.env
  chmod u+rw /tmp/omnia-backend.env
  ENV_FILE="/tmp/omnia-backend.env"
  export OMNIA_ENV_FILE="$ENV_FILE"
  echo "[cloud-agent-start] WARN: backend/.env not writable — materialize → $ENV_FILE" >&2
fi
if [[ ! -f "$ROOT/frontend/.env" && -f "$ROOT/frontend/.env.example" ]]; then
  cp "$ROOT/frontend/.env.example" "$ROOT/frontend/.env" 2>/dev/null || true
fi

append_if_missing() {
  local file="$1" key="$2" val="$3"
  [[ -f "$file" && -w "$file" ]] || return 0
  if ! grep -qE "^${key}=" "$file"; then
    printf '%s=%s\n' "$key" "$val" >>"$file"
  fi
}
# Defaults from process env / .env.example (never hardcode Founder email here —
# Cursor secret scan treats OPENAPI_EMAIL vault value as a blocked literal).
_default_admin_email="${ADMIN_EMAIL:-}"
if [[ -z "$_default_admin_email" && -f "$ROOT/backend/.env.example" ]]; then
  _default_admin_email="$(grep -E '^ADMIN_EMAIL=' "$ROOT/backend/.env.example" | head -1 | cut -d= -f2- || true)"
fi
_default_admin_password="${ADMIN_PASSWORD:-OmniaFounder2026!}"
_default_demo_password="${DEMO_ADMIN_PASSWORD:-OmniaDemo2026!}"
[[ -n "$_default_admin_email" ]] && append_if_missing "$ENV_FILE" "ADMIN_EMAIL" "$_default_admin_email"
append_if_missing "$ENV_FILE" "ADMIN_PASSWORD" "$_default_admin_password"
append_if_missing "$ENV_FILE" "DEMO_ADMIN_PASSWORD" "$_default_demo_password"
# S9 / D-120 — O6 PASS: rubinetto B2B ON (Stripe mode resta indipendente)
if [[ -f "$ENV_FILE" && -w "$ENV_FILE" ]]; then
  if grep -qE '^OMNIA_SELF_SERVE_ENABLED=' "$ENV_FILE"; then
    sed -i 's/^OMNIA_SELF_SERVE_ENABLED=.*/OMNIA_SELF_SERVE_ENABLED=true/' "$ENV_FILE"
  else
    append_if_missing "$ENV_FILE" "OMNIA_SELF_SERVE_ENABLED" "true"
  fi
fi

# Vault → .env (Stripe test prefer + OPENAPI_* + AI mail keys; never echo values)
if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  set +e
  if [[ -w "$ENV_FILE" ]]; then
    "$ROOT/backend/.venv/bin/python" "$ROOT/scripts/stripe-vault-materialize.py" "$ENV_FILE"
    _stripe_mat=$?
  else
    echo "[cloud-agent-start] WARN: skip stripe vault materialize ($ENV_FILE not writable)" >&2
    _stripe_mat=0
  fi
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
  echo "[cloud-agent-start] starting mongod (dbpath=$MONGO_DBPATH)"
  mongod \
    --dbpath "$MONGO_DBPATH" \
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
    --share-file /tmp/omnia-stack/SHARE_URL.txt --env "$ENV_FILE" || true
  "$ROOT/backend/.venv/bin/python" "$ROOT/scripts/sync-stripe-webhook-url.py" \
    --share-file /tmp/omnia-stack/SHARE_URL.txt || true
  set -e
fi

# Integrity: report secret presence (names only). Non-fatal.
# NEVER backfill STRIPE_* from .env into process (stale live risk).
if [[ -f "$ROOT/scripts/check-secrets-presence.sh" ]]; then
  set +e
  if [[ -f "$ENV_FILE" ]]; then
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
    done < "$ENV_FILE"
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
