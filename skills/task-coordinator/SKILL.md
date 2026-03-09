---
name: task-coordinator
description: 任务协调器 - 管理执行-审查-改进的自动循环工作流，实现从自然语言到完成结果的自动化流程。ALWAYS use this skill when user wants to "automate task", "coordinate workflow", "execute and review", "auto-complete", "coordinate tasks", "automate end-to-end", "run workflow", "manage iteration loop", "自动完成", "执行并审查", "协调任务", "自动化流程", "管理迭代循环", "把任务自动完成", "把需求变成结果", "把想法转成实现", "将任务转换为完成结果", "把...写成", "把...转成", "把...变成", "将...转换为", or discusses automating workflows, coordinating tasks, managing execution-review-improve cycles, or transforming requirements into completed results with automatic iteration. Supports configurable iteration limits, custom quality gates (min_score, required_checks), detailed performance metrics tracking, AND backward compatibility with v1.0.0 API. MUST trigger for ANY workflow automation or task coordination request including conversion patterns like "把 [task/requirement] 写成/转成/变成 [completed result]".
version: 2.0.0
entry_point: main.py
author: Claude Code
tags: [coordinator, agent, workflow, auto-task]
---

## Version History
- **v2.0.0** (2026-03-07): 升级到v2.0.0 - 可配置迭代次数、增强工作流报告、自定义质量门禁、性能指标追踪、向后兼容v1.0.0
- **v1.0.0**: 初始版本 - 固定3次迭代的基础工作流

## What's New in v2.0.0

### 1. Configurable Iteration Limits
```json
{
  "type": "code_generation",
  "prompt": "Write a secure password hash function",
  "max_iterations": 5
}
```

### 2. Custom Quality Gates
```json
{
  "type": "code_generation",
  "prompt": "Create a user login system",
  "quality_gates": {
    "min_score": 85,
    "required_checks": ["security", "style", "performance"]
  }
}
```

### 3. Enhanced Workflow Report
```json
{
  "quality_metrics": {
    "total_iterations": 2,
    "final_score": 92,
    "improvement_trajectory": [75, 92],
    "quality_gates_met": true
  },
  "performance_metrics": {
    "total_time_seconds": 45.3,
    "executor_calls": 2,
    "reviewer_calls": 2
  },
  "recommendations": [
    "Quality gates met after 2 iterations",
    "Consider reducing max_iterations to 2"
  ]
}
```

### 4. Backward Compatibility
v1.0.0 API calls continue to work without changes:
```json
{
  "type": "code_generation",
  "prompt": "Write a function"
}
```

## v2.0.0 API Format

### Basic Request (v1.0.0 compatible)
```json
{
  "type": "code_generation",
  "prompt": "Write a fibonacci function"
}
```

### Enhanced Request (v2.0.0)
```json
{
  "type": "code_generation",
  "prompt": "Write a secure password hashing function with bcrypt",
  "max_iterations": 3,
  "quality_gates": {
    "min_score": 90,
    "required_checks": ["security", "error_handling", "documentation"]
  },
  "reporting": {
    "detailed_metrics": true,
    "include_recommendations": true
  }
}
```

### Quality Gates Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_score` | int | 70 | Minimum score to pass review |
| `required_checks` | array | [] | Required review categories (security, style, performance, etc.) |

### Reporting Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `detailed_metrics` | bool | false | Include performance metrics |
| `include_recommendations` | bool | false | Include improvement recommendations |

## Supported Task Types

| Type | Description |
|------|-------------|
| `code_generation` | Generate code from natural language |
| `content_creation` | Create articles, documents, etc. |
| `data_analysis` | Analyze data and generate insights |
| `file_conversion` | Convert files between formats |
| `generic` | Any other task type |

## Workflow Process

1. **Execute**: task-executor generates initial output
2. **Review**: quality-reviewer checks quality and security
3. **Improve**: If quality gates not met, loop back to step 1
4. **Complete**: Return final result with detailed metrics

## Output Format

### Success Response
```json
{
  "success": true,
  "final_output": "Generated code/content here",
  "quality_metrics": {...},
  "performance_metrics": {...},
  "recommendations": [...]
}
```

### Failure Response
```json
{
  "success": false,
  "error": "Failed to meet quality gates after 3 iterations",
  "best_attempt": "Last generated output",
  "final_score": 65,
  "required_score": 85
}
```
