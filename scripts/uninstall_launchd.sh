#!/usr/bin/env bash
set -euo pipefail
LABEL="com.musk.a-share-research"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_NUM="$(id -u)"
launchctl bootout "gui/$UID_NUM" "$PLIST" >/dev/null 2>&1 || true
rm -f "$PLIST"
echo "已卸载本地自动任务：$LABEL"
