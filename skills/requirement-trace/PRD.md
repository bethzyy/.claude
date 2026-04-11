# Requirement Trace Skill - PRD 文档

## 文档信息

| 属性 | 值 |
|------|-----|
| **名称** | requirement-trace |
| **版本** | v2.0.0 |
| **状态** | ✅ 已实现 |
| **入口文件** | main.py |
| **技术栈** | Python |
| **最后更新** | 2026-03-24 |

---

## 1. 产品概述

### 1.1 产品定位

Requirement Trace 是一个需求追踪技能，记录项目需求的变更历史，自动维护 REQUIREMENTS.md 文件。

### 1.2 核心价值

- **变更追踪**: 完整记录需求变更历史
- **依赖管理**: 支持 blocks/blocked-by 关系
- **验收标准**: 定义清晰的"完成"条件
- **统计分析**: 自动生成统计和阻塞报告

### 1.3 触发模式

```
"track requirements", "log feature requests", "update requirements",
"record需求", "追踪需求", "记录功能变更", "更新需求文档",
"记录一下", "备忘一下", "TODO", "改需求", "需求管理", "PRD"
```

---

## 2. 功能需求

### F1: 需求管理

| 操作 | 描述 | 必需参数 |
|------|------|----------|
| `add` | 添加新需求 | `--requirement` |
| `list` | 列出需求 | - |
| `search` | 搜索需求 | `--query` |
| `get` | 获取特定需求 | `--id` |
| `update` | 更新需求 | `--id` |
| `complete` | 标记完成 | `--id` |

### F2: 依赖管理

| 操作 | 描述 | 参数 |
|------|------|------|
| `link` | 链接依赖 | `--id`, `--link-to`, `--link-type` |
| `block` | 标记阻塞 | `--id` |
| `unblock` | 解除阻塞 | `--id` |

### F3: 报告功能

| 操作 | 描述 |
|------|------|
| `stats` | 获取统计信息 |
| `blocked-report` | 获取阻塞需求报告 |

### F4: 需求属性

| 属性 | 类型 | 描述 |
|------|------|------|
| `--type` | feature/bugfix/enhancement/change | 需求类型 |
| `--priority` | high/medium/low | 优先级 |
| `--owner` | string | 负责人 |
| `--milestone` | string | 里程碑 |
| `--labels` | string | 标签（逗号分隔） |
| `--parent` | string | 父需求 ID |
| `--blocks` | string | 阻塞的需求 |
| `--blocked-by` | string | 被阻塞的需求 |
| `--acceptance-criteria` | string | 验收标准 |
| `--estimate` | int | 预估工时 |

---

## 3. 技术架构

### 3.1 模块结构

```
.claude/skills/requirement-trace/
├── main.py                    # CLI 入口
├── scripts/
│   └── requirement_manager.py # 需求管理器
└── knowledge/                 # 知识库
    ├── patterns.md           # 成功模式
    ├── anti-patterns.md      # 常见陷阱
    └── tips.md               # 使用技巧
```

### 3.2 REQUIREMENTS.md 格式

```markdown
# Project Requirements

## Statistics
- **Total**: 5
- **Active**: 3
- **Completed**: 2
- **Blocked**: 1

## Active Requirements

### REQ-001: [Requirement Title]

- **Status**: Active
- **Type**: Feature
- **Priority**: High
- **Owner**: @username
- **Milestone**: v1.0.0
- **Labels**: `frontend`, `ui`
- **Parent**: EPIC-001
- **Blocked**: false

#### Dependencies
- **Blocks**: REQ-002, REQ-003
- **Blocked By**: None

#### Acceptance Criteria
- [ ] 用户可切换深色/浅色模式
- [ ] 系统记住用户偏好

#### Change History
- YYYY-MM-DD HH:MM: 初始需求
```

---

## 4. 使用示例

### 4.1 添加需求

```bash
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "C:/D/CAIE_tool/MyAIProduct/multicc" \
  --action add \
  --requirement "添加深色模式支持" \
  --type feature \
  --priority medium \
  --labels "ui,theme" \
  --acceptance-criteria "用户可切换深色/浅色模式;系统记住用户偏好" \
  --estimate 8
```

### 4.2 链接依赖

```bash
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "C:/D/CAIE_tool/MyAIProduct/multicc" \
  --action link \
  --id REQ-001 \
  --link-to REQ-002 \
  --link-type blocks
```

### 4.3 获取统计

```bash
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "C:/D/CAIE_tool/MyAIProduct/multicc" \
  --action stats
```

### 4.4 完成需求

```bash
python .claude/skills/requirement-trace/scripts/requirement_manager.py \
  --project-dir "C:/D/CAIE_tool/MyAIProduct/multicc" \
  --action complete \
  --id REQ-001
```

---

## 5. 需求编号规则

- 顺序编号: REQ-001, REQ-002, ...
- 每个需求包含完整变更历史
- 依赖关系双向同步（blocks/blocked-by 自动更新）

---

## 6. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0.0 | 2026-03-11 | 重大增强：依赖管理、验收标准、分层结构、标签、里程碑、统计报告 |
| v1.0.0 | - | 初始版本：基础需求追踪 |

---

## 7. 相关文件

- **SKILL.md**: `.claude/skills/requirement-trace/SKILL.md`
- **主入口**: `.claude/skills/requirement-trace/main.py`
- **管理器**: `.claude/skills/requirement-trace/scripts/requirement_manager.py`
