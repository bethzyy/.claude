# Anti-Patterns for Requirement Trace

This document records common pitfalls and mistakes to avoid when using the requirement-trace skill.

---

## Anti-Pattern 1: Vague Requirement Descriptions

**Problem**: Requirements are too vague to be actionable.

**❌ Bad Example**:
```
Title: "添加功能"
Description: "需要添加功能"
```

**✅ Good Example**:
```
Title: "添加用户登录功能，支持邮箱和手机号"
Description: "实现用户登录功能，支持邮箱登录和手机号登录两种方式"
```

**Why it matters**: Vague requirements lead to confusion and rework.

---

## Anti-Pattern 2: Missing Context in Source

**Problem**: Source field doesn't capture the original user intent.

**❌ Bad Example**:
```
Source: "Dark mode"
```

**✅ Good Example**:
```
Source: "用户请求：这个项目需要一个深色模式的功能，因为晚上用太亮了"
```

**Why it matters**: Original context helps understand the "why" behind requirements.

---

## Anti-Pattern 3: No Acceptance Criteria

**Problem**: Requirements without clear "Done" definition.

**❌ Bad Example**:
```
Acceptance Criteria: _No acceptance criteria defined._
```

**✅ Good Example**:
```
Acceptance Criteria:
- [ ] User can switch between dark/light mode
- [ ] System remembers user preference
- [ ] Toggle button is visible in settings
```

**Why it matters**: Without acceptance criteria, it's unclear when a requirement is complete.

---

## Anti-Pattern 4: Ignoring Dependencies

**Problem**: Not recording dependencies leads to blocked work.

**❌ Bad Example**:
```
REQ-001 and REQ-002 both active, but REQ-002 cannot start until REQ-001 is done
(no dependency recorded)
```

**✅ Good Example**:
```
REQ-001.Blocks = REQ-002
REQ-002.BlockedBy = REQ-001
REQ-002.Blocked = true
```

**Why it matters**: Dependencies help identify bottlenecks and plan work correctly.

---

## Anti-Pattern 5: Outdated Status

**Problem**: Requirements marked as "Active" when work is complete or blocked.

**❌ Bad Example**:
```
REQ-001: Status = Active (but actually completed 2 weeks ago)
```

**✅ Good Example**:
```
REQ-001: Status = Completed (marked with completion date and note)
```

**Why it matters**: Accurate status enables reliable progress tracking.

---

## Anti-Pattern 6: Missing Change History

**Problem**: Updates without recording what changed.

**❌ Bad Example**:
```
Change History:
- 2026-03-01 10:00: Initial requirement
(Status changed from Medium to High, but no history entry)
```

**✅ Good Example**:
```
Change History:
- 2026-03-11 14:00: Priority changed from Medium to High due to user feedback
- 2026-03-01 10:00: Initial requirement
```

**Why it matters**: Change history provides audit trail and context.

---

## Anti-Pattern 7: Breaking Hierarchy

**Problem**: Creating child requirements without proper parent linkage.

**❌ Bad Example**:
```
REQ-001: User Authentication System
REQ-002: User Login
REQ-003: Password Reset
(No parent-child relationship recorded)
```

**✅ Good Example**:
```
REQ-001: User Authentication System (Epic)
REQ-002: User Login (--parent REQ-001)
REQ-003: Password Reset (--parent REQ-001)
```

**Why it matters**: Hierarchy helps organize and track complex features.

---

## Anti-Pattern 8: Duplicate Requirements

**Problem**: Same requirement recorded multiple times.

**❌ Bad Example**:
```
REQ-001: Add dark mode
REQ-005: Dark mode support
REQ-008: Implement dark theme
```

**✅ Good Example**:
```
REQ-001: Add dark mode support
(Search before adding to avoid duplicates)
```

**Why it matters**: Duplicates cause confusion and wasted effort.

---

## Anti-Pattern 9: No Priority Assignment

**Problem**: All requirements have default priority (Medium).

**❌ Bad Example**:
```
All requirements: Priority = Medium
```

**✅ Good Example**:
```
REQ-001: Priority = High (blocking other work)
REQ-002: Priority = Medium (normal feature)
REQ-003: Priority = Low (nice to have)
```

**Why it matters**: Priority helps with planning and resource allocation.

---

## Anti-Pattern 10: Not Using Labels

**Problem**: No categorization of requirements.

**❌ Bad Example**:
```
REQ-001: Labels = _None_
REQ-002: Labels = _None_
REQ-003: Labels = _None_
```

**✅ Good Example**:
```
REQ-001: Labels = `frontend`, `ui`
REQ-002: Labels = `backend`, `api`
REQ-003: Labels = `security`, `auth`
```

**Why it matters**: Labels enable filtering and grouping of requirements.

---

## Anti-Pattern 11: Not Recording Effort

**Problem**: No estimation or tracking of work required.

**❌ Bad Example**:
```
Effort: _Not estimated_
(No idea how long requirements will take)
```

**✅ Good Example**:
```
Effort:
- Estimate: 8h
- Actual: 10h (updated after completion)
```

**Why it matters**: Effort tracking enables better planning and velocity calculation.

---

## Anti-Pattern 12: Orphaned Blocked Requirements

**Problem**: Blocked requirements left without resolution plan.

**❌ Bad Example**:
```
REQ-002: Blocked = true, BlockedBy = REQ-001
(REQ-001 completed but REQ-002 still marked as blocked)
```

**✅ Good Example**:
```
When REQ-001 is completed:
- Automatically check if it was blocking anything
- Unblock REQ-002
- Notify user that REQ-002 can now proceed
```

**Why it matters**: Orphaned blocked requirements hide available work.

---

## Summary

| Anti-Pattern | Impact | Solution |
|-------------|--------|----------|
| Vague descriptions | Confusion | Be specific and detailed |
| Missing context | Lost intent | Capture original user expression |
| No acceptance criteria | Unclear completion | Define testable criteria |
| Ignoring dependencies | Bottlenecks | Use link action |
| Outdated status | Wrong progress | Update status promptly |
| Missing change history | No audit trail | Record all changes |
| Breaking hierarchy | Disorganization | Use parent linkage |
| Duplicate requirements | Wasted effort | Search before adding |
| No priority | Poor planning | Assign appropriate priority |
| Not using labels | No categorization | Add relevant labels |
| Not recording effort | No velocity | Estimate and track |
| Orphaned blocked | Hidden work | Review blocked regularly |
