#!/bin/bash
# GitHub上传脚本 - 执行-审查Agent系统
# 使用方法: bash upload_agent_system.sh

echo "================================"
echo "执行-审查Agent系统 - GitHub上传"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 检查Git状态
echo -e "${YELLOW}[1/6] 检查Git状态...${NC}"
if [ ! -d ".git" ]; then
    echo "  → 初始化Git仓库"
    git init
else
    echo "  → Git仓库已存在"
fi

# 2. 添加Agent系统核心文件
echo -e "${YELLOW}[2/6] 添加核心代码...${NC}"
git add .claude/skills/task-executor/executor.py
git add .claude/skills/task-executor/skill_integrator.py
git add .claude/skills/task-executor/main.py
git add .claude/skills/task-executor/SKILL.md

git add .claude/skills/quality-reviewer/
git add .claude/skills/task-coordinator/

git add .claude/skills/README-AGENT-SYSTEM.md
echo "  → 核心代码已添加"

# 3. 添加测试文件
echo -e "${YELLOW}[3/6] 添加测试文件...${NC}"
git add test/skill-evals/task-executor/test_skill_integration.py
echo "  → 测试文件已添加"

# 4. 添加文档
echo -e "${YELLOW}[4/6] 添加文档...${NC}"
git add AGENT-SYSTEM-FILES.md
git add .claude/CLAUDE.md
echo "  → 文档已添加"

# 5. 查看状态
echo -e "${YELLOW}[5/6] Git状态...${NC}"
git status --short

# 6. 提交
echo -e "${YELLOW}[6/6] 创建提交...${NC}"
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
- Self-evolution capability learning

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

echo ""
echo -e "${GREEN}✓ 提交完成！${NC}"
echo ""
echo "下一步："
echo "  1. 添加远程仓库: git remote add origin https://github.com/USERNAME/REPO.git"
echo "  2. 推送到GitHub: git push -u origin main"
echo ""
echo "================================"
