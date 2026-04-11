---
name: bug-retro
description: "[已升级] Bug复盘已升级为全自动化专家复盘+自动修复。ALWAYS use this skill when the user says: 复盘, 复盘这个bug, 复盘这次修复, 记录经验, 提炼经验, 经验沉淀, 总结经验, 经验总结, 积累经验, bug复盘, bug总结, 记录这个bug, 记录修复经验, lessons learned, post-mortem, record experience, bug retrospective, review this fix, distill experience, or when the user discusses extracting lessons, insights, or reusable patterns from a bug fix or debugging session. Even if the user just says '复盘一下' without context, trigger this skill."
version: 2.0.0
tags: [memory, experience, learning, retrospective, debugging, autofix]
---

# Bug Retrospective → Expert Retro AutoFix

> **已升级**: 此 skill 已升级为全自动化版本 `expert-retro-autofix`。

## 重定向

此 skill 已被 `expert-retro-autofix` 替代。新版本支持：
- 自动扫描项目发现问题（5层扫描）
- 三人专家圆桌讨论（ZhipuAI GLM）
- 自动生成改进方案并逐步执行修复
- Git checkpoint 保护 + 测试回归验证
- 经验沉淀闭环

**请使用 `expert-retro-autofix` skill 代替。**

---

# Legacy Mode（旧模式保留）

如果只需要简单提取单个 bug 的经验（不触发全自动流程），继续使用以下步骤：

## Why this matters

Every debugging session teaches something. Without explicit extraction, that knowledge evaporates when the session ends. By capturing the **pattern** and **insight** (not the code), you build a searchable experience base that makes you progressively better at debugging.

## Process

### Step 1: Identify the bug from context

Scan the current conversation for the bug that was just fixed. Look for:
- Error messages, stack traces, or abnormal behavior the user reported
- The diagnostic steps taken (logs read, commands run, files inspected)
- The root cause identified
- The fix applied

If no clear bug fix exists in the current conversation, ask the user to briefly describe the problem and how it was resolved before proceeding.

### Step 2: Extract four dimensions

Distill the debugging session into these four dimensions. Think of this as writing advice to your future self:

**1. Problem Pattern (问题模式)**
What category of problem is this? Common categories:
- Encoding issue (编码问题)
- Dependency conflict (依赖冲突)
- Configuration error (配置错误)
- Logic flaw (逻辑缺陷)
- Resource leak (资源泄漏)
- Concurrency issue (并发问题)
- Environment mismatch (环境差异)
- API misuse (API误用)
- Permission issue (权限问题)
- Performance bottleneck (性能瓶颈)
- State management (状态管理)
- Other (describe)

Describe the **symptoms** — what does this problem look like from the outside? This helps recognize it next time.

**2. Root Cause Category (根因分类)**
What caused the problem at the deepest level? Be specific, not vague. "Wrong encoding" is better than "it was a bug."

**3. Technique Used (解决技巧)**
What approach, tool, or mental model helped crack this? Examples:
- Read the error message word by word (逐字读报错)
- Binary search bisecting (二分法定位)
- Checked the documentation (查文档)
- Added logging to narrow scope (加日志缩小范围)
- Compared working vs broken state (对比正常和异常状态)
- Searched for similar issues online (搜索类似问题)
- Traced the data flow (追踪数据流)
- Checked environment variables (检查环境变量)

**4. Reusable Insight (可复用洞察)**

This is the **most valuable** part. Write one clear sentence that answers: "Next time I see something similar, what should I check FIRST?"

Format it as a rule of thumb, not a tutorial. Think heuristic, not procedure.

Good examples:
> Chrome CDP 相关问题，第一步检查 9222 端口是否被旧进程占用，而不是直接重启浏览器
> Python GBK 编码报错，先检查文件实际编码而非默认假设 UTF-8
> Selenium 元素找不到，先检查是否在 iframe 里，再检查等待策略

Bad examples:
> 我修了一个 bug，方法是改了代码 (not actionable)
> 用 pip install 安装依赖 (too generic)

### Step 3: Write to project memory

Create a memory file in the project memory directory. Use the Write tool to create the file.

**File path**: Use the current project's memory directory. Check `C:\Users\yingy\.claude\projects\` for the matching project subfolder. For example:
- MDEase project: `C:\Users\yingy\.claude\projects\C--D-CAIE-tool-MyAIProduct-MDEase\memory\exp-[kebab-case-name].md`
- Root project: `C:\Users\yingy\.claude\projects\C--D-CAIE-tool-MyAIProduct-pm\memory\exp-[kebab-case-name].md`

Choose the filename based on the core topic (e.g., `exp-chrome-cdp-port-conflict.md`, `exp-gbk-encoding-detection.md`).

**File content** — use this exact structure:

```markdown
---
name: exp-[kebab-case-name]
description: [One sentence capturing the core insight — this shows up in MEMORY.md index]
type: project
---

## 问题模式
[Describe symptoms and pattern]

## 根因分类
[Category] — [Specific cause]

## 解决技巧
1. [Technique 1]
2. [Technique 2]

## 可复用洞察
> [One sentence heuristic — check X before Y]

## 关键词
[keyword1, keyword2, keyword3]

## 日期
[YYYY-MM-DD]
```

**Constraints**:
- Do NOT include specific code changes or fix recipes. Store patterns and insights, not diffs.
- The `description` field should be under 100 characters — it appears in the MEMORY.md index.
- Keywords should be terms someone might search for when encountering a similar problem.

### Step 4: Update MEMORY.md index

Read `C:\Users\yingy\.claude\projects\C--D-CAIE-tool-MyAIProduct-pm\memory\MEMORY.md` first.

- If the file does not exist, create it with a header: `# Experience Index` and a section for bug retrospectives.
- If it exists, append a new entry under the appropriate section.

Add one line:
```
- [经验标题](exp-file-name.md) — 一句话核心洞察
```

Keep the title descriptive but concise. The insight after the dash should be the most actionable part.

### Step 5: Present the retrospective

Show the user a clean summary:

```
## 复盘完成

**问题模式**: [pattern]
**核心洞察**: [insight]
**存储位置**: memory/exp-[name].md
```

Ask if the user wants to adjust anything before finalizing.

## Example output

Given a conversation where the user had a Chrome automation script failing with timeout errors, and the fix was killing stale Chrome processes holding port 9222:

```markdown
---
name: exp-chrome-cdp-port-conflict
description: Chrome CDP超时排查 - 先检查端口占用而非重启浏览器
type: project
---

## 问题模式
Chrome 通过 CDP (Chrome DevTools Protocol) 连接时频繁超时，报错 "connection refused" 或 "timeout waiting for debug connection"

## 根因分类
环境问题 — 旧 Chrome 进程未释放调试端口 9222

## 解决技巧
1. 用 netstat -ano | findstr 9222 确认端口被哪个 PID 占用
2. taskkill /PID <pid> /F 杀掉残留进程
3. 添加端口检测逻辑：连接前先探测端口是否可用

## 可复用洞察
> Chrome CDP 连接问题，第一步用 netstat 检查 9222 端口占用情况，不要直接重启浏览器

## 关键词
chrome, cdp, timeout, port conflict, netstat, 9222

## 日期
2026-04-05
```
