# Research Pipeline 开源完善路线图

## 目标
从"个人工具"升级为"可开源的通用框架"

## 版本规划

### v0.2.0 - 通用LLM支持（Week 1-2）⭐ 当前优先级

**目标**：去除Codex CLI依赖，支持多种LLM后端。

**核心改动**：
- [ ] 创建 `llm_providers/` 模块
  - [ ] `base.py` - LLM Provider抽象接口
  - [ ] `claude.py` - Anthropic Claude API
  - [ ] `openai.py` - OpenAI API (GPT-4)
  - [ ] `ollama.py` - 本地Ollama模型（可选）
  
- [ ] 重构 `codex_runner.py` → `llm_runner.py`
  - [ ] 统一的JSON Schema验证
  - [ ] 统一的错误处理
  - [ ] 统一的重试逻辑
  - [ ] 保持原有的沙箱安全设计

- [ ] 配置文件更新
  ```yaml
  llm:
    provider: "claude"  # claude, openai, ollama
    model: "claude-3-5-sonnet-20241022"  # 或留空使用默认
    api_key_env: "ANTHROPIC_API_KEY"  # 环境变量名
    reasoning_effort:
      triage: low
      synthesis: medium
      deep_dive: high
      qc: medium
  ```

- [ ] 更新测试
  - [ ] 修改 `test_codex_command_and_schemas.py` 支持多provider
  - [ ] 添加mock测试（不实际调用API）

**验收标准**：
- [ ] 用Claude API完整跑通一次流程（5份PDF）
- [ ] 用OpenAI API完整跑通一次流程（5份PDF）
- [ ] 输出质量与原Codex版本相当
- [ ] 所有测试通过

**预估工作量**：12-16小时

---

### v0.3.0 - 数据采集模块（Week 3-4）

**目标**：扩展到不仅处理研报，还能采集公告、融资余额、价格数据。

**新增模块**：
- [ ] `collectors/` - 数据采集
  - [ ] `announcement.py` - A股公告爬虫（巨潮资讯/东方财富）
  - [ ] `financing.py` - 融资融券数据（交易所官网）
  - [ ] `price.py` - 价格数据（tushare/akshare免费接口）
  - [ ] `base.py` - 数据采集抽象接口

- [ ] 数据库扩展
  ```sql
  CREATE TABLE IF NOT EXISTS announcements (
      announcement_id TEXT PRIMARY KEY,
      ticker TEXT NOT NULL,
      title TEXT NOT NULL,
      announce_date TEXT NOT NULL,
      category TEXT NOT NULL,
      content_hash TEXT NOT NULL,
      raw_text TEXT,
      analyzed_at TEXT
  );
  
  CREATE TABLE IF NOT EXISTS financing_data (
      date TEXT NOT NULL,
      ticker TEXT NOT NULL,
      financing_balance REAL,
      financing_buy REAL,
      financing_sell REAL,
      PRIMARY KEY (date, ticker)
  );
  
  CREATE TABLE IF NOT EXISTS price_data (
      date TEXT NOT NULL,
      ticker TEXT NOT NULL,
      open REAL,
      high REAL,
      low REAL,
      close REAL,
      volume REAL,
      PRIMARY KEY (date, ticker)
  );
  ```

- [ ] CLI扩展
  ```bash
  # 采集指定日期的公告
  python -m research_pipeline collect announcements --date 2026-08-31
  
  # 采集融资余额
  python -m research_pipeline collect financing --date 2026-08-31
  
  # 采集价格数据
  python -m research_pipeline collect price --date 2026-08-31 --days 30
  
  # 一键采集全部
  python -m research_pipeline collect all --date 2026-08-31
  ```

- [ ] 配置文件
  ```yaml
  collectors:
    announcement:
      enabled: true
      source: "eastmoney"  # eastmoney, cninfo
      rate_limit: 1.0  # 秒/请求
    
    financing:
      enabled: true
      source: "sse"  # sse(上交所), szse(深交所)
    
    price:
      enabled: true
      source: "akshare"  # akshare, tushare
      api_token_env: "TUSHARE_TOKEN"  # 可选
  ```

**验收标准**：
- [ ] 能采集指定股票列表的公告（watchlist.csv）
- [ ] 能采集融资余额数据
- [ ] 能采集价格数据
- [ ] 数据存入数据库，有去重机制
- [ ] 错误处理完善（限流、超时、数据源失效）

**预估工作量**：16-20小时

---

### v0.4.0 - 预期差分析与可视化（Week 5-6）

**目标**：整合研报、公告、融资余额、价格，生成"预期差雷达"。

**新增模块**：
- [ ] `analyzers/` - 分析引擎
  - [ ] `expectation_diff.py` - 预期差计算
  - [ ] `evidence_tracker.py` - 证据等级跟踪
  - [ ] `signal_detector.py` - 信号检测（融资余额异常、价格突破等）

- [ ] 新的输出报告
  ```text
  outputs/daily/YYYY-MM-DD-HHmm/
  ├── 06-预期差雷达.md          # 新增
  ├── 07-证据跟踪.md            # 新增
  ├── 08-异常信号.md            # 新增
  └── radar_dashboard.html      # 新增可视化
  ```

- [ ] 预期差计算逻辑
  ```python
  # 对比上一份研报的变化
  - 盈利预测调整幅度
  - 目标价调整幅度
  - 评级变化
  - 新增催化剂
  - 风险变化
  
  # 对比公告的一致性
  - 研报预测 vs 实际公告
  - 提前量、准确度
  
  # 对比市场表现
  - 融资余额变化 vs 研报观点
  - 价格走势 vs 目标价
  ```

