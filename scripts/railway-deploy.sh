#!/usr/bin/env bash
# Deploy OMNIA API to Railway (D-123).
# Account token may live in RAILWAY_TOKEN (vault name from the runbook) or RAILWAY_API_TOKEN.
# Project token must be RAILWAY_TOKEN and is scoped to one environment.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_SERVICE="${RAILWAY_API_SERVICE:-omnia-api}"
PROJECT_NAME="${RAILWAY_PROJECT_NAME:-omnia-api}"

echo "=== railway-deploy ==="
bash "$ROOT/scripts/railway-prep-check.sh"

if [[ -z "${RAILWAY_TOKEN:-}${RAILWAY_API_TOKEN:-}" ]]; then
  echo "BLOCKED: RAILWAY_TOKEN missing."
  echo "Founder: Railway → Account → Tokens → workspace «No workspace» → vault omnia2 come RAILWAY_TOKEN → nuovo agent → «vai Railway»."
  exit 2
fi

set +e
python3 "$ROOT/scripts/railway_token_kind.py" >/tmp/railway-kind.out
kind_rc=$?
set -e
kind_line="$(cat /tmp/railway-kind.out)"
rm -f /tmp/railway-kind.out

if [[ "$kind_rc" -ne 0 || "${kind_line%% *}" == "invalid" || -z "$kind_line" ]]; then
  echo "BLOCKED: RAILWAY_TOKEN presente ma Railway non lo accetta."
  echo "Crea un account token: https://railway.com/account/tokens → workspace «No workspace»."
  echo "Sostituisci il valore nel vault omnia2 (nome RAILWAY_TOKEN) e riavvia l'agent con «vai Railway»."
  echo "Non usare un token di workspace, né un project id."
  exit 2
fi

read -r kind src_var project_id <<<"$kind_line"
echo "Token classificato: $kind (variabile $src_var)"

# CLI 5: account/workspace → RAILWAY_API_TOKEN; project → RAILWAY_TOKEN. Mai entrambi.
if [[ "$kind" == "account" ]]; then
  if [[ "$src_var" == "RAILWAY_TOKEN" ]]; then
    export RAILWAY_API_TOKEN="$RAILWAY_TOKEN"
  fi
  unset RAILWAY_TOKEN
elif [[ "$kind" == "project" ]]; then
  if [[ "$src_var" == "RAILWAY_API_TOKEN" ]]; then
    export RAILWAY_TOKEN="$RAILWAY_API_TOKEN"
  fi
  unset RAILWAY_API_TOKEN
  if [[ -n "${project_id:-}" ]]; then
    export RAILWAY_PROJECT_ID="$project_id"
  fi
else
  echo "BLOCKED: classificazione inattesa: $kind_line"
  exit 2
fi

install_railway() {
  export PATH="$HOME/.local/bin:$PATH"
  if command -v railway >/dev/null 2>&1; then
    return 0
  fi
  echo "Installing Railway CLI (user prefix)…"
  npm install -g --prefix "$HOME/.local" @railway/cli
  export PATH="$HOME/.local/bin:$PATH"
  command -v railway >/dev/null 2>&1
}

install_railway
export CI=1
cd "$ROOT"

dotenv_get() {
  python3 - "$1" "$ROOT/backend/.env" <<'PY'
import sys
key, path = sys.argv[1], sys.argv[2]
val = ""
try:
    for line in open(path, encoding="utf-8", errors="replace"):
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        k, v = raw.split("=", 1)
        if k.strip() == key:
            val = v.strip().strip('"').strip("'")
except FileNotFoundError:
    pass
sys.stdout.write(val)
PY
}

resolve_value() {
  local key="$1"
  local val="${!key:-}"
  if [[ -z "$val" ]]; then
    val="$(dotenv_get "$key")"
  fi
  printf '%s' "$val"
}

set_var() {
  local key="$1" value="$2"
  if [[ -z "$value" ]]; then
    echo "SKIP $key"
    return 0
  fi
  local err
  err="$(mktemp)"
  if printf '%s' "$value" | railway variable set "$key" --stdin --service "$API_SERVICE" --skip-deploys --json >"$err" 2>&1; then
    echo "OK  variable $key"
  else
    echo "FAIL variable $key"
    python3 - "$err" "$value" <<'PY'
import sys
path, secret = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8", errors="replace").read()
if secret:
    text = text.replace(secret, "[redacted]")
sys.stdout.write(text[:500])
PY
    echo
    rm -f "$err"
    return 1
  fi
  rm -f "$err"
}

service_names() {
  railway service list --json | python3 -c '
import json, sys
raw = sys.stdin.read()
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    sys.exit(0)
names = set()
def walk(o):
    if isinstance(o, dict):
        n = o.get("name")
        if isinstance(n, str):
            names.add(n)
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for i in o:
            walk(i)
walk(data)
print("\n".join(sorted(names)))
'
}

echo "Linking project…"
init_args=(--name "$PROJECT_NAME" --json)
if [[ -n "${RAILWAY_WORKSPACE_ID:-}" ]]; then
  init_args+=(--workspace "$RAILWAY_WORKSPACE_ID")
fi
if [[ -n "${RAILWAY_PROJECT_ID:-}" ]]; then
  railway link --project "$RAILWAY_PROJECT_ID" --json >/tmp/railway-link.out
  echo "OK  linked project"
else
  railway init "${init_args[@]}" >/tmp/railway-link.out
  echo "OK  project created ($PROJECT_NAME)"
fi

