# A股研报智能筛选系统

> **版本**: v0.2.0（已优化）  
> **最后更新**: 2026-09-01

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
- 💰 **成本追踪** - 实时显示 API 使用成本

---

## 🚀 快速开始

### 1. 安装

```bash
# 克隆项目
git clone <repository-url>
cd research_pipeline

# 创建虚拟环境（Python 3.11+）
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖（推荐使用锁定版本）
pip install -r requirements.lock
```

### 2. 配置 LLM Provider

**Claude（推荐）**:
```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
```

**OpenAI**:
```bash
export OPENAI_API_KEY="sk-xxxxx"
```

### 3. 测试运行

```bash
# 运行 demo（不需要 API Key）
python -m research_pipeline demo

# 查看结果
open outputs/demo/dashboard.html
```

### 4. 正式使用

```bash
# 1. 放入 PDF 研报
mkdir -p inbox/$(date +%Y-%m-%d)
cp /path/to/reports/*.pdf inbox/$(date +%Y-%m-%d)/

# 2. 运行分析
python -m research_pipeline run --date $(date +%Y-%m-%d) --session 0900

# 3. 查看结果
open outputs/daily/$(date +%Y-%m-%d)-0900/dashboard.html
```

**完整文档**: 查看 [`docs/`](docs/) 目录
- [安装指南](docs/installation.md)
- [使用指南](docs/usage.md)
- [故障排除](docs/troubleshooting.md)

---

## 📊 每次运行生成什么

```text
outputs/daily/YYYY-MM-DD-HHmm/
├── dashboard.html                 # ⭐ 可视化仪表盘
├── 00-今日研报一页纸.md          # ⭐ 核心结论（1 页）
├── 01-今日必读Top10.md           # ⭐ 最重要的 10 份
├── 02-主题共识与分歧.md          # 同事件多机构观点
├── 03-全量研报索引.csv           # 完整清单
├── 04-风险与催化跟踪.md          # 风险提示
├── 05-质量检查.md                # 数据完整性
├── deep_dive/                     # Top 10 深度分析
└── machine/                       # 机器可读数据
```

---

## 💰 成本估算

**假设**: 每天 60 份研报，Claude 3.5 Sonnet

| 阶段 | Token 用量 | 成本/天 | 成本/月 |
|------|-----------|--------|---------|
| 初筛 (60份) | ~300K input + 60K output | ~$1.80 | ~$54 |
| 深度 (10份) | ~160K input + 80K output | ~$1.68 | ~$50 |
| **总计** | ~460K input + 140K output | **~$3.50** | **~$105** |

**运行后自动显示实际成本**:
```
=============================================================
LLM API Cost Summary
=============================================================
Total Cost: $3.42 USD

Cost by Stage:
  triage: $1.85
  synthesis: $0.68
  deep_dive: $0.78
  qc: $0.11
=============================================================
```

**降低成本**: 参见 [使用指南 - 成本控制](docs/usage.md#成本控制)

---

## 🆕 v0.2.0 优化亮点

✅ **架构清理**
- 统一使用新 LLM 架构
- 清理所有 Codex CLI 遗留引用
- 更准确的错误提示

✅ **成本追踪**
- 实时记录 API 使用
- 按阶段分类成本
- 运行结束自动显示摘要

✅ **文档改进**
- 整合为清晰的文档结构
- 删除过时的诊断报告
- 新增完整的安装、使用、故障排除指南

✅ **依赖管理**
- 收紧版本范围，提升稳定性
- 新增 `requirements.lock` 确保可重现性

✅ **日志管理**
- 实现日志轮转（10MB，保留 5 个备份）
- 自动清理旧日志（30 天）

详见 [优化报告](OPTIMIZATION_REPORT.md)

---

## 📚 文档

- **[安装指南](docs/installation.md)** - 完整安装步骤和环境配置
- **[使用指南](docs/usage.md)** - 日常使用、成本控制、配置调优
- **[故障排除](docs/troubleshooting.md)** - 常见问题诊断和解决
- **[优化报告](OPTIMIZATION_REPORT.md)** - 项目优化总结

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

## 📄 许可证

[MIT License](LICENSE)

---

**版本**: v0.2.0（已优化）  
**最后更新**: 2026-09-01  
**状态**: ✅ 生产就绪
