#!/usr/bin/env bash
# D-086 / D-088 — idempotent Cloud Agent install (system deps, venv, pip, yarn, FE build).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Build pods often run install as root while agents boot as ubuntu (environment.json).
# Paths created here must be writable by the runtime user on start.
RUNTIME_USER="${OMNIA_RUNTIME_USER:-ubuntu}"

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

# Seed missing keys from process env or .env.example (no hardcoded secrets in this script).
_env_example_val() {
  local key="$1"
  [[ -f "$ROOT/backend/.env.example" ]] || return 0
  grep -E "^${key}=" "$ROOT/backend/.env.example" | head -1 | cut -d= -f2- || true
}
ensure_env_key "$ROOT/backend/.env" "ADMIN_EMAIL" "${ADMIN_EMAIL:-$(_env_example_val ADMIN_EMAIL)}"
ensure_env_key "$ROOT/backend/.env" "ADMIN_PASSWORD" "${ADMIN_PASSWORD:-$(_env_example_val ADMIN_PASSWORD)}"
ensure_env_key "$ROOT/backend/.env" "DEMO_ADMIN_PASSWORD" "${DEMO_ADMIN_PASSWORD:-$(_env_example_val DEMO_ADMIN_PASSWORD)}"
ensure_env_key "$ROOT/backend/.env" "JWT_SECRET" "${JWT_SECRET:-change-me-to-a-long-random-string}"

# Origin-tmp agents get Origin git auth only. When GITHUB_TOKEN is set as an
# Environment secret, wire push access to the real omnia2 GitHub repo.
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  git -C "$ROOT" config --global \
    "url.https://x-access-token:${GITHUB_TOKEN}@github.com/.insteadOf" \
    "https://github.com/"
  if git -C "$ROOT" remote get-url github >/dev/null 2>&1; then
    git -C "$ROOT" remote set-url github "https://github.com/mcnicastro-netizen/omnia2.git"
  else
    git -C "$ROOT" remote add github "https://github.com/mcnicastro-netizen/omnia2.git"
  fi
  echo "[cloud-agent-install] github remote wired via GITHUB_TOKEN → omnia2"
else
  echo "[cloud-agent-install] WARN: GITHUB_TOKEN missing — cannot push to GitHub omnia2 from this Origin-backed agent"
fi

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

# If install ran as root, hand runtime paths to ubuntu so start can write
# mongod journal + vault materialize into backend/.env.
if [[ "$(id -u)" -eq 0 ]] && id "$RUNTIME_USER" >/dev/null 2>&1; then
  echo "[cloud-agent-install] chown runtime paths → ${RUNTIME_USER}"
  chown -R "${RUNTIME_USER}:${RUNTIME_USER}" \
    "$ROOT/.mongo-data" \
    "$ROOT/backend/.env" \
    "$ROOT/frontend/.env" \
    "$ROOT/backend/.venv" \
    "$ROOT/frontend/node_modules" \
    "$ROOT/frontend/build" \
    2>/dev/null || true
  # Keep repo tree usable for the agent user when checkout was root-owned.
  chown -R "${RUNTIME_USER}:${RUNTIME_USER}" "$ROOT" 2>/dev/null || true
fi

echo "[cloud-agent-install] done"
