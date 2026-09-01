#!/usr/bin/env python3
"""
Research Pipeline - 极简启动器
无需 Web UI，直接命令行交互
"""

import subprocess
import sys
import time
from pathlib import Path

def print_header():
    print("\n" + "="*70)
    print("  📊 Research Pipeline - 极简启动器")
    print("="*70 + "\n")

def print_menu():
    print("请选择操作：")
    print()
    print("  1. 运行 Demo（测试示例）")
    print("  2. 运行真实分析")
    print("  3. 查看最新结果")
    print("  4. 打开输出文件夹")
    print("  5. 退出")
    print()

def run_demo():
    print("\n" + "="*70)
    print("🚀 运行 Demo")
    print("="*70 + "\n")

    project_root = Path(__file__).parent
    venv_python = project_root / ".venv" / "bin" / "python3"

    try:
        result = subprocess.run(
            [str(venv_python), "-m", "research_pipeline", "demo"],
            cwd=str(project_root)
        )

        if result.returncode == 0:
            print("\n" + "="*70)
            print("✅ Demo 完成！")
            print("="*70)
            print()

            dashboard = project_root / "outputs/demo/dashboard.html"
            if dashboard.exists():
                print("📊 正在打开结果...")
                subprocess.run(["open", str(dashboard)])
            else:
                print("⚠️  未找到输出文件")
        else:
            print("\n❌ Demo 运行失败")

    except Exception as e:
        print(f"\n❌ 错误: {e}")

    input("\n按 Enter 继续...")

def open_results():
    project_root = Path(__file__).parent
    dashboard = project_root / "outputs/demo/dashboard.html"

    if dashboard.exists():
        print("\n📊 正在打开结果...")
        subprocess.run(["open", str(dashboard)])
        time.sleep(1)
    else:
        print("\n⚠️  结果文件不存在，请先运行 Demo")
        input("\n按 Enter 继续...")

def open_folder():
    project_root = Path(__file__).parent
    output_dir = project_root / "outputs"

    print("\n📁 正在打开输出文件夹...")
    subprocess.run(["open", str(output_dir)])
    time.sleep(1)

def main():
    while True:
        print_header()
        print_menu()

        choice = input("输入选项 (1-5): ").strip()

        if choice == "1":
            run_demo()
        elif choice == "2":
            print("\n功能开发中...")
            input("\n按 Enter 继续...")
        elif choice == "3":
            open_results()
        elif choice == "4":
            open_folder()
        elif choice == "5":
            print("\n👋 再见！\n")
            break
        else:
            print("\n❌ 无效选项\n")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 再见！\n")
        sys.exit(0)
