#!/bin/bash

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 查找最新的 dashboard.html
LATEST_DASHBOARD=$(find "$DIR/outputs" -name "dashboard.html" -type f | sort -r | head -n 1)

if [ -n "$LATEST_DASHBOARD" ]; then
    open "$LATEST_DASHBOARD"
    osascript -e 'display notification "已打开最新结果" with title "Research Pipeline"'
else
    osascript -e 'display notification "未找到结果文件，请先运行Demo" with title "Research Pipeline" sound name "Basso"'
fi
