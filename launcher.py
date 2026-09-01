#!/usr/bin/env python3
"""
Research Pipeline - 完整启动器
方案：Python 启动脚本 + Web UI
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def main():
    print("="*70)
    print("  📊 Research Pipeline - 完整版启动器")
    print("="*70)
    print()
    print("  功能：")
    print("  • 自动启动 Web 服务")
    print("  • 自动打开浏览器")
    print("  • 在浏览器中操作")
    print()
    print("="*70)
    print()

    # 获取项目根目录
    project_root = Path(__file__).parent

    # 检查虚拟环境
    venv_python = project_root / ".venv" / "bin" / "python3"
    if not venv_python.exists():
        print("❌ 错误：找不到虚拟环境")
        print(f"   期望路径: {venv_python}")
        print()
        print("请先运行：")
        print("  python3 -m venv .venv")
        print("  source .venv/bin/activate")
        print("  pip install -r requirements.txt")
        return 1

    print("✅ 虚拟环境检查通过")
    print()

    # 检查 Flask
    try:
        result = subprocess.run(
            [str(venv_python), "-c", "import flask"],
            capture_output=True,
            timeout=5
        )
        if result.returncode != 0:
            print("⚠️  Flask 未安装，正在安装...")
            subprocess.run(
                [str(venv_python), "-m", "pip", "install", "flask"],
                check=True
            )
            print("✅ Flask 安装完成")
    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1

    print()
    print("🚀 启动 Web 服务...")
    print()

    # 启动 Web 服务
    web_launcher = project_root / "web_launcher.py"

    try:
        # 使用 subprocess 启动
        process = subprocess.Popen(
            [str(venv_python), str(web_launcher)],
            cwd=str(project_root)
        )

        print("✅ Web 服务已启动")
        print("📍 地址: http://localhost:8080")
        print()
        print("⏹️  按 Ctrl+C 停止服务")
        print()
        print("="*70)

        # 等待服务启动
        time.sleep(2)

        # 自动打开浏览器
        print("🌐 正在打开浏览器...")
        webbrowser.open("http://localhost:8080")

        # 等待用户中断
        process.wait()

    except KeyboardInterrupt:
        print()
        print("="*70)
        print("🛑 正在停止服务...")
        process.terminate()
        process.wait()
        print("✅ 服务已停止")
        print("="*70)
        return 0

    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
