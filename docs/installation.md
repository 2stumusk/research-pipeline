# A股研报智能筛选系统 - 安装指南

> **版本**: v0.2.0  
> **更新日期**: 2026-09-01

## 系统要求

### 必需
- **Python**: 3.11 - 3.13（推荐 3.11 或 3.13）
- **操作系统**: macOS / Linux / Windows
- **磁盘空间**: 至少 2GB（用于数据库和输出）
- **内存**: 建议 4GB+

### LLM Provider（二选一）
- **Anthropic Claude**: 需要 API Key（推荐）
- **OpenAI**: 需要 API Key

## 安装步骤

### 1. 获取代码

```bash
git clone <repository-url>
cd research_pipeline
```

### 2. 创建虚拟环境

**macOS/Linux**:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

**Windows**:
```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. 安装依赖

**推荐：使用锁定版本（保证可重现性）**
```bash
pip install --upgrade pip
pip install -r requirements.lock
```

**可选：使用版本范围（获取更新）**
```bash
pip install -r requirements.txt
```

### 4. 验证安装

```bash
python -m research_pipeline doctor
```

应该看到类似输出：
```
A股研报系统环境检查
====================================
✅ Python: 3.11.x
✅ Python模块 pymupdf: 已安装
✅ Python模块 yaml: 已安装
✅ Python模块 jsonschema: 已安装
✅ Python模块 jinja2: 已安装
✅ Python模块 anthropic: 已安装
✅ Python模块 openai: 已安装
⚠️  LLM Provider: 未配置（请设置 API Key）
✅ Git仓库: 正常
✅ SQLite: 正常
✅ 工作区写权限: 正常
✅ 观察池: 14 条
```

## 配置 LLM Provider

### 选项 A: Anthropic Claude（推荐）

1. 获取 API Key：https://console.anthropic.com/
2. 设置环境变量：

**macOS/Linux**:
```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# 持久化（可选）
echo 'export ANTHROPIC_API_KEY="sk-ant-xxxxx"' >> ~/.bashrc
# 或 ~/.zshrc
```

**Windows**:
```cmd
set ANTHROPIC_API_KEY=sk-ant-xxxxx
```

3. 验证配置：
```bash
python -m research_pipeline doctor
```

### 选项 B: OpenAI

1. 获取 API Key：https://platform.openai.com/
2. 设置环境变量：

```bash
export OPENAI_API_KEY="sk-xxxxx"
```

3. 修改配置文件：
```bash
# 编辑 config/config.yaml
# 将 llm.provider 改为 "openai"（如果该字段存在）
```

## 配置观察池

编辑 `config/watchlist.csv`，添加你关注的股票：

```csv
market,ticker,name,holding,priority,theme,notes
CN,688012,中微公司,true,5,半导体设备,当前持仓
CN,002371,北方华创,false,4,半导体设备,观察中
```

**字段说明**:
- `market`: 市场代码（CN=中国A股）
- `ticker`: 股票代码
- `name`: 公司名称
- `holding`: 是否持仓（true/false）
- `priority`: 优先级（1-5，5最高）
- `theme`: 行业主题
- `notes`: 备注

## 测试运行

### Demo模式（无需API Key）

```bash
python -m research_pipeline demo
```

查看生成的结果：
```bash
open outputs/demo/dashboard.html
# Windows: start outputs/demo/dashboard.html
```

### 完整运行（需要API Key）

1. 准备测试PDF：
```bash
mkdir -p inbox/$(date +%Y-%m-%d)
cp /path/to/test-reports/*.pdf inbox/$(date +%Y-%m-%d)/
```

2. 运行分析：
```bash
python -m research_pipeline run --date $(date +%Y-%m-%d) --session 0900
```

3. 查看结果：
```bash
open outputs/daily/$(date +%Y-%m-%d)-0900/dashboard.html
```

## 常见问题

### Python 版本不兼容

**症状**: `SyntaxError` 或模块导入失败

**解决**:
```bash
# 检查 Python 版本
python --version

# 如果不是 3.11-3.13，重新创建虚拟环境
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock
```

### 依赖安装失败

**症状**: `pip install` 报错

**解决**:
```bash
# 升级 pip
pip install --upgrade pip setuptools wheel

# 清理缓存重试
pip cache purge
pip install -r requirements.lock
```

### API Key 无效

**症状**: `LLM provider 未配置或不可用`

**解决**:
1. 确认 API Key 正确
2. 检查环境变量：`echo $ANTHROPIC_API_KEY`
3. 重新导出环境变量
4. 验证：`python -m research_pipeline doctor`

### 磁盘空间不足

**症状**: 写入失败或数据库错误

**解决**:
```bash
# 检查空间
df -h .

# 清理旧日志（保留30天）
find logs -name "*.log*" -mtime +30 -delete

# 归档旧输出
tar -czf outputs-archive-$(date +%Y%m).tar.gz outputs/
rm -rf outputs/daily/2026-07-*
```

## 下一步

安装完成后，请参阅：
- [使用指南](usage.md) - 日常使用说明
- [配置说明](configuration.md) - 详细配置选项
- [故障排除](troubleshooting.md) - 常见问题解决

## 卸载

```bash
# 删除虚拟环境
rm -rf .venv

# 删除数据（可选）
rm -rf database/ outputs/ logs/

# 删除项目目录
cd ..
rm -rf research_pipeline
```
