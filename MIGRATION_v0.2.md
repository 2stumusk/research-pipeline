# 迁移指南：v0.1.0 → v0.1.2

## 重要变更总结

### 1. 依赖一致性

**变更**: `pyproject.toml` 和 `requirements.txt` 现在都包含 Flask。

```
Flask>=3.0,<4
```

**操作**: 重新安装依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置向后兼容性增强

新增 `load_llm_config` 函数作为 `normalize_llm_config` 的向后兼容别名。接受 Path、AppConfig 或 dict。

**操作**: 现有离线脚本无需修改即可继续使用。

### 3. GUI 安全增强

GUI (`gui_app.py`) 增强了安全性和可用性：

- **Session ID 验证**: 生成 `gui-HHMMSS-<hex>` 格式，拒绝路径遍历和无效时间字段
- **输入目录隔离**: 每次运行创建唯一输入目录 `inbox/<date>-<session>`
- **文件冲突处理**: 同名不同内容的文件自动添加 SHA256 前缀，使用流式哈希处理大文件
- **部分成功处理**: 解析 CLI JSON 输出（无论返回码），状态为 `partial` 且有 dashboard 时视为可查看警告

**操作**: 无需手动操作，GUI 会自动处理。

### 4. CLI Doctor 输出调整

`doctor` 命令输出更明确：

- **现在**: "Codex (生产环境后端)"（明确标签）
- 不再要求 `anthropic` 和 `openai` 模块（Codex 模式下非必需）

**操作**: 重新运行 `python -m research_pipeline doctor` 确认状态。

## 迁移步骤

### 步骤 1: 备份

```bash
# 备份现有配置和数据
cp -r config config.backup
cp -r database database.backup
```

### 步骤 2: 更新代码

```bash
git pull origin main
```

### 步骤 3: 更新依赖

```bash
source .venv/bin/activate
pip install --upgrade -r requirements.txt
```

### 步骤 4: 验证环境

```bash
python -m research_pipeline doctor
```

### 步骤 5: 测试运行

```bash
# Dry run 测试（不调用 Codex）
python -m research_pipeline run --date 2024-01-15 --dry-run

# 正式运行（小批量测试）
mkdir -p inbox/2024-01-15
cp test-report.pdf inbox/2024-01-15/
python -m research_pipeline run --date 2024-01-15 --session 0900
```

## 配置迁移

配置文件 `config/config.yaml` 保持向后兼容，无需修改。如之前使用了实验性 `llm` 配置段，可以保留（不会影响生产流水线）或删除。

## 测试迁移

运行测试确保迁移成功：

```bash
bash scripts/run_tests.sh
```

## 常见迁移问题

### Q: 我的旧配置文件还兼容吗？

A: 是的，`codex` 段的配置向后兼容。

### Q: 旧的输出和数据库会丢失吗？

A: 不会。数据库 schema 和输出格式保持不变，旧数据可正常读取。

### Q: GUI 行为有什么变化？

A: GUI 现在更安全（session 验证、文件冲突处理、时间字段验证）且更健壮（解析部分成功的输出）。对用户可见的界面基本不变。

## 获取帮助

迁移过程中遇到问题？

1. 检查 `logs/pipeline.log` 和 `logs/doctor.log`
2. 运行 `python -m research_pipeline doctor` 诊断
3. 查阅 [README.md](README.md) 和 [QUICKSTART.md](QUICKSTART.md)

---

**迁移完成后**: 删除备份目录（确认一切正常后）

```bash
rm -rf config.backup database.backup
```

---

**版本**: v0.1.2
**更新**: 维护性修复，Claude CLI 辅助编写
