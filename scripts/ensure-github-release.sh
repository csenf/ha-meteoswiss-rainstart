#!/usr/bin/env bash
# Create a GitHub Release for vX.Y.Z if one is missing. Used when promote
# already pushed the tag and ci-tag-release did not create a new one.
#
# Usage: scripts/ensure-github-release.sh <MAJOR.MINOR.PATCH>
# Env:
#   GH_TOKEN  — required by gh
#   GH_REPO   — owner/name (default GITHUB_REPOSITORY, then
#               csenf/ha-meteoswiss-rainstart)
# Last stdout line is CREATED=0 or CREATED=1.
set -euo pipefail

version="${1:-}"
if ! [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Usage: $0 MAJOR.MINOR.PATCH" >&2
  exit 1
fi

tag="v${version}"
repo="${GH_REPO:-${GITHUB_REPOSITORY:-csenf/ha-meteoswiss-rainstart}}"

if gh release view "$tag" --repo "$repo" >/dev/null 2>&1; then
  echo "GitHub Release ${tag} already exists." >&2
  echo "CREATED=0"
  exit 0
fi

gh release create "$tag" --repo "$repo" --title "$tag" --generate-notes
echo "CREATED=1"
