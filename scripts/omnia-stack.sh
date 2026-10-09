#!/usr/bin/env bash
# OMNIA durable stack — API + production preview (same-origin /api) + public tunnel.
# Adopts already-healthy listeners; never kills a working port.
# Share: https://<trycloudflare>.trycloudflare.com  (no Cursor Port Forward needed)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_PORT="${API_PORT:-43121}"
PREVIEW_PORT="${PREVIEW_PORT:-43123}"
API_ORIGIN="http://127.0.0.1:${API_PORT}"
LOG_DIR="${LOG_DIR:-/tmp/omnia-stack}"
CLOUDFLARED_BIN="${CLOUDFLARED_BIN:-}"
ENABLE_TUNNEL="${ENABLE_TUNNEL:-1}"
mkdir -p "$LOG_DIR"

status_file="$LOG_DIR/status.json"
share_file="$LOG_DIR/SHARE_URL.txt"
pid_api="$LOG_DIR/api.pid"
pid_preview="$LOG_DIR/preview.pid"
pid_tunnel="$LOG_DIR/cloudflared.pid"
tunnel_log="$LOG_DIR/cloudflared.log"

resolve_cloudflared() {
  if [[ -n "$CLOUDFLARED_BIN" && -x "$CLOUDFLARED_BIN" ]]; then
    echo "$CLOUDFLARED_BIN"
    return 0
  fi
  if command -v cloudflared >/dev/null 2>&1; then
    command -v cloudflared
    return 0
  fi
  for candidate in /tmp/cloudflared "$ROOT/scripts/bin/cloudflared" "$HOME/.local/bin/cloudflared"; do
    if [[ -x "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

ensure_cloudflared_bin() {
  local bin
  if bin="$(resolve_cloudflared)"; then
    printf '%s\n' "$bin"
    return 0
  fi
  echo "[omnia-stack] downloading cloudflared → /tmp/cloudflared" >&2
  curl -fsSL -o /tmp/cloudflared \
    "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
  chmod +x /tmp/cloudflared
  printf '%s\n' /tmp/cloudflared
}

# P-019 / P-018 — after a healthy tunnel URL: sync FRONTEND_* + optional Stripe webhook
sync_runtime_public_urls() {
  local public_url="$1"
  [[ -n "${public_url:-}" ]] || return 0
  local py="${ROOT}/backend/.venv/bin/python"
  [[ -x "$py" ]] || py="python3"
  local changed=0
  if [[ -f "$ROOT/scripts/sync-public-base-url.py" ]]; then
    local out
    out="$("$py" "$ROOT/scripts/sync-public-base-url.py" --url "$public_url" --env "$ROOT/backend/.env" 2>&1 || true)"
    echo "$out" | sed 's/^/[omnia-stack] /' >&2 || true
    if echo "$out" | grep -q 'CHANGED=1'; then
      changed=1
    fi
  fi
  if [[ -f "$ROOT/scripts/sync-stripe-webhook-url.py" ]]; then
    "$py" "$ROOT/scripts/sync-stripe-webhook-url.py" --url "$public_url" 2>&1 \
      | sed 's/^/[omnia-stack] /' >&2 || true
  fi
  # Uvicorn --reload does not re-read env; bounce API only when public base URL changed
  if [[ "$changed" == "1" ]]; then
    echo "[omnia-stack] public base URL changed — restarting API so FRONTEND_* take effect" >&2
    if [[ -f "$pid_api" ]]; then
      kill "$(cat "$pid_api")" 2>/dev/null || true
      rm -f "$pid_api"
    fi
    adopt_or_start_api || true
  fi
}

write_status() {
  local api_ok="$1" preview_ok="$2" tunnel_ok="$3" public_url="$4" msg="${5:-}"
  python3 - "$status_file" "$API_PORT" "$PREVIEW_PORT" "$api_ok" "$preview_ok" "$tunnel_ok" "$public_url" "$msg" <<'PY'
import json, sys
from datetime import datetime, timezone
path, api_port, preview_port, api_ok, preview_ok, tunnel_ok, public_url, msg = sys.argv[1:]
payload = {
  "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
  "api_port": int(api_port),
  "preview_port": int(preview_port),
  "api_ok": api_ok == "true",
  "preview_ok": preview_ok == "true",
  "tunnel_ok": tunnel_ok == "true",
  "message": msg,
  "preview_url": f"http://127.0.0.1:{preview_port}",
  "public_url": public_url or None,
  "crm_login_url": f"{public_url}/it/login" if public_url else f"http://127.0.0.1:{preview_port}/it/login",
  "note": "Public share = public_url (cloudflared). Local = preview_url. No Port Forward trafila.",
}
with open(path, "w", encoding="utf-8") as f:
  json.dump(payload, f, ensure_ascii=False)
  f.write("\n")
PY
  if [[ -n "${public_url:-}" ]]; then
    printf '%s\n' "$public_url" >"$share_file"
    printf '%s/it/login\n' "$public_url" >"$LOG_DIR/CRM_LOGIN_URL.txt"
    if [[ "$tunnel_ok" == "true" ]]; then
      sync_runtime_public_urls "$public_url"
    fi
  fi
}

port_pids() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
  else
    fuser "${port}/tcp" 2>/dev/null | tr -s ' ' '\n' | grep -E '^[0-9]+$' || true
  fi
}

health_http() {
  local url="$1"
  curl -sf --max-time 3 "$url" >/dev/null 2>&1
}

read_public_url() {
  if [[ -f "$share_file" ]]; then
    local u
    u="$(tr -d '[:space:]' <"$share_file" || true)"
    if [[ "$u" =~ ^https://[a-z0-9-]+\.trycloudflare\.com$ ]]; then
      echo "$u"
      return 0
    fi
  fi
  if [[ -f "$tunnel_log" ]]; then
    grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$tunnel_log" | tail -n1 || true
  fi
}

tunnel_alive() {
  local url="$1"
  [[ -n "$url" ]] || return 1
  # Cluster DNS often prefers broken IPv6 for *.trycloudflare.com — force A + resolve
  local host ip
  host="${url#https://}"
  host="${host%%/*}"
  if command -v dig >/dev/null 2>&1; then
    ip="$(dig @1.1.1.1 +short "$host" A 2>/dev/null | head -n1 || true)"
  fi
  local probe="${url}/it/login"
  if [[ -n "${ip:-}" ]]; then
    curl -4 -sf --max-time 8 --resolve "${host}:443:${ip}" "$probe" >/dev/null 2>&1
  else
    curl -4 -sf --max-time 8 "$probe" >/dev/null 2>&1
  fi
}

adopt_or_start_api() {
  if health_http "${API_ORIGIN}/api/"; then
    local p
    p="$(port_pids "$API_PORT" | head -n1 || true)"
    [[ -n "${p:-}" ]] && echo "$p" >"$pid_api"
    return 0
  fi
  local pids
  pids="$(port_pids "$API_PORT" || true)"
  if [[ -n "${pids:-}" ]]; then
    echo "[omnia-stack] api unhealthy — restarting pids: $pids"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 1
  fi
  cd "$ROOT/backend"
  local UV
  if [[ -x .venv/bin/uvicorn ]]; then UV=".venv/bin/uvicorn"; else UV="uvicorn"; fi
  nohup "$UV" server:app --host 0.0.0.0 --port "$API_PORT" --reload \
    >>"$LOG_DIR/api.log" 2>&1 &
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
  # Guard: never serve a SPA that calls the developer's localhost API
  if rg -q '127\.0\.0\.1:43121' "$ROOT/frontend/build/static/js/main."*.js 2>/dev/null; then
    echo "[omnia-stack] stale build bakes localhost API — rebuilding with same-origin /api..."
    (cd "$ROOT/frontend" && REACT_APP_BACKEND_URL= yarn build) >>"$LOG_DIR/build.log" 2>&1
  fi
}

adopt_or_start_preview() {
  ensure_build
  if health_http "http://127.0.0.1:${PREVIEW_PORT}/healthz" \
    || health_http "http://127.0.0.1:${PREVIEW_PORT}/"; then
    local p
    p="$(port_pids "$PREVIEW_PORT" | head -n1 || true)"
    [[ -n "${p:-}" ]] && echo "$p" >"$pid_preview"
    return 0
  fi
  local pids
  pids="$(port_pids "$PREVIEW_PORT" || true)"
  if [[ -n "${pids:-}" ]]; then
    echo "[omnia-stack] preview unhealthy — restarting pids: $pids"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 1
  fi
  cd "$ROOT/frontend"
  nohup env PREVIEW_PORT="$PREVIEW_PORT" API_ORIGIN="$API_ORIGIN" \
    CRM_PUBLIC_PREVIEW="${CRM_PUBLIC_PREVIEW:-0}" \
    node preview-server.js >>"$LOG_DIR/preview.log" 2>&1 &
  echo $! >"$pid_preview"
  for _ in $(seq 1 30); do
    health_http "http://127.0.0.1:${PREVIEW_PORT}/healthz" && return 0
    sleep 0.4
  done
  return 1
}

restart_preview() {
  local pids
  pids="$(port_pids "$PREVIEW_PORT" || true)"
  if [[ -n "${pids:-}" ]]; then
    echo "[omnia-stack] restarting preview pids: $pids"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 1
  fi
  adopt_or_start_preview
}

tunnel_process_pids() {
  pgrep -f "cloudflared tunnel --url http://127.0.0.1:${PREVIEW_PORT}" 2>/dev/null || true
}

adopt_or_start_tunnel() {
  if [[ "$ENABLE_TUNNEL" != "1" ]]; then
    printf '\n'
    return 0
  fi

  local existing="" running=""
  running="$(tunnel_process_pids | head -n1 || true)"
  existing="$(read_public_url || true)"

  # Prefer a live cloudflared process only if its URL still answers (P-002).
  if [[ -n "${running:-}" ]]; then
    echo "$running" >"$pid_tunnel"
    if [[ -z "${existing:-}" ]]; then
      existing="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$tunnel_log" 2>/dev/null | tail -n1 || true)"
    fi
    if [[ -n "${existing:-}" ]] && tunnel_alive "$existing"; then
      printf '%s\n' "$existing" >"$share_file"
      printf '%s/it/login\n' "$existing" >"$LOG_DIR/CRM_LOGIN_URL.txt"
      printf '%s\n' "$existing"
      return 0
    fi
    if [[ -n "${existing:-}" ]]; then
      echo "[omnia-stack] tunnel process up but URL stale (${existing}) — restarting" >&2
      # shellcheck disable=SC2086
      kill $running 2>/dev/null || true
      sleep 1
      running=""
      existing=""
      rm -f "$share_file" 2>/dev/null || true
    fi
  fi

  if [[ -n "${existing:-}" ]] && tunnel_alive "$existing"; then
    local tp
    tp="$(tunnel_process_pids | head -n1 || true)"
    [[ -n "${tp:-}" ]] && echo "$tp" >"$pid_tunnel"
    printf '%s\n' "$existing"
    return 0
  fi

  if [[ -n "${running:-}" ]]; then
    echo "[omnia-stack] tunnel process up but no URL yet — waiting" >&2
    local url=""
    for _ in $(seq 1 20); do
      url="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$tunnel_log" 2>/dev/null | tail -n1 || true)"
      if [[ -n "$url" ]] && tunnel_alive "$url"; then
        printf '%s\n' "$url"
        return 0
      fi
      sleep 0.5
    done
  fi

  local old
  old="$(tunnel_process_pids || true)"
  if [[ -n "${old:-}" ]]; then
    echo "[omnia-stack] tunnel without healthy URL — restarting: $old" >&2
    # shellcheck disable=SC2086
    kill $old 2>/dev/null || true
    sleep 1
  fi

  local bin
  bin="$(ensure_cloudflared_bin)"
  : >"$tunnel_log"
  # Prefer HTTP/2: QUIC quick tunnels often return Cloudflare 530 in this env
  nohup "$bin" tunnel --url "http://127.0.0.1:${PREVIEW_PORT}" \
    --protocol http2 \
    --ha-connections 1 \
    >>"$tunnel_log" 2>&1 &
  echo $! >"$pid_tunnel"

  local url=""
  local i
  for i in $(seq 1 40); do
    url="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$tunnel_log" | tail -n1 || true)"
    if [[ -n "$url" ]]; then
      # give the connector a moment; do not require health for return
      if tunnel_alive "$url" || [[ "$i" -gt 12 ]]; then
        printf '%s\n' "$url"
        return 0
      fi
    fi
    sleep 0.5
  done
  if [[ -n "$url" ]]; then
    printf '%s\n' "$url"
    return 0
  fi
  return 1
}

print_share() {
  local url="$1"
  echo
  echo "════════════════════════════════════════════════════════"
  echo "  OMNIA pubblico (condivisibile — niente Port Forward)"
  if [[ -n "$url" ]]; then
    echo "  Portale / app:  $url"
    echo "  CRM login:      $url/it/login"
    echo "  QC dashboard:   $url/it/app/dashboard   (CRM_PUBLIC_PREVIEW auto-session)"
    echo "  QC screenshot:  $url/_qc/"
    echo "  (salvato in $share_file)"
  else
    echo "  Tunnel non attivo — usa ENABLE_TUNNEL=1 $0 ensure"
    echo "  Locale: http://127.0.0.1:${PREVIEW_PORT}/it/login"
  fi
  echo "════════════════════════════════════════════════════════"
}

# P-031 — if public search is empty, re-run demo seeds (visibility=public).
ensure_portal_inventory() {
  local py total
  [[ "${api_ok:-false}" == true ]] || return 0
  if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then py="$ROOT/backend/.venv/bin/python"
  else py="python3"; fi
  total="$("$py" - <<'PY' 2>/dev/null || echo 0
import json, urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:43121/api/cloud/search?limit=1", timeout=5) as r:
        print(int(json.load(r).get("total") or 0))
except Exception:
    print(0)
PY
)"
  total="${total//[^0-9]/}"
  total="${total:-0}"
  if [[ "$total" -gt 0 ]]; then
    echo "[omnia-stack] portal inventory ok total=$total"
    return 0
  fi
  echo "[omnia-stack] portal inventory empty — re-seeding demo + nicastro (P-031)" >&2
  "$py" "$ROOT/backend/scripts/seed_demo_gestionale.py" \
    || echo "[omnia-stack] seed demo failed (non-fatal)" >&2
  "$py" "$ROOT/backend/scripts/seed_nicastro_agency.py" \
    || echo "[omnia-stack] seed nicastro failed (non-fatal)" >&2
  total="$("$py" - <<'PY' 2>/dev/null || echo 0
import json, urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:43121/api/cloud/search?limit=1", timeout=5) as r:
        print(int(json.load(r).get("total") or 0))
except Exception:
    print(0)
PY
)"
  total="${total//[^0-9]/}"
  echo "[omnia-stack] portal inventory after seed total=${total:-0}"
}

