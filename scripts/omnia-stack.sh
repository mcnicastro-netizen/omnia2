#!/usr/bin/env bash
# OMNIA durable stack — API + production preview (same-origin /api).
# Keeps processes alive across agent edits; auto-restarts on crash.
# Founder access: Cursor Ports → omnia-preview (:43123). Do NOT rely on localtunnel.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_PORT="${API_PORT:-43121}"
PREVIEW_PORT="${PREVIEW_PORT:-43123}"
API_ORIGIN="http://127.0.0.1:${API_PORT}"
LOG_DIR="${LOG_DIR:-/tmp/omnia-stack}"
mkdir -p "$LOG_DIR"

status_file="$LOG_DIR/status.json"
pid_api="$LOG_DIR/api.pid"
pid_preview="$LOG_DIR/preview.pid"

write_status() {
  local api_ok="$1" preview_ok="$2" msg="${3:-}"
  cat >"$status_file" <<EOF
{"ts":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","api_port":$API_PORT,"preview_port":$PREVIEW_PORT,"api_ok":$api_ok,"preview_ok":$preview_ok,"message":$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$msg"),"preview_url":"http://127.0.0.1:${PREVIEW_PORT}","note":"Use Cursor Ports forward on ${PREVIEW_PORT} — avoid localtunnel/cloudflare quick tunnels"}
EOF
}

alive() {
  local pidfile="$1"
  [[ -f "$pidfile" ]] || return 1
  local pid
  pid="$(cat "$pidfile" 2>/dev/null || true)"
  [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null
}

health_http() {
  local url="$1"
  curl -sf --max-time 3 "$url" >/dev/null 2>&1
}

start_api() {
  if alive "$pid_api" && health_http "${API_ORIGIN}/api/"; then
    return 0
  fi
  if alive "$pid_api"; then
    kill "$(cat "$pid_api")" 2>/dev/null || true
    sleep 1
  fi
  # free port if orphaned
  fuser -k "${API_PORT}/tcp" 2>/dev/null || true
  sleep 0.5
  cd "$ROOT/backend"
  if [[ -x .venv/bin/uvicorn ]]; then
    UV=".venv/bin/uvicorn"
  else
    UV="uvicorn"
  fi
  nohup "$UV" server:app --host 0.0.0.0 --port "$API_PORT" --reload \
    >"$LOG_DIR/api.log" 2>&1 &
  echo $! >"$pid_api"
  for _ in $(seq 1 40); do
    health_http "${API_ORIGIN}/api/" && return 0
    sleep 0.5
  done
  return 1
}

ensure_build() {
  if [[ ! -f "$ROOT/frontend/build/index.html" ]]; then
    echo "[omnia-stack] building frontend (missing build/)..."
    (cd "$ROOT/frontend" && REACT_APP_BACKEND_URL= yarn build) >>"$LOG_DIR/build.log" 2>&1
  fi
}

start_preview() {
  ensure_build
  if alive "$pid_preview" && health_http "http://127.0.0.1:${PREVIEW_PORT}/healthz"; then
    return 0
  fi
  if alive "$pid_preview"; then
    kill "$(cat "$pid_preview")" 2>/dev/null || true
    sleep 1
  fi
  fuser -k "${PREVIEW_PORT}/tcp" 2>/dev/null || true
  sleep 0.5
  cd "$ROOT/frontend"
  nohup env PREVIEW_PORT="$PREVIEW_PORT" API_ORIGIN="$API_ORIGIN" \
    node preview-server.js >"$LOG_DIR/preview.log" 2>&1 &
  echo $! >"$pid_preview"
  for _ in $(seq 1 30); do
    health_http "http://127.0.0.1:${PREVIEW_PORT}/healthz" && return 0
    sleep 0.4
  done
  return 1
}

cmd="${1:-ensure}"

case "$cmd" in
  ensure|up|start)
    api_ok=false
    preview_ok=false
    msg=""
    if start_api; then api_ok=true; else msg="api_start_failed"; fi
    if start_preview; then preview_ok=true; else msg="${msg:+$msg;}preview_start_failed"; fi
    write_status "$api_ok" "$preview_ok" "${msg:-ok}"
    echo "[omnia-stack] api_ok=$api_ok preview_ok=$preview_ok → http://127.0.0.1:${PREVIEW_PORT}"
    cat "$status_file"
    [[ "$api_ok" == true && "$preview_ok" == true ]]
    ;;
  watch)
    echo "[omnia-stack] watchdog every 8s (logs: $LOG_DIR)"
    while true; do
      "$0" ensure || true
      sleep 8
    done
    ;;
  status)
    if [[ -f "$status_file" ]]; then cat "$status_file"; else echo '{"error":"not_started"}'; fi
    echo
    echo -n "live api: "; curl -sf -o /dev/null -w '%{http_code}\n' --max-time 3 "${API_ORIGIN}/api/" || echo down
    echo -n "live preview: "; curl -sf -o /dev/null -w '%{http_code}\n' --max-time 3 "http://127.0.0.1:${PREVIEW_PORT}/healthz" || echo down
    ;;
  rebuild)
    echo "[omnia-stack] rebuilding frontend..."
    (cd "$ROOT/frontend" && REACT_APP_BACKEND_URL= yarn build) | tee -a "$LOG_DIR/build.log"
    # static files — no restart required; bounce preview for safety
    if alive "$pid_preview"; then kill "$(cat "$pid_preview")" 2>/dev/null || true; fi
    "$0" ensure
    ;;
  stop)
    alive "$pid_preview" && kill "$(cat "$pid_preview")" 2>/dev/null || true
    alive "$pid_api" && kill "$(cat "$pid_api")" 2>/dev/null || true
    write_status false false stopped
    echo "[omnia-stack] stopped"
    ;;
  *)
    echo "Usage: $0 {ensure|watch|status|rebuild|stop}"
    exit 2
    ;;
esac
