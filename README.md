# A股研报智能筛选系统

> **v0.2.0** - 基于 LLM API 的研报信息压缩流水线

一个本地优先的研报筛选系统，帮你从每天 20-100 份券商 PDF 中快速提取核心信息。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ 核心特性

- 🤖 **智能筛选** - 自动评分（0-100）并排序，只读 Top 10
- 🔄 **去重聚类** - 10 家券商写同一事件，自动合并为共识+分歧
- 📊 **结构化输出** - 一页纸摘要 + HTML 仪表盘 + CSV 索引
- 🚀 **自动化运行** - 每天 09:00 和 21:00 自动处理
- 💾 **数据持久化** - SQLite 保存历史，避免重复分析
- 🔌 **多 LLM 支持** - Claude、OpenAI，易于扩展

---

## 📊 每次运行生成什么

```text
outputs/daily/YYYY-MM-DD-HHmm/
├── 00-今日研报一页纸.md          # 核心结论（1 页）
├── 01-今日必读Top10.md           # 最重要的 10 份
├── 02-主题共识与分歧.md          # 同事件多机构观点
├── 03-全量研报索引.csv           # 完整清单
├── 04-风险与催化跟踪.md          # 风险提示
├── 05-质量检查.md                # 数据完整性
├── dashboard.html                 # 可视化仪表盘
├── deep_dive/                     # Top 10 深度分析
└── machine/                       # 机器可读数据
```

**输出示例**：

```markdown
# 今日研报一页纸 - 2026-08-31

## 核心发现
1. 中微公司 Q2 业绩超预期，营收同比+45%
2. 长鑫存储扩产计划提前，带动设备需求
3. 光模块价格承压，但 800G 放量在即

## 风险提示
- 美国制裁政策不确定性
- DRAM 价格波动风险
```

---

## 🚀 快速开始

### 1. 系统要求

- **Python**: 3.11+
- **操作系统**: macOS / Linux / Windows
- **依赖**: PyMuPDF, PyYAML, anthropic/openai

### 2. 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/research-pipeline.git
cd research-pipeline

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -m research_pipeline init
```

### 3. 配置 LLM Provider

**选项 A: Claude（推荐）**

```bash
# 获取 API Key: https://console.anthropic.com/
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# 编辑配置
cp config/config.v0.2.yaml config/config.yaml
# 确认 provider: "claude"
```

**选项 B: OpenAI**

```bash
# 获取 API Key: https://platform.openai.com/
export OPENAI_API_KEY="sk-xxxxx"

# 编辑配置文件
vim config/config.yaml
# 修改: provider: "openai"
```

### 4. 配置观察池

编辑 `config/watchlist.csv`，添加你关注的股票：

```csv
market,ticker,name,holding,priority,theme,notes
CN,688012,中微公司,true,5,半导体设备,当前持仓
CN,002371,北方华创,false,4,半导体设备,观察中
```

### 5. 测试运行

```bash
# 运行 demo（不调用真实 API）
python -m research_pipeline demo

