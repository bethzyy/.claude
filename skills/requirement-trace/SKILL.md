---
name: requirement-trace
version: 2.0.0
description: 需求追踪skill - 记录项目需求的变更历史。ALWAYS use this skill when user wants to "track requirements", "log feature requests", "update requirements", "record需求", "追踪需求", "记录功能变更", "更新需求文档", "save requirement", "log需求变更", "记录需求", "添加需求", "需求追踪", "requirement tracking", "feature request", "记录这个需求", "把这个需求记下来", "记住这个需求", "记录一下", "log this requirement", "add requirement", "记一下", "备忘一下", "mark this", "note down", "这个功能要做", "接下来要实现", "TODO", "改需求", "需求变了", "功能调整", "把需求写成文档", "把功能列表整理", "需求管理", "backlog", "需求清单", "feature list", "product requirements", "PRD", "requirement document", "需求文档", "功能需求", "产品需求", "需求变更", "change request", "requirement change", or discusses tracking project requirements, feature changes, backlog management, or product planning. Automatically maintains REQUIREMENTS.md with dependencies, acceptance criteria, and change history.
---

# Requirement Trace Skill v2.0.0

## Overview

This skill tracks project requirements and their change history. It automatically maintains a `REQUIREMENTS.md` file in the project directory, recording all feature requests, requirement changes, dependencies, acceptance criteria, and their evolution over time.

## What's New in v2.0.0

- **Dependencies Management**: Link requirements with "blocks" and "blocked-by" relationships
- **Acceptance Criteria**: Define clear "Done" criteria for each requirement
- **Hierarchical Structure**: Parent-child relationships for Epic/Story/Task breakdown
- **Labels & Milestones**: Better organization and filtering
- **Statistics & Reports**: Automatic statistics and blocked requirements reports
- **Effort Tracking**: Estimate and actual hours for each requirement

## When to Use

Use this skill whenever:
- User expresses a new requirement or feature request for a project
- User wants to modify or update existing requirements
- User wants to review requirement history or status
- User asks to "record this requirement", "track requirements", or "add to backlog"
- User mentions "TODO", "feature to implement", or "this function needs to be done"
- User discusses requirement changes or "change requests"
- User wants to organize feature lists or product requirements
- Any functional change or feature discussion happens for a project

## Trigger Patterns

### Core Triggers
- "track requirements", "log feature requests", "update requirements"
- "record需求", "追踪需求", "记录功能变更", "更新需求文档"
- "requirement tracking", "feature request", "requirement management"

### Conversation Triggers
- "记录一下", "备忘一下", "记下来", "记住这个"
- "mark this", "note down", "log this"
- "这个功能要做", "接下来要实现", "TODO"
- "把需求写成文档", "把功能列表整理"

### Change Management Triggers
- "改需求", "需求变了", "功能调整"
- "change request", "requirement change"

### Document Triggers
- "需求管理", "backlog", "需求清单"
- "feature list", "product requirements", "PRD"
- "需求文档", "功能需求", "产品需求"

## How It Works

### 1. Determine Project Context

First, identify the relevant project directory:
- Check the current working directory
- Look for project markers (package.json, pyproject.toml, .git, etc.)
- If multiple projects exist, ask user to clarify

### 2. Record Requirements

```bash
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "<project_path>" \
  --action add \
  --requirement "<requirement text>" \
  [--type feature|bugfix|enhancement|change] \
  [--priority high|medium|low] \
  [--source "<original user prompt>"] \
  [--owner "@username"] \
  [--milestone "v1.0.0"] \
  [--labels "frontend,ui"] \
  [--parent "EPIC-001"] \
  [--blocks "REQ-002,REQ-003"] \
  [--blocked-by "REQ-001"] \
  [--acceptance-criteria "User can login;System validates email"] \
  [--estimate 8]
```

### 3. Manage Dependencies

```bash
# Link requirements (REQ-001 blocks REQ-002)
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "<project_path>" \
  --action link \
  --id REQ-001 \
  --link-to REQ-002 \
  --link-type blocks

# Block a requirement
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "<project_path>" \
  --action block \
  --id REQ-002 \
  --note "Waiting for REQ-001"

# Unblock a requirement
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "<project_path>" \
  --action unblock \
  --id REQ-002
```

### 4. Review Requirements

```bash
# List all requirements
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "<project_path>" \
  --action list

# List blocked requirements only
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "<project_path>" \
  --action list \
  --blocked

# Search requirements
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "<project_path>" \
  --action search \
  --query "<search term>"

# Get statistics
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "<project_path>" \
  --action stats

# Get blocked requirements report
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "<project_path>" \
  --action blocked-report
```

