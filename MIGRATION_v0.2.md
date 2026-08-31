# 从 v0.1.x 迁移到 v0.2.0

## 🎯 核心变更

v0.2.0 移除了对 **Codex CLI** 的依赖，改用通用的 LLM API（Claude、OpenAI）。

---

## ⚡ 5分钟快速迁移

### 1. 安装新依赖

```bash
cd /path/to/research_pipeline
source .venv/bin/activate
pip install anthropic openai
```

### 2. 设置 API Key

**选择一个 Provider**：

```bash
# 选项 A: Claude（推荐）
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# 选项 B: OpenAI
export OPENAI_API_KEY="sk-xxxxx"

# 持久化（可选）
echo 'export ANTHROPIC_API_KEY="sk-ant-xxxxx"' >> ~/.zshrc
source ~/.zshrc
```

**获取 API Key**：
- Claude: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/

### 3. 更新配置文件

```bash
# 使用新配置格式
cp config/config.v0.2.yaml config/config.yaml
```

或手动修改 `config/config.yaml`：

```yaml
# 旧格式（v0.1.x）
codex:
  binary: "codex"
  models:
    triage: ""
  reasoning_effort:
    triage: "low"

# 新格式（v0.2.0）
llm:
  provider: "claude"  # 或 "openai"
  model: ""           # 留空使用默认
  api_key_env: "ANTHROPIC_API_KEY"
  max_retries: 3
  reasoning_effort:
    triage: "low"
    synthesis: "medium"
    deep_dive: "high"
    qc: "medium"
```

### 4. 测试运行

```bash
# 测试配置
python -m research_pipeline demo

# 正式运行
./run.sh 0900
```

✅ **完成！你的系统已升级到 v0.2.0**

---

## 📋 详细变更说明

### 破坏性变更

#### 1. 配置文件格式

**旧配置**（v0.1.x）：
```yaml
codex:
  binary: "codex"
  models:
    triage: ""
  reasoning_effort:
    triage: "low"
```

**新配置**（v0.2.0）：
```yaml
llm:
  provider: "claude"
  model: ""
  api_key_env: "ANTHROPIC_API_KEY"
  reasoning_effort:
    triage: "low"
```

#### 2. 依赖变更

**移除**：
- ❌ Codex CLI 二进制程序

**新增**：
- ✅ `anthropic>=0.34,<1`
- ✅ `openai>=1.0,<2`

#### 3. 环境变量

**旧方式**：
- 无需环境变量（Codex CLI 自带认证）

**新方式**：
- 必须设置 `ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY`

---

## 🔄 代码迁移

### 如果你有自定义代码

#### 导入语句更新

**旧代码**：
```python
from research_pipeline.codex_runner import CodexRunner, CodexError
```

**新代码**（推荐）：
```python
from research_pipeline.llm_runner import LLMRunner, LLMRunnerError
```

**兼容方式**（v0.2.x 仍支持）：
```python
# 这仍然能工作，但会显示 DeprecationWarning
from research_pipeline.codex_runner import CodexRunner, CodexError
```

#### 配置加载

**旧代码**：
```python
# 直接从 config 读取 codex 配置
codex_config = config.get("codex")
```

**新代码**：
```python
from research_pipeline.config_loader import load_llm_config

llm_config = load_llm_config(Path("config/config.yaml"))
```

#### Runner 创建

**旧代码**：
```python
runner = CodexRunner(config, logger)
```

**新代码**：
```python
from research_pipeline.llm_runner import create_runner_from_yaml

runner = create_runner_from_yaml(
    config_path=Path("config/config.yaml"),
    stage="triage"
)
```

---

## 💰 成本对比

### v0.1.x (Codex CLI)
- **计费方式**：按 OpenAI 使用量
- **模型**：Codex 默认模型
- **成本**：约 $2-3/天（60份研报）

### v0.2.0 (直接 API)
- **计费方式**：按 Provider 定价
- **模型**：可选 Claude 或 GPT-4
- **成本**：

| Provider | 模型 | 成本/天 | 成本/月 |
|---------|------|--------|---------|
| Claude | Sonnet 3.5 | ~$3.5 | ~$105 |
| OpenAI | GPT-4o | ~$2.8 | ~$84 |

**节省成本的方法**：
```yaml
# 降低深度分析数量
pipeline:
  deep_dive_n: 5  # 从 10 降到 5，节省 50%

# 使用更便宜的模型做初筛
llm:
  provider: "claude"
  # 可以为不同 stage 设置不同模型
```

---

## 🆕 新增功能

### 1. 多 Provider 支持

现在可以轻松切换 LLM Provider：

```yaml
# 使用 Claude
llm:
  provider: "claude"
  api_key_env: "ANTHROPIC_API_KEY"

# 使用 OpenAI
llm:
  provider: "openai"
  api_key_env: "OPENAI_API_KEY"
```

### 2. Stage-specific 配置

为不同阶段设置不同参数：

