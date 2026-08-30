#!/usr/bin/env bash
# Push current HEAD and SemVer tags reachable from HEAD to GitHub over SSH
# (write deploy key). Pre-public leftover tags are not copied.
#
# Env:
#   GH_DEPLOY_KEY  — passphrase-free private key (full PEM / OpenSSH)
#   GH_REPO        — owner/name (default csenf/ha-meteoswiss-rainstart)
set -euo pipefail

cd "$(dirname "$0")/.."

GH_DEPLOY_KEY="${GH_DEPLOY_KEY:-}"
GH_REPO="${GH_REPO:-csenf/ha-meteoswiss-rainstart}"

if [ -z "$GH_DEPLOY_KEY" ]; then
  echo "Set GH_DEPLOY_KEY to a passphrase-free GitHub deploy private key." >&2
  exit 1
fi

KEY_FILE="$(mktemp)"
cleanup() { rm -f "$KEY_FILE"; }
trap cleanup EXIT

printf '%s\n' "$GH_DEPLOY_KEY" > "$KEY_FILE"
chmod 600 "$KEY_FILE"
if ! ssh-keygen -y -f "$KEY_FILE" -P "" > /dev/null 2>&1; then
  echo "GH_DEPLOY_KEY is not a valid, passphrase-free private key." >&2
  exit 1
fi

export GIT_SSH_COMMAND="ssh -i ${KEY_FILE} -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=accept-new"
remote="git@github.com:${GH_REPO}.git"
git push "$remote" HEAD:refs/heads/main
while IFS= read -r tag; do
  git push "$remote" "refs/tags/${tag}"
done < <(bash scripts/reachable-semver-tags.sh)
