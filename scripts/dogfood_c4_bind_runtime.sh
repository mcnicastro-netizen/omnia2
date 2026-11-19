#!/usr/bin/env bash
# D-175 C4 — Bind OMNIA API/preview to Dogfood CLEAN work copy (never permanent).
# Founder creates invented accounts on this runtime. No real email (Resend HOLD).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PORT="${OMNIA_DF_MONGO_PORT:-27018}"
DB="${OMNIA_DOGFOOD_RUNTIME_DB:-omnia_df_clean_c4}"
CREDS="$ROOT/dogfood/secrets/mongo-df-credentials.json"
PUB="$(cat /tmp/omnia-stack/SHARE_URL.txt 2>/dev/null || true)"
if [[ -z "${PUB:-}" ]]; then
  PUB="http://127.0.0.1:43123"
fi
PUB="${PUB%/}"
HOST="$(python3 - <<PY
from urllib.parse import urlparse
print(urlparse("$PUB").hostname or "127.0.0.1")
PY
)"

RT_PWD="$(python3 -c "import json; print(json.load(open('$CREDS'))['runtime'])")"
MONGO_URL="mongodb://omnia_df_runtime:${RT_PWD}@127.0.0.1:${PORT}/?authSource=admin"

# Ensure CLEAN exists (idempotent workcopy without drop unless asked)
if [[ "${C4_REFRESH_WORKCOPY:-0}" == "1" ]]; then
  backend/.venv/bin/python scripts/dogfood_c4_workcopy.py --kind clean --target "$DB" --drop-target
fi

# Stop current API on 43121
pids="$(ss -ltnp 2>/dev/null | awk '/:43121/ {print}' | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | sort -u || true)"
if [[ -n "${pids:-}" ]]; then
  # shellcheck disable=SC2086
  kill $pids 2>/dev/null || true
  sleep 1
fi

export OMNIA_ENV=dogfood
export DOGFOOD_ROOT="$ROOT/dogfood"
export OMNIA_DF_MONGO_PORT="$PORT"
export DB_NAME="$DB"
export MONGO_URL
export OMNIA_DOGFOOD_RUNTIME_URI="$MONGO_URL"
export OMNIA_DOGFOOD_RUNTIME_DB="$DB"
export OMNIA_DOGFOOD_PERMANENT_DB=omnia_df_perm_main
export OMNIA_API_PUBLIC_URL="$PUB"
export FRONTEND_URL="$PUB"
export FRONTEND_ORIGIN="$PUB"
export FRONTEND_PUBLIC_URL="$PUB"
export OMNIA_DOGFOOD_TUNNEL_HOST="$HOST"
export OMNIA_DOGFOOD_ALLOWED_API_HOSTS="127.0.0.1,localhost,$HOST"
export OMNIA_DOGFOOD_ALLOWED_FE_HOSTS="127.0.0.1,localhost,$HOST"
# Prefer test Stripe; never LIVE. Resend held by dogfood perimeter even if key present.
export STRIPE_MODE=test

mkdir -p /tmp/omnia-stack
{
  echo "OMNIA_ENV=dogfood"
  echo "DB_NAME=$DB"
  echo "MONGO_PORT=$PORT"
  echo "FRONTEND_URL=$PUB"
  echo "TUNNEL_HOST=$HOST"
  echo "bound_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >/tmp/omnia-stack/DOGFOOD_C4_BIND.txt

cd "$ROOT/backend"
nohup "$ROOT/backend/.venv/bin/uvicorn" server:app --host 0.0.0.0 --port 43121 --reload \
  >>/tmp/omnia-stack/api.log 2>&1 &
echo $! >/tmp/omnia-stack/api.pid

ok=0
for _ in $(seq 1 60); do
  if curl -sf "http://127.0.0.1:43121/api/" >/dev/null 2>&1; then ok=1; break; fi
  sleep 0.5
done
if [[ "$ok" != "1" ]]; then
  echo "FAIL api_not_healthy" >&2
  tail -80 /tmp/omnia-stack/api.log >&2 || true
  exit 2
fi

# Confirm runtime DB
"$ROOT/backend/.venv/bin/python" - <<PY
import os, json
from pymongo import MongoClient
uri=os.environ["MONGO_URL"]
db=os.environ["DB_NAME"]
c=MongoClient(uri, serverSelectionTimeoutMS=5000)
n=c[db].commercial_customers.count_documents({})
print(json.dumps({
  "ok": True,
  "dogfood": True,
  "db": db,
  "cc_count": n,
  "portal": os.environ.get("FRONTEND_URL"),
  "note": "Invented data only. Permanent not bound. Resend HOLD in dogfood.",
}, indent=2))
PY

echo "PORTALE=$PUB"
echo "LOGIN=$PUB/it/login"
echo "REGISTER=$PUB/it/register"
echo "VERIFY_HELPER=python3 scripts/dogfood_c4_print_verify_link.py --email <email>"
