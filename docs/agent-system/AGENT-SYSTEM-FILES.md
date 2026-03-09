# 执行-审查Agent系统 - GitHub上传清单

## 📦 需要上传的文件

> **提示**: Agent系统的所有文档已整理到 `.claude/docs/agent-system/` 目录

### 核心代码（.claude/skills/）

```
.claude/skills/
├── task-executor/
│   ├── executor.py              # 执行Agent v2.0.0
│   ├── skill_integrator.py      # Skill集成器
│   ├── main.py                  # 命令行入口
│   ├── SKILL.md                 # Skill配置
│   └── review_criteria/         # 审查标准（如果存在）
│
├── quality-reviewer/
│   ├── reviewer.py              # 审查Agent
│   ├── main.py
│   ├── SKILL.md
│   └── review_criteria/         # 审查标准定义
│
├── task-coordinator/
│   ├── coordinator.py           # 任务协调器
│   ├── main.py
│   └── SKILL.md
│
└── README-AGENT-SYSTEM.md       # 系统文档
```

### 测试文件（test/）

```
test/skill-evals/task-executor/
└── test_skill_integration.py    # 集成测试
```

### 文档（.claude/）

```
.claude/
├── CLAUDE.md                    # 项目主文档
└── skills/
    └── README-AGENT-SYSTEM.md   # Agent系统文档
```

---

## 📝 .gitignore 配置

确保 `.gitignore` 包含以下内容：

```gitignore
# Python
__pycache__/
*.py[cod]
*.so
.Python
*.egg-info/
venv/
.venv/

# 测试和临时文件
test/skill-evals/**/capabilities/
test/skill-evals/**/learning_modules/
test/skill-evals/**/knowledge_base/
*.log

# 敏感信息
.env
.env.local
*.key
ZHIPU_API_KEY
API_KEY

# IDE
.vscode/
.idea/
*.swp
*.swo
```

---

## 🎯 上传命令

```bash
# 1. 初始化Git仓库（如果还没有）
cd C:/D/CAIE_tool/MyAIProduct
git init

# 2. 添加Agent系统文件
git add .claude/skills/task-executor/
git add .claude/skills/quality-reviewer/
git add .claude/skills/task-coordinator/
git add .claude/skills/README-AGENT-SYSTEM.md
git add test/skill-evals/task-executor/

# 3. 提交
git commit -m "feat: Add Executor-Reviewer Agent System v2.0.0

- SkillIntegrator: Unified interface for image-gen, web-search, toutiao-cnt, toutiao-img
- ExecutorAgent v2.0: Real skill integration instead of placeholders
- Composite tasks: article_with_images, research_and_write
- QualityReviewer: Security scanning, code review, content validation
- TaskCoordinator: Auto execution-review-improvement loop
- Integration tests: test_skill_integration.py
- Documentation: README-AGENT-SYSTEM.md

Features:
- 8-level fallback for image generation (98-99% reliability)
- 4-level fallback for web search (MCP → Tavily → DuckDuckGo → AI)
- Automatic article generation with images
- Security vulnerability scanning (OWASP Top 10)
- Self-evolution capability learning"

# 4. 连接到GitHub
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 5. 推送
git push -u origin main
```

---

## 📋 README.md 模板

建议在仓库根目录添加 README.md：

```markdown
# AI Agent System - 执行-审查协作系统

一个高度自主的双Agent协作系统，实现"执行-审查-改进"的闭环工作流。

## 系统架构

```
用户自然语言输入
    ↓
执行Agent (task-executor) ← Skill集成器
    ↓ 调用真实skills
审查Agent (quality-reviewer)
    ↓ 质量检查
任务协调器 (task-coordinator)
    ↓ 自动改进
返回最终结果
```

## 核心特性

### 执行Agent (v2.0.0)
- ✅ Skill集成：image-gen, web-search, toutiao-cnt, toutiao-img
- ✅ 复合任务：文章生成+配图、研究+写作
- ✅ 自我进化能力学习

### 审查Agent
- ✅ 安全漏洞扫描 (OWASP Top 10)
- ✅ 代码质量检查
- ✅ 内容准确性验证

### 任务协调器
- ✅ 自动执行-审查循环
- ✅ 智能改进反馈

## 快速开始

```bash
# 测试Skill集成
python test/skill-evals/task-executor/test_skill_integration.py

# 执行复合任务
python .claude/skills/task-coordinator/main.py \
    --type composite \
    --composite-type article_with_images \
    --topic "量子计算" \
    --num-images 3
```

## 文档

- [系统架构](.claude/skills/README-AGENT-SYSTEM.md)
- [项目指南](CLAUDE.md)

## 版本

- **v2.0.0** (2026-03-05): Skill集成实现
- **v1.0.0**: 初始版本
```

---

## ⚠️ 上传前检查清单

- [ ] 确认没有敏感信息（API密钥、密码等）
- [ ] 测试代码可以正常运行
- [ ] `.gitignore` 配置正确
- [ ] README.md 文档完整
- [ ] 版本号和日期更新

---

## 📊 文件大小预估

- 核心代码: ~15KB
- 测试代码: ~5KB
- 文档: ~10KB
- **总计**: ~30KB

---

**创建时间**: 2026-03-05
**版本**: 2.0.0
