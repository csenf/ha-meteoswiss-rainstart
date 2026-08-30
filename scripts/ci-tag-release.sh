#!/usr/bin/env bash
# CI-only: compute the next semantic version from Conventional Commits since
# the last vX.Y.Z tag, stamp manifest.json, commit that, tag the commit, and
# push both. Git tags are the source of truth. Home Assistant reads the
# stamped manifest on that tagged commit.
#
# Usage: scripts/ci-tag-release.sh
#   Run from repo root in CI, on main, after `actions/checkout` with
#   fetch-depth: 0 (tags must be fetched) and a configured git identity.
#
# What it does:
#   - Finds the latest vX.Y.Z tag reachable from HEAD (default v0.0.0 if none)
#   - Scans commit subjects/bodies since that tag for Conventional Commit types
#   - Bump rules (highest wins):
#       major -> "BREAKING CHANGE" or a "!:" type marker
#       minor -> any commit type is "feat"
#       patch -> any commit type is "fix" or "perf"
#       none  -> only docs/style/refactor/test/chore/ci -> exits without changes
#   - Stamps custom_components/meteoswiss_rainstart/manifest.json
#   - Commits that file as chore(release): vX.Y.Z (chore does not bump again)
#   - Creates annotated tag vX.Y.Z on that commit and pushes commit + tag
#   - Prints the resolved version to stdout on its own last line as
#     "VERSION=<version>" so CI can capture it into a step output
#
# Idempotent: if HEAD is already tagged, or nothing warrants a release,
# it prints the current/latest version and exits 0 without creating a tag.
#
# Dependencies: git, python3 (via stamp-version.sh)
set -euo pipefail

cd "$(dirname "$0")/.."

COMPONENT="custom_components/meteoswiss_rainstart"

last_tag=$(bash scripts/reachable-semver-tags.sh | head -n1 || true)
if [ -z "$last_tag" ]; then
  last_tag="v0.0.0"
  range="HEAD"
else
  range="${last_tag}..HEAD"
fi

# Already tagged? Nothing to do.
if git tag --points-at HEAD | grep -qE '^v[0-9]+\.[0-9]+\.[0-9]+$'; then
  current=$(git tag --points-at HEAD | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -n1)
  echo "HEAD already tagged ${current}; skipping." >&2
  echo "RELEASED=0"
  echo "VERSION=${current#v}"
  exit 0
fi

subjects=$(git --no-pager log "$range" --pretty=format:'%s%n%b' 2>/dev/null || true)

bump="none"
if [ -n "$subjects" ]; then
  if echo "$subjects" | grep -qE 'BREAKING CHANGE|^[a-z]+(\([^)]*\))?!:'; then
    bump="major"
  elif echo "$subjects" | grep -qE '^feat(\([^)]*\))?:'; then
    bump="minor"
  elif echo "$subjects" | grep -qE '^(fix|perf)(\([^)]*\))?:'; then
    bump="patch"
  fi
fi

if [ "$bump" = "none" ]; then
  echo "No feat/fix/perf/breaking commits since ${last_tag}; skipping release." >&2
  echo "RELEASED=0"
  echo "VERSION=${last_tag#v}"
  exit 0
fi

version="${last_tag#v}"
major="${version%%.*}"
rest="${version#*.}"
minor="${rest%%.*}"
patch="${rest#*.}"

case "$bump" in
  major) major=$((major + 1)); minor=0; patch=0 ;;
  minor) minor=$((minor + 1)); patch=0 ;;
  patch) patch=$((patch + 1)) ;;
esac

new_version="${major}.${minor}.${patch}"
new_tag="v${new_version}"

echo "Last tag: ${last_tag}" >&2
echo "Bump: ${bump}" >&2
echo "New version: ${new_version}" >&2

bash scripts/stamp-version.sh "$new_version" "$COMPONENT"
rm -f "${COMPONENT}/VERSION"
git add "${COMPONENT}/manifest.json"
if ! git diff --cached --quiet -- "${COMPONENT}/manifest.json"; then
  git commit -m "chore(release): ${new_tag}"
fi

git tag -a "$new_tag" -m "Release ${new_tag}"
git push origin HEAD:refs/heads/main
git push origin "$new_tag"

echo "RELEASED=1"
echo "VERSION=${new_version}"
