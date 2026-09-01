#!/bin/bash
# 一键启动脚本 - macOS

echo "======================================================================"
echo "  📊 Research Pipeline - 一键启动"
echo "======================================================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 找不到 python3"
    echo "请先安装 Python 3.11+"
    exit 1
fi

# 进入项目目录
cd "$(dirname "$0")"

# 运行启动器
python3 launcher.py
