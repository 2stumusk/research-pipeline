# 第三方 Claude API 配置完成

## ✅ 你的配置信息

- **API 服务**: https://cc-vibe.com
- **API Key**: YOUR_API_KEY
- **模型**: claude-sonnet-5

---

## 🚀 使用方法

### 方法 1：命令行设置（推荐）

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate

# 设置环境变量
export ANTHROPIC_API_KEY="YOUR_API_KEY"
export ANTHROPIC_BASE_URL="https://cc-vibe.com"

# 运行 Demo
python -m research_pipeline demo

# 查看结果
open outputs/demo/dashboard.html
```

---

### 方法 2：修改配置文件

编辑 `config/config.yaml`：

```yaml
llm:
  provider: "claude"
  model: "claude-sonnet-5"
  api_key_env: "ANTHROPIC_API_KEY"
  base_url: "https://cc-vibe.com"
  
  max_retries: 3
  timeout: 120
  
  temperature:
    triage: 0.0
    synthesis: 0.0
    deep_dive: 0.1
    qc: 0.0
  
  reasoning_effort:
    triage: "low"
    synthesis: "medium"
    deep_dive: "high"
    qc: "low"
```

然后运行：
```bash
export ANTHROPIC_API_KEY="YOUR_API_KEY"
python -m research_pipeline demo
```

---

### 方法 3：一键运行脚本

创建快捷脚本 `run_with_api.sh`：

```bash
#!/bin/bash

cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate

export ANTHROPIC_API_KEY="YOUR_API_KEY"
export ANTHROPIC_BASE_URL="https://cc-vibe.com"

echo "🚀 运行 Research Pipeline (使用 cc-vibe API)"
echo ""

python -m research_pipeline demo

echo ""
echo "✅ 完成！正在打开结果..."
open outputs/demo/dashboard.html
```

使用：
```bash
chmod +x run_with_api.sh
./run_with_api.sh
```

---

## 🧪 测试

立即测试是否配置成功：

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
source .venv/bin/activate

export ANTHROPIC_API_KEY="YOUR_API_KEY"
export ANTHROPIC_BASE_URL="https://cc-vibe.com"

# 运行测试
python -m research_pipeline demo
```

---

## 📊 预期结果

如果配置正确，你会看到：
1. 系统开始分析 Demo PDF 文件
2. 调用 cc-vibe.com 的 Claude API
3. 生成研报分析结果
4. 输出到 `outputs/demo/` 目录

---

## ⚠️ 常见问题

### 1. 连接失败
检查 API 地址是否正确：
```bash
curl https://cc-vibe.com
```

### 2. 认证失败
确认 API Key 正确且有效

### 3. 模型不支持
如果 `claude-sonnet-5` 不可用，改为：
- `claude-3-5-sonnet-20241022`
- `claude-3-sonnet-20240229`

---

现在试试吧！
