# 🔌 使用第三方 Claude API 配置指南

## 概述

如果你使用的是第三方 Claude API 服务（如中转 API、代理服务等），需要修改 API 端点。

---

## 方法 1：修改 Claude Provider

### 1. 打开文件

```bash
vim research_pipeline/llm_providers/claude.py
```

### 2. 找到 `__init__` 方法（约第 20 行）

原来的代码：
```python
def __init__(
    self,
    api_key: str | None = None,
    model: str | None = None,
    **kwargs: Any,
):
    super().__init__(model=model, **kwargs)
    
    # 读取 API key
    self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not self.api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    # 创建客户端
    self.client = anthropic.Anthropic(api_key=self.api_key)
```

### 3. 修改为支持自定义端点

修改后的代码：
```python
def __init__(
    self,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,  # 新增：自定义 API 端点
    **kwargs: Any,
):
    super().__init__(model=model, **kwargs)
    
    # 读取 API key
    self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not self.api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    # 读取自定义端点
    self.base_url = base_url or os.getenv("ANTHROPIC_BASE_URL")
    
    # 创建客户端
    if self.base_url:
        # 使用自定义端点
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
    else:
        # 使用官方端点
        self.client = anthropic.Anthropic(api_key=self.api_key)
```

---

## 方法 2：通过配置文件设置

### 1. 修改 config.yaml

```yaml
llm:
  provider: "claude"
  model: ""
  api_key_env: "ANTHROPIC_API_KEY"
  
  # 新增：自定义 API 端点
  base_url: "https://your-api-service.com/v1"  # 替换成你的第三方 API 地址
  
  max_retries: 3
  timeout: 120
```

### 2. 修改 config_loader.py

找到 `load_llm_config` 函数，添加 `base_url` 读取：

```python
def load_llm_config(config_path: Path) -> dict[str, Any]:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if 'llm' in config:
        llm_config = config['llm']
        return {
            'provider': llm_config.get('provider', 'claude'),
            'model': llm_config.get('model', ''),
            'api_key_env': llm_config.get('api_key_env'),
            'base_url': llm_config.get('base_url'),  # 新增
            'max_retries': llm_config.get('max_retries', 3),
            'timeout': llm_config.get('timeout', 120),
            # ...
        }
```

---

## 方法 3：通过环境变量（最简单）

### 1. 设置环境变量

```bash
# 设置 API Key
export ANTHROPIC_API_KEY="your_api_key"

# 设置自定义端点
export ANTHROPIC_BASE_URL="https://your-api-service.com/v1"
```

### 2. 修改 claude.py 读取环境变量

在 `__init__` 方法中：
```python
# 读取自定义端点（从环境变量）
self.base_url = os.getenv("ANTHROPIC_BASE_URL")

if self.base_url:
    self.client = anthropic.Anthropic(
        api_key=self.api_key,
        base_url=self.base_url
    )
```

---

## 常见第三方 API 服务

### 1. Claude2API（示例）
```bash
export ANTHROPIC_BASE_URL="https://claude2api.com/v1"
export ANTHROPIC_API_KEY="your_key"
```

### 2. OpenRouter
```bash
export ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1"
export ANTHROPIC_API_KEY="your_openrouter_key"
```

### 3. 自建中转服务
```bash
export ANTHROPIC_BASE_URL="https://your-proxy.com/anthropic/v1"
export ANTHROPIC_API_KEY="your_key"
```

---

## 完整修改示例

### claude.py 完整修改

```python
class ClaudeProvider(LLMProvider):
    """Claude API provider using Anthropic SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,  # 支持自定义端点
        **kwargs: Any,
    ):
        super().__init__(model=model, **kwargs)
        
        # 读取 API key
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. "
                "Set it with: export ANTHROPIC_API_KEY='your_key'"
            )
        
        # 读取自定义端点
        self.base_url = base_url or os.getenv("ANTHROPIC_BASE_URL")
        
        # 创建客户端
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
            logger.info(f"Using custom API endpoint: {self.base_url}")
        
        self.client = anthropic.Anthropic(**client_kwargs)
```

---

## 使用方法

### 方式 1：命令行设置

```bash
# 设置环境变量
export ANTHROPIC_API_KEY="your_third_party_key"
export ANTHROPIC_BASE_URL="https://your-service.com/v1"

# 运行
python -m research_pipeline demo
```

### 方式 2：配置文件

编辑 `config/config.yaml`：
```yaml
llm:
  provider: "claude"
  api_key_env: "ANTHROPIC_API_KEY"
  base_url: "https://your-service.com/v1"
```

---

## 测试

修改完成后，测试一下：

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate

# 设置环境变量
export ANTHROPIC_API_KEY="your_key"
export ANTHROPIC_BASE_URL="https://your-service.com/v1"

# 运行测试
python -m research_pipeline demo
```

---

## 需要我帮你修改吗？

告诉我：
1. 你的第三方 API 服务地址是什么？
2. 你有 API Key 了吗？

我可以直接帮你修改代码！
