#!/bin/bash
# 自动修复脚本 - A股研报系统

set -e

echo "========================================"
echo "🔧 A股研报系统 - 自动修复"
echo "========================================"
echo ""

PROJECT_ROOT="/Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline"
cd "$PROJECT_ROOT"

# 步骤 1: 查找合适的 Python 版本
echo "📍 步骤 1: 检查 Python 版本..."
PYTHON_BIN=""

for py_cmd in python3.13 python3.12 python3.11 python3; do
    if command -v "$py_cmd" &> /dev/null; then
        version=$("$py_cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)

        if [ "$major" -eq 3 ] && [ "$minor" -ge 11 ] && [ "$minor" -le 13 ]; then
            PYTHON_BIN="$py_cmd"
            echo "✅ 找到合适的 Python: $py_cmd ($version)"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "❌ 未找到 Python 3.11-3.13"
    echo "请先安装: brew install python@3.11"
    exit 1
fi

# 步骤 2: 备份并删除旧环境
echo ""
echo "📍 步骤 2: 清理旧虚拟环境..."
if [ -d ".venv" ]; then
    echo "备份旧环境到 .venv.backup..."
    rm -rf .venv.backup 2>/dev/null || true
    mv .venv .venv.backup
    echo "✅ 旧环境已备份"
fi

# 步骤 3: 创建新虚拟环境
echo ""
echo "📍 步骤 3: 创建新虚拟环境..."
"$PYTHON_BIN" -m venv .venv
echo "✅ 虚拟环境创建完成"

# 步骤 4: 激活环境并升级 pip
echo ""
echo "📍 步骤 4: 升级 pip..."
source .venv/bin/activate
pip install --upgrade pip --quiet
echo "✅ pip 已升级"

# 步骤 5: 安装依赖
echo ""
echo "📍 步骤 5: 安装项目依赖..."
pip install -r requirements.txt --quiet
echo "✅ 依赖安装完成"

# 步骤 6: 验证安装
echo ""
echo "📍 步骤 6: 验证安装..."
python -c "import pymupdf, yaml, jsonschema, jinja2, anthropic, openai; print('✅ 所有核心模块导入成功')"

# 步骤 7: 运行环境检查
echo ""
echo "📍 步骤 7: 运行系统诊断..."
echo "========================================"
python -m research_pipeline doctor || true
echo "========================================"

# 步骤 8: 提示后续操作
echo ""
echo "✅ 修复完成！"
echo ""
echo "🎯 后续操作："
echo ""
echo "1️⃣  配置 API Key（二选一）："
echo "   Claude:  export ANTHROPIC_API_KEY='sk-ant-xxxxx'"
echo "   OpenAI:  export OPENAI_API_KEY='sk-xxxxx'"
echo ""
echo "2️⃣  运行 Demo 测试（不需要 API Key）："
echo "   python -m research_pipeline demo"
echo "   open outputs/demo/dashboard.html"
echo ""
echo "3️⃣  运行真实分析（需要 API Key）："
echo "   mkdir -p inbox/\$(date +%Y-%m-%d)"
echo "   cp /path/to/*.pdf inbox/\$(date +%Y-%m-%d)/"
echo "   python -m research_pipeline run --date \$(date +%Y-%m-%d) --session 0900"
echo ""