```yaml
llm:
  temperature:
    triage: 0.0      # 初筛：确定性输出
    synthesis: 0.0   # 综合：确定性
    deep_dive: 0.1   # 深度：稍微有创造性
    qc: 0.0          # 质检：确定性

  max_tokens:
    triage: 4096
    synthesis: 8192
    deep_dive: 16384  # 深度分析允许更长输出
    qc: 4096
```

### 3. 改进的错误处理

```python
from research_pipeline.llm_runner import LLMRunnerError

try:
    runner.run(prompt=prompt, json_schema=schema)
except LLMRunnerError as e:
    # 更清晰的错误信息
    print(f"LLM 调用失败: {e}")
```

---

## ⚠️ 已知问题

### 1. 模型差异

不同 Provider 的输出可能略有差异：

| Provider | 特点 | 适用场景 |
|---------|------|---------|
| Claude | 更擅长长文本分析 | 研报深度分析 |
| OpenAI | 更快，成本略低 | 大批量初筛 |

**建议**：初筛用 OpenAI，深度分析用 Claude。

### 2. Rate Limit

API 调用有频率限制：

```python
# 如遇 429 错误，调整重试配置
llm:
  max_retries: 5
  retry_delay: 3.0  # 增加重试延迟
```

### 3. 向后兼容警告

使用旧导入会看到警告：

```
DeprecationWarning: codex_runner is deprecated and will be removed in v0.3.0.
Please update your imports: from research_pipeline.llm_runner import LLMRunner
```

**解决**：更新导入语句（见上文"代码迁移"）

---

## 🧪 验证迁移成功

### 1. 检查配置

```bash
python -c "
from pathlib import Path
from research_pipeline.config_loader import load_llm_config

config = load_llm_config(Path('config/config.yaml'))
print(f'Provider: {config[\"provider\"]}')
print(f'Model: {config.get(\"model\", \"(default)\")}')
print('✅ 配置加载成功')
"
```

### 2. 测试 API 连接

```bash
python tests/test_llm_providers.py --provider claude
```

预期输出：
```
✅ basic_generation: PASS
✅ structured_output: PASS
✅ retry_logic: PASS
```

### 3. 运行 Demo

```bash
python -m research_pipeline demo
```

检查输出目录：
```bash
ls -lh outputs/demo/
# 应该看到生成的 Markdown 和 HTML 文件
```

---

## 🆘 迁移问题排查

### 问题1：API Key 未找到

**错误信息**：
```
LLMRunnerError: Provider configuration invalid: ANTHROPIC_API_KEY not set
```

**解决**：
```bash
# 检查环境变量
echo $ANTHROPIC_API_KEY

# 如果为空，重新设置
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# 确认已设置
env | grep API_KEY
```

### 问题2：依赖未安装

**错误信息**：
```
ModuleNotFoundError: No module named 'anthropic'
```

**解决**：
```bash
# 确认虚拟环境已激活
which python  # 应该显示 .venv/bin/python

# 重新安装
pip install anthropic openai
```

### 问题3：配置文件格式错误

**错误信息**：
```
KeyError: 'llm'
```

**解决**：
```bash
# 使用新配置模板
cp config/config.v0.2.yaml config/config.yaml

# 或者检查 YAML 语法
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
```

### 问题4：输出质量下降

**可能原因**：不同模型输出风格不同

**解决**：
```yaml
# 调整 temperature
llm:
  temperature:
    deep_dive: 0.0  # 更确定性

# 或切换 Provider
llm:
  provider: "claude"  # Claude 通常更擅长分析
```

---

## 📞 需要帮助？

如果遇到迁移问题：

1. **检查文档**：
   - `README.md` - 基础使用
   - `QUICKSTART.md` - 快速开始
   - `7_DAY_GUIDE.md` - 详细指南

2. **查看示例**：
   ```bash
   python -m research_pipeline demo
   ```

3. **提交 Issue**：
   - GitHub Issues: [链接待补充]
   - 包含错误信息和配置文件

---

## 🎉 迁移检查清单

完成以下步骤确认迁移成功：

- [ ] 安装了 `anthropic` 和 `openai` 包
- [ ] 设置了 API Key 环境变量
- [ ] 更新了 `config/config.yaml` 格式
- [ ] `test_llm_providers.py` 测试通过
- [ ] `demo` 命令成功运行
- [ ] 生成的输出质量符合预期
- [ ] 没有 DeprecationWarning（或已更新导入）

---

## 🚀 下一步

迁移完成后，你可以：

1. **正常使用**：
   ```bash
   ./run.sh 0900
   ./run.sh 2100
   ```

2. **探索新功能**：
   - 尝试不同的 Provider
   - 调整 stage-specific 参数
   - 优化成本配置

3. **升级到未来版本**：
   - v0.3.0 将移除 `codex_runner` 兼容层
   - 建议尽快更新代码中的导入语句

---

**版本**：v0.2.0  
**发布日期**：2026-09-01  
**最后更新**：2026-08-31
