#!/bin/bash
# 一键运行脚本 - 最简单的方式

cd "$(dirname "$0")"

clear

echo "======================================================================"
echo "  📊 Research Pipeline - 一键运行"
echo "======================================================================"
echo ""
echo "  正在启动..."
echo ""

# 激活环境
source .venv/bin/activate

# 运行 Demo
echo "🚀 运行 Demo..."
echo ""
python3 -m research_pipeline demo

# 检查结果
if [ -f "outputs/demo/dashboard.html" ]; then
    echo ""
    echo "======================================================================"
    echo "  ✅ 完成！"
    echo "======================================================================"
    echo ""
    echo "  正在打开结果..."
    echo ""
    sleep 1
    open outputs/demo/dashboard.html
else
    echo ""
    echo "  ❌ 输出文件不存在"
fi

echo ""
echo "按任意键关闭..."
read -n 1
