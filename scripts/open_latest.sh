#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="$ROOT/outputs/daily/latest/dashboard.html"
if [[ ! -f "$TARGET" ]]; then
  TARGET="$ROOT/outputs/demo/dashboard.html"
fi
if [[ ! -f "$TARGET" ]]; then
  echo "尚无可打开的 dashboard.html。" >&2
  exit 1
fi
open "$TARGET"
