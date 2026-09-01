# 快速开始指南

## 前置要求

1. **Python 3.11+**
2. **Codex CLI** - 生产环境必需

   安装 Codex CLI 并完成认证，然后验证：
   ```bash
   codex --version
   ```

## 安装步骤

### 1. 克隆并设置环境

```bash
git clone <repository-url>
cd research_pipeline

python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. 初始化项目

```bash
python -m research_pipeline init
```

这会创建必要的目录结构和数据库。

### 3. 验证环境

```bash
python -m research_pipeline doctor
```

确认所有检查通过，特别是 "Codex (生产环境后端)" 一项。

## 使用方式

### 方式 1：命令行（推荐用于生产）

```bash
# 1. 准备 PDF 文件
mkdir -p inbox/2024-01-15
cp /path/to/reports/*.pdf inbox/2024-01-15/

# 2. 运行分析
python -m research_pipeline run --date 2024-01-15 --session 0900

# 3. 查看结果
open outputs/daily/2024-01-15-0900/dashboard.html
```

### 方式 2：图形界面（推荐用于快速测试）

```bash
python gui_app.py
```

在 GUI 中：
1. 点击 "选择 PDF 文件" 上传研报
2. 点击 "开始分析"
3. 分析完成后点击 "查看分析报告"

GUI 会自动：
- 生成唯一的 session ID（`gui-HHMMSS`）
- 创建独立的输入目录
- 处理同名文件冲突
- 解析输出路径（即使 CLI 返回非零退出码）

### 方式 3：仅入库（不调用 Codex）

适用于批量 PDF 入库，稍后再分析：

```bash
python -m research_pipeline ingest --date 2024-01-15
```

## 输出文件说明

所有输出位于 `outputs/daily/<date>-<session>/`：

| 文件 | 说明 |
|------|------|
| `dashboard.html` | 交互式仪表板（推荐首选） |
| `00-今日研报一页纸.md` | 一页核心总结 |
| `01-今日必读Top10.md` | 优先级排序的必读列表 |
| `02-主题共识与分歧.md` | 事件聚类和机构分歧 |
| `03-全量研报索引.csv` | 全量研报索引表 |
| `04-风险与催化跟踪.md` | 风险信号和催化事件 |
| `deep_dive/*.md` | 重点研报深度分析 |
| `machine/*.json` | 结构化数据（供程序使用） |

## 常见问题

### Q: Codex 检查失败？

确保已安装并登录 Codex CLI：

```bash
codex --version
codex login  # 如果尚未登录
```

### Q: 如何自定义配置？

编辑 `config/config.yaml` 或创建 `config.local.yaml` 覆盖默认值：

```yaml
# config.local.yaml
codex:
  max_parallel: 5  # 增加并行数

pipeline:
  top_n: 15        # Top N 从 10 改为 15
  deep_dive_n: 15
```

### Q: 支持哪些 PDF？

- 格式：标准 PDF（文本型或 OCR 后）
- 建议：券商研报、行业报告、宏观研究
- 不支持：纯扫描版（需先 OCR）、加密 PDF

### Q: 如何处理敏感研报？

- 所有 PDF 和提取文本保存在本地，不会上传到外部服务
- Codex 在沙箱中执行，默认为 `read-only` 模式
- 可通过 `config/config.yaml` 中的 `codex.sandbox` 调整安全级别

### Q: 实验性 Claude/OpenAI provider 是什么？

这些是显式构造专用的实验性 provider，不会从正式流水线调用，不会上传报告内容。正式分析使用 Codex。

### Q: Dry run 模式是什么？

Dry run 跳过 Codex 调用，使用本地兜底逻辑生成输出，用于：
- 测试 PDF 提取
- 验证配置
- 在 Codex 不可用时查看基本结构

```bash
python -m research_pipeline run --date 2024-01-15 --dry-run
```

## 下一步

- 阅读 [README.md](README.md) 了解完整架构
- 查看 [AGENTS.md](AGENTS.md) 了解研究纪律和评分标准
- 参考 [MIGRATION_v0.2.md](MIGRATION_v0.2.md)（如果从旧版本升级）
- 运行测试：`bash scripts/run_tests.sh`

## 技术支持

遇到问题？

1. 运行 `python -m research_pipeline doctor` 诊断环境
2. 检查 `logs/pipeline.log` 查看详细日志
3. 确认 Codex CLI 版本：`codex --version`

---

**提示**: 首次运行建议使用少量 PDF（3-5 份）测试流程，确认无误后再批量处理。
