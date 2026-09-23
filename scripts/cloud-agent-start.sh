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
append_if_missing "$ROOT/backend/.env" "ADMIN_EMAIL" "[REDACTED]"
append_if_missing "$ROOT/backend/.env" "ADMIN_PASSWORD" "[REDACTED]"
append_if_missing "$ROOT/backend/.env" "DEMO_ADMIN_PASSWORD" "OmniaDemo2026!"

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

if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  echo "[cloud-agent-start] seed demo gestionale"
  "$ROOT/backend/.venv/bin/python" "$ROOT/backend/scripts/seed_demo_gestionale.py" \
    || echo "[cloud-agent-start] seed demo skipped/failed (non-fatal)" >&2
fi

echo "[cloud-agent-start] done"
