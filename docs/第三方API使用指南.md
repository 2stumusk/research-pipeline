# 第三方 Claude API 使用指南

## ✅ 代码已修改完成

已支持自定义 API 端点，现在可以使用第三方 Claude API 服务。

---

## 🚀 使用方法

### 方法 1：通过环境变量（推荐）

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate

# 设置 API Key
export ANTHROPIC_API_KEY="YOUR_API_KEY"

# 设置第三方 API 端点（替换成你的实际地址）
export ANTHROPIC_BASE_URL="https://your-api-service.com/v1"

# 运行 Demo
python -m research_pipeline demo
```

---

### 方法 2：通过配置文件

编辑 `config/config.yaml`：

```yaml
llm:
  provider: "claude"
  model: ""  # 留空使用默认模型
  api_key_env: "ANTHROPIC_API_KEY"
  
  # 添加自定义 API 端点
  base_url: "https://your-api-service.com/v1"
  
  max_retries: 3
  timeout: 120
  
  temperature:
    triage: 0.0
    synthesis: 0.0
    deep_dive: 0.1
    qc: 0.0
  
  max_tokens:
    triage: 4096
    synthesis: 8192
    deep_dive: 16384
    qc: 4096
```

然后设置 API Key：
```bash
export ANTHROPIC_API_KEY="YOUR_API_KEY"
```

运行：
```bash
python -m research_pipeline demo
```

---

## 📝 常见第三方 API 服务端点

根据你的服务商，选择对应的端点：

### 1. Claude2API（示例）
```bash
export ANTHROPIC_BASE_URL="https://api.claude2api.com/v1"
```

### 2. OpenRouter
```bash
export ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1"
```

### 3. 自建代理
```bash
export ANTHROPIC_BASE_URL="https://your-proxy.example.com/v1"
```

---

## 🧪 测试

运行测试确认配置正确：

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate

# 设置环境变量
export ANTHROPIC_API_KEY="YOUR_API_KEY"
export ANTHROPIC_BASE_URL="https://your-api-service.com/v1"

# 运行 Demo
python -m research_pipeline demo

# 查看结果
open outputs/demo/dashboard.html
```

---

## ⚠️ 注意事项

1. **API Key 安全**
   - 不要把 API Key 提交到 Git
   - 使用环境变量而不是硬编码

2. **端点格式**
   - 确保 URL 以 `/v1` 结尾（或服务商要求的路径）
   - 使用 HTTPS 协议

3. **兼容性**
   - 确保第三方 API 完全兼容 Anthropic API 格式
   - 某些服务可能不支持所有功能

---

## 💡 提示

如果不知道第三方 API 端点地址，请查看服务商的文档。

需要帮助请告诉我你的 API 服务商名称！
