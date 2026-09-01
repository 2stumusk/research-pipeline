# 🚀 快速启动指南

## 问题：web_launcher.py 没反应

可能原因：
1. Flask 未正确安装
2. 端口问题
3. 环境问题

---

## ✅ 最简单的方法：直接打开 Mock UI

### 方案 1：使用脚本

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
python3 open_ui.py
```

### 方案 2：直接打开 HTML

```bash
open /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline/mock_ui.html
```

### 方案 3：在 Finder 中

1. 打开 Finder
2. 前往：`/Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline`
3. 双击 `mock_ui.html`

---

## 🎯 Mock UI 功能

打开后你可以：
- ✅ 看到完整的界面设计
- ✅ 拖拽 PDF 文件（演示）
- ✅ 切换 Provider 设置
- ✅ 点击按钮看模拟过程
- ✅ 查看统计信息

---

## 📝 真实功能运行

如果要运行真实分析（不是 UI 预览）：

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate
python3 -m research_pipeline demo
open outputs/demo/dashboard.html
```

---

## 💡 推荐

**先试试这个**：

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
python3 open_ui.py
```

会自动在浏览器中打开界面预览！
