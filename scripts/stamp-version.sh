#!/usr/bin/env bash
# Stamp the Home Assistant integration version that Core actually reads.
#
# Git tags are the source of truth. This script copies that version into
# manifest.json (required by HA; shown in Settings → Devices & Services).
# Do not write a VERSION file; Home Assistant does not read it.
#
# Usage: scripts/stamp-version.sh <x.y.z[+dev.gSHA]> <component_dir>
set -euo pipefail

VERSION="${1:-}"
TARGET="${2:-}"

if [ -z "$VERSION" ] || [ -z "$TARGET" ]; then
  echo "Usage: $0 <x.y.z[+dev.gSHA]> <component_dir>" >&2
  exit 1
fi

if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(\+dev\.g[0-9a-f]+)?$ ]]; then
  echo "Invalid version '${VERSION}'. Expected MAJOR.MINOR.PATCH or MAJOR.MINOR.PATCH+dev.gSHA." >&2
  exit 1
fi

MANIFEST="${TARGET}/manifest.json"
if [ ! -f "$MANIFEST" ]; then
  echo "manifest.json not found in ${TARGET}" >&2
  exit 1
fi

python3 - "$MANIFEST" "$VERSION" <<'PY'
import json
import sys

path, version = sys.argv[1], sys.argv[2]
with open(path, encoding="utf-8") as fh:
    data = json.load(fh)
data["version"] = version
with open(path, "w", encoding="utf-8") as fh:
    json.dump(data, fh, indent=2)
    fh.write("\n")
PY
