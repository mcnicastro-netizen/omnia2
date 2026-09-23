#!/usr/bin/env bash
# D-086 / D-088 — ensure system deps for Cloud Agents (idempotent).
# Mongo + python3-venv must exist even when the pod did NOT boot from a
# finished Dockerfile environment build (JIT / no_finished_builds).
set -euo pipefail

log() { echo "[ensure-system-deps] $*"; }

need_sudo=0
if [[ "$(id -u)" -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
    need_sudo=1
  fi
fi

run_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  elif [[ "$need_sudo" -eq 1 ]]; then
    sudo -n "$@"
  else
    log "ERROR: need root/sudo to install: $*"
    return 1
  fi
}

ensure_apt_packages() {
  local -a missing=()
  local pkg
  for pkg in "$@"; do
    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
      missing+=("$pkg")
    fi
  done
  if [[ ${#missing[@]} -eq 0 ]]; then
    return 0
  fi
  log "apt-get install: ${missing[*]}"
  run_root env DEBIAN_FRONTEND=noninteractive apt-get update -qq
  run_root env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${missing[@]}"
}

ensure_mongodb_org() {
  if command -v mongod >/dev/null 2>&1; then
    log "mongod already present: $(command -v mongod)"
    return 0
  fi

  log "mongod missing — installing mongodb-org 8.0"
  # Keyring + list (idempotent)
  if [[ ! -f /usr/share/keyrings/mongodb-server-8.0.gpg ]]; then
    curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc \
      | run_root gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor
  fi
  if [[ ! -f /etc/apt/sources.list.d/mongodb-org-8.0.list ]]; then
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse" \
      | run_root tee /etc/apt/sources.list.d/mongodb-org-8.0.list >/dev/null
  fi
  run_root env DEBIAN_FRONTEND=noninteractive apt-get update -qq
  run_root env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq mongodb-org

  if ! command -v mongod >/dev/null 2>&1; then
    log "ERROR: mongod still missing after apt install"
    return 1
  fi
  log "mongod installed: $(mongod --version 2>/dev/null | head -1)"
}

ensure_python_venv() {
  # python3 -m venv needs ensurepip / python3-venv on Ubuntu
  if python3 -c 'import ensurepip' 2>/dev/null; then
    log "python3 ensurepip OK"
    return 0
  fi
  log "python3-venv missing — installing"
  ensure_apt_packages python3.12-venv python3-venv || ensure_apt_packages python3-venv
  if ! python3 -c 'import ensurepip' 2>/dev/null; then
    log "ERROR: ensurepip still unavailable"
    return 1
  fi
}

ensure_mongodb_org
ensure_python_venv
log "done"
