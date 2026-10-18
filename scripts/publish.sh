#!/usr/bin/env bash
# Publish this folder to github.com/mynk03/mynk03 (the profile README repo).
#
#   ./scripts/publish.sh            refresh auto sections, commit, push
#   ./scripts/publish.sh --refresh  only refresh README auto sections locally (no push)
#
# Reads GITHUB_PAT from ../.env (mynk/.env). The token is never written to git config or disk.
set -euo pipefail
cd "$(dirname "$0")/.."

OWNER="mynk03"
REPO="$OWNER/$OWNER"
ENV_FILE="../.env"

[[ -f "$ENV_FILE" ]] || { echo "error: $ENV_FILE not found (add GITHUB_PAT=... there)" >&2; exit 1; }
GITHUB_PAT=$(grep -E '^GITHUB_PAT=' "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '"'"'"' \r')
[[ -n "$GITHUB_PAT" ]] || { echo "error: GITHUB_PAT is empty in $ENV_FILE" >&2; exit 1; }
export GH_TOKEN="$GITHUB_PAT"

login=$(gh api user --jq .login)
[[ "$login" == "$OWNER" ]] || { echo "error: token belongs to '$login', expected '$OWNER'. Aborting." >&2; exit 1; }
echo "token ok: $login"

bash .github/scripts/update-readme.sh
[[ "${1:-}" == "--refresh" ]] && exit 0

if ! gh api "repos/$REPO" >/dev/null 2>&1; then
  echo "creating public repo $REPO"
  gh repo create "$REPO" --public --description "Profile README"
fi

git add -A
git diff --staged --quiet || git commit -m "Update profile README"

auth=$(printf 'x-access-token:%s' "$GITHUB_PAT" | base64)
git -c "http.https://github.com/.extraheader=AUTHORIZATION: basic $auth" \
  push "https://github.com/$REPO.git" HEAD:main
echo "pushed: https://github.com/$OWNER"
