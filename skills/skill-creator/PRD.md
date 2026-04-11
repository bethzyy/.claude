# Skill Creator Skill - PRD 文档

## 文档信息

| 属性 | 值 |
|------|-----|
| **名称** | skill-creator |
| **版本** | - |
| **状态** | ✅ 已实现 |
| **入口文件** | - |
| **技术栈** | Python + Claude API |
| **最后更新** | 2026-03-24 |

---

## 1. 产品概述

### 1.1 产品定位

Skill Creator 是一个技能创建工具，帮助用户创建新技能、修改和改进现有技能，以及测量技能性能。

### 1.2 核心价值

- **完整工作流**: 从草稿到测试到优化
- **迭代改进**: 基于评估结果持续改进
- **描述优化**: 自动优化技能描述以提高触发准确率
- **盲测对比**: A/B 测试比较两个版本

### 1.3 触发模式

```
"create a skill", "make a skill", "new skill",
"创建技能", "新建技能", "优化技能"
```

---

## 2. 功能需求

### F1: 技能创建流程

```
1. 确定技能目标
2. 编写技能草稿（SKILL.md）
3. 创建测试用例（evals.json）
4. 运行测试（带技能 vs 不带）
5. 评估结果（定性 + 定量）
6. 根据反馈改进
7. 重复直到满意
```

### F2: SKILL.md 结构

```yaml
---
name: skill-name
description: 触发条件和使用场景
compatibility: 必需工具（可选）
---

# 技能说明
...
```

### F3: 测试用例格式

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "用户任务提示",
      "expected_output": "预期结果描述",
      "files": []
    }
  ]
}
```

### F4: 描述优化

- **生成触发评估**: 20 个查询（应触发 + 不应触发）
- **用户审核**: HTML 界面编辑评估集
- **优化循环**: 自动迭代优化描述
- **最佳选择**: 基于测试分数选择最佳描述

---

## 3. 技术架构

### 3.1 模块结构

```
skill-creator/
├── SKILL.md                   # 技能说明
├── agents/                    # 子代理指令
│   ├── grader.md             # 评分代理
│   ├── comparator.md         # 对比代理
│   └── analyzer.md           # 分析代理
├── scripts/                   # 工具脚本
│   ├── aggregate_benchmark.py
│   ├── run_loop.py
│   └── package_skill.py
├── eval-viewer/              # 评估查看器
│   └── generate_review.py
└── assets/
    └── eval_review.html      # 评估模板
```

### 3.2 渐进式加载

| 层级 | 内容 | 大小限制 |
|------|------|----------|
| 元数据 | name + description | ~100 词 |
| SKILL.md 主体 | 详细指令 | <500 行 |
| 捆绑资源 | scripts/references | 无限制 |

---

## 4. 使用示例

### 4.1 创建新技能

```
用户: 我想创建一个技能来处理 PDF 文件

AI: 好的，让我们确定一下：
1. 这个技能应该做什么？
2. 什么时候应该触发？
3. 预期的输出格式是什么？
...
```

### 4.2 改进现有技能

```
用户: 我想改进我的 PDF 技能

AI: 让我先看看现有的技能，然后运行测试...
```

### 4.3 优化描述

```
用户: 优化技能描述

AI: 我将生成 20 个触发评估，请审核...
```

---

## 5. 评估工作流

### 5.1 并行测试

```
对每个测试用例：
├── with_skill: 使用技能运行
└── without_skill: 不使用技能运行（基线）
```

### 5.2 评分

- 断言验证
- 自动评分
- 生成 grading.json

### 5.3 查看器

```bash
python eval-viewer/generate_review.py <workspace> --skill-name <name>
```

---

## 6. 描述优化流程

```bash
# 生成评估集
# 用户审核后运行
python -m scripts.run_loop \
  --eval-set trigger_eval.json \
  --skill-path <path> \
  --model <model-id> \
  --max-iterations 5
```

---

## 7. 关键原则

### 7.1 编写风格

- 使用祈使句
- 解释"为什么"
- 避免过度 MUST 规则
- 保持通用性

### 7.2 惊喜原则

- 不包含恶意代码
- 意图不应让用户惊讶
- 不创建误导性技能

---

## 8. 相关文件

- **SKILL.md**: `.claude/skills/skill-creator/SKILL.md`
- **评分代理**: `.claude/skills/skill-creator/agents/grader.md`
- **分析代理**: `.claude/skills/skill-creator/agents/analyzer.md`
