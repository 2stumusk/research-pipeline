# 🔧 问题排查和解决

## 问题：点击"运行 Demo"没反应

### 可能原因

1. **端口已被占用**
   - 端口 8080 已有 Python 进程在运行（PID 25657）
   - 需要先停止旧服务

2. **JavaScript 请求未发送**
   - 浏览器控制台可能有错误
   - 需要检查网络请求

---

## ✅ 解决方案

### 方案 1：重启服务（推荐）

```bash
# 1. 停止旧服务
pkill -f "web_launcher\|web_dashboard\|Python.*8080"

# 2. 启动调试版本
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate
python3 web_debug.py
```

**调试版本特点**：
- ✅ 详细日志输出
- ✅ 控制台实时反馈
- ✅ 更简单的界面
- ✅ 更清晰的错误提示

---

### 方案 2：直接运行 Demo（不用 Web UI）

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate
python3 -m research_pipeline demo
open outputs/demo/dashboard.html
```

这个方法**100%可靠**，直接看结果。

---

### 方案 3：检查浏览器控制台

1. 在浏览器中按 **F12** 或 **Cmd+Option+I**
2. 点击 **Console** 标签
3. 点击「运行 Demo」按钮
4. 查看是否有错误信息

---

## 🐛 调试步骤

如果还是不行，请告诉我：

1. **浏览器控制台显示什么？**
   - 按 F12 查看

2. **终端有输出吗？**
   - 运行服务的终端窗口

3. **点击按钮后有任何反应吗？**
   - 按钮颜色变化？
   - 页面刷新？

---

## 💡 建议

**现在试试方案 2**（最可靠）：

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate
python3 -m research_pipeline demo
```

等 1-2 分钟后：

```bash
open outputs/demo/dashboard.html
```

这个**一定能看到结果**！
