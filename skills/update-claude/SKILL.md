---
name: update-claude
description: Automatically update CLAUDE.md with recent project changes. Scans for new files, modified structure, and updates documentation. Use when user says "update CLAUDE.md", "sync documentation", "refresh project docs", or "update project readme".
version: 1.0.0
author: Claude Code
tags: [documentation, maintenance, sync]
---

# Update CLAUDE.md Skill

自动扫描项目变化并更新 CLAUDE.md 文档。

## 触发条件

当用户说以下任一内容时触发：
- "更新 CLAUDE.md"
- "sync documentation"
- "刷新项目文档"
- "update project docs"
- "更新项目说明"

## 工作流程

1. **扫描项目结构**
   - 检测新增的目录/项目
   - 检测新的主要文件
   - 分析项目架构变化

2. **对比 CLAUDE.md**
   - 找出文档中缺失的内容
   - 识别过时的信息
   - 标记需要更新的部分

3. **生成更新建议**
   - 列出需要添加的项目
   - 列出需要删除的内容
   - 列出需要修改的部分

4. **应用更新**
   - 更新主项目列表
   - 添加新命令
   - 更新版本历史
   - 添加新章节（如有必要）

## 自动检测内容

### 新项目检测
扫描 `C:\D\CAIE_tool\MyAIProduct\` 下的目录：
- 检测 `README.md` 或 `CLAUDE.md`（表示独立项目）
- 检测 `package.json`、`requirements.txt`（表示代码项目）
- 检测主要源代码文件

### 新技能检测
扫描 `.claude/skills/` 和 `skills/` 目录：
- 检测新的 SKILL.md 文件
- 分析 skill 功能和用途

### 配置文件检测
扫描重要的配置文件：
- `.env.example`
- `config.*`
- `*.config.js`

## 更新规则

1. **主项目列表**（Quick Reference → Main Projects）
   - 添加检测到的新项目
   - 更新现有项目的描述

2. **常用命令**（Common Commands）
   - 添加新项目的启动命令
   - 更新现有命令

3. **全局技能**（Global Skills Architecture）
   - 添加新发现的 skills
   - 更新 skill 说明

4. **版本历史**（Version History）
   - 添加今天日期的更新记录

5. **新增章节**
   - 为重要的新功能添加专门章节

## 示例输出

```markdown
## 检测到的变化

### 新增项目
- ✅ skills/web-search - Web Search Skill

### 新增技能
- ✅ web-search - Multi-level fallback search

### 需要更新
- Main Projects 表格：添加 web-search
- Common Commands：添加 web-search 命令
- Global Skills：添加 web-search skill
- Version History：添加 2026-03-03 条目

## 已应用更新
✓ 更新主项目列表
✓ 添加常用命令
✓ 更新全局技能部分
✓ 添加 Web Search Skill 专门章节
✓ 更新版本历史
```

## 注意事项

- 保留原有的格式和结构
- 不删除手动添加的内容
- 保持 Markdown 格式整洁
- 询问用户后再应用重大更改
