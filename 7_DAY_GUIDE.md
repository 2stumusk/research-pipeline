# Research Pipeline 完善计划 - 7天实战指南

> **目标**：每天2-3小时，7天内完成v0.2.0的核心重构

---

## 📅 Day 1：环境准备与测试（周一，2小时）

### 今天要完成的事

1. **安装新依赖**（15分钟）
```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline

# 激活虚拟环境
source .venv/bin/activate

# 安装 LLM Provider 依赖
pip install anthropic openai

# 更新 requirements.txt
cat >> requirements.txt << EOF
anthropic>=0.34,<1
openai>=1.0,<2
EOF
```

2. **配置 API Key**（5分钟）

选择一个 Provider（建议从 Claude 开始）：

```bash
# 方式1：临时设置（本次会话）
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# 方式2：永久设置（推荐）
echo 'export ANTHROPIC_API_KEY="sk-ant-xxxxx"' >> ~/.zshrc
source ~/.zshrc

# 验证
echo $ANTHROPIC_API_KEY
```

3. **运行测试脚本**（30分钟）

```bash
# 测试 Claude Provider
python tests/test_llm_providers.py --provider claude

# 如果成功，会看到：
# ✅ basic_generation: PASS
# ✅ structured_output: PASS
# ✅ retry_logic: PASS
```

**预期输出**：
```
Testing CLAUDE - Basic Generation
==================================================
Prompt: 请用一句话总结：人工智能在投资研究中的应用前景。
Calling LLM...

✅ Success!
Model: claude-3-5-sonnet-20241022
Usage: {'input_tokens': 45, 'output_tokens': 128}

Response:
人工智能在投资研究中的应用前景广阔，可以...
```

4. **解决问题**（60分钟）

如果测试失败，常见问题：

**问题1：ModuleNotFoundError: No module named 'anthropic'**
```bash
# 确认虚拟环境已激活
which python  # 应该显示 .venv/bin/python
pip list | grep anthropic
```

**问题2：API Key 错误**
```bash
# 检查环境变量
echo $ANTHROPIC_API_KEY

# 检查是否有多余空格
export ANTHROPIC_API_KEY=$(echo $ANTHROPIC_API_KEY | xargs)
```

**问题3：网络连接问题**
```bash
# 测试网络
curl -I https://api.anthropic.com

# 如果需要代理
export https_proxy=http://127.0.0.1:7890
```

5. **今天的验收标准**

- [ ] `pip list` 显示 anthropic 和 openai 已安装
- [ ] `test_llm_providers.py` 至少一个 Provider 测试通过
- [ ] 能看到 LLM 返回的中文内容

**完成时间检查**：如果超过2小时还没通过测试，先暂停，明天继续。不要死磕。

---

## 📅 Day 2：创建适配器（周二，2.5小时）

### 今天要完成的事

1. **创建配置加载器**（45分钟）

创建 `research_pipeline/config_loader.py`：

```python
"""Configuration loader for LLM settings."""

import os
from pathlib import Path
from typing import Any
import yaml

def load_llm_config(config_path: Path) -> dict[str, Any]:
    """Load LLM configuration from YAML file.
    
    Supports both old 'codex' format and new 'llm' format.
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # If new format exists, use it
    if 'llm' in config:
        return config['llm']
    
    # Otherwise, convert old codex format
    codex_config = config.get('codex', {})
    return {
        'provider': 'claude',  # default to claude
        'model': '',
        'api_key_env': 'ANTHROPIC_API_KEY',
        'max_retries': codex_config.get('retries', 3),
        'timeout': codex_config.get('timeout_seconds', 120),
        'reasoning_effort': codex_config.get('reasoning_effort', {}),
    }
```

测试：
```bash
python -c "
from pathlib import Path
from research_pipeline.config_loader import load_llm_config

config = load_llm_config(Path('config/config.v0.2.yaml'))
print(config)
"
```

2. **修改 llm_runner.py 支持配置文件**（45分钟）

在 `llm_runner.py` 末尾添加：

```python
def create_runner_from_yaml(
    config_path: Path,
    stage: str = "triage"
) -> LLMRunner:
    """Create LLMRunner from YAML config file.
    
    Args:
        config_path: Path to config YAML file
        stage: Stage name (triage, synthesis, deep_dive, qc)
    
    Returns:
        Configured LLMRunner for the specified stage
    """
    from .config_loader import load_llm_config
    
    llm_config = load_llm_config(config_path)
    
    # Get stage-specific settings
    reasoning_effort = llm_config.get('reasoning_effort', {})
    temperature_map = llm_config.get('temperature', {})
    max_tokens_map = llm_config.get('max_tokens', {})
    
    # Map reasoning effort to temperature (if not explicitly set)
    effort = reasoning_effort.get(stage, 'medium')
    if stage not in temperature_map:
        temperature_map[stage] = {
            'low': 0.0,
            'medium': 0.0,
            'high': 0.1
        }.get(effort, 0.0)
    
    return create_runner_from_config({
        'provider': llm_config['provider'],
        'model': llm_config.get('model'),
        'api_key_env': llm_config.get('api_key_env'),
        'max_retries': llm_config.get('max_retries', 3),
        'timeout': llm_config.get('timeout', 120),
    })
```

