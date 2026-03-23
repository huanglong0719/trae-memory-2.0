# Trae Memory 2.0 推送到 GitHub 指南

## 方法一：手动创建仓库后推送

### 步骤 1：在 GitHub 上创建仓库

1. 访问 https://github.com/new
2. 仓库名称：`trae-memory-2.0`
3. 描述：`融合 EvoMap 理念的自我进化记忆系统 - Trae Memory 的升级版本`
4. 选择 **Public** 或 **Private**
5. **不要** 勾选 "Add a README file"、".gitignore"、"Choose a license"
6. 点击 "Create repository"

### 步骤 2：推送代码到 GitHub

根据您的 GitHub 用户名，替换下面的 `<YOUR_USERNAME>` 和 `<YOUR_TOKEN>`：

```powershell
# 添加远程仓库（使用 Token）
git remote add origin https://<YOUR_USERNAME>:<YOUR_TOKEN>@github.com/<YOUR_USERNAME>/trae-memory-2.0.git

# 推送到 GitHub
git push -u origin master
```

### 示例（替换为您的实际信息）：

```powershell
# 假设您的 GitHub 用户名是 long，Token 是 ghp_xxxxx
git remote add origin https://long:ghp_xxxxx@github.com/long/trae-memory-2.0.git
git push -u origin master
```

---

## 方法二：使用 GitHub CLI（推荐）

如果您已安装 GitHub CLI，可以更简单地创建和推送：

### 步骤 1：登录 GitHub CLI

```powershell
gh auth login
```

### 步骤 2：创建仓库并推送

```powershell
# 创建仓库
gh repo create trae-memory-2.0 --public --description "融合 EvoMap 理念的自我进化记忆系统" --source=. --remote=origin --push
```

---

## 方法三：使用 Git 命令行工具

### 1. 创建 Personal Access Token

访问：https://github.com/settings/tokens/new

- Note: `Trae Memory 2.0 Push`
- Select scopes: 勾选 **repo** (Full control of private repositories)
- 点击 "Generate token"
- **复制并保存 Token**（只显示一次）

### 2. 推送代码

```powershell
# 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/trae-memory-2.0.git

# 推送
git push -u origin master
```

系统会提示输入用户名和密码：
- Username: 您的 GitHub 用户名
- Password: 使用刚才创建的 Personal Access Token

---

## 验证推送

推送成功后，访问：
```
https://github.com/YOUR_USERNAME/trae-memory-2.0
```

应该能看到所有文件。

---

## 后续更新

之后如果需要更新代码，只需执行：

```powershell
git add .
git commit -m "更新说明"
git push
```

---

## 注意事项

1. **Token 安全**：不要将 Token 提交到代码库中
2. **.gitignore**：已自动忽略 `__pycache__/` 和 `*.pyc` 文件
3. **许可证**：建议在 GitHub 仓库中添加 MIT License
4. **Issues**：可以在 GitHub 仓库中启用 Issues 收集反馈

---

## 快速复制的命令

```powershell
# 1. 添加远程仓库（替换 YOUR_USERNAME 和 YOUR_TOKEN）
git remote add origin https://YOUR_USERNAME:YOUR_TOKEN@github.com/YOUR_USERNAME/trae-memory-2.0.git

# 2. 推送
git push -u origin master

# 3. 验证
git remote -v
```

---

**仓库名称**: trae-memory-2.0  
**描述**: 融合 EvoMap 理念的自我进化记忆系统  
**许可证**: MIT  
