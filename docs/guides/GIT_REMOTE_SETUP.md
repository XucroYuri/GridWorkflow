# Git 双云端仓库配置说明

> **配置日期**: 2026-01-08  
> **仓库性质**: Gitee (内部开发主仓库) + GitHub (快速部署临时仓库)

---

## 📋 仓库地址与性质

| 平台 | 仓库地址 | 性质 | 用途 |
|------|----------|------|------|
| **Gitee** | https://gitee.com/chengdu-flower-food/grid-workflow | **内部开发主仓库** | 日常开发、代码管理、版本控制 |
| **GitHub** | https://github.com/XucroYuri/GridWorkflow | **快速部署临时仓库** | Vercel 等平台快速部署，仅用于部署流程 |

---

## 🔧 远程仓库配置

当前项目配置了以下远程仓库：

```bash
# 查看远程配置
git remote -v

# 输出：
# origin  https://gitee.com/chengdu-flower-food/grid-workflow.git (fetch/push)
# gitee   https://gitee.com/chengdu-flower-food/grid-workflow.git (fetch/push)
# github  https://github.com/XucroYuri/GridWorkflow.git (fetch/push)
# all     (fetch: gitee, push: gitee + github)
```

| 远程名 | 拉取源 | 推送目标 | 用途 |
|--------|--------|----------|------|
| `origin` | Gitee | Gitee | 默认操作 (拉取优先使用 Gitee) |
| `gitee` | Gitee | Gitee | 明确指定 Gitee |
| `github` | GitHub | GitHub | 明确指定 GitHub |
| `all` | Gitee | Gitee + GitHub | 同步推送到两个仓库 |

---

## 📤 推送操作

### 推送到单个仓库

```bash
# 推送到 Gitee (默认)
git push origin main

# 推送到 GitHub
git push github main
```

### 同步推送到两个仓库

```bash
# 一次推送到 Gitee 和 GitHub
git push all main
```

---

## 📥 拉取操作

```bash
# 从 Gitee 拉取 (默认，国内更快)
git pull origin main

# 从 GitHub 拉取
git pull github main
```

---

## 🔄 克隆仓库

### 国内用户 (推荐)

```bash
git clone https://gitee.com/chengdu-flower-food/grid-workflow.git
cd grid-workflow
```

### 国际用户

```bash
git clone https://github.com/XucroYuri/GridWorkflow.git
cd GridWorkflow
```

---

## ⚙️ 为已克隆仓库配置双远程

如果你已经克隆了仓库，可以添加另一个远程：

```bash
# 如果从 GitHub 克隆，添加 Gitee
git remote add gitee https://gitee.com/chengdu-flower-food/grid-workflow.git

# 如果从 Gitee 克隆，添加 GitHub
git remote add github https://github.com/XucroYuri/GridWorkflow.git

# 配置聚合推送
git remote add all https://gitee.com/chengdu-flower-food/grid-workflow.git
git remote set-url --add --push all https://gitee.com/chengdu-flower-food/grid-workflow.git
git remote set-url --add --push all https://github.com/XucroYuri/GridWorkflow.git
```

---

## 🔐 SSH 配置 (可选)

如果使用 SSH 方式，配置如下：

```bash
# Gitee SSH
git remote set-url gitee git@gitee.com:chengdu-flower-food/grid-workflow.git

# GitHub SSH
git remote set-url github git@github.com:XucroYuri/GridWorkflow.git
```

---

## ❓ 常见问题

### Q: 为什么 Gitee 是主仓库？

A: Gitee 是**内部开发主仓库**，所有日常开发、代码审查、版本管理都在 Gitee 进行。GitHub 仅作为**快速部署的临时仓库**，用于 Vercel 等平台的自动化部署流程。

### Q: 两个仓库会冲突吗？

A: 不会。使用 `git push all main` 可以确保两个仓库同步。**建议日常开发只推送到 Gitee，仅在需要部署时同步到 GitHub**。

### Q: Vercel 部署使用哪个仓库？

A: Vercel 部署使用 GitHub 仓库（快速部署临时仓库），因为 Vercel 对 GitHub 集成支持更好。部署前需要将代码从 Gitee 同步到 GitHub。

---

**文档维护者**: AI Architect  
**最后更新**: 2026-01-08

