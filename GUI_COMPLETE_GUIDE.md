# 完整版 GUI 使用指南

## 🎉 已创建完整版本

现在有 3 个文件可以使用：

### 1. launcher.py（Python 启动器）⭐ 推荐

**最简单的启动方式**：

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
python3 launcher.py
```

**功能**：
- ✅ 自动检查环境
- ✅ 自动安装依赖
- ✅ 启动 Web 服务
- ✅ 自动打开浏览器
- ✅ 一键运行

---

### 2. 启动.sh（一键脚本）

**双击或命令行运行**：

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
./启动.sh
```

---

### 3. web_dashboard.py（增强版 Web UI）

**完整功能版本**：

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate
python3 web_dashboard.py
```

**新增功能**：
- ✅ 文件上传
- ✅ 实时进度条
- ✅ 统计信息
- ✅ 运行历史
- ✅ 快速操作按钮
- ✅ 帮助提示

---

## 🚀 快速开始

### 方案 A：使用启动器（最简单）⭐

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
python3 launcher.py
```

### 方案 B：使用增强版 Web UI

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate
python3 web_dashboard.py
```

---

## 📱 界面预览

### 增强版 Web Dashboard 包含：

```
┌─────────────────────────────────────────┐
│  📊 Research Pipeline                    │
│  智能研报分析系统                        │
├─────────────────────────────────────────┤
│  ✅ 服务运行中                           │
│     http://localhost:8080                │
├─────────────────────────────────────────┤
│  🚀 快速操作                             │
│  [🎯 运行 Demo]                          │
│  [📊 查看最新结果]                       │
│  [📁 打开输出文件夹]                     │
│                                         │
│  📁 上传研报 PDF                         │
│  [点击选择文件]                          │
│                                         │
│  ⚡ 运行日志                             │
│  ● 系统就绪                             │
│  ℹ 当前模式: Mock                        │
├─────────────────────────────────────────┤
│  ⚙️ 配置         │  📈 今日统计          │
│  Provider: Mock  │  PDF: 0  运行: 0     │
│  深度分析: 10    │                      │
└─────────────────────────────────────────┘
```

---

## 🎯 使用流程

1. **启动服务**
   ```bash
   python3 launcher.py
   ```

2. **浏览器自动打开**
   - 地址：http://localhost:8080
   - 看到完整的 Dashboard

3. **点击「运行 Demo」**
   - 自动运行测试
   - 实时显示进度
   - 完成后自动提示

4. **点击「查看最新结果」**
   - 打开生成的 Dashboard
   - 查看分析结果

---

## 💡 对比

| 版本 | 文件 | 特点 |
|------|------|------|
| Mock UI | mock_ui.html | 静态预览 |
| 基础版 | web_launcher.py | 基本功能 |
| **完整版** | **web_dashboard.py** | **所有功能** ⭐ |
| 启动器 | launcher.py | 一键启动 ⭐ |

---

## 🔥 现在就试试

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
python3 launcher.py
```

一条命令，全自动！
