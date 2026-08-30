#!/usr/bin/env bash
# Poll public GitHub until main moves past SINCE_SHA (release stamp) or
# TIMEOUT_SECS elapses. Always exits 0. Last stdout line is MOVED=1 or 0.
#
# Env:
#   GH_REPO        — owner/name (default csenf/ha-meteoswiss-rainstart)
#   GH_REMOTE_URL  — ls-remote URL (default https://github.com/${GH_REPO}.git)
#   SINCE_SHA      — SHA that was just pushed (required)
#   TIMEOUT_SECS   — default 180
#   INTERVAL_SECS  — default 10
set -euo pipefail

GH_REPO="${GH_REPO:-csenf/ha-meteoswiss-rainstart}"
GH_REMOTE_URL="${GH_REMOTE_URL:-https://github.com/${GH_REPO}.git}"
SINCE_SHA="${SINCE_SHA:-}"
TIMEOUT_SECS="${TIMEOUT_SECS:-180}"
INTERVAL_SECS="${INTERVAL_SECS:-10}"

if [ -z "$SINCE_SHA" ]; then
  echo "Set SINCE_SHA to the commit just pushed to GitHub." >&2
  exit 1
fi

start="$(date +%s)"
while true; do
  current="$(git ls-remote "$GH_REMOTE_URL" refs/heads/main | awk '{print $1}')"
  if [ -n "$current" ] && [ "$current" != "$SINCE_SHA" ]; then
    echo "GitHub main moved to ${current}." >&2
    echo "MOVED=1"
    exit 0
  fi
  now="$(date +%s)"
  if [ $((now - start)) -ge "$TIMEOUT_SECS" ]; then
    echo "GitHub main still ${SINCE_SHA:-unknown}; continuing." >&2
    echo "MOVED=0"
    exit 0
  fi
  sleep "$INTERVAL_SECS"
done
