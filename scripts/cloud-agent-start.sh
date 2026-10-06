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

# Materialize Cloud Agent vault → backend/.env BEFORE stack boot.
# uvicorn + load_dotenv must see the same values; never echo secret values.
upsert_env_key() {
  local file="$1" key="$2"
  local val="${!key:-}"
  [[ -n "$val" ]] || return 0
  [[ -f "$file" ]] || touch "$file"
  python3 - "$file" "$key" "$val" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
key = sys.argv[2]
val = sys.argv[3]
lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
out = []
found = False
prefix = key + "="
commented = "#" + prefix
for line in lines:
    stripped = line.lstrip()
    if stripped.startswith(prefix) or stripped.startswith(commented):
        if not found:
            out.append(f"{key}={val}")
            found = True
        # drop duplicate key lines
        continue
    out.append(line)
if not found:
    out.append(f"{key}={val}")
path.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
}

# Prefer process/vault over template .env (D-Secrets / Stripe sandbox).
for _k in \
  RESEND_API_KEY GEMINI_API_KEY GOOGLE_API_KEY EMERGENT_LLM_KEY FAL_KEY \
  TAVILY_API_KEY JWT_SECRET GOOGLE_CLIENT_ID \
  STRIPE_SECRET_KEY STRIPE_PUBLISHABLE_KEY STRIPE_PUBLIC_KEY \
  STRIPE_WEBHOOK_SECRET STRIPE_ENABLED STRIPE_MODE
do
  upsert_env_key "$ROOT/backend/.env" "$_k"
done

# Auto-enable sandbox when sk_test_ is in vault and STRIPE_ENABLED still false/empty.
if [[ -n "${STRIPE_SECRET_KEY:-}" && "${STRIPE_SECRET_KEY}" == sk_test_* ]]; then
  if [[ "${STRIPE_ENABLED:-}" != "true" ]]; then
    export STRIPE_ENABLED=true
    upsert_env_key "$ROOT/backend/.env" "STRIPE_ENABLED"
  fi
  if [[ -z "${STRIPE_MODE:-}" ]]; then
    export STRIPE_MODE=test
    upsert_env_key "$ROOT/backend/.env" "STRIPE_MODE"
  fi
fi
# Alias publishable
if [[ -z "${STRIPE_PUBLISHABLE_KEY:-}" && -n "${STRIPE_PUBLIC_KEY:-}" ]]; then
  export STRIPE_PUBLISHABLE_KEY="$STRIPE_PUBLIC_KEY"
  upsert_env_key "$ROOT/backend/.env" "STRIPE_PUBLISHABLE_KEY"
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

# Integrity: report secret presence (names only). Non-fatal — empty vault ≠ deleted keys.
if [[ -f "$ROOT/scripts/check-secrets-presence.sh" ]]; then
  set +e
  # Fill gaps from .env only when process env empty (vault already wins via upsert above)
  if [[ -f "$ROOT/backend/.env" ]]; then
    while IFS= read -r line; do
      case "$line" in
        RESEND_API_KEY=*|GEMINI_API_KEY=*|GOOGLE_API_KEY=*|EMERGENT_LLM_KEY=*|FAL_KEY=*|TAVILY_API_KEY=*|STRIPE_SECRET_KEY=*|STRIPE_PUBLISHABLE_KEY=*|STRIPE_ENABLED=*|STRIPE_MODE=*|GOOGLE_CLIENT_ID=*|JWT_SECRET=*)
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
