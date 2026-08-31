# Week 1 任务清单

## ✅ 已完成 (2小时)

- [x] 创建 `llm_providers/` 模块架构
  - [x] `base.py` - 抽象接口定义
  - [x] `claude.py` - Claude API 实现
  - [x] `openai_provider.py` - OpenAI API 实现
  - [x] `__init__.py` - 工厂函数

- [x] 创建 `llm_runner.py` - 统一调用接口
  - [x] 重试逻辑
  - [x] 错误处理
  - [x] 向后兼容 (CodexError)

- [x] 创建配置文件 `config.v0.2.yaml`
- [x] 创建测试脚本 `test_llm_providers.py`
- [x] 创建项目路线图 `ROADMAP.md`

---

## 🔄 进行中 (剩余10-14小时)

### 第一步：安装依赖并测试 (2小时)

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline

# 激活虚拟环境
source .venv/bin/activate

# 安装新依赖
pip install anthropic openai

# 设置 API Key (选择一个)
export ANTHROPIC_API_KEY="your_key_here"
# 或
export OPENAI_API_KEY="your_key_here"

# 运行测试
python tests/test_llm_providers.py --provider claude
# 或
python tests/test_llm_providers.py --provider openai
```

**验收标准**：
- [ ] 测试脚本全部通过
- [ ] 能正常调用 Claude/OpenAI API
- [ ] 结构化输出符合预期

---

### 第二步：重构 pipeline.py (4-6小时)

需要修改的地方：
1. 将所有 `from .codex_runner import CodexRunner` 改为 `from .llm_runner import LLMRunner`
2. 将 `CodexRunner` 实例化改为 `LLMRunner`
3. 将 `CodexError` 改为 `LLMRunnerError`
4. 保持原有的批处理逻辑不变

**关键文件**：
- `research_pipeline/pipeline.py` (约500行)
- `research_pipeline/cli.py` 
- `research_pipeline/demo.py`

**任务**：
```bash
# 1. 备份原始文件
cp research_pipeline/pipeline.py research_pipeline/pipeline.py.backup
cp research_pipeline/cli.py research_pipeline/cli.py.backup

# 2. 开始重构 (需要手动编辑)
# 搜索并替换：
# - CodexRunner → LLMRunner
# - CodexError → LLMRunnerError
# - codex_runner → llm_runner
# - self.config.get("codex.*") → self.config.get("llm.*")
```

---

### 第三步：更新测试套件 (2-3小时)

修改现有测试以支持新的 LLM Provider：

```bash
# 修改这些测试文件
tests/test_codex_command_and_schemas.py → tests/test_llm_runner.py
tests/test_pipeline_fake_codex.py → tests/test_pipeline_fake_llm.py
```

**任务**：
- [ ] 创建 Mock LLM Provider (不调用真实 API)
- [ ] 更新测试用例
- [ ] 确保所有测试通过

---

### 第四步：更新文档 (2-3小时)

```bash
# 更新以下文档
README.md          # 更新安装和配置说明
QUICKSTART.md      # 更新快速开始指南
BUILD_NOTES.md     # 添加 v0.2.0 更新记录
```

**关键变更**：
1. 去掉 Codex CLI 安装步骤
2. 添加 API Key 配置说明
3. 更新配置文件示例
4. 添加多 Provider 支持说明

---

## 📝 验收清单

Week 1 结束时，必须达到：

- [ ] 所有单元测试通过 (包括新的和更新的)
- [ ] 用 Claude API 完整跑通一次流程 (5份PDF)
- [ ] 用 OpenAI API 完整跑通一次流程 (5份PDF)
- [ ] 输出质量与原 Codex 版本相当
- [ ] 文档更新完成
- [ ] 代码可以推送到 Git (准备开源)

---

## 💡 注意事项

### API 成本估算

**Claude 3.5 Sonnet**：
- Input: $3 / 1M tokens
- Output: $15 / 1M tokens

**GPT-4o**：
- Input: $2.5 / 1M tokens  
- Output: $10 / 1M tokens

**每天处理 60 份研报的预估成本**：
- 初筛 (60份 × 4k tokens input × 1k tokens output): ~$1.5/天
- 深度分析 (10份 × 16k tokens input × 8k tokens output): ~$2/天
- **总计：约 $3.5/天，$100/月**

### 向后兼容

保留 `codex_runner.py`，添加废弃警告：

```python
# codex_runner.py (deprecated)
import warnings
from .llm_runner import LLMRunner as CodexRunner
from .llm_runner import LLMRunnerError as CodexError

warnings.warn(
    "codex_runner is deprecated, use llm_runner instead",
    DeprecationWarning,
    stacklevel=2
)
```

---

## 🚦 下一步 (Week 2)

完成 Week 1 后：
- [ ] 提交代码到 Git
- [ ] 发布 v0.2.0-alpha 版本
- [ ] 开始 Week 2：数据采集模块

---

最后更新：2026-08-31
下次检查点：完成第一步测试后