echo "Ensuring MongoDB…"
names="$(service_names || true)"
mongo_name="$(printf '%s\n' "$names" | python3 -c '
import sys
rows=[r.strip() for r in sys.stdin if r.strip()]
for r in rows:
    if "mongo" in r.lower():
        print(r)
        break
')"
if [[ -z "$mongo_name" ]]; then
  railway add --database mongo --json >/tmp/railway-mongo.out
  mongo_name="$(python3 - /tmp/railway-mongo.out <<'PY'
import json, sys
raw = open(sys.argv[1], encoding="utf-8", errors="replace").read()
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    data = None
found = []
def walk(o):
    if isinstance(o, dict):
        n = o.get("name")
        if isinstance(n, str):
            found.append(n)
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for i in o:
            walk(i)
if data is not None:
    walk(data)
for n in found:
    if "mongo" in n.lower():
        print(n)
        break
else:
    if found:
        print(found[-1])
PY
)"
fi
if [[ -z "$mongo_name" ]]; then
  echo "FAIL MongoDB service name unknown"
  exit 1
fi
echo "OK  MongoDB service: $mongo_name"

if ! printf '%s\n' "$names" | grep -qx "$API_SERVICE"; then
  railway add --service "$API_SERVICE" --json >/tmp/railway-svc.out
fi
echo "OK  API service: $API_SERVICE"

echo "Setting variables (values not printed)…"
set_var MONGO_URL "\${{${mongo_name}.MONGO_URL}}"
set_var DB_NAME "omnia"
set_var COOKIE_SECURE "true"
set_var STORAGE_BACKEND "local"
set_var OMNIA_ENV "production"
set_var CORS_ORIGINS "https://www.omniarealestateecosystem.it,https://app.omniarealestateecosystem.it,https://cloud.omniarealestateecosystem.it"
set_var FRONTEND_URL "https://www.omniarealestateecosystem.it"
set_var FRONTEND_BASE_URL "https://www.omniarealestateecosystem.it"
set_var OMNIA_PUBLIC_URL "https://www.omniarealestateecosystem.it"
sender="$(resolve_value SENDER_EMAIL)"
if [[ -z "$sender" ]]; then
  sender="OMNIA <info@omniarealestateecosystem.it>"
fi
set_var SENDER_EMAIL "$sender"

for key in JWT_SECRET ADMIN_EMAIL ADMIN_PASSWORD DEMO_ADMIN_PASSWORD GEMINI_API_KEY RESEND_API_KEY \
  STRIPE_SECRET_KEY STRIPE_PUBLISHABLE_KEY STRIPE_WEBHOOK_SECRET STRIPE_ENABLED OMNIA_SELF_SERVE_ENABLED \
  FAL_KEY TAVILY_API_KEY GOOGLE_CLIENT_ID OPENAPI_ENABLED OPENAPI_API_KEY OPENAPI_EMAIL OPENAPI_TOKEN \
  OPENAPI_CATASTO_BASE OPENAPI_OAUTH_BASE; do
  set_var "$key" "$(resolve_value "$key")"
done

echo "Ensuring volumes…"
railway volume --service "$API_SERVICE" add --mount-path /app/.media --json >/tmp/railway-vol-media.out || echo "WAIT volume /app/.media (già presente o non creato)"
railway volume --service "$API_SERVICE" add --mount-path /app/.backups --json >/tmp/railway-vol-bak.out || echo "WAIT volume /app/.backups (già presente o non creato)"

echo "Deploying Dockerfile.railway…"
railway up --service "$API_SERVICE" -y --ci

echo "Generating domain…"
railway domain --service "$API_SERVICE" --port 8080 --json >/tmp/railway-domain.out || railway domain --service "$API_SERVICE" --json >/tmp/railway-domain.out
public_url="$(python3 - /tmp/railway-domain.out <<'PY'
import json, re, sys
raw = open(sys.argv[1], encoding="utf-8", errors="replace").read()
urls = []
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    data = None
def walk(o):
    if isinstance(o, dict):
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for i in o:
            walk(i)
    elif isinstance(o, str) and "railway.app" in o:
        urls.append(o if o.startswith("http") else "https://" + o)
if data is not None:
    walk(data)
if not urls:
    urls = re.findall(r"https://[A-Za-z0-9.-]+\.up\.railway\.app", raw)
print(urls[0].rstrip("/") if urls else "")
PY
)"

if [[ -n "$public_url" ]]; then
  echo "OK  domain $public_url"
  set_var PUBLIC_BASE_URL "$public_url"
  railway redeploy --service "$API_SERVICE" --yes --json >/tmp/railway-redeploy.out || true
  echo "Smoke: $public_url/api/health"
  sleep 5
  curl -fsS --retry 5 --retry-delay 10 --retry-all-errors "$public_url/api/health" || echo "WAIT health non ancora verde — controlla i log Railway"
else
  echo "WAIT domain non letto dall'output CLI. Genera il dominio in dashboard e imposta PUBLIC_BASE_URL."
fi

echo "DONE — next:"
echo "  1) Vault: OMNIA_API_PUBLIC_URL=${public_url:-<dominio Railway>}"
if [[ -n "${RAILWAY_PROJECT_ID:-}" ]]; then
  echo "  2) Vault opzionale: RAILWAY_PROJECT_ID=$RAILWAY_PROJECT_ID"
fi
echo "  3) Cloudflare CNAME api → Railway (memory/DNS_SETUP_GUIDE.md)"
echo "  4) «vai Vercel»"
