#!/usr/bin/env bash
# Push the current HEAD to GitHub mcnicastro-netizen/omnia2.
#
# Via principale: Cloud Agent avviato SUL repo GitHub omnia2
#   → `git push origin <branch>` con auth Cursor/GitHub nativa.
#   GITHUB_TOKEN NON serve.
#
# Fallback (agent Origin-tmp o remote sbagliato):
#   1) prova HTTPS github.com (insteadOf Cloud può già iniettare il token)
#   2) se c'è GITHUB_TOKEN, usalo solo per GitHub omnia2 — NON riscrive origin.
#
# Usage: bash scripts/github-omnia2-push.sh [branch]
# Default branch = current HEAD branch.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TARGET_HOST_PATH="github.com/mcnicastro-netizen/omnia2"
TARGET_HTTPS="https://github.com/mcnicastro-netizen/omnia2.git"
BRANCH="${1:-$(git rev-parse --abbrev-ref HEAD)}"

if [[ "$BRANCH" == "HEAD" ]]; then
  echo "[github-omnia2] ERROR: detached HEAD — passa un nome branch" >&2
  exit 1
fi

clean_url() {
  # Strip credentials for comparison; never print the raw URL with tokens.
  printf '%s' "$1" | sed -E 's#https://[^@]+@#https://#; s#git@github.com:#https://github.com/#; s#ssh://git@github.com/#https://github.com/#'
}

is_omnia2_github() {
  local u
  u="$(clean_url "$1")"
  [[ "$u" == *"${TARGET_HOST_PATH}"* ]]
}

native_push() {
  local remote="$1"
  echo "[github-omnia2] native push → ${remote} ${BRANCH} (no username prompt)"
  GIT_TERMINAL_PROMPT=0 git push "$remote" "HEAD:refs/heads/${BRANCH}"
}

origin_url="$(git remote get-url origin 2>/dev/null || true)"
if [[ -n "$origin_url" ]] && is_omnia2_github "$origin_url"; then
  native_push origin
  exit 0
fi

echo "[github-omnia2] origin non è GitHub omnia2 — fallback (origin NON viene cambiato)"

if GIT_TERMINAL_PROMPT=0 git push "$TARGET_HTTPS" "HEAD:refs/heads/${BRANCH}"; then
  exit 0
fi

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "[github-omnia2] ERROR: push GitHub fallito e GITHUB_TOKEN assente." >&2
  echo "Apri l'agent su https://github.com/mcnicastro-netizen/omnia2 (via principale)." >&2
  exit 1
fi

echo "[github-omnia2] retry con GITHUB_TOKEN (header, token non loggato)"
# Prefer extraHeader over embedding the token in the remote URL.
GIT_TERMINAL_PROMPT=0 git \
  -c "http.https://github.com/.extraHeader=Authorization: Bearer ${GITHUB_TOKEN}" \
  push "$TARGET_HTTPS" "HEAD:refs/heads/${BRANCH}"
