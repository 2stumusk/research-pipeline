#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "尚未初始化虚拟环境。请先执行：bash scripts/install_macos.sh" >&2
  exit 1
fi
SESSION="${1:-0900}"
if [[ $# -gt 0 ]]; then shift; fi
if [[ "$SESSION" != "0900" && "$SESSION" != "2100" ]]; then
  echo "首个参数必须为 0900 或 2100。" >&2
  exit 2
fi
cd "$ROOT"
exec "$PYTHON" -m research_pipeline run --session "$SESSION" "$@"