3. **创建简单的集成测试**（30分钟）

创建 `tests/test_integration_simple.py`:

```python
#!/usr/bin/env python3
"""Simple integration test: 1 PDF → LLM analysis."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from research_pipeline.llm_runner import create_runner_from_yaml

def main():
    # Load config
    config_path = Path("config/config.v0.2.yaml")
    
    print("Creating LLM runner from config...")
    runner = create_runner_from_yaml(config_path, stage="triage")
    
    # Simulate a simple research report triage
    prompt = """
    分析以下研报摘要，评分0-100：
    
    标题：中微公司（688012）：Q2业绩超预期
    要点：
    1. 营收同比+45%
    2. 毛利率提升至48%
    3. 先进制程刻蚀设备订单充足
    
    请判断这份研报的重要性（0-100）。
    """
    
    schema = {
        "type": "object",
        "properties": {
            "importance_score": {"type": "integer", "minimum": 0, "maximum": 100},
            "reasoning": {"type": "string"}
        },
        "required": ["importance_score", "reasoning"]
    }
    
    print("\nCalling LLM...")
    response = runner.run(prompt=prompt, json_schema=schema)
    
    print(f"\n✅ Success!")
    print(f"Score: {response.structured_output['importance_score']}")
    print(f"Reasoning: {response.structured_output['reasoning']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

运行测试：
```bash
python tests/test_integration_simple.py
```

4. **今天的验收标准**

- [ ] `config_loader.py` 能正确加载配置
- [ ] `create_runner_from_yaml()` 能创建 runner
- [ ] `test_integration_simple.py` 测试通过
- [ ] LLM 能返回结构化的评分结果

---

## 📅 Day 3：重构 pipeline.py（周三，3小时）

### 今天要完成的事

**目标**：让现有的 `pipeline.py` 支持新的 `LLMRunner`，但不破坏原有逻辑。

1. **备份原文件**（5分钟）
```bash
cp research_pipeline/pipeline.py research_pipeline/pipeline.py.backup
cp research_pipeline/codex_runner.py research_pipeline/codex_runner.py.backup
```

2. **添加兼容层**（30分钟）

修改 `codex_runner.py`，在文件开头添加：

```python
"""DEPRECATED: Use llm_runner instead.

This module is kept for backward compatibility.
"""

