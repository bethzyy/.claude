---
name: requirement-trace
description: 需求追踪skill - 记录项目需求的变更历史。ALWAYS use this skill when user wants to "track requirements", "log feature requests", "update requirements", "record需求", "追踪需求", "记录功能变更", "更新需求文档", "save requirement", "log需求变更", "记录需求", "添加需求", "需求追踪", "requirement tracking", "feature request", "记录这个需求", "把这个需求记下来", "记住这个需求", "记录一下", "log this requirement", "add requirement", or discusses tracking project requirements and feature changes. Automatically maintains REQUIREMENTS.md in project directory with timestamp, requirement details, and change history.
---

# Requirement Trace Skill

## Overview

This skill tracks project requirements and their change history. It automatically maintains a `REQUIREMENTS.md` file in the project directory, recording all feature requests, requirement changes, and their evolution over time.

## When to Use

Use this skill whenever:
- User expresses a new requirement or feature request for a project
- User wants to modify or update existing requirements
- User wants to review requirement history
- User asks to "record this requirement" or "track requirements"
- Any functional change or feature discussion happens for a project

## How It Works

### 1. Determine Project Context

First, identify the relevant project directory:
- Check the current working directory
- Look for project markers (package.json, pyproject.toml, .git, etc.)
- If multiple projects exist, ask user to clarify

### 2. Record Requirements

Use the Python script to manage requirements:

```bash
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "<project_path>" \
  --action add \
  --requirement "<requirement text>" \
  [--type feature|bugfix|enhancement|change] \
  [--priority high|medium|low] \
  [--source "<original user prompt or context>"]
```

### 3. Review Requirements

To view or search requirements:

```bash
# List all requirements
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "<project_path>" \
  --action list

# Search requirements
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "<project_path>" \
  --action search \
  --query "<search term>"
```

## REQUIREMENTS.md Format

The skill maintains a structured markdown file:

```markdown
# Project Requirements

## Overview
[Brief project description]

## Active Requirements

### REQ-001: [Requirement Title]
- **Status**: Active | Completed | Deprecated
- **Type**: Feature | Bugfix | Enhancement | Change
- **Priority**: High | Medium | Low
- **Created**: YYYY-MM-DD HH:MM
- **Source**: [Original user prompt or context]
- **Description**: [Detailed requirement description]

#### Change History
- YYYY-MM-DD HH:MM: [Change description]
- YYYY-MM-DD HH:MM: Initial requirement

---

## Completed Requirements

### REQ-000: [Completed Requirement]
- **Completed**: YYYY-MM-DD
- [Same structure as above]
```

## Workflow

1. **When user mentions a new requirement:**
   - Parse the requirement from conversation
   - Determine the project context
   - Add the requirement to REQUIREMENTS.md
   - Confirm with user

2. **When user modifies a requirement:**
   - Identify the existing requirement
   - Add a change history entry
   - Update status if needed

3. **When user asks about requirements:**
   - Read REQUIREMENTS.md
   - Present relevant requirements
   - Offer to filter by status/type/priority

## Example Usage

**User says:** "这个项目需要一个深色模式的功能"

**Action:**
```bash
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "C:/D/CAIE_tool/MyAIProduct/multicc" \
  --action add \
  --requirement "添加深色模式支持" \
  --type feature \
  --priority medium \
  --source "用户请求：这个项目需要一个深色模式的功能"
```

**User says:** "把需求REQ-001标记为完成"

**Action:**
```bash
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "C:/D/CAIE_tool/MyAIProduct/multicc" \
  --action complete \
  --id REQ-001
```

## Notes

- Requirements are numbered sequentially (REQ-001, REQ-002, etc.)
- Each requirement includes full change history
- The file is human-readable and can be manually edited
- Source field preserves original user context for future reference
