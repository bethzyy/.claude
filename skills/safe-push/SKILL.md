---
name: safe-push
description: >
  Securely commit and push project code to GitHub with a three-phase pipeline:
  security scan (API keys, secrets, sensitive data detection) → documentation sync
  (README/PRD/CLAUDE.md) → git add/commit/push. ALWAYS use this skill when the user
  says "提交", "推送", "push", "commit", "安全推送", "提交代码", "推上去",
  "提交到github", "push到github", "commit and push", "帮我提交", "把这个push上去",
  "提交一下", "push一下", or asks to push/sync/commit code to a remote git repository.
  Also trigger when user specifies a target repo (e.g., "提交到 bethzyy/devBoard"),
  wants to commit-only without pushing, or asks to check for sensitive data before
  committing. Do NOT trigger for: creating GitHub repos, pull requests, git
  pull/fetch/merge, CI/CD workflows, server deployment, or git setup/configuration.
version: 1.2.0
tags: [git, security, github, documentation, workflow]
---

# Safe Push — 安全推送工作流

三阶段流水线，确保每次推送到 GitHub 的代码既安全又文档齐全。

## 总览

```
Phase 1: Security Scan → Phase 2: Doc Sync → Phase 3: Commit & Push
    (安全扫描)              (文档同步)           (提交推送)
```

每个阶段必须通过才能进入下一个。发现安全问题时**立即停止**并报告。

---

## Phase 1: Security Scan（安全扫描）

这是最重要的阶段。永远不要跳过。

### 1.1 扫描待提交文件中的敏感模式

用 Grep 在项目目录（不含 `node_modules/`, `__pycache__/`, `.git/`）中搜索：

**敏感关键词模式：**
```
api[_-]?key|secret|password|token|credential|apikey|ZHIPU_API
```

**实际密钥格式（命中任何一个 = 立即停止）：**
```
sk-[a-zA-Z0-9]{10,}
ghp_[a-zA-Z0-9]{36}
github_pat_[a-zA-Z0-9_]{82}
AKIA[0-9A-Z]{16}
AIza[a-zA-Z0-9_-]{35}
-----BEGIN (RSA |DSA |EC )?PRIVATE KEY
```

### 1.2 检查 .gitignore 覆盖范围

确认 `.gitignore` 包含以下规则（如缺失则补充）：
```
.env
.env.*
__pycache__/
*.pyc
data/
```

### 1.3 检查 git status

运行 `git status`，检查：
- 是否有意外的配置文件（`.env`, `credentials.json`）出现在未跟踪列表
- `data/` 目录是否被正确排除
- 是否有超大二进制文件

### 1.4 安全扫描结果处理

- **发现实际密钥（sk-, ghp_, AKIA 等）→ 立即停止**，报告文件名和行号，等用户处理
- **发现敏感关键词（api_key, secret 等）但不是实际密钥 → 警告**，列出文件和行号，继续但提醒用户确认
- **全部通过 → 进入 Phase 2**

---

## Phase 2: Doc Sync（文档同步）

确保项目文档反映代码的实际状态。

### 2.1 检测文档文件

检查项目根目录下是否存在：
- `README.md`
- `PRD.md`（可选）
- `CLAUDE.md`（可选）

### 2.2 对比文档与实际状态

逐项检查文档内容是否与代码一致：

**README.md 重点检查：**
- 项目描述是否准确
- Features 列表是否完整
- 架构图/目录结构是否与实际文件一致
- 命令是否可用
- Design System / 配色等 UI 描述是否与模板 CSS 一致

**PRD.md 重点检查：**
- 功能需求状态（Done / In Progress / Planned）是否与实际匹配
- 数据模型是否与代码结构一致

**CLAUDE.md 重点检查：**
- 架构描述是否与实际代码结构一致
- 命令是否正确
- API 列表是否完整

### 2.3 更新规则

- 只修改过时的部分，不要重写整个文件
- 保持原有的文档结构和格式风格
- 新增内容时遵循已有的标题层级和表格格式
- 如果文档内容已经准确，不需要做任何修改

---

## Phase 3: Commit & Push（提交推送）

