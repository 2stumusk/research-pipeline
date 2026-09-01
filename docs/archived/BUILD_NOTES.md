# 构建与验收记录

版本：0.2.0  
验收日期：2026-09-01

---

## v0.2.0 - LLM API 重构

### 新增功能

- **通用 LLM Provider 架构**
  - 抽象接口 (`llm_providers/base.py`)
  - Claude Provider (`llm_providers/claude.py`)
  - OpenAI Provider (`llm_providers/openai_provider.py`)
  - 工厂模式 (`llm_providers/__init__.py`)

- **统一调用接口**
  - `llm_runner.py` 替代 `codex_runner.py`
  - 重试逻辑（指数退避）
  - 结构化输出验证
  - Stage-specific 配置

- **新配置系统**
  - `config_loader.py` - 配置加载器
  - `config.v0.2.yaml` - 新格式模板
  - 向后兼容旧格式

- **向后兼容层**
  - `codex_runner_compat_layer.py`
  - 旧代码无需修改即可运行
  - DeprecationWarning 提示

### 技术改进

- 移除 Codex CLI 依赖
- 直接使用 LLM API（降低延迟）
- 更清晰的错误信息
- 更好的类型提示

### 测试覆盖

**架构验证测试** - ✅ 通过
- 配置加载测试
- Runner 创建测试
- Schema 验证测试
- 向后兼容测试

**Provider 测试** - ⏳ 需要 API Key
- 基础文本生成
- 结构化输出
- 重试逻辑

**集成测试** - ⏳ 需要真实 PDF
- PDF 提取
- 初筛卡生成
- 深度分析
- 输出渲染

### 已知限制

- 扫描页仍不支持 OCR
- 需要手动设置 API Key
- 某些 Provider 特定功能未实现
- 单元测试覆盖率待提高

---

## v0.1.1 - 初始发布

### 已实现

- 递归发现 PDF、SHA-256 去重、逐页文本提取、扫描页识别；
- SQLite 保存研报、初筛卡、运行记录、事件聚类和历史深度分析；
- Codex CLI 非交互调用，按阶段设置推理强度，并以 JSON Schema 强制统一结构；
- 重要性、方向、置信度分开评分，重大持仓负面信息只提高阅读优先级，不篡改方向；
- 同事件语义聚类、机构共识与分歧、重复惩罚；
- Top 10、重点深度分析、历史增量比较、风险与催化跟踪；
- Markdown、UTF-8 BOM CSV、自包含 HTML 仪表盘、机器可读 JSON；
- 09:00/21:00 增量运行、已分析卡片和深度分析复用；
- macOS LaunchAgent 自动检查与补跑；
- 单批失败不阻断全局，聚类、综合摘要和 QC 均有明确的降级路径。
- `success` / `partial` / `dry_run` / `no_input` 状态分层，并记录物理 PDF、哈希去重、提取成功和降级卡覆盖率；
- 严格 `YYYY-MM-DD` 日期验证，防止意外路径穿越；
- 成功后可选非破坏性归档复制，以及可配置 LaunchAgent 检查间隔；
- Codex 调用使用一次性 ASCII 工作区和 UTF-8 安全子进程环境，已解决当前 macOS/Codex CLI 在中文项目路径下的工具路径编码崩溃。

## 验收结果

- Python 单元与集成测试：21/21 通过；
- JSON Schema：全部通过 Draft 2020-12 校验；
- 完整 dry-run：通过；
- 本地替身 Codex 全链路：通过，包括命令组装、结构化输出校验、早晚两次运行与历史复用；
- 真实 Codex CLI `0.148.0-alpha.21` 单次结构化 Schema 冒烟：通过；
- 真实 Codex CLI 三阶段临时 PDF 端到端：`status=success`、`fallback_card_count=0`、`errors=[]`、11 个必需产物无缺失；
- Python `compileall`：通过；
- 全部 Shell 脚本 `bash -n`：通过；
- Python 项目 wheel 构建：通过；
- 全新复制目录中的 `init` 与 `demo` 冒烟测试：通过。

## 尚未实测的边界

【未获取到】约 60 份真实授权券商 PDF 的完整每日批次，因此不对真实研报输出质量、页码命中率、总耗时或账户调用量作未经验证的声明。已用临时虚构 PDF 验证真实账户下的提取、初筛、聚类、综合摘要、结构校验与产物落盘链路。

## 设计边界

- 默认不自动 OCR；疑似扫描页只标记，避免批量误识别和高成本；
- 默认关闭网络搜索，外部事实核验应与研报原文分析分开；
- 模型名留空，使用账户当时可用的默认 Codex 模型，避免硬编码模型退役；
- 系统用于个人研究信息压缩，不替代对原文、公告、财报和交易风险的独立判断。
