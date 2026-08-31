# Research Pipeline v0.2.0 使用指南

> 10 分钟快速上手

---

## 🎯 三种使用模式

### 模式 1：Mock 模式（推荐新手）✨

**无需 API Key，立即可用！**

```bash
# 1. 进入项目目录
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline

# 2. 激活虚拟环境
source .venv/bin/activate

# 3. 复制配置文件
cp config/config.v0.2.yaml config/config.yaml

# 4. 编辑配置，设置 provider 为 mock
vim config/config.yaml
# 修改这一行：
#   provider: "mock"

# 5. 运行 Demo
python -m research_pipeline demo

# 6. 查看结果
open outputs/demo/dashboard.html
```

**✅ 完成！你已经看到完整的输出格式了。**

---

### 模式 2：Claude API（真实模式）

```bash
# 1. 获取 API Key
# 访问: https://console.anthropic.com/
# 注册 → 获取 API Key

# 2. 设置环境变量
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# 3. 编辑配置
vim config/config.yaml
# 确认：
#   provider: "claude"
#   api_key_env: "ANTHROPIC_API_KEY"

# 4. 准备研报
mkdir -p inbox/2026-09-01
cp ~/Downloads/*.pdf inbox/2026-09-01/

# 5. 运行分析
./run.sh 0900

# 6. 查看结果
open outputs/daily/2026-09-01-0900/dashboard.html
```

**成本**: ~$3-5/天（60 份研报）

---

### 模式 3：OpenAI API

```bash
# 1. 获取 API Key
# 访问: https://platform.openai.com/

# 2. 设置环境变量
export OPENAI_API_KEY="sk-xxxxx"

# 3. 编辑配置
vim config/config.yaml
# 修改：
#   provider: "openai"
#   api_key_env: "OPENAI_API_KEY"

# 4. 运行
./run.sh 0900
```

**成本**: ~$2.5-4/天（60 份研报）

---

## 📂 日常使用流程

### 每天早上

```bash
# 1. 放入昨晚下载的研报
mkdir -p inbox/$(date +%Y-%m-%d)
cp ~/Downloads/研报/*.pdf inbox/$(date +%Y-%m-%d)/

# 2. 运行分析
./run.sh 0900

# 3. 查看结果
open outputs/daily/$(date +%Y-%m-%d)-0900/dashboard.html
```

### 每天晚上

```bash
# 1. 放入下午的研报
cp ~/Downloads/研报/*.pdf inbox/$(date +%Y-%m-%d)/

# 2. 运行分析
./run.sh 2100

# 3. 查看结果
open outputs/daily/$(date +%Y-%m-%d)-2100/dashboard.html
```

---

## ⚙️ 配置观察池

编辑 `config/watchlist.csv`：

```csv
market,ticker,name,holding,priority,theme,notes
CN,688012,中微公司,true,5,半导体设备,重点持仓
CN,002371,北方华创,false,4,半导体设备,观察
```

**字段说明**：
- `holding`: true=持仓，影响评分权重
- `priority`: 1-5，优先级
- `theme`: 主题分类

---

## 🔧 常用命令

```bash
# 环境检查
python -m research_pipeline doctor

# Dry-run（测试流程，不调用 LLM）
python -m research_pipeline run --date 2026-09-01 --dry-run

# 强制重新分析
python -m research_pipeline run --date 2026-09-01 --force

# 只做初筛，不做深度分析
python -m research_pipeline run --date 2026-09-01 --no-deep-dive
```

---

## 📊 输出说明

```
outputs/daily/YYYY-MM-DD-HHmm/
├── 00-今日研报一页纸.md          # ⭐ 核心结论（1页）
├── 01-今日必读Top10.md           # ⭐ 最重要的 10 份
├── 02-主题共识与分歧.md          # 同事件多机构观点
├── 03-全量研报索引.csv           # Excel 可打开
├── 04-风险与催化跟踪.md          # 风险提示
├── 05-质量检查.md                # 数据完整性
├── dashboard.html                 # ⭐⭐⭐ 推荐！
└── deep_dive/                     # 深度分析
```

---

## ❓ 常见问题

### Q: 提示找不到 API Key

```bash
# 检查
echo $ANTHROPIC_API_KEY

# 重新设置
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# 永久设置
echo 'export ANTHROPIC_API_KEY="..."' >> ~/.zshrc
source ~/.zshrc
```

### Q: 想先测试不花钱

**使用 Mock 模式！** 见上文"模式 1"

### Q: 成本太高

```yaml
# 编辑 config/config.yaml
pipeline:
  deep_dive_n: 5  # 从 10 降到 5，节省 50%
```

### Q: 输出质量不好

```yaml
llm:
  temperature:
    deep_dive: 0.0  # 更确定性
  provider: "claude"  # Claude 通常更好
```

---

## 🚀 自动化

```bash
# 安装定时任务（每天 09:00 和 21:00 自动运行）
bash scripts/install_launchd.sh

# 查看日志
tail -f logs/pipeline.log

# 卸载
bash scripts/uninstall_launchd.sh
```

---

## 📚 更多帮助

- 完整文档：`README.md`
- 迁移指南：`MIGRATION_v0.2.md`
- 7天教程：`7_DAY_GUIDE.md`

---

**立即开始**：

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate
python -m research_pipeline demo
open outputs/demo/dashboard.html
```

✅ 无需配置，立即可用！
