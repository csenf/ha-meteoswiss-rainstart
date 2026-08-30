#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-}"

if [ -z "$TARGET" ]; then
  echo "Usage: $0 <target-dir>" >&2
  echo "Example: $0 /config/custom_components/meteoswiss_rainstart" >&2
  exit 1
fi

rsync -av --delete \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  "${ROOT}/custom_components/meteoswiss_rainstart/" \
  "${TARGET}/"

if [ -n "${VERSION:-}" ]; then
  bash "${ROOT}/scripts/stamp-version.sh" "$VERSION" "$TARGET"
fi

echo "Deployed to ${TARGET}"
echo "Restart Home Assistant to load manifest changes."
