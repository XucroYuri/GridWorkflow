# Git 仓库配置完整指南

> **创建日期**: 2026-01-08  
> **目的**: 完整配置三仓库备份策略

---

## 📋 仓库策略说明

| 仓库 | 地址 | 性质 | 说明 |
|------|------|------|------|
| **Gitee** | https://gitee.com/chengdu-flower-food/grid-workflow | **主备份** | 内部开发主仓库，所有日常开发在此进行 |
| **GitHub (huachi)** | https://github.com/huachi-design/GridWorkflow | **次级备份** | 公开备份仓库，在文档中明文指向，用于 Vercel 部署 |
| **GitHub (backup)** | https://github.com/XucroYuri/GridWorkflow | **安全隐形备份** | 不在文档中体现，但每次提交自动同步推送 |

---

## 🔧 完整配置步骤

### 步骤 1: 创建 GitHub 仓库（huachi-design）

1. 访问 https://github.com/huachi-design
2. 点击右上角 **"New repository"** 或 **"+"** → **"New repository"**
3. 填写仓库信息：
   - **Repository name**: `GridWorkflow`
   - **Description**: `AI 驱动的视频创作工作流平台`
   - **Visibility**: Private（推荐）或 Public
   - **⚠️ 重要**: **不要**勾选以下选项：
     - ❌ Add a README file
     - ❌ Add .gitignore
     - ❌ Choose a license
4. 点击 **"Create repository"**

### 步骤 2: 添加远程仓库

在本地项目目录执行：

```bash
# 添加 GitHub 次级备份（huachi-design）
git remote add github-huachi https://github.com/huachi-design/GridWorkflow.git

# 验证远程仓库
git remote -v
```

预期输出应包含：
```
github-huachi  https://github.com/huachi-design/GridWorkflow.git (fetch)
github-huachi  https://github.com/huachi-design/GridWorkflow.git (push)
```

### 步骤 3: 配置聚合推送（all remote）

```bash
# 如果 all remote 已存在，先添加 huachi 仓库
git remote set-url --add --push all https://github.com/huachi-design/GridWorkflow.git

# 验证 all remote 配置
git remote show all
```

预期输出应显示三个推送目标：
- Gitee
- GitHub (huachi-design)
- GitHub (XucroYuri)

### 步骤 4: 首次推送到新仓库

```bash
# 推送到所有仓库（包括新创建的 huachi-design）
git push all main

# 或者单独推送到新仓库
git push github-huachi main
```

> ⚠️ **注意**: 如果推送时提示 "Repository not found" 或需要认证：
> - 确保仓库已创建且你有推送权限
> - 使用 HTTPS 时，GitHub 可能需要 Personal Access Token（而不是密码）
> - 使用 SSH 时，确保 SSH 密钥已添加到 GitHub 账号

### 步骤 5: 验证配置

```bash
# 查看所有远程仓库
git remote -v

# 测试推送到所有仓库
git push all main
```

---

## ✅ 配置完成检查清单

- [ ] huachi-design/GridWorkflow 仓库已创建
- [ ] `github-huachi` remote 已添加
- [ ] `all` remote 包含三个推送目标
- [ ] 首次推送成功
- [ ] 文档中的 GitHub 链接已更新为 huachi-design/GridWorkflow

---

## 🔄 日常使用

### 推送到所有仓库（推荐）

```bash
git push all main
```

这会自动推送到：
1. Gitee（主备份）
2. GitHub huachi-design（次级备份）
3. GitHub XucroYuri（隐形备份）

### 单独推送

```bash
# 只推送到 Gitee
git push gitee main

# 只推送到 GitHub 次级备份
git push github-huachi main

# 只推送到 GitHub 隐形备份（通常不需要）
git push github-backup main
```

---

## ⚠️ 注意事项

1. **安全隐形备份**: `github-backup` (XucroYuri/GridWorkflow) 不在文档中公开提及，但每次 `git push all main` 都会自动同步推送
2. **文档更新**: 所有公开文档中的 GitHub 链接都应指向 `huachi-design/GridWorkflow`
3. **Vercel 部署**: 使用 `huachi-design/GridWorkflow` 仓库进行部署

---

## 🆘 故障排除

### 问题: 推送时提示 "Repository not found"

**原因**: `huachi-design/GridWorkflow` 仓库尚未创建

**解决**: 按照"步骤 1"创建仓库，然后重新执行配置步骤

### 问题: 推送失败，提示权限错误

**原因**: 没有访问仓库的权限

**解决**: 
1. 确认 GitHub 账号有 `huachi-design` 组织的访问权限
2. 检查 SSH 密钥或访问令牌配置
3. 使用 HTTPS 方式时，确保已配置凭据

### 问题: all remote 推送失败

**原因**: 某个仓库配置错误或不存在

**解决**: 
1. 检查 `git remote -v` 确认所有 remote 配置正确
2. 单独测试每个 remote 的推送
3. 移除有问题的 remote，重新添加

---

**文档维护者**: AI Architect  
**最后更新**: 2026-01-08