cmd="${1:-ensure}"

case "$cmd" in
  ensure|up|start)
    api_ok=false
    preview_ok=false
    tunnel_ok=false
    public_url=""
    msg=""
    if adopt_or_start_api; then api_ok=true; else msg="api_start_failed"; fi
    if [[ "$api_ok" == true ]]; then ensure_portal_inventory || true; fi
    if adopt_or_start_preview; then preview_ok=true; else msg="${msg:+$msg;}preview_start_failed"; fi
    if [[ "$preview_ok" == true ]]; then
      if public_url="$(adopt_or_start_tunnel)"; then
        # Never mark tunnel_ok without a live probe (P-002)
        if [[ -n "$public_url" ]] && tunnel_alive "$public_url"; then
          tunnel_ok=true
        elif [[ -n "$public_url" ]]; then
          tunnel_ok=false
          msg="${msg:+$msg;}tunnel_stale_or_dead"
        else
          tunnel_ok=false
          msg="${msg:+$msg;}tunnel_start_failed"
        fi
      else
        msg="${msg:+$msg;}tunnel_start_failed"
        public_url=""
        tunnel_ok=false
      fi
    fi
    write_status "$api_ok" "$preview_ok" "$tunnel_ok" "$public_url" "${msg:-ok}"
    echo "[omnia-stack] api_ok=$api_ok preview_ok=$preview_ok tunnel_ok=$tunnel_ok"
    print_share "$public_url"
    [[ "$api_ok" == true && "$preview_ok" == true ]]
    ;;
  share|url)
    public_url="$(read_public_url || true)"
    if [[ -z "${public_url:-}" ]] || ! tunnel_alive "$public_url"; then
      "$0" ensure >/dev/null || true
      public_url="$(read_public_url || true)"
    fi
    print_share "$public_url"
    [[ -n "${public_url:-}" ]]
    ;;
  restart-preview)
    adopt_or_start_api || true
    restart_preview
    public_url="$(adopt_or_start_tunnel || true)"
    write_status true true "$([[ -n $public_url ]] && echo true || echo false)" "$public_url" "preview_restarted"
    print_share "$public_url"
    ;;
  watch)
    echo "[omnia-stack] watchdog every 15s (logs: $LOG_DIR) — api+preview+tunnel"
    while true; do
      "$0" ensure >/dev/null || "$0" ensure || true
      sleep 15
    done
    ;;
  status)
    if [[ -f "$status_file" ]]; then cat "$status_file"; else echo '{"error":"not_started"}'; fi
    echo
    echo -n "live api: "; curl -sf -o /dev/null -w '%{http_code}\n' --max-time 3 "${API_ORIGIN}/api/" || echo down
    echo -n "live preview: "; curl -sf -o /dev/null -w '%{http_code}\n' --max-time 3 "http://127.0.0.1:${PREVIEW_PORT}/healthz" || echo down
    public_url="$(read_public_url || true)"
    echo -n "live tunnel: "
    if [[ -n "${public_url:-}" ]]; then
      if tunnel_alive "$public_url"; then
        echo "200 ${public_url}"
      else
        echo "down ${public_url}"
      fi
    else
      echo none
    fi
    echo -n "listeners ${PREVIEW_PORT}: "; port_pids "$PREVIEW_PORT" | tr '\n' ' '; echo
    ;;
  rebuild)
    echo "[omnia-stack] rebuilding frontend..."
    (cd "$ROOT/frontend" && REACT_APP_BACKEND_URL= yarn build) | tee -a "$LOG_DIR/build.log"
    restart_preview || true
    public_url="$(adopt_or_start_tunnel || true)"
    write_status true true "$([[ -n ${public_url:-} ]] && echo true || echo false)" "${public_url:-}" "rebuilt"
    print_share "${public_url:-}"
    ;;
  stop)
    [[ -f "$pid_tunnel" ]] && kill "$(cat "$pid_tunnel")" 2>/dev/null || true
    pgrep -f "cloudflared tunnel --url http://127.0.0.1:${PREVIEW_PORT}" | xargs -r kill 2>/dev/null || true
    [[ -f "$pid_preview" ]] && kill "$(cat "$pid_preview")" 2>/dev/null || true
    [[ -f "$pid_api" ]] && kill "$(cat "$pid_api")" 2>/dev/null || true
    write_status false false false "" stopped
    echo "[omnia-stack] stopped (owned pids only)"
    ;;
  *)
    echo "Usage: $0 {ensure|share|watch|status|rebuild|restart-preview|stop}"
    exit 2
    ;;
esac
