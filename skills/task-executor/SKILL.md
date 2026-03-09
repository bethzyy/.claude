---
name: task-executor
description: 执行Agent - 负责代码生成、内容创作、数据分析等任务执行，支持自我进化能力学习。ALWAYS use this skill when user wants to "execute task", "generate code", "create content", "write code", "produce content", "make something", "build output", "执行任务", "生成代码", "创建内容", "完成任务", "写代码", "产出内容", "制作输出", "构建代码", "把需求写成代码", "把想法变成实现", "把任务转成代码", "将需求转换为代码", "把...写成", "把...转成", "把...变成", "将...转换为", or discusses executing tasks, generating code, creating content, or transforming requirements into implementations. Supports code generation (multiple languages), content creation (articles, documents), data analysis, file conversion, AND self-improvement learning capabilities. MUST trigger for ANY task execution request including conversion patterns like "把 [requirement] 写成/转成/变成 [output]".
version: 2.0.0
entry_point: main.py
author: Claude Code
tags: [executor, agent, task-execution, auto-learn]
---

## Version History
- **v2.0.0** (2026-03-07): 描述格式标准化 - 添加转换模式、pushy语言、完整触发词
- **v1.0.0**: 初始版本 - 基础任务执行功能
