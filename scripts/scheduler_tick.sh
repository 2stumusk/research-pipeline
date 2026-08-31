#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "缺少 $PYTHON；请先运行 scripts/install_macos.sh" >&2
  exit 1
fi
cd "$ROOT"
exec "$PYTHON" -m research_pipeline scheduler-tick
