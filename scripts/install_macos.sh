#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "未找到 python3。请先安装 Python 3.11 或更高版本。" >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit(f"需要 Python >= 3.11，当前为 {sys.version.split()[0]}")
PY

if [[ ! -d .venv ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

if command -v git >/dev/null 2>&1 && [[ ! -d .git ]]; then
  git init -q
fi

.venv/bin/python -m research_pipeline init

echo
echo "环境检查："
set +e
.venv/bin/python -m research_pipeline doctor
DOCTOR_STATUS=$?
set -e

echo
if ! command -v codex >/dev/null 2>&1; then
  echo "尚未检测到 Codex CLI。安装后执行一次 codex 完成登录："
  echo "  curl -fsSL https://chatgpt.com/codex/install.sh | sh"
  echo "  codex"
else
  echo "已检测到 Codex CLI：$(codex --version 2>/dev/null || true)"
fi

echo
echo "安装完成。下一步："
echo "  1. 编辑 config/watchlist.csv"
echo "  2. 将 PDF 放入 inbox/YYYY-MM-DD/"
echo "  3. 执行 ./run.sh 0900"

# Codex 未安装不应使 Python 项目安装失败。
exit 0
