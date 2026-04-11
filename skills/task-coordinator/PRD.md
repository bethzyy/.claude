# Task Coordinator Skill - PRD 文档

## 文档信息

| 属性 | 值 |
|------|-----|
| **名称** | task-coordinator |
| **版本** | v2.0.0 |
| **状态** | ✅ 已实现 |
| **入口文件** | main.py |
| **技术栈** | Python + Claude API |
| **最后更新** | 2026-03-24 |

---

## 1. 产品概述

### 1.1 产品定位

Task Coordinator 是任务协调器，管理执行-审查-改进的自动循环工作流，实现从自然语言到完成结果的自动化流程。

### 1.2 核心价值

- **自动化工作流**: 执行 → 审查 → 改进的自动循环
- **可配置迭代**: 支持自定义最大迭代次数
- **质量门禁**: 自定义最低分数和必需检查项
- **性能指标**: 详细的时间和 Token 使用追踪

### 1.3 触发模式

```
"automate task", "coordinate workflow", "execute and review",
"auto-complete", "自动完成", "执行并审查", "协调任务",
"把任务自动完成", "把需求变成结果", "把想法转成实现"
```

---

## 2. 功能需求

### F1: 工作流程

```
1. Execute: task-executor 生成初始输出
2. Review: quality-reviewer 检查质量和安全
3. Improve: 如果质量门禁未通过，回到步骤 1
4. Complete: 返回最终结果和详细指标
```

### F2: 可配置迭代

```json
{
  "type": "code_generation",
  "prompt": "Write a secure password hash function",
  "max_iterations": 5
}
```

### F3: 自定义质量门禁

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

### F4: 增强工作流报告

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

---

## 3. 技术架构

### 3.1 模块结构

```
.claude/skills/task-coordinator/
├── main.py                    # CLI 入口
├── scripts/
│   └── coordinator.py        # 协调逻辑
└── requirements.txt
```

### 3.2 Agent 协作

```
Task Coordinator
    ├→ Task Executor (生成/改进)
    └→ Quality Reviewer (审查/验证)
```

---

## 4. 使用示例

### 4.1 基础请求（v1.0.0 兼容）

```json
{
  "type": "code_generation",
  "prompt": "Write a fibonacci function"
}
```

### 4.2 增强请求（v2.0.0）

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

---

## 5. 支持的任务类型

| 类型 | 描述 |
|------|------|
| `code_generation` | 从自然语言生成代码 |
| `content_creation` | 创建文章、文档等 |
| `data_analysis` | 分析数据并生成洞察 |
| `file_conversion` | 文件格式转换 |
| `generic` | 其他任务类型 |

---

## 6. 输出格式

### 成功响应

```json
{
  "success": true,
  "final_output": "Generated code/content here",
  "quality_metrics": {...},
  "performance_metrics": {...},
  "recommendations": [...]
}
```

### 失败响应

```json
{
  "success": false,
  "error": "Failed to meet quality gates after 3 iterations",
  "best_attempt": "Last generated output",
  "final_score": 65,
  "required_score": 85
}
```

---

## 7. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0.0 | 2026-03-07 | 可配置迭代次数、增强工作流报告、自定义质量门禁、性能指标追踪、向后兼容 v1.0.0 |
| v1.0.0 | - | 初始版本 - 固定 3 次迭代的基础工作流 |

---

## 8. 相关文件

- **SKILL.md**: `.claude/skills/task-coordinator/SKILL.md`
- **主入口**: `.claude/skills/task-coordinator/main.py`
