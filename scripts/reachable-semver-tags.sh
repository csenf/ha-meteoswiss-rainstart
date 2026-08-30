#!/usr/bin/env bash
# Print vX.Y.Z tags whose commit is an ancestor of HEAD, newest first.
# archive/v0.2.0 and pre-public leftovers are skipped.
set -euo pipefail

cd "$(dirname "$0")/.."

git tag -l 'v[0-9]*.[0-9]*.[0-9]*' --sort=-v:refname | while IFS= read -r tag; do
  if git merge-base --is-ancestor "${tag}^{commit}" HEAD; then
    printf '%s\n' "$tag"
  fi
done
