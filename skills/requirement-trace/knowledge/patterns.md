# Success Patterns for Requirement Trace

This document records successful patterns for using the requirement-trace skill.

---

## Pattern 1: Complete Requirement Recording

**When to use**: When user expresses a new requirement or feature request.

**Best Practice**:
- Always capture the requirement title (short and clear)
- Record the original user expression as `Source`
- Ask for priority if not mentioned
- Suggest appropriate labels based on context

**Example**:
```
User: "这个项目需要一个深色模式的功能"

Action:
- Title: "添加深色模式支持"
- Source: "这个项目需要一个深色模式的功能"
- Type: feature
- Priority: medium (ask if unclear)
- Labels: ui, theme
- Acceptance Criteria: "用户可切换深色/浅色模式;系统记住用户偏好"
```

---

## Pattern 2: Change Tracking

**When to use**: When user modifies or updates an existing requirement.

**Best Practice**:
- Always add a change history entry
- Record what changed and why
- Update affected fields (status, priority, etc.)

**Example**:
```
User: "REQ-001 的优先级改成高"

Action:
- Update priority to High
- Add change note: "优先级从 medium 改为 high，因为用户反馈紧急"
```

---

## Pattern 3: Dependency Management

**When to use**: When user mentions relationships between requirements.

**Best Practice**:
- Use `link` action instead of manual update
- Always specify link type (blocks/blocked-by)
- Both requirements are updated automatically

**Example**:
```
User: "REQ-001 必须先完成，REQ-002 才能开始"

Action:
- Use link action with type "blocks"
- REQ-001.Blocks = REQ-002
- REQ-002.BlockedBy = REQ-001
- REQ-002.Blocked = true
```

---

## Pattern 4: Acceptance Criteria Definition

**When to use**: When adding new requirements with clear "Done" conditions.

**Best Practice**:
- Break down into specific, testable criteria
- Use semicolon separator for multiple criteria
- Criteria should be verifiable

**Example**:
```
Good acceptance criteria:
"用户可以切换深色/浅色模式;系统记住用户偏好;切换按钮在设置中可见"

Bad acceptance criteria (too vague):
"深色模式功能完成"
```

---

## Pattern 5: Blocked Requirements Handling

**When to use**: When a requirement cannot proceed due to dependencies.

**Best Practice**:
- Always specify what's blocking it
- Use `block` action with reason
- Track in blocked-report

**Example**:
```
User: "REQ-002 暂时做不了，等 REQ-001"

Action:
- block REQ-002 with reason "Waiting for REQ-001 to complete"
- Update blocked-report will show this
```

---

## Pattern 6: Statistics Review

**When to use**: When user asks about project status or progress.

**Best Practice**:
- Use `stats` action for quick overview
- Use `blocked-report` for bottleneck identification
- Offer to filter by status/priority

**Example**:
```
User: "需求进度怎么样？"

Action:
- Run stats action
- Present: Total, Active, Completed, Blocked counts
- Highlight blocked requirements as potential issues
```

---

## Pattern 7: Hierarchical Breakdown

**When to use**: When user mentions large features that need breakdown.

**Best Practice**:
- Create parent requirement (Epic)
- Create child requirements with `--parent` flag
- Use labels to group related requirements

**Example**:
```
User: "我们需要一个用户认证系统"

Action:
1. Add REQ-001: "用户认证系统" (Epic, no parent)
2. Add REQ-002: "用户注册功能" (--parent REQ-001)
3. Add REQ-003: "用户登录功能" (--parent REQ-001)
4. Add REQ-004: "密码重置功能" (--parent REQ-001)
```

---

## Pattern 8: Effort Estimation

**When to use**: When planning sprints or releases.

**Best Practice**:
- Provide estimate at requirement creation
- Update actual hours when completed
- Use for velocity tracking

**Example**:
```
User: "这个需求估计要多久？"

Action:
- Suggest estimate based on complexity
- Record with --estimate flag
- Update --actual when completed
```

---

## Pattern 9: Context Preservation

**When to use**: Always, when recording requirements.

**Best Practice**:
- Always capture original user expression
- Include relevant context from conversation
- Source field should be verbatim when possible

**Example**:
```
Good Source: "用户请求：这个项目需要一个深色模式的功能，因为晚上用太亮了"

Bad Source: "Dark mode" (loses context)
```

---

## Pattern 10: Regular Review

**When to use**: Periodically, to keep requirements up to date.

**Best Practice**:
- Review blocked requirements weekly
- Update status of stale requirements
- Complete requirements that are done

**Example**:
```
Weekly review:
1. Run blocked-report
2. Check each blocked requirement
3. Unblock if dependency is resolved
4. Complete if work is finished
```
