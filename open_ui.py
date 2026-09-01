#!/usr/bin/env python3
"""
最简单的测试版本 - 直接打开 Mock UI
"""

import webbrowser
from pathlib import Path

# 获取当前目录
current_dir = Path(__file__).parent
mock_ui = current_dir / "mock_ui.html"

print("="*60)
print("📊 Research Pipeline - 打开 Mock UI")
print("="*60)
print(f"文件: {mock_ui}")
print("")

if mock_ui.exists():
    print("✅ 找到 mock_ui.html")
    print("🌐 正在打开浏览器...")
    webbrowser.open(str(mock_ui))
    print("")
    print("✅ 已在浏览器中打开！")
    print("")
    print("💡 这是界面预览版本")
    print("💡 可以拖拽文件、查看界面效果")
    print("")
else:
    print("❌ 找不到 mock_ui.html")
    print(f"请确认文件存在: {mock_ui}")

print("="*60)
