#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
LABEL="com.musk.a-share-research"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_NUM="$(id -u)"

if [[ ! -x "$PYTHON" ]]; then
  echo "尚未初始化虚拟环境。请先运行：bash scripts/install_macos.sh" >&2
  exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$ROOT/logs"

INTERVAL="$(ROOT="$ROOT" PYTHON="$PYTHON" PLIST="$PLIST" LABEL="$LABEL" "$PYTHON" - <<'PY'
import os
import plistlib
import sys
from pathlib import Path

root = Path(os.environ["ROOT"]).resolve()
sys.path.insert(0, str(root))

from research_pipeline.config import load_config

python = Path(os.environ["PYTHON"]).resolve()
plist = Path(os.environ["PLIST"]).expanduser()
label = os.environ["LABEL"]
home = Path.home()
interval = max(60, int(load_config().get("automation.poll_interval_seconds", 600)))

payload = {
    "Label": label,
    "ProgramArguments": [str(python), "-m", "research_pipeline", "scheduler-tick"],
    "WorkingDirectory": str(root),
    "StartInterval": interval,
    "RunAtLoad": True,
    "KeepAlive": False,
    "ProcessType": "Background",
    "StandardOutPath": str(root / "logs" / "scheduler.stdout.log"),
    "StandardErrorPath": str(root / "logs" / "scheduler.stderr.log"),
    "EnvironmentVariables": {
        "PATH": f"{home}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin",
        "PYTHONUNBUFFERED": "1",
    },
}
plist.write_bytes(plistlib.dumps(payload, fmt=plistlib.FMT_XML, sort_keys=False))
print(interval)
PY
)"

launchctl bootout "gui/$UID_NUM" "$PLIST" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$UID_NUM" "$PLIST"
launchctl enable "gui/$UID_NUM/$LABEL" >/dev/null 2>&1 || true
launchctl kickstart -k "gui/$UID_NUM/$LABEL" >/dev/null 2>&1 || true

echo "已安装本地自动任务：$LABEL"
echo "计划时间由 config/config.yaml 中的 Asia/Shanghai、09:00、21:00 控制。"
echo "LaunchAgent 每 $INTERVAL 秒做一次轻量检查，并在未成功运行时补跑。"
echo "日志：$ROOT/logs/scheduler.stdout.log 与 scheduler.stderr.log"
