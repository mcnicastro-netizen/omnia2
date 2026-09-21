#!/usr/bin/env bash
# D-086 — idempotent Cloud Agent install (venv, pip, yarn, FE build).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p "$ROOT/.mongo-data"

ensure_env() {
  local example="$1" dest="$2"
  if [[ ! -f "$dest" && -f "$example" ]]; then
    cp "$example" "$dest"
    echo "[cloud-agent-install] created $dest from example"
  fi
}

ensure_env_key() {
  local file="$1" key="$2" val="$3"
  [[ -f "$file" ]] || return 0
  if ! grep -qE "^${key}=" "$file"; then
    printf '%s=%s\n' "$key" "$val" >>"$file"
    echo "[cloud-agent-install] appended $key to $file"
  fi
}

ensure_env "$ROOT/backend/.env.example" "$ROOT/backend/.env"
ensure_env "$ROOT/frontend/.env.example" "$ROOT/frontend/.env"
ensure_env_key "$ROOT/backend/.env" "ADMIN_EMAIL" "mcnicastro@gmail.com"
ensure_env_key "$ROOT/backend/.env" "ADMIN_PASSWORD" "OmniaFounder2026!"
ensure_env_key "$ROOT/backend/.env" "DEMO_ADMIN_PASSWORD" "OmniaDemo2026!"
ensure_env_key "$ROOT/backend/.env" "JWT_SECRET" "change-me-to-a-long-random-string"

echo "[cloud-agent-install] python venv + pip"
cd "$ROOT/backend"
python3 -m venv .venv
"$ROOT/backend/.venv/bin/pip" install -q -U pip
"$ROOT/backend/.venv/bin/pip" install -q -r "$ROOT/backend/requirements.txt"

echo "[cloud-agent-install] yarn install + production build"
cd "$ROOT/frontend"
yarn install --frozen-lockfile
REACT_APP_BACKEND_URL= yarn build

echo "[cloud-agent-install] done"
