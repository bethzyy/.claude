# Task Executor Skill - PRD 文档

## 文档信息

| 属性 | 值 |
|------|-----|
| **名称** | task-executor |
| **版本** | v2.0.0 |
| **状态** | ✅ 已实现 |
| **入口文件** | main.py |
| **技术栈** | Python + Claude API |
| **最后更新** | 2026-03-24 |

---

## 1. 产品概述

### 1.1 产品定位

Task Executor 是执行 Agent，负责代码生成、内容创作、数据分析等任务的执行，支持自我进化能力学习。

### 1.2 核心价值

- **多语言代码生成**: Python, JavaScript, TypeScript, Go, Java 等
- **内容创作**: 文章、文档、报告
- **数据分析**: 数据处理和洞察生成
- **文件转换**: 格式转换
- **自我学习**: 从反馈中学习改进

### 1.3 触发模式

```
"execute task", "generate code", "create content", "write code",
"执行任务", "生成代码", "创建内容", "完成任务", "写代码",
"把需求写成代码", "把想法变成实现", "把任务转成代码"
```

---

## 2. 功能需求

### F1: 支持的任务类型

| 类型 | 描述 |
|------|------|
| `code_generation` | 从自然语言生成代码 |
| `content_creation` | 创建文章、文档等 |
| `data_analysis` | 分析数据并生成洞察 |
| `file_conversion` | 文件格式转换 |
| `generic` | 其他任务类型 |

### F2: 输入格式

```json
{
  "task_id": "task_001",
  "type": "code_generation",
  "prompt": "Write a secure password hash function",
  "context": {
    "language": "python",
    "requirements": ["bcrypt", "salt"]
  }
}
```

### F3: 输出格式

```json
{
  "success": true,
  "result": {
    "type": "code",
    "language": "python",
    "content": "import bcrypt\n...",
    "files": [
      {
        "path": "password_hash.py",
        "content": "..."
      }
    ]
  },
  "metadata": {
    "tokens_used": 1500,
    "execution_time_ms": 3500
  }
}
```

---

## 3. 技术架构

### 3.1 模块结构

```
.claude/skills/task-executor/
├── main.py                    # CLI 入口
├── scripts/
│   └── executor.py           # 执行逻辑
└── requirements.txt
```

### 3.2 与 Task Coordinator 配合

```
Task Coordinator
    ↓ 调用
Task Executor (生成初始输出)
    ↓ 返回
Quality Reviewer (检查质量)
    ↓ 反馈
Task Executor (改进输出)
```

---

## 4. 使用示例

### 4.1 代码生成

```json
{
  "task_id": "code_001",
  "type": "code_generation",
  "prompt": "Create a REST API endpoint for user registration"
}
```

### 4.2 内容创作

```json
{
  "task_id": "content_001",
  "type": "content_creation",
  "prompt": "Write a technical blog post about microservices"
}
```

### 4.3 数据分析

```json
{
  "task_id": "data_001",
  "type": "data_analysis",
  "prompt": "Analyze the sales data and identify trends",
  "context": {
    "data_path": "sales.csv"
  }
}
```

---

## 5. 自我进化能力

- **学习反馈**: 从 Quality Reviewer 的反馈中学习
- **模式记忆**: 记住成功的代码模式
- **持续改进**: 每次执行后优化输出质量

---

## 6. 依赖项

```
anthropic
```

---

## 7. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0.0 | 2026-03-07 | 描述格式标准化 - 添加转换模式、多语言触发词 |
| v1.0.0 | - | 初始版本 - 基础任务执行功能 |

---

## 8. 相关文件

- **SKILL.md**: `.claude/skills/task-executor/SKILL.md`
- **主入口**: `.claude/skills/task-executor/main.py`
