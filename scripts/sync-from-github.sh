#!/usr/bin/env bash
# Fast-forward Gitea origin from public GitHub: main plus SemVer tags
# whose commit is an ancestor of GitHub main. archive/* leftovers are
# skipped. Never force-pushes.
#
# Env:
#   GH_REPO        — owner/name (default csenf/ha-meteoswiss-rainstart)
#   GH_REMOTE_URL  — fetch URL (default https://github.com/${GH_REPO}.git)
#   GITEA_REMOTE   — remote to update (default origin)
set -euo pipefail

cd "$(dirname "$0")/.."

GH_REPO="${GH_REPO:-csenf/ha-meteoswiss-rainstart}"
GH_REMOTE_URL="${GH_REMOTE_URL:-https://github.com/${GH_REPO}.git}"
GITEA_REMOTE="${GITEA_REMOTE:-origin}"

if git remote get-url github >/dev/null 2>&1; then
  git remote set-url github "$GH_REMOTE_URL"
else
  git remote add github "$GH_REMOTE_URL"
fi

git fetch github --tags --prune

if ! git rev-parse --verify refs/remotes/github/main >/dev/null 2>&1; then
  echo "GitHub remote has no main branch." >&2
  exit 1
fi

gh_sha="$(git rev-parse refs/remotes/github/main)"

if git rev-parse --verify "refs/remotes/${GITEA_REMOTE}/main" >/dev/null 2>&1; then
  local_sha="$(git rev-parse "refs/remotes/${GITEA_REMOTE}/main")"
else
  git fetch "$GITEA_REMOTE" main
  local_sha="$(git rev-parse "refs/remotes/${GITEA_REMOTE}/main")"
fi

if [ "$local_sha" != "$gh_sha" ]; then
  if ! git merge-base --is-ancestor "$local_sha" "$gh_sha"; then
    echo "GitHub main is not a fast-forward of ${GITEA_REMOTE}/main; refusing." >&2
    exit 1
  fi
  git push "$GITEA_REMOTE" "${gh_sha}:refs/heads/main"
fi

while IFS= read -r tag; do
  [ -z "$tag" ] && continue
  if ! git merge-base --is-ancestor "${tag}^{commit}" "$gh_sha"; then
    continue
  fi
  if git ls-remote --exit-code "$GITEA_REMOTE" "refs/tags/${tag}" >/dev/null 2>&1; then
    continue
  fi
  git push "$GITEA_REMOTE" "refs/tags/${tag}"
done < <(git tag -l 'v[0-9]*.[0-9]*.[0-9]*')
