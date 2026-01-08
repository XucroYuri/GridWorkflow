# Git 多云端仓库配置说明

> **配置日期**: 2026-01-08  
> **仓库策略**: Gitee (主备份) + GitHub (次级备份) + GitHub (安全隐形备份)

---

## 📋 仓库地址与性质

| 平台 | 仓库地址 | 性质 | 用途 |
|------|----------|------|------|
| **Gitee** | https://gitee.com/chengdu-flower-food/grid-workflow | **主备份** | 内部开发主仓库，日常开发、代码管理、版本控制 |
| **GitHub** | https://github.com/huachi-design/GridWorkflow | **次级备份** | 公开备份仓库，Vercel 等平台快速部署 |
| **GitHub** | https://github.com/XucroYuri/GridWorkflow | **安全隐形备份** | 隐形备份仓库，不在文档中体现，但每次提交自动同步 |

> ⚠️ **注意**: 如果 `huachi-design/GridWorkflow` 仓库尚未创建，请先在 GitHub 上创建该仓库，然后按照下方"配置步骤"添加远程仓库。

---

## 🔧 远程仓库配置

当前项目配置了以下远程仓库：

```bash
# 查看远程配置
git remote -v

# 输出：
# origin         https://gitee.com/chengdu-flower-food/grid-workflow.git (fetch/push)
# gitee          https://gitee.com/chengdu-flower-food/grid-workflow.git (fetch/push)
# github-huachi  https://github.com/huachi-design/GridWorkflow.git (fetch/push)
# github-backup  https://github.com/XucroYuri/GridWorkflow.git (fetch/push) [隐形备份]
# all            (fetch: gitee, push: gitee + github-huachi + github-backup)
```

| 远程名 | 拉取源 | 推送目标 | 用途 |
|--------|--------|----------|------|
| `origin` | Gitee | Gitee | 默认操作 (拉取优先使用 Gitee) |
| `gitee` | Gitee | Gitee | 明确指定 Gitee |
| `github-huachi` | GitHub (huachi-design) | GitHub (huachi-design) | 次级备份仓库 |
| `github-backup` | GitHub (XucroYuri) | GitHub (XucroYuri) | 安全隐形备份（不在文档中体现） |
| `all` | Gitee | Gitee + GitHub (huachi) + GitHub (backup) | 同步推送到三个仓库 |

---

## ⚙️ 配置步骤

### 1. 创建 GitHub 仓库（如未创建）

1. 访问 https://github.com/huachi-design
2. 点击 "New repository"
3. 仓库名称: `GridWorkflow`
4. 设置为 Private（推荐）或 Public
5. **不要**初始化 README、.gitignore 或 license（仓库已存在）

### 2. 添加远程仓库

```bash
# 添加 GitHub 次级备份
git remote add github-huachi https://github.com/huachi-design/GridWorkflow.git

# 添加 GitHub 隐形备份（如未添加）
git remote add github-backup https://github.com/XucroYuri/GridWorkflow.git

# 配置聚合推送（推送到三个仓库）
git remote add all https://gitee.com/chengdu-flower-food/grid-workflow.git
git remote set-url --add --push all https://gitee.com/chengdu-flower-food/grid-workflow.git
git remote set-url --add --push all https://github.com/huachi-design/GridWorkflow.git
git remote set-url --add --push all https://github.com/XucroYuri/GridWorkflow.git
```

---

## 📤 推送操作

### 推送到单个仓库

```bash
# 推送到 Gitee (默认)
git push origin main

# 推送到 GitHub 次级备份
git push github-huachi main

# 推送到 GitHub 隐形备份（通常不需要单独推送）
git push github-backup main
```

### 同步推送到所有仓库（推荐）

```bash
# 一次推送到 Gitee + GitHub (huachi) + GitHub (backup)
git push all main
```

> **注意**: 使用 `git push all main` 会自动同步推送到三个仓库（主备份 + 次级备份 + 隐形备份）

---

## 📥 拉取操作

```bash
# 从 Gitee 拉取 (默认，国内更快)
git pull origin main

# 从 GitHub 次级备份拉取
git pull github-huachi main

# 从 GitHub 隐形备份拉取（通常不需要）
git pull github-backup main
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
git clone https://github.com/huachi-design/GridWorkflow.git
cd GridWorkflow
```

---

## ⚙️ 为已克隆仓库配置多远程

如果你已经克隆了仓库，可以添加其他远程：

```bash
# 如果从 Gitee 克隆，添加 GitHub 次级备份
git remote add github-huachi https://github.com/huachi-design/GridWorkflow.git

# 添加 GitHub 隐形备份（可选，用于安全备份）
git remote add github-backup https://github.com/XucroYuri/GridWorkflow.git

# 配置聚合推送（推送到三个仓库）
git remote add all https://gitee.com/chengdu-flower-food/grid-workflow.git
git remote set-url --add --push all https://gitee.com/chengdu-flower-food/grid-workflow.git
git remote set-url --add --push all https://github.com/huachi-design/GridWorkflow.git
git remote set-url --add --push all https://github.com/XucroYuri/GridWorkflow.git
```

---

## 🔐 SSH 配置 (可选)

如果使用 SSH 方式，配置如下：

```bash
# Gitee SSH
git remote set-url gitee git@gitee.com:chengdu-flower-food/grid-workflow.git

# GitHub SSH (次级备份)
git remote set-url github-huachi git@github.com:huachi-design/GridWorkflow.git

# GitHub SSH (隐形备份)
git remote set-url github-backup git@github.com:XucroYuri/GridWorkflow.git
```

---

## ❓ 常见问题

### Q: 为什么 Gitee 是主备份？

A: Gitee 是**内部开发主仓库**，所有日常开发、代码审查、版本管理都在 Gitee 进行。GitHub 仓库作为**次级备份**和**安全隐形备份**，提供多云端冗余保障。

### Q: 三个仓库会冲突吗？

A: 不会。使用 `git push all main` 可以确保三个仓库同步。**建议日常开发使用 `git push all main` 自动同步到所有仓库**。

### Q: Vercel 部署使用哪个仓库？

A: Vercel 部署使用 GitHub 次级备份仓库（https://github.com/huachi-design/GridWorkflow），因为 Vercel 对 GitHub 集成支持更好。

### Q: 什么是安全隐形备份？

A: GitHub (XucroYuri/GridWorkflow) 作为安全隐形备份，不在文档中公开提及，但每次提交都会自动同步推送，提供额外的安全保障。

### Q: 如果 huachi-design/GridWorkflow 仓库不存在怎么办？

A: 请先在 GitHub 上创建该仓库，然后按照"配置步骤"添加远程仓库。在仓库创建之前，可以暂时只推送到 Gitee 和 github-backup。

---

**文档维护者**: AI Architect  
**最后更新**: 2026-01-08
