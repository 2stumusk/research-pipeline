# 使用指南

> 适用于已完成安装的用户

## 快速开始

### 每日工作流程

1. **准备研报**（早9点或晚9点）
```bash
# 创建日期目录
mkdir -p inbox/$(date +%Y-%m-%d)

# 复制当天收到的 PDF 研报
cp ~/Downloads/研报/*.pdf inbox/$(date +%Y-%m-%d)/
```

2. **运行分析**
```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行分析（0900 或 2100）
python -m research_pipeline run --date $(date +%Y-%m-%d) --session 0900

# 或使用简化启动器
python simple_launcher.py
```

3. **查看结果**
```bash
# 打开 HTML 仪表盘（推荐）
open outputs/daily/$(date +%Y-%m-%d)-0900/dashboard.html

# 或查看 Markdown 报告
open outputs/daily/$(date +%Y-%m-%d)-0900/00-今日研报一页纸.md
```

## 命令行选项

### 基本运行

```bash
python -m research_pipeline run --date YYYY-MM-DD --session 0900
```

### 高级选项

```bash
# 强制重新分析（忽略缓存）
python -m research_pipeline run --date 2026-09-01 --session 0900 --force

# Dry run（不调用 LLM，测试流程）
python -m research_pipeline run --date 2026-09-01 --session 0900 --dry-run

# 跳过深度分析（节省成本）
python -m research_pipeline run --date 2026-09-01 --session 0900 --no-deep-dive

# 跳过质量检查
python -m research_pipeline run --date 2026-09-01 --session 0900 --no-qc

# 指定输入目录
python -m research_pipeline run --date 2026-09-01 --session 0900 --input-dir /path/to/pdfs
```

## 输出文件说明

每次运行生成以下文件结构：

```
outputs/daily/YYYY-MM-DD-HHMM/
├── 00-今日研报一页纸.md          # ⭐ 核心结论（1页）
├── 01-今日必读Top10.md           # ⭐ 最重要的10份
├── 02-主题共识与分歧.md          # 多机构观点对比
├── 03-全量研报索引.csv           # 完整清单
├── 04-风险与催化跟踪.md          # 风险提示
├── 05-质量检查.md                # 数据完整性报告
├── dashboard.html                 # ⭐ 可视化仪表盘
├── deep_dive/                     # Top 10 深度分析
│   ├── 01-xxx.md
│   └── ...
└── machine/                       # 机器可读数据
    ├── run_metadata.json
    ├── report_cards.json
    ├── clusters.json
    ├── deep_dives.json
    └── digest.json
```

**推荐阅读顺序**:
1. `dashboard.html` - 快速浏览全局
2. `00-今日研报一页纸.md` - 核心发现
3. `01-今日必读Top10.md` - 深入阅读
4. `deep_dive/` - 详细分析

## 成本控制

### 查看成本

运行完成后，终端会显示：
```
=============================================================
LLM API Cost Summary
=============================================================
Total Calls: 23
Input Tokens: 458,234
Output Tokens: 89,012
Total Tokens: 547,246
Total Cost: $3.42 USD

Cost by Stage:
  triage: $1.85
  synthesis: $0.68
  deep_dive: $0.78
  qc: $0.11
=============================================================
```

### 降低成本的方法

1. **减少深度分析数量**

编辑 `config/config.yaml`:
```yaml
pipeline:
  deep_dive_n: 5  # 从 10 降到 5，节省约 50%
```

2. **跳过深度分析**
```bash
python -m research_pipeline run --date 2026-09-01 --session 0900 --no-deep-dive
```

3. **使用更便宜的模型**

编辑 `config/config.yaml`:
```yaml
llm:
  provider: "openai"  # OpenAI 通常比 Claude 便宜
```

4. **只在工作日运行**
```yaml
automation:
  schedules: []  # 禁用自动运行，手动触发
```

## 自动化运行

### 设置定时任务

**macOS**:
```bash
bash scripts/install_launchd.sh
```

系统会在每天 09:00 和 21:00 自动运行。

**查看日志**:
```bash
tail -f logs/pipeline.log
```

**卸载自动任务**:
```bash
bash scripts/uninstall_launchd.sh
```

### 修改运行时间

编辑 `config/config.yaml`:
```yaml
automation:
  schedules:
    - "09:00"  # 上午 9 点
    - "21:00"  # 晚上 9 点
    - "15:00"  # 可添加更多时间
```

## 常见场景

### 处理历史数据

```bash
# 分析过去某天的研报
python -m research_pipeline run --date 2026-08-15 --session 0900

# 批量处理多天
for date in 2026-08-{01..31}; do
  python -m research_pipeline run --date $date --session 0900
done
```

### 重新分析某一天

```bash
# 使用 --force 强制重新分析
python -m research_pipeline run --date 2026-08-30 --session 0900 --force
```

### 只分析特定 PDF

```bash
# 创建临时目录
mkdir -p /tmp/special-reports

# 复制感兴趣的 PDF
cp file1.pdf file2.pdf /tmp/special-reports/

# 指定输入目录
python -m research_pipeline run \
  --date 2026-09-01 \
  --session 1500 \
  --input-dir /tmp/special-reports
```

### 调试问题

```bash
# 1. Dry run 测试（不调用 LLM）
python -m research_pipeline run --date 2026-09-01 --session 0900 --dry-run

# 2. 查看详细日志
tail -f logs/pipeline.log

# 3. 环境检查
python -m research_pipeline doctor

# 4. 查看数据库
sqlite3 database/research.db
```

## 配置调优

### 提高质量

```yaml
llm:
  reasoning_effort:
    deep_dive: "high"  # 提高推理深度

pipeline:
  deep_dive_n: 15     # 增加深度分析数量
```

### 提高速度

```yaml
pipeline:
  deep_dive_n: 5      # 减少深度分析
  batch_max_reports: 6  # 增加批处理大小

llm:
  reasoning_effort:
    triage: "low"     # 降低初筛推理深度
```

### 调整评分权重

```yaml
scoring:
  watchlist_relevance: 25  # 提高观察池权重
  novelty: 15             # 降低新颖性权重
```

## 维护任务

### 清理旧数据

```bash
# 清理 30 天前的日志
find logs -name "*.log*" -mtime +30 -delete

# 归档旧输出
tar -czf outputs-$(date +%Y%m).tar.gz outputs/daily/2026-08-*
rm -rf outputs/daily/2026-08-*

# 清理数据库（谨慎！）
# sqlite3 database/research.db "DELETE FROM runs WHERE created_at < date('now', '-90 days');"
```

### 备份数据

```bash
# 备份数据库
cp database/research.db database/research.db.backup

# 备份配置
tar -czf config-backup-$(date +%Y%m%d).tar.gz config/
```

### 更新依赖

```bash
# 更新到最新兼容版本
pip install -r requirements.txt --upgrade

# 生成新的锁定文件
pip freeze > requirements.lock

# 测试
python -m research_pipeline doctor
python -m research_pipeline demo
```

## 下一步

- [配置说明](configuration.md) - 详细配置选项
- [故障排除](troubleshooting.md) - 常见问题解决
- [API 成本优化](cost-optimization.md) - 降低 API 开销
