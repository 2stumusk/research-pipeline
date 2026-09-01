# 🔑 GitHub Token 创建指南

## 问题
GitHub 不再支持密码认证，需要使用 Personal Access Token。

---

## 创建 Token 步骤

### 1. 访问 Token 设置页面
打开浏览器访问：
```
https://github.com/settings/tokens
```

### 2. 生成新 Token
1. 点击右上角 **"Generate new token"** → 选择 **"Generate new token (classic)"**
2. 填写信息：
   - **Note**: `research-pipeline` (给这个 token 起个名字)
   - **Expiration**: `No expiration` 或选择有效期
   - **Select scopes**: 勾选 ✅ **`repo`** (完整的仓库访问权限)
3. 滚动到底部，点击 **"Generate token"**

### 3. 复制 Token
⚠️ **重要**：生成后会显示类似这样的 token：
```
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**立即复制保存**，关闭页面后就看不到了！

---

## 使用 Token 推送

### 方法 1：在命令行中使用

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline

# 推送代码
git push -u origin main
```

当提示输入密码时：
- **Username**: `961958105@qq.com` 或 `2stumusk`
- **Password**: 粘贴你刚才复制的 Token（不是 GitHub 密码）

---

## ⚠️ 注意

1. **密码输入是隐藏的**
   - 你输入时看不到任何字符
   - 直接粘贴 Token 然后按回车

2. **不要输入 GitHub 密码**
   - 必须使用 Token
   - 密码不会工作

3. **保存 Token**
   - 可以保存在密码管理器
   - 或记录在安全的地方

---

## 快捷方式

如果不想每次都输入，可以配置 credential helper：

```bash
# macOS 使用 keychain 保存
git config --global credential.helper osxkeychain
```

下次输入 Token 后会自动保存。

---

现在去创建 Token：https://github.com/settings/tokens