# 查看输出
open outputs/demo/dashboard.html
```

### 6. 正式使用

```bash
# 1. 放入 PDF 研报
mkdir -p inbox/2026-08-31
cp /path/to/reports/*.pdf inbox/2026-08-31/

# 2. 运行分析
./run.sh 0900

# 3. 查看结果
open outputs/daily/2026-08-31-0900/dashboard.html
```

---

## 📖 使用指南

### 目录结构

```text
research_pipeline/
├── config/
│   ├── config.yaml          # 主配置文件
│   └── watchlist.csv        # 观察池
├── inbox/                   # 输入：PDF 研报
│   └── YYYY-MM-DD/
├── outputs/                 # 输出：分析结果
│   └── daily/
├── database/                # SQLite 数据库
├── research_pipeline/       # 源代码
└── tests/                   # 测试
```

### 配置说明

**核心配置** (`config/config.yaml`):

```yaml
llm:
  provider: "claude"              # LLM Provider
  model: ""                       # 留空使用默认
  api_key_env: "ANTHROPIC_API_KEY"
  max_retries: 3
  reasoning_effort:
    triage: "low"                 # 初筛：快速
    synthesis: "medium"           # 综合：中等
    deep_dive: "high"             # 深度：高质量
    qc: "medium"                  # 质检：中等

pipeline:
  batch_max_reports: 4            # 每批处理数量
  top_n: 10                       # Top N 必读
  deep_dive_n: 10                 # 深度分析数量
  archive_after_success: false    # 是否归档
```

**性能调优**:

```yaml
# 降低成本
pipeline:
  deep_dive_n: 5       # 从 10 降到 5，节省 50%

# 提高质量
llm:
  temperature:
    deep_dive: 0.0     # 更确定性的输出
```

### 自动化运行

```bash
# 安装自动任务（macOS）
bash scripts/install_launchd.sh

# 查看日志
tail -f logs/pipeline.log

# 卸载
bash scripts/uninstall_launchd.sh
```

系统会在每天 09:00 和 21:00 自动运行。

---

## 🎯 工作流程

```mermaid
graph LR
    A[PDF 研报] --> B[SHA-256 去重]
    B --> C[文本提取]
    C --> D[LLM 初筛卡]
    D --> E[事件聚类]
    E --> F[Top 10 筛选]
    F --> G[深度分析]
    G --> H[生成报告]
```

**关键步骤**:

1. **入库去重** - SHA-256 哈希，避免重复处理
2. **文本提取** - PyMuPDF 逐页提取，识别扫描页
3. **初筛评分** - LLM 生成结构化卡片（JSON Schema）
4. **事件聚类** - 同一事件多份研报合并
5. **Top 10** - 综合评分、持仓优先级、去重惩罚
6. **深度分析** - 只对最重要的报告做深度解读
7. **质量检查** - 独立 QC，标记数据缺口

---

## 💰 成本估算

**假设**: 每天 60 份研报，Claude 3.5 Sonnet

| 阶段 | Token 用量 | 成本/天 | 成本/月 |
|------|-----------|--------|---------|
| 初筛 (60份) | ~300K input + 60K output | ~$1.80 | ~$54 |
| 深度 (10份) | ~160K input + 80K output | ~$1.68 | ~$50 |
| **总计** | ~460K input + 140K output | **~$3.50** | **~$105** |

**节省成本**:
- 降低 `deep_dive_n` 到 5: 节省 50%
- 使用 OpenAI GPT-4o: 节省 20%
- 只在工作日运行: 节省 30%

---

## 🔧 高级用法

### 命令行选项

```bash
# 指定日期和会话
python -m research_pipeline run \
  --date 2026-08-31 \
  --session 0900

# 强制重新分析
python -m research_pipeline run \
  --date 2026-08-31 \
  --session 0900 \
  --force

# Dry run（不调用 LLM）
python -m research_pipeline run \
  --date 2026-08-31 \
  --session 0900 \
  --dry-run

# 不做深度分析
python -m research_pipeline run \
  --date 2026-08-31 \
  --session 0900 \
  --no-deep-dive
```

### 环境检查

```bash
# 检查环境配置
python -m research_pipeline doctor

# 输出示例：
# ✅ Python 3.11.5
# ✅ SQLite 3.39.5
# ✅ API Key 已设置
# ✅ 配置文件有效
```

---

## 📚 文档

- [快速开始](QUICKSTART.md) - 10分钟上手指南
- [迁移指南](MIGRATION_v0.2.md) - 从 v0.1.x 升级
- [开发指南](7_DAY_GUIDE.md) - 7天完整指南
- [路线图](ROADMAP.md) - 未来计划
- [更新日志](CHANGELOG.md) - 版本历史

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)（待创建）。

### 贡献方向

- 🌐 **新 LLM Provider** - DeepSeek、Kimi、通义千问
- 📊 **数据采集** - 公告、融资余额、价格数据
- 🎨 **可视化** - 更丰富的图表和仪表盘
- 🧪 **测试** - 提高测试覆盖率
- 📖 **文档** - 改进文档和示例

---

## 📄 许可证

[MIT License](LICENSE)

---

## ⚠️ 免责声明

本项目仅供学习研究使用，不构成任何投资建议。

- 投资有风险，入市需谨慎
- 请遵守研报授权范围，不传播原始 PDF
- 输出内容仅供参考，不保证准确性

---

## 🙏 致谢

- [Anthropic Claude](https://www.anthropic.com/) - 强大的 LLM
- [OpenAI](https://openai.com/) - GPT-4 系列模型
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF 处理
- 所有贡献者

---

## 📞 联系方式

- **Issues**: [GitHub Issues](https://github.com/yourusername/research-pipeline/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/research-pipeline/discussions)
- **Email**: your.email@example.com

---

## 🌟 Star History

如果这个项目对你有帮助，请给我们一个 Star ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/research-pipeline&type=Date)](https://star-history.com/#yourusername/research-pipeline&Date)

---

**版本**: v0.2.0  
**最后更新**: 2026-08-31  
**维护者**: [Your Name](https://github.com/yourusername)
