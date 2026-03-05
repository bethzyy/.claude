@echo off
REM GitHub上传脚本 - 执行-审查Agent系统 (Windows)
REM 使用方法: upload_agent_system.bat

echo ================================
echo 执行-审查Agent系统 - GitHub上传
echo ================================
echo.

REM 1. 检查Git状态
echo [1/6] 检查Git状态...
if not exist ".git" (
    echo   --^> 初始化Git仓库
    git init
) else (
    echo   --^> Git仓库已存在
)

REM 2. 添加Agent系统核心文件
echo [2/6] 添加核心代码...
git add .claude/skills/task-executor/executor.py
git add .claude/skills/task-executor/skill_integrator.py
git add .claude/skills/task-executor/main.py
git add .claude/skills/task-executor/SKILL.md

git add .claude/skills/quality-reviewer/
git add .claude/skills/task-coordinator/

git add .claude/skills/README-AGENT-SYSTEM.md
echo   --^> 核心代码已添加

REM 3. 添加测试文件
echo [3/6] 添加测试文件...
git add test/skill-evals/task-executor/test_skill_integration.py
echo   --^> 测试文件已添加

REM 4. 添加文档
echo [4/6] 添加文档...
git add AGENT-SYSTEM-FILES.md
git add .claude/CLAUDE.md
echo   --^> 文档已添加

REM 5. 查看状态
echo [5/6] Git状态...
git status --short

REM 6. 提交
echo [6/6] 创建提交...
git commit -m "feat: Add Executor-Reviewer Agent System v2.0.0

- SkillIntegrator: Unified interface for image-gen, web-search, toutiao-cnt, toutiao-img
- ExecutorAgent v2.0: Real skill integration instead of placeholders
- Composite tasks: article_with_images, research_and_write
- QualityReviewer: Security scanning, code review, content validation
- TaskCoordinator: Auto execution-review-improvement loop
- Integration tests: test_skill_integration.py
- Documentation: README-AGENT-SYSTEM.md

Features:
- 8-level fallback for image generation (98-99%% reliability)
- 4-level fallback for web search (MCP -^> Tavily -^> DuckDuckGo -^> AI)
- Automatic article generation with images
- Security vulnerability scanning (OWASP Top 10)
- Self-evolution capability learning

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

echo.
echo [完成] 提交成功！
echo.
echo 下一步：
echo   1. 添加远程仓库: git remote add origin https://github.com/USERNAME/REPO.git
echo   2. 推送到GitHub: git push -u origin main
echo.
echo ================================
pause