## REQUIREMENTS.md Format

```markdown
# Project Requirements

## Overview
[Brief project description]

## Statistics
- **Total**: 5
- **Active**: 3
- **Completed**: 2
- **Blocked**: 1

## Active Requirements

### REQ-001: [Requirement Title]

- **Status**: Active
- **Type**: Feature | Bugfix | Enhancement | Change
- **Priority**: High | Medium | Low
- **Created**: YYYY-MM-DD HH:MM
- **Updated**: YYYY-MM-DD HH:MM
- **Owner**: @username
- **Milestone**: v1.0.0
- **Labels**: `frontend`, `ui/ux`
- **Parent**: EPIC-001
- **Source**: [Original user prompt or context]
- **Blocked**: false
- **Description**: [Detailed requirement description]
- **Effort**:
  - **Estimate**: 8h
  - **Actual**: 10h

#### Dependencies
- **Blocks**: REQ-002, REQ-003
- **Blocked By**: None

#### Acceptance Criteria
- [ ] User can switch between dark/light mode
- [ ] System remembers user preference
- [ ] Toggle button is visible in settings

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
   - Ask for priority/type if not clear
   - Add the requirement to REQUIREMENTS.md
   - Confirm with user

2. **When user modifies a requirement:**
   - Identify the existing requirement
   - Add a change history entry
   - Update status/dependencies if needed

3. **When user asks about requirements:**
   - Read REQUIREMENTS.md
   - Present relevant requirements
   - Offer to filter by status/type/priority/blocked

4. **When user mentions dependencies:**
   - Use link action to establish relationships
   - Update blocked status automatically

## Example Usage

### Adding a Requirement

**User says:** "这个项目需要一个深色模式的功能"

**Action:**
```bash
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "C:/D/CAIE_tool/MyAIProduct/multicc" \
  --action add \
  --requirement "添加深色模式支持" \
  --type feature \
  --priority medium \
  --source "用户请求：这个项目需要一个深色模式的功能" \
  --labels "ui,theme" \
  --acceptance-criteria "用户可切换深色/浅色模式;系统记住用户偏好" \
  --estimate 8
```

### Linking Dependencies

**User says:** "REQ-001 必须先完成，REQ-002 才能开始"

**Action:**
```bash
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "C:/D/CAIE_tool/MyAIProduct/multicc" \
  --action link \
  --id REQ-001 \
  --link-to REQ-002 \
  --link-type blocks
```

### Getting Statistics

**User says:** "需求统计怎么样？"

**Action:**
```bash
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "C:/D/CAIE_tool/MyAIProduct/multicc" \
  --action stats
```

### Completing a Requirement

**User says:** "把需求REQ-001标记为完成"

**Action:**
```bash
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "C:/D/CAIE_tool/MyAIProduct/multicc" \
  --action complete \
  --id REQ-001
```

## Available Actions

| Action | Description | Required Args |
|--------|-------------|---------------|
| `add` | Add new requirement | `--requirement` |
| `list` | List requirements | - |
| `search` | Search by keyword | `--query` |
| `get` | Get specific requirement | `--id` |
| `update` | Update requirement | `--id` |
| `complete` | Mark as completed | `--id` |
| `link` | Link dependencies | `--id`, `--link-to`, `--link-type` |
| `block` | Mark as blocked | `--id` |
| `unblock` | Remove blocked status | `--id` |
| `stats` | Get statistics | - |
| `blocked-report` | Get blocked requirements report | - |

## Notes

- Requirements are numbered sequentially (REQ-001, REQ-002, etc.)
- Each requirement includes full change history
- Dependencies are bidirectional (blocks/blocked-by auto-sync)
- Statistics are automatically updated on every change
- The file is human-readable and can be manually edited
- Source field preserves original user context for future reference

## Knowledge Base

This skill includes a knowledge base for self-improvement:
- `knowledge/patterns.md` - Success patterns for requirement tracking
- `knowledge/anti-patterns.md` - Common pitfalls to avoid
- `knowledge/tips.md` - Usage tips and best practices

## Version History

- **v2.0.0** (2026-03-11): Major enhancement
  - Added dependencies management (blocks/blocked-by)
  - Added acceptance criteria support
  - Added hierarchical structure (parent)
  - Added labels, milestone, owner fields
  - Added statistics and blocked reports
  - Added effort tracking (estimate/actual)
  - Enhanced trigger patterns
  - Created knowledge base structure

- **v1.0.0** (Initial): Basic requirement tracking
