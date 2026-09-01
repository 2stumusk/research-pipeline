# GUI 启动器使用指南

## 问题解决：tkinter 不可用

你的 Python 3.14 没有安装 tkinter 支持。

**解决方案**：使用 Web 版本（无需 tkinter）

---

## ✅ 新方案：Web Dashboard

已创建 `web_launcher.py`，使用浏览器作为界面。

### 启动方式

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate
python web_launcher.py
```

**会自动**：
1. 启动本地服务器（http://localhost:5000）
2. 打开浏览器
3. 显示 Web 界面

---

## 🎨 三个界面对比

| 版本 | 文件名 | 运行方式 | 功能 |
|------|--------|---------|------|
| **Mock UI** | mock_ui.html | 浏览器打开 | 界面预览 |
| ~~Desktop GUI~~ | ~~gui_launcher.py~~ | ~~需要 tkinter~~ | ~~不可用~~ |
| **Web Dashboard** ⭐ | web_launcher.py | Python 运行 | **推荐使用** |

---

## 🚀 立即使用

### 方案 1：Mock UI（查看效果）

```bash
open /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline/mock_ui.html
```

### 方案 2：Web Dashboard（真实功能）⭐

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate
python web_launcher.py
```

然后在浏览器中：
1. 点击「运行 Demo」
2. 查看运行日志
3. 点击「查看结果」

---

## 💡 优势对比

### Web Dashboard 优势
- ✅ 无需 tkinter
- ✅ 更美观现代
- ✅ 跨平台（Mac/Windows/Linux）
- ✅ 可以远程访问
- ✅ 易于更新维护

### 使用体验
```
打开浏览器 → http://localhost:5000
↓
选择配置（Mock 模式）
↓
点击「运行 Demo」
↓
实时查看日志
↓
自动打开结果 Dashboard
```

---

## 📝 下一步

现在运行：

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate
python web_launcher.py
```

浏览器会自动打开，然后点击「运行 Demo」即可！
