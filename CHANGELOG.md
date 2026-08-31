# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] - 2026-09-01

### 🎉 重大更新

v0.2.0 移除了对 Codex CLI 的依赖，改用通用的 LLM API。这使得项目更易于安装、配置和扩展。

### Added

- **通用 LLM Provider 支持** 🚀
  - 新增 `llm_providers/` 模块，提供统一的 LLM 抽象接口
  - 支持 Anthropic Claude API
  - 支持 OpenAI API (GPT-4o)
  - 易于扩展到其他 LLM Provider

- **新的配置系统**
  - `llm` 配置块替代 `codex` 配置
  - Stage-specific 配置（triage, synthesis, deep_dive, qc）
  - 支持 temperature 和 max_tokens 精细控制
  - 配置加载器 (`config_loader.py`)

- **改进的错误处理**
  - 统一的 `LLMRunnerError` 异常类型
  - 更清晰的错误信息
  - 重试逻辑优化（指数退避）

- **文档完善**
  - `MIGRATION_v0.2.md` - 迁移指南
  - `ROADMAP.md` - 完整路线图
  - `7_DAY_GUIDE.md` - 7天实战指南
  - `COMPLETION_CHECKLIST.md` - 完成度检查清单

- **测试套件**
  - `test_llm_providers.py` - Provider 单元测试
  - `test_architecture.py` - 架构验证测试
  - `test_integration_day2.py` - 集成测试

### Changed

- **配置文件格式** ⚠️ BREAKING CHANGE
  - `codex:` 配置块改为 `llm:`
  - 新增 `provider`, `api_key_env` 字段
  - `reasoning_effort` 语义保留，实现改为 temperature 映射

- **依赖变更** ⚠️ BREAKING CHANGE
  - 移除 Codex CLI 依赖
  - 新增 `anthropic>=0.34,<1`
  - 新增 `openai>=1.0,<2`

- **模块重命名**
  - `codex_runner.py` → `llm_runner.py`（保留兼容层）
  - `CodexRunner` → `LLMRunner`
  - `CodexError` → `LLMRunnerError`

### Deprecated

- `codex_runner` 模块（仍可用，但显示 DeprecationWarning）
  - 将在 v0.3.0 中移除
  - 请使用 `llm_runner` 替代

### Removed

- Codex CLI 二进制依赖
- `codex.binary` 配置项
- `codex.sandbox` 配置项
- `codex.ask_for_approval` 配置项

### Fixed

- 修复多语言路径下的编码问题（改用 API 调用）
- 修复并发调用时的状态管理问题
- 改进 JSON Schema 验证错误提示

### Security

- API Key 从环境变量读取，不再存储在配置文件
- 默认使用 HTTPS 连接
- 增强 Schema 验证以防止注入攻击

---

## [0.1.1] - 2026-08-21

### Added

- 初始发布
- 基于 Codex CLI 的研报分析流水线
- SQLite 数据库持久化
- 每日自动运行（09:00, 21:00）
- Top 10 筛选和深度分析
- HTML 仪表盘输出

### Testing

- 21/21 单元测试通过
- Dry-run 集成测试通过
- 真实 Codex CLI 端到端测试通过

---

## [Unreleased]

### Planned for v0.3.0

- 数据采集模块（公告、融资余额、价格）
- 预期差分析引擎
- 支持更多 LLM Provider（DeepSeek, Kimi）
- Web UI（可选）
- Docker 镜像

---

## Migration Guides

- [v0.1.x → v0.2.0](MIGRATION_v0.2.md)

---

## Notes

### Breaking Changes Summary

#### v0.2.0

**必须**：
1. 安装新依赖：`pip install anthropic openai`
2. 设置 API Key：`export ANTHROPIC_API_KEY="..."`
3. 更新配置文件：`codex:` → `llm:`

**可选**：
- 更新代码导入：`codex_runner` → `llm_runner`（兼容层仍支持）

详见 [MIGRATION_v0.2.md](MIGRATION_v0.2.md)

---

## Version History

| Version | Date | Type | Summary |
|---------|------|------|---------|
| 0.2.0 | 2026-09-01 | Major | 移除 Codex CLI，支持通用 LLM API |
| 0.1.1 | 2026-08-21 | Minor | 初始发布 |

---

[0.2.0]: https://github.com/yourusername/research-pipeline/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/yourusername/research-pipeline/releases/tag/v0.1.1
