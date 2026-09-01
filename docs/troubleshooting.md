# 故障排除指南

> 常见问题的诊断和解决方案

## LLM Provider 问题

### ❌ "LLM provider 未配置或不可用"

**原因**: API Key 未设置或无效

**解决步骤**:

1. 检查环境变量：
```bash
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
```

2. 重新设置 API Key：
```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
```

3. 验证配置：
```bash
python -m research_pipeline doctor
```

4. 如果仍然失败，检查 API Key 是否有效：
```bash
# Claude
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'

# OpenAI
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```

### ❌ "Rate limit exceeded"

**原因**: API 调用频率超限

**解决**:
```yaml
# 编辑 config/config.yaml
llm:
  max_retries: 5      # 增加重试次数
  retry_delay: 3.0    # 增加重试延迟

pipeline:
  batch_max_reports: 2  # 减少批处理大小
```

### ❌ "Request timeout"

**原因**: 请求超时（PDF 太大或网络慢）

**解决**:
```yaml
# 编辑 config/config.yaml
llm:
  timeout: 3600  # 增加超时时间（秒）

pipeline:
  triage_max_pages: 15  # 减少处理页数
```

## PDF 处理问题

### ⚠️ "可提取文本过少，可能是扫描版 PDF"

**原因**: PDF 是图片扫描版，无法提取文字

**解决**:
- **最佳方案**: 使用 OCR 工具转换 PDF
  ```bash
  # macOS 使用 Tesseract
  brew install tesseract tesseract-lang
  
  # 转换 PDF（需要额外脚本）
  ```
- **临时方案**: 跳过该文件，或手动输入关键信息

### ❌ "PDF 文本提取失败"

**原因**: PDF 损坏或加密

**解决**:
```bash
# 检查 PDF
pdfinfo file.pdf

# 如果加密，尝试解密
qpdf --decrypt input.pdf output.pdf

# 如果损坏，尝试修复
gs -o repaired.pdf -sDEVICE=pdfwrite input.pdf
```

### ⚠️ 扫描页过多

**查看扫描页列表**:
```bash
# 查看 machine/report_cards.json
jq '.[] | select(.scanned_pages | length > 5) | {report_id, scanned_pages}' \
  outputs/daily/2026-09-01-0900/machine/report_cards.json
```

**解决**: 找到扫描页较多的研报，用 OCR 版本替换

## 数据库问题

### ❌ "database is locked"

**原因**: 多个进程同时访问数据库

**解决**:
```bash
# 1. 检查是否有其他进程运行
ps aux | grep research_pipeline

# 2. 删除锁文件（如果确认没有其他进程）
rm database/pipeline.lock

# 3. 检查数据库完整性
sqlite3 database/research.db "PRAGMA integrity_check;"
```

### ❌ 数据库损坏

**恢复步骤**:
```bash
# 1. 备份损坏的数据库
cp database/research.db database/research.db.corrupted

# 2. 尝试导出数据
sqlite3 database/research.db .dump > dump.sql

# 3. 重建数据库
rm database/research.db
sqlite3 database/research.db < dump.sql

# 4. 如果失败，从备份恢复或重新初始化
python -m research_pipeline init
```

## 性能问题

### 🐌 运行太慢

**诊断**:
```bash
# 查看日志，识别慢的阶段
tail -f logs/pipeline.log | grep "耗时"
```

**优化**:
```yaml
# config/config.yaml
pipeline:
  batch_max_reports: 6    # 增加批处理（更多并行）
  deep_dive_n: 5          # 减少深度分析

llm:
  max_parallel: 5         # 增加并行数（需要更多 API quota）
```

### 💰 成本太高

**查看成本分解**:
```bash
# 运行后会显示成本摘要
# 或查看 machine/run_metadata.json
jq '.cost_summary' outputs/daily/2026-09-01-0900/machine/run_metadata.json
```

**优化策略**:
1. 减少深度分析：`deep_dive_n: 5`
2. 使用更便宜的模型：`provider: "openai"`
3. 跳过 QC：`--no-qc`
4. 只在必要时运行

详见 [成本优化指南](cost-optimization.md)

## 输出质量问题

### ⚠️ Top 10 不符合预期

**原因**: 评分权重或观察池配置不当

**调整评分**:
```yaml
# config/config.yaml
scoring:
  watchlist_relevance: 30   # 提高观察池权重
  novelty: 10              # 降低新颖性权重
  holding_negative_boost: 15  # 增加持仓负面增强
```

**检查观察池**:
```bash
# 查看 config/watchlist.csv
cat config/watchlist.csv

# 确保:
# 1. holding=true 的股票有正确的 priority
# 2. 公司名称和 ticker 准确
```

### ⚠️ 事件聚类不准确

**原因**: LLM 聚类失败，使用了本地兜底

**解决**:
1. 检查日志中的错误：`grep "聚类失败" logs/pipeline.log`
2. 确认 API Key 正常
3. 尝试 `--force` 重新运行
4. 增加超时时间：`llm.timeout: 3600`

### ⚠️ 质量检查失败

**查看问题**:
```bash
# 查看 05-质量检查.md
cat outputs/daily/2026-09-01-0900/05-质量检查.md
```

**常见问题**:
- 数据缺口过多：某些研报提取失败
- 评分异常：评分权重可能需要调整
- 时间不一致：PDF 文件名日期与内容日期不符

## 日志和调试

### 查看详细日志

```bash
# 实时查看
tail -f logs/pipeline.log

# 搜索错误
grep -i error logs/pipeline.log

# 搜索某个 report_id 的处理过程
grep "abc123def456" logs/pipeline.log
```

### 启用调试模式

```python
# 临时修改 research_pipeline/cli.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 检查中间输出

```bash
# 查看 LLM 的原始输入输出
ls outputs/daily/2026-09-01-0900/machine/work/audit/

# 查看初筛结果
cat outputs/daily/2026-09-01-0900/machine/work/triage_batch_001.output.json

# 查看聚类结果
cat outputs/daily/2026-09-01-0900/machine/work/clusters.output.json
```

## 依赖问题

### ❌ 模块导入失败

**解决**:
```bash
# 重新安装依赖
pip install -r requirements.lock --force-reinstall

# 检查虚拟环境
which python
python --version
```

### ❌ 版本冲突

**解决**:
```bash
# 清理环境重建
deactivate
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock
```

## 获取帮助

如果以上方法都无法解决问题，请：

1. **收集信息**:
```bash
# 运行诊断
python -m research_pipeline doctor > diagnostic.txt

# 收集日志
tail -100 logs/pipeline.log > recent.log

# 系统信息
python --version
uname -a
```

2. **检查配置**:
```bash
# 脱敏后的配置
cat config/config.yaml | grep -v api_key
```

3. **最小化复现**:
```bash
# 尝试 demo 模式
python -m research_pipeline demo

# 尝试单个 PDF
python -m research_pipeline run \
  --date 2026-09-01 \
  --session test \
  --input-dir /path/to/single-pdf \
  --dry-run
```

4. **提交 Issue** 附上以上信息

## 紧急恢复

### 完全重置

```bash
# ⚠️ 这会删除所有数据！

# 1. 备份重要数据
cp -r outputs outputs-backup
cp database/research.db database/research.db.backup

# 2. 清理环境
rm -rf .venv database/ outputs/ logs/

# 3. 重新安装
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock

# 4. 重新初始化
python -m research_pipeline init
```

### 恢复备份

```bash
# 恢复数据库
cp database/research.db.backup database/research.db

# 恢复输出
cp -r outputs-backup/* outputs/
```
