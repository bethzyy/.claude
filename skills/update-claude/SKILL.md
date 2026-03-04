---
name: update-claude
description: Automatically update CLAUDE.md with recent project changes. Scans for new files, modified structure, and updates documentation. Supports multi-document selection - can update main project CLAUDE.md or any subproject CLAUDE.md. Use when user says "update CLAUDE.md", "sync documentation", "refresh project docs", "update project readme", "更新进度", "更新cc", "update cc", "update cc docs", "cc update", or discusses updating Claude Code project documentation.
version: 2.0.0
author: Claude Code
tags: [documentation, maintenance, sync]
---

# Update CLAUDE.md Skill v2.0

自动扫描项目变化并更新 CLAUDE.md 文档。支持选择更新主项目或任意子项目的文档。

## 触发条件

当用户说以下任一内容时触发：
- "更新cc" ⭐ 快捷触发
- "update cc"
- "cc update"
- "更新 CLAUDE.md"
- "sync documentation"
- "刷新项目文档"
- "update project docs"
- "更新项目说明"
- "更新进度"
- "update cc docs"

## 工作流程（v2.0 新增）

### 步骤1：发现所有 CLAUDE.md 文件
扫描项目，找到所有 CLAUDE.md 文件：
- 主项目：`MyAIProduct/CLAUDE.md`
- 子项目：`food/CLAUDE.md`, `jobMatchTool/CLAUDE.md`, `post/CLAUDE.md` 等

### 步骤2：交互式选择
显示所有找到的 CLAUDE.md 文件，让用户选择：

```
检测到以下 CLAUDE.md 文件：
  [1] 主项目 - MyAIProduct/CLAUDE.md
  [2] food - food/CLAUDE.md
  [3] jobMatchTool - jobMatchTool/CLAUDE.md
  [4] post - post/CLAUDE.md
  [5] xiaohongshu-pub - skills/xiaohongshu-pub/ (无CLAUDE.md)
  ...
  [0] all - 更新所有文档

请选择要更新的文档（输入编号，默认:1）:
```

### 步骤3：扫描项目结构
针对选择的文档，扫描对应目录：
- 检测新增的目录/项目
- 检测新的主要文件
- 分析项目架构变化

### 步骤4：对比选定的 CLAUDE.md
- 找出文档中缺失的内容
- 识别过时的信息
- 标记需要更新的部分

### 步骤5：生成更新建议
- 列出需要添加的项目
- 列出需要删除的内容
- 列出需要修改的部分

### 步骤6：应用更新
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

## 示例输出（v2.0）

### 交互选择阶段
```
检测到以下 CLAUDE.md 文件：
  [1] 主项目 - MyAIProduct/CLAUDE.md
  [2] food - food/CLAUDE.md
  [3] post - post/CLAUDE.md
  [4] jobMatchTool - jobMatchTool/CLAUDE.md
  [0] all - 更新所有文档

请选择要更新的文档（输入编号，默认:1）: 3
```

### 扫描和更新阶段
```markdown
## 正在更新：jobMatchTool/CLAUDE.md

### 检测到的变化

### 新增功能
- ✅ 图片重用优化
- ✅ 自动内容检查

### 需要更新
- 版本历史：添加 2026-03-04 条目
- 功能特性：更新说明

## 已应用更新
✓ 更新版本历史
✓ 添加新功能说明
```

### 批量更新（选择 all）
```markdown
## 批量更新模式

正在更新以下文档：
- [1/4] MyAIProduct/CLAUDE.md... ✓
- [2/4] food/CLAUDE.md... ✓
- [3/4] post/CLAUDE.md... ✓
- [4/4] jobMatchTool/CLAUDE.md... ✓

所有文档已更新完成！
```

## 版本历史

- **v2.0.0** (2026-03-04): 多文档支持
  - 支持选择更新主项目或子项目文档
  - 交互式文档选择界面
  - 支持批量更新（all 选项）
  - 智能检测子项目变化

- **v1.2.0** (2026-03-04): 快捷触发词
  - 添加"更新cc"、"update cc"快捷触发

- **v1.1.0**: 初始版本
  - 自动扫描主项目变化
  - 更新主 CLAUDE.md

## 注意事项

- 保留原有的格式和结构
- 不删除手动添加的内容
- 保持 Markdown 格式整洁
- 询问用户后再应用重大更改
- 更新前会显示预览
