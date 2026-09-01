#!/bin/bash
# 启动 Web Dashboard 的快捷脚本

echo "🚀 启动 Research Pipeline Web Dashboard..."
echo "📍 端口: 8080 (避免与 AirPlay 冲突)"
echo ""

# 激活虚拟环境
source .venv/bin/activate

# 运行 Web 服务
python3 web_launcher.py
