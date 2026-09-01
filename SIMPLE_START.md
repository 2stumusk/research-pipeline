# 🎯 最简单的使用方式

Web UI 交互有问题，现在给你**3个超简单的方式**：

---

## 方式 1：双击运行（最简单）⭐⭐⭐

### macOS Finder 中：

1. 打开文件夹：
   ```
   /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
   ```

2. 双击文件：
   ```
   一键运行.sh
   ```

3. 会自动运行并打开结果！

---

## 方式 2：命令行菜单

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline
python3 simple_launcher.py
```

**会显示菜单**：
```
1. 运行 Demo（测试示例）
2. 运行真实分析
3. 查看最新结果
4. 打开输出文件夹
5. 退出
```

输入数字选择即可！

---

## 方式 3：一行命令（最直接）

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline && source .venv/bin/activate && python3 -m research_pipeline demo && open outputs/demo/dashboard.html
```

复制粘贴，回车，等待，自动打开结果！

---

## 🎉 推荐顺序

1. **先试方式 3**（一行命令）- 最快看到效果
2. **再试方式 2**（菜单）- 更方便日常使用
3. **最后试方式 1**（双击）- 最简单，但可能需要授权

---

## 现在就试试方式 3：

```bash
cd /Users/musk2/Desktop/产业链分析/自动化分析项目-prompt/research_pipeline && source .venv/bin/activate && python3 -m research_pipeline demo && open outputs/demo/dashboard.html
```

**一条命令搞定！**