### 3.1 确认变更范围

运行 `git status` 和 `git diff --stat`，向用户展示即将提交的文件列表。

### 3.2 Stage 文件

- 使用 `git add <具体文件名>` 逐个添加
- **不要使用 `git add .` 或 `git add -A`**
- 不要添加 `.env`、`credentials`、`data/` 等敏感或生成文件

### 3.3 生成 commit message

- 基于实际变更内容生成，不是固定模板
- 格式：一句话描述做了什么（why 优先于 what）
- 如果有安全修复或重要变更，在 message 中体现
- 结尾附上 `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`
- 使用 HEREDOC 格式避免引号问题

### 3.4 确保分支存在

检查当前是否有分支和远程仓库，按顺序处理：

**检查当前分支：**
```bash
git branch --list
```

如果没有分支（空仓库），创建 main 分支：
```bash
git checkout -b main
```

如果已有分支但不是 main，使用当前分支继续。

**检查远程仓库：**

用户可能说了具体的 repo 名称（如"提交到 bethzyy/devBoard"），也可能只是说"提交"。按以下逻辑处理：

1. 运行 `git remote -v` 检查是否已有 remote origin
2. **用户指定了 repo 名称**（如"提交到 xxx/yyy"）：
   - 设置 remote：`git remote add origin https://github.com/xxx/yyy.git`
   - 如果 remote 已存在但指向不同 repo，询问用户是否要切换
3. **用户没有指定 repo**：
   - 如果已有 remote origin → 直接使用当前 remote
   - 如果没有 remote → 从目录名推断仓库名，询问用户确认
   - 如果远程 repo 不存在 → 使用 GitHub API 创建：读取 `LLM_Configs/github/apikey.txt` 获取 token，然后 `curl -X POST https://api.github.com/user/repos` 创建同名公开仓库

**确保 main 分支存在远程：**
```bash
git branch -M main
git push -u origin main
```

### 3.5 推送

- `git push` 推送到远程
- 如果 push 失败（网络/认证问题）：
  - 报告错误信息
  - **保留本地 commit**（不要 reset）
  - 告诉用户可以稍后手动 `git push`

### 3.6 完成报告

推送成功后，简要报告：
- 提交了几个文件
- commit hash（前 7 位）
- 远程仓库地址

---

## 边界情况处理

| 情况 | 处理方式 |
|------|---------|
| 项目没有 git 仓库 | 提示用户先 `git init`，不要自动初始化 |
| 没有 remote origin | 从目录名推断，或让用户指定 `owner/repo` |
| 远程 repo 不存在 | 用 GitHub API 自动创建同名公开仓库 |
| 没有任何分支（空仓库） | 自动创建 main 分支 `git checkout -b main` |
| `data/` 目录没在 .gitignore 中 | 自动补充到 .gitignore |
| 用户说"只提交不改文档" | 跳过 Phase 2，直接 Phase 1 + Phase 3 |
| 用户说"不push只commit" | 执行 Phase 1 + Phase 2 + commit，跳过 push |
| 检测到实际密钥 | **硬停**，报告位置，等用户处理后再继续 |
| 多个 remote | 使用当前跟踪的 remote（`git branch -vv` 查看） |
| 用户指定了 repo 名称 | 覆盖当前 remote，push 到指定 repo |

---

## 版本历史

- **v1.2.0** (2026-04-14): Description 优化
  - 移除与部署 skill 冲突的触发词（发版、发布、publish、deploy）
  - 增加 commit-only 场景和指定目标 repo 场景
  - 增加负面边界（Do NOT trigger for）提升精度
  - Description 从关键词堆砌改为意图描述+边界约束
- **v1.1.0** (2026-04-14): 增强版
  - 自动创建 main 分支（空仓库场景）
  - 支持用户指定目标 repo 或自动推断
  - 远程 repo 不存在时自动通过 GitHub API 创建
- **v1.0.0** (2026-04-14): 初始版本
  - 三阶段流水线：安全扫描 → 文档同步 → 提交推送
  - 支持 API key / 密钥 / 敏感数据检测
  - 自动同步 README / PRD / CLAUDE.md
