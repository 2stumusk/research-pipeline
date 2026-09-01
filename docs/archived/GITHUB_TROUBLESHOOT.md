# 🔧 GitHub 仓库地址问题

## 问题
中文仓库名在命令行中可能无法识别。

## 解决方案

### 方法 1：获取正确的仓库地址

1. 打开你的 GitHub 仓库页面：
   ```
   https://github.com/2秒tumusk/研究管道
   ```

2. 点击绿色的 **"Code"** 按钮

3. 复制显示的 HTTPS 地址（GitHub 会自动处理编码）

4. 在终端运行：
   ```bash
   cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
   
   # 删除旧的 remote
   git remote remove origin
   
   # 添加正确的地址（用你复制的地址）
   git remote add origin [你复制的地址]
   
   # 推送
   git push -u origin main
   git push --tags
   ```

---

### 方法 2：重命名仓库（推荐）

中文名称可能会有各种问题，建议改成英文名：

1. 在 GitHub 仓库页面，点击 **Settings**
2. 在 "Repository name" 处改名，例如：
   - `research-pipeline`
   - `a-share-analyzer`
   - `report-analyzer`
3. 点击 **Rename**
4. 然后运行：
   ```bash
   git remote remove origin
   git remote add origin https://github.com/2秒tumusk/research-pipeline.git
   git push -u origin main
   git push --tags
   ```

---

### 方法 3：使用 SSH 方式

如果配置了 SSH key：

```bash
git remote remove origin
git remote add origin git@github.com:2秒tumusk/研究管道.git
git push -u origin main
git push --tags
```

---

## 💡 建议

**最简单的方法**：重命名仓库为英文名 `research-pipeline`

然后运行：
```bash
git remote remove origin
git remote add origin https://github.com/2秒tumusk/research-pipeline.git
git push -u origin main
git push --tags
```
