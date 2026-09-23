#!/usr/bin/env bash
# D-086 / D-088 — idempotent Cloud Agent install (system deps, venv, pip, yarn, FE build).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p "$ROOT/.mongo-data"

# Belt-and-suspenders: Dockerfile *should* ship mongod, but JIT pods and
# environments with no_finished_builds often do not. Never fail later in start.
bash "$ROOT/scripts/ensure-system-deps.sh"

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
ensure_env_key "$ROOT/backend/.env" "ADMIN_EMAIL" "[REDACTED]"
ensure_env_key "$ROOT/backend/.env" "ADMIN_PASSWORD" "[REDACTED]"
ensure_env_key "$ROOT/backend/.env" "DEMO_ADMIN_PASSWORD" "OmniaDemo2026!"
ensure_env_key "$ROOT/backend/.env" "JWT_SECRET" "change-me-to-a-long-random-string"

echo "[cloud-agent-install] python venv + pip"
cd "$ROOT/backend"
if [[ ! -x .venv/bin/python ]]; then
  rm -rf .venv
  python3 -m venv .venv
fi
"$ROOT/backend/.venv/bin/pip" install -q -U pip
"$ROOT/backend/.venv/bin/pip" install -q -r "$ROOT/backend/requirements.txt"

echo "[cloud-agent-install] yarn install + production build"
cd "$ROOT/frontend"
if [[ ! -d node_modules/express ]]; then
  yarn install --frozen-lockfile
fi
if [[ ! -f build/index.html ]]; then
  REACT_APP_BACKEND_URL= yarn build
fi

echo "[cloud-agent-install] done"
