#!/usr/bin/env bash
# Print a local-only Home Assistant version. Never commit this string.
#
# On a vX.Y.Z tag that matches manifest.json: VERSION=X.Y.Z
# Otherwise: VERSION=X.Y.Z+dev.g<shortsha>
#
# Usage: scripts/dev-version.sh
# Last stdout line is VERSION=...
set -euo pipefail

cd "$(dirname "$0")/.."

COMPONENT="custom_components/meteoswiss_rainstart"
MANIFEST="${COMPONENT}/manifest.json"
if [ ! -f "$MANIFEST" ]; then
  echo "manifest.json not found in ${COMPONENT}" >&2
  exit 1
fi

base="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])' "$MANIFEST")"
base="${base%%+*}"
if ! [[ "$base" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "manifest.json version '${base}' is not MAJOR.MINOR.PATCH" >&2
  exit 1
fi

exact="$(git --no-pager describe --tags --exact-match HEAD 2>/dev/null || true)"
if [ "$exact" = "v${base}" ]; then
  echo "VERSION=${base}"
  exit 0
fi

sha="$(git rev-parse --short=7 HEAD)"
echo "VERSION=${base}+dev.g${sha}"