import warnings
warnings.warn(
    "codex_runner is deprecated, use llm_runner instead",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from llm_runner
from .llm_runner import (
    LLMRunner as CodexRunner,
    LLMRunnerError as CodexError,
    create_runner_from_config,
)

__all__ = ['CodexRunner', 'CodexError', 'create_runner_from_config']
```

**重要**：删除 `codex_runner.py` 的所有其他代码，只保留上面的导入。

3. **验证兼容性**（30分钟）

```bash
# 运行原有测试（应该仍然能通过）
python -m pytest tests/ -v
```

如果测试失败，说明兼容层有问题，需要调整。

4. **逐步替换导入语句**（90分钟）

在 `pipeline.py` 中：

```bash
# 搜索
from .codex_runner import CodexRunner, CodexError

# 替换为
from .llm_runner import LLMRunner, LLMRunnerError

# 然后在类/函数中：
# CodexRunner → LLMRunner
# CodexError → LLMRunnerError
```

**策略**：一次只改一个函数，改完立即测试：

```bash
# 测试 dry-run（不调用 LLM）
python -m research_pipeline demo
```

5. **今天的验收标准**

- [ ] `codex_runner.py` 改为兼容层
- [ ] `pipeline.py` 导入语句已更新
- [ ] `python -m research_pipeline demo` 仍能运行
- [ ] 没有破坏现有功能

---

## 📅 Day 4：端到端测试（周四，2.5小时）

### 今天要完成的事

**目标**：用真实的 PDF 和 LLM API 跑通完整流程。

1. **准备测试数据**（15分钟）

```bash
# 创建测试目录
mkdir -p inbox/2026-09-01

# 放入 2-3 份真实研报 PDF
# 或者用虚拟 PDF 测试（如果没有真实研报）
```

2. **更新配置文件**（15分钟）

复制新配置：
```bash
cp config/config.v0.2.yaml config/config.yaml.new
```

编辑 `config/config.yaml.new`：
- 确认 `llm.provider` 设置正确
- 确认 `llm.api_key_env` 指向正确的环境变量
- 调整 `pipeline.deep_dive_n` 为 2（减少 API 调用）

3. **小规模测试运行**（60分钟）

```bash
# 使用新配置运行
python -m research_pipeline run \
    --date 2026-09-01 \
    --session test \
    --config config/config.yaml.new
```

**观察输出**：
- [ ] PDF 是否正确提取？
- [ ] LLM 是否正确调用？
- [ ] 是否生成了输出文件？
- [ ] 输出文件内容是否合理？

4. **检查输出质量**（45分钟）

打开生成的文件：
```bash
cd outputs/daily/2026-09-01-test/
open dashboard.html
cat 00-今日研报一页纸.md
cat 01-今日必读Top10.md
```

**质量检查清单**：
- [ ] 研报摘要是否准确？
- [ ] 重要性评分是否合理？
- [ ] Top 10 排序是否符合预期？
- [ ] 是否有明显的 LLM 幻觉/错误？

5. **成本统计**（15分钟）

检查 API 使用量：
```bash
# 在输出目录中查找 token usage
grep -r "usage" outputs/daily/2026-09-01-test/machine/
```

计算成本：
- Input tokens × $3/1M
- Output tokens × $15/1M

6. **今天的验收标准**

- [ ] 能完整跑通 2-3 份PDF的分析
- [ ] 输出质量可接受
- [ ] 成本在预期范围内（<$1）
- [ ] 没有系统错误

---

## 📅 Day 5：文档更新（周五，2小时）

### 今天要完成的事

1. **更新 README.md**（45分钟）

关键修改：

```markdown
## 安装

### 1. 克隆项目
\`\`\`bash
git clone <your-repo>
cd research_pipeline
\`\`\`

### 2. 安装依赖
\`\`\`bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
\`\`\`

### 3. 配置 LLM Provider

**选项 A：Claude（推荐）**
\`\`\`bash
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
\`\`\`

**选项 B：OpenAI**
\`\`\`bash
export OPENAI_API_KEY="sk-xxxxx"
\`\`\`

编辑 `config/config.yaml`:
\`\`\`yaml
llm:
  provider: "claude"  # 或 "openai"
  model: ""           # 留空使用默认
  api_key_env: "ANTHROPIC_API_KEY"
\`\`\`

### 4. 运行测试
\`\`\`bash
python -m research_pipeline demo
\`\`\`
```

2. **更新 QUICKSTART.md**（30分钟）

删除 Codex CLI 相关内容，替换为 LLM Provider 配置。

3. **更新 BUILD_NOTES.md**（30分钟）

添加 v0.2.0 记录：

```markdown
## v0.2.0 (2026-09-01)

### 重大变更
- 移除 Codex CLI 依赖
- 新增通用 LLM Provider 支持（Claude、OpenAI）
- 新增 `llm_providers/` 模块
- 新增 `llm_runner.py` 替代 `codex_runner.py`

### 破坏性变更
- 配置文件格式变更：`codex:` → `llm:`
- 需要手动设置 API Key 环境变量

### 迁移指南
详见 `MIGRATION_v0.2.md`
```

4. **创建迁移指南**（15分钟）

创建 `MIGRATION_v0.2.md`:

```markdown
# 从 v0.1.x 迁移到 v0.2.0

## 快速迁移（5分钟）

1. 安装新依赖：
   \`\`\`bash
   pip install anthropic openai
   \`\`\`

2. 设置 API Key：
   \`\`\`bash
   export ANTHROPIC_API_KEY="your_key"
   \`\`\`

3. 更新配置文件：
   \`\`\`bash
   cp config/config.v0.2.yaml config/config.yaml
   \`\`\`

4. 测试运行：
   \`\`\`bash
   python -m research_pipeline demo
   \`\`\`

## 详细变更说明
...
```

5. **今天的验收标准**

- [ ] 新用户能根据 README 在 30 分钟内运行
- [ ] 所有 Codex CLI 引用已删除
- [ ] 迁移指南清晰易懂

---

## 📅 Day 6-7：打磨与发布（周末，3-4小时）

### Day 6（周六，2小时）：代码质量

1. **代码格式化**（30分钟）
```bash
pip install black ruff

# 格式化代码
black research_pipeline/ tests/

# Lint 检查
ruff check research_pipeline/ tests/
```

2. **添加类型标注**（60分钟）

为核心模块添加类型标注：
```bash
pip install mypy

# 检查类型
mypy research_pipeline/llm_runner.py
mypy research_pipeline/llm_providers/
```

3. **更新测试覆盖率**（30分钟）
```bash
pip install pytest pytest-cov

# 运行测试并生成覆盖率报告
pytest tests/ --cov=research_pipeline --cov-report=html

# 查看报告
open htmlcov/index.html
```

### Day 7（周日，1.5小时）：发布准备

1. **创建 CHANGELOG.md**（20分钟）

```markdown
# Changelog

## [0.2.0] - 2026-09-01

### Added
- Universal LLM provider support (Claude, OpenAI)
- New `llm_providers/` module with abstract interface
- Configuration-based provider selection

### Changed
- Replaced Codex CLI with direct API calls
- Updated configuration format (`llm` vs `codex`)

### Removed
- Codex CLI dependency

### Migration
See MIGRATION_v0.2.md
```

2. **Git 提交**（30分钟）

```bash
# 初始化 Git（如果还没有）
git init
git add .gitignore

# 添加所有新文件
git add research_pipeline/llm_providers/
git add research_pipeline/llm_runner.py
git add tests/test_llm_providers.py
git add config/config.v0.2.yaml
git add ROADMAP.md WEEK1_TASKS.md MIGRATION_v0.2.md CHANGELOG.md

# 提交
git commit -m "feat: Add universal LLM provider support (v0.2.0)

- Remove Codex CLI dependency
- Add Claude and OpenAI provider support
- Update configuration format
- Add migration guide and tests

BREAKING CHANGE: Configuration format changed from 'codex' to 'llm'
"

# 打标签
git tag v0.2.0
```

3. **创建 GitHub 仓库**（30分钟）

```bash
# 在 GitHub 上创建仓库：research-pipeline

# 添加远程仓库
git remote add origin https://github.com/yourusername/research-pipeline.git

# 推送
git push -u origin main
git push --tags
```

4. **发布公告**（10分钟）

在 GitHub Releases 页面创建 v0.2.0 发布：

```markdown
# v0.2.0 - Universal LLM Support 🚀

## 重大更新

不再依赖 Codex CLI！现在支持：
- ✅ Anthropic Claude API
- ✅ OpenAI GPT-4 API
- ✅ 易于扩展到其他 LLM

## 快速开始

\`\`\`bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your_key"
python -m research_pipeline demo
\`\`\`

## 破坏性变更

配置文件格式更新，详见 [MIGRATION_v0.2.md](MIGRATION_v0.2.md)

## 下一步

- Week 2: 数据采集模块
- Week 3-4: 预期差分析
- Week 5-6: 完善文档，准备开源

**完整路线图**: [ROADMAP.md](ROADMAP.md)
```

---

## ✅ 7天总验收清单

完成所有7天的任务后，确认：

### 技术指标
- [ ] 所有单元测试通过
- [ ] 集成测试通过（真实 PDF + LLM API）
- [ ] 输出质量不低于 Codex 版本
- [ ] API 成本可控（<$5/天）

### 代码质量
- [ ] 通过 black 格式化
- [ ] 通过 ruff lint 检查
- [ ] 核心模块有类型标注
- [ ] 测试覆盖率 >60%

### 文档质量
- [ ] README 清晰易懂
- [ ] 新用户能在 30 分钟内运行
- [ ] 迁移指南完整
- [ ] CHANGELOG 准确

### 发布准备
- [ ] 代码已提交到 Git
- [ ] 已打标签 v0.2.0
- [ ] 已推送到 GitHub
- [ ] 已创建 Release

---

## 🚨 常见问题

### Q: API 成本太高怎么办？

**A**: 调整配置：
```yaml
pipeline:
  deep_dive_n: 3  # 从 10 降到 3
  batch_max_reports: 2  # 从 4 降到 2
```

### Q: LLM 返回结果质量不好？

**A**: 调整 temperature 和 reasoning effort：
```yaml
llm:
  temperature:
    deep_dive: 0.0  # 更确定性
  reasoning_effort:
    deep_dive: "high"  # 更高质量（仅Claude支持）
```

### Q: 某个 Provider 不work？

**A**: 先用测试脚本验证：
```bash
python tests/test_llm_providers.py --provider claude
python tests/test_llm_providers.py --provider openai
```

### Q: 时间不够用？

**A**: 优先级排序：
1. **必须做**：Day 1-4（核心功能）
2. **应该做**：Day 5（文档）
3. **可选做**：Day 6-7（打磨发布）

---

## 📞 需要帮助？

如果卡住了，告诉我：
1. 在第几天的哪个步骤？
2. 具体的错误信息是什么？
3. 已经尝试了什么解决方法？

我会帮你快速解决！

---

最后更新：2026-08-31  
预计完成时间：2026-09-07