**验收标准**：
- [ ] 能识别研报观点的变化（相对上一份）
- [ ] 能识别研报与公告的一致性
- [ ] 能识别融资余额异常（单日+30%等）
- [ ] 生成可读性强的预期差报告

**预估工作量**：16-20小时

---

### v0.5.0 - 开源准备（Week 7-8）

**目标**：完善文档、示例、部署指南，准备开源发布。

**任务清单**：

- [ ] 文档完善
  - [ ] `README_EN.md` - 英文版README
  - [ ] `CONTRIBUTING.md` - 贡献指南
  - [ ] `CHANGELOG.md` - 版本历史
  - [ ] `docs/ARCHITECTURE.md` - 架构设计文档
  - [ ] `docs/API.md` - API文档
  - [ ] `docs/FAQ.md` - 常见问题
  - [ ] `docs/DEPLOYMENT.md` - 部署指南

- [ ] 示例项目
  - [ ] `examples/basic/` - 基础示例（5份PDF）
  - [ ] `examples/multi_day/` - 多日运行示例
  - [ ] `examples/custom_scoring/` - 自定义评分逻辑
  - [ ] `examples/notification/` - 通知集成（企业微信、钉钉）

- [ ] Docker支持
  - [ ] `Dockerfile` - 容器化部署
  - [ ] `docker-compose.yml` - 一键启动
  - [ ] 环境变量配置说明

- [ ] CI/CD
  - [ ] GitHub Actions - 自动测试
  - [ ] GitHub Actions - 自动发布PyPI
  - [ ] 代码质量检查（black, ruff, mypy）

- [ ] 开源许可
  - [ ] 选择许可证（建议MIT或Apache 2.0）
  - [ ] 添加LICENSE文件
  - [ ] 检查第三方依赖的许可兼容性

- [ ] 数据合规
  - [ ] 研报使用指南（提醒用户遵守授权）
  - [ ] 数据源合规说明
  - [ ] 爬虫robots.txt遵守

**验收标准**：
- [ ] 新用户能在30分钟内跑通demo
- [ ] 文档覆盖率>80%
- [ ] Docker镜像能正常运行
- [ ] 所有测试在CI中通过

**预估工作量**：16-20小时

---

## 技术债务清单

### 高优先级
- [ ] 添加类型标注（mypy检查）
- [ ] 添加日志级别控制
- [ ] 优化数据库索引（大批量数据性能）
- [ ] 添加配置验证（启动时检查config.yaml）

### 中优先级
- [ ] 支持多语言研报（英文、日文）
- [ ] 支持自定义Prompt模板
- [ ] Web UI（可选，基于Streamlit）
- [ ] 通知集成（企业微信、Slack、Telegram）

### 低优先级
- [ ] 支持更多LLM（文心一言、Kimi、通义千问）
- [ ] 云端部署模板（AWS、阿里云、腾讯云）
- [ ] 数据导出（Excel、Word报告）

---

## 里程碑

| 版本 | 完成时间 | 核心特性 |
|------|---------|----------|
| v0.1.1 | ✅ 2026-08-21 | Codex版本，个人使用 |
| v0.2.0 | Week 2 | 通用LLM支持 |
| v0.3.0 | Week 4 | 数据采集模块 |
| v0.4.0 | Week 6 | 预期差分析 |
| v0.5.0 | Week 8 | 开源发布 |

---

## 开源发布检查清单

发布前确认：
- [ ] 所有测试通过
- [ ] 文档完整（中英文）
- [ ] 示例可运行
- [ ] Docker镜像可用
- [ ] LICENSE已添加
- [ ] 敏感信息已清理（API key、个人路径等）
- [ ] GitHub仓库设置完成（README、Topics、Description）
- [ ] 发布到PyPI
- [ ] 发布公告（V2EX、掘金、Reddit r/python）

---

## 社区建设计划

### 内容输出
- [ ] 技术博客系列（每周1篇）
  - "如何用Python+LLM做投资研究"
  - "从个人工具到开源项目的8周改造"
  - "研报分析的工程化实践"
  
- [ ] 视频教程（B站、YouTube）
  - 10分钟快速上手
  - 30分钟深度讲解
  - 1小时自定义开发

### 社区渠道
- [ ] GitHub Discussions - 技术讨论
- [ ] Discord服务器 - 实时交流
- [ ] 知识星球/Patreon - 付费支持（可选）

### 贡献者激励
- [ ] Good First Issue标签
- [ ] 贡献者名单
- [ ] 月度贡献者感谢

---

## 成功指标

### 技术指标
- GitHub Stars: 100+ (3个月)
- PyPI下载量: 1000+/月
- Issue响应时间: <48小时
- PR合并率: >60%

### 社区指标
- 活跃贡献者: 5+ 
- Discord成员: 100+
- 技术博客阅读: 5000+

### 商业指标（可选）
- 技术咨询: 2-3单/年
- 付费支持: 5-10人
- 企业定制: 1-2单/年

---

## 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| LLM API成本高 | 高 | 文档强调成本预估，提供本地模型选项 |
| 数据源失效 | 中 | 多数据源备份，社区贡献新源 |
| 法律合规问题 | 高 | 明确使用条款，不提供数据 |
| 维护时间不足 | 中 | 寻找co-maintainer，设定明确边界 |
| 用户期望过高 | 中 | README明确"研究工具，非投资建议" |

---

最后更新：2026-08-31
