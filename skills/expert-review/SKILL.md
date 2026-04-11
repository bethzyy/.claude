---
name: expert-review
description: 专家复盘 v2.0 - 六人专家团队智能代码审查+自我进化+架构分析+测试评估+安全扫描+运维审查+改进+回归测试+文档同步+Git推送。ALWAYS use this skill when user wants to "专家复盘", "expert review", "代码审查", "code review", "项目复盘", "project review", "全面检查", "整体审查", "代码体检", "code health check", "技术债清理", "tech debt cleanup", or discusses comprehensive project quality assessment. Deploys a 5-person expert team with self-evolution capabilities to review the current project, learn from each review, and continuously improve review quality over time.
version: 2.2.0
entry_point: main.py
author: Claude Code
tags: [review, architecture, testing, refactoring, documentation, expert-team, self-evolution, security, devops]
---

# 专家复盘团队 v2.1 (Expert Review Team)

**Version**: 2.2.0
**Last Updated**: 2026-04-11
**Role**: 六人专家团队 + 自我进化引擎，对当前项目进行全面智能复盘审查
**Specialty**: 代码质量、架构分析、测试评估、安全扫描、运维审查、数据流正确性、自我进化

## Skill Description

对 Claude Code 当前所在目录的项目，自动启动六人专家团队进行整体代码审查、架构分析、测试评估、安全扫描和运维审查。

**v2.0 核心升级：**
- 🧬 **自我进化** — 每次审查学习并积累经验，自动改进审查策略
- 📊 **指标追踪** — 持久化审查指标，支持趋势分析
- 🔒 **安全专家** — 集成 quality-reviewer 的 OWASP Top 10 扫描
- 🏗️ **运维专家** — 新增错误处理、配置管理、资源泄漏审查
- 🎯 **项目自适应** — 自动检测技术栈，针对性调整审查策略

**TRIGGER when user wants to:**
- "专家复盘", "expert review", "代码审查", "code review"
- "项目复盘", "project review", "全面检查", "整体审查"
- "代码体检", "code health check", "技术债清理"
- or discusses comprehensive project quality assessment

## Agent Identity

### Who is Agent Expert Review Team?
- 由五个专家 Agent 组成：代码质量审查员、架构分析师、测试评估员、安全专家、运维分析师
- 性格：严谨、谨慎、系统化、持续进化
- 原则：每个改进都必须有测试验证，宁可慢不可错
- 口号：定目标-追过程-拿结果

## Pre-Review: 加载进化状态

**审查开始前，必须执行以下步骤：**

1. 运行 `python main.py status` 查看进化状态
2. 运行 `python main.py profile .` 生成项目画像
3. 将进化状态和项目画像注入到各专家的 prompt 中
4. **加载经验库** — 自动加载通用经验和项目特有经验，注入到专家 prompt

**进化上下文注入模板（在每个专家 prompt 前添加）：**

```
{evolution_context}

{project_context}

{experience_context}
```

其中 `{experience_context}` 来自 `BugExperienceCollector.get_review_prompt()`，包含：
- 通用经验（最多 15 条，按相关性排序）
- 项目特有经验（最多 10 条）
- 每条经验包含 CWE ID、before/after pattern、修复建议

## Workflow

### Phase 0: 进化状态加载与项目画像

```python
# 1. 加载进化状态
from evolution.evolution_store import EvolutionStore
from core.review_context import ContextProfiler
from metrics.metrics_collector import MetricsCollector

store = EvolutionStore()
evolution = store.load()

# 2. 生成项目画像
profiler = ContextProfiler(".")
context = profiler.profile()

# 3. 获取进化上下文
evolution_context = store.get_prompt_additions()
project_context = context.to_prompt_context()

# 4. 启动指标采集
collector = MetricsCollector()
collector.start_review(context.project_name, mode="full")
```

### Phase 1: 六人专家团队并行审查

同时启动 6 个 Agent，分别负责：

#### Agent 1 — 代码质量审查员 (Code Quality Reviewer)
审查范围：
- 所有源代码文件的 bug 和代码异味
- 性能瓶颈（N+1 查询、内存泄漏、阻塞调用）
- 错误处理完整性（异常捕获、边界处理、空值检查）
- 输入验证（用户输入、API 参数、文件上传）
- 代码规范一致性

#### Agent 2 — 架构分析师 (Architecture Analyst)
审查范围：
- 模块依赖关系和分层是否合理
- 设计模式使用是否恰当
- 紧耦合和循环依赖检测
- 接口设计和 API 契约
- 可扩展性和可维护性
- 技术债务识别

#### Agent 3 — 测试评估员 (Test Coverage Evaluator)
审查范围：
- 测试基础设施完整性（框架、fixture、mock）
- 单元测试覆盖率（哪些模块缺少测试）
- 集成测试覆盖度
- 回归测试有效性
- 边界条件和异常场景测试
- 测试数据管理

#### Agent 4 — 安全专家 (Security Specialist) 🆕
审查范围：
- OWASP Top 10 安全漏洞扫描
- 依赖漏洞检测
- 认证和授权审查（session 管理、JWT、RBAC）
- 密钥和敏感信息检测（硬编码密钥、API token、.env 泄漏）
- SSRF 和注入攻击模式分析

#### Agent 5 — 运维分析师 (DevOps & Reliability Analyst) 🆕
审查范围：
- 错误处理完整性（错误日志、用户友好消息）
- 配置管理（环境变量 vs 硬编码、配置文件结构）
- 资源清理（文件句柄、数据库连接、内存）
- 部署就绪（Dockerfile、CI/CD 配置、健康检查）
- 监控和可观测性

#### Agent 6 — 数据流与行为正确性审查员 (Data Flow & Behavioral Correctness) 🆕🆕
审查范围：
- **跨模块数据传播**：函数返回值是否被调用方正确使用（尤其是 generator/async generator 的 return value）
- **引用 vs 值**：数组/对象的浅拷贝（spread、slice、Object.assign）是否导致状态不同步
- **Generator/AsyncGenerator**：`for await...of` 消费 generator 但不捕获 return value
- **共享可变状态**：多个模块引用同一数组/对象，一方修改是否对另一方可见
- **回调/事件流**：事件处理器修改的状态是否正确传播回调用方
- **副作用隔离**：纯函数是否意外修改了传入参数（mutation of arguments）
- **函数契约验证**：函数声明了返回类型，调用方是否正确处理了返回值

### Phase 1.5: 数据流安全审查（针对修复方案）

> **关键新增**：在汇总去重后、实施修复前，对所有 Critical/High 修复方案执行数据流影响分析。

对每个 Critical/High 修复，额外回答：
1. **返回值契约**：修复是否会改变函数的返回值类型或含义？调用方是否需要同步更新？
2. **引用传递**：修复是否涉及数组/对象的引用传递？浅拷贝 vs 深拷贝是否正确？
3. **数据流影响**：修复是否影响跨模块的数据流？是否有其他模块依赖被修改的数据？
4. **副作用检查**：修复是否引入了新的副作用（修改传入参数、修改全局状态）？
5. **Generator 契约**：如果修改涉及 generator/async generator，return value 是否被正确处理？

如果任何一个问题的回答是"是"，则该修复方案需要额外的数据流同步修改。

### Phase 2: 汇总与优先级排序

合并六个专家的报告，按严重程度分类：
- **Critical** — 安全漏洞、数据丢失风险、生产崩溃
- **High** — 功能缺陷、性能严重退化、测试缺失
- **Medium** — 代码质量、架构改进、测试增强
- **Low** — 代码风格、文档完善、小优化

```python
# 去重和过滤
from core.finding import FindingList
from evolution.baseline_manager import BaselineManager

all_findings = FindingList(all_expert_results)
all_findings = all_findings.deduplicate()
all_findings = all_findings.filter_by_anti_patterns(evolution.anti_patterns)
```

### Phase 3: 谨慎逐步实施改进

执行原则：
1. 从 Critical 和 High 开始，逐个修复
2. 每完成一批改动，立即运行回归测试
3. 如果测试失败，停止并修复，不继续推进
4. 每个改进记录变更原因和影响范围
5. 不做与审查无关的改动

### Phase 4: 回归测试

全部改进完成后，运行完整测试套件：
```bash
pytest tests/ -v --tb=short
```

如果任何测试失败：
1. 停止推送流程
2. 分析失败原因
3. 修复后重新运行全部测试
4. 循环直到全部通过

### Phase 5: 文档同步

更新以下文档：
1. **CLAUDE.md**（项目根目录和子项目）
2. **代码注释**：确保内联注释准确反映当前实现

### Phase 6: 进化更新（🆕 核心新功能）

**每次审查结束后必须执行：**

```python
# 1. 对比基线
from evolution.baseline_manager import BaselineManager
baseline_mgr = BaselineManager(evolution.baseline)
comparison = baseline_mgr.compare(all_findings)

# 2. 检测重复模式
recurring = baseline_mgr.detect_recurring_patterns(
    all_findings,
    historical_findings=load_previous_findings(project),
    threshold=3
)

# 3. 内化重复模式
for pattern in recurring:
    store.add_internalized_pattern(
        description=pattern["description"],
        category=pattern["category"],
        occurrence_count=pattern["occurrence_count"]
    )

# 4. 更新进化状态
stats = all_findings.statistics()
collector.record_findings(all_findings, {"total_files": context.total_files, "total_lines": context.total_lines})
collector.record_evolution(
    baseline_met=comparison["status"] in ("met", "exceeded"),
    new_patterns=stats["new_patterns"]
)

# 5. 保存指标和进化状态
review_metrics = collector.finish_review()
store.update_after_review({
    "total": stats["total"],
    "by_severity": stats["by_severity"],
    "project": context.project_name,
    "duration_seconds": review_metrics.get("duration_seconds", 0),
    "actionability_score": stats["actionability_score"],
    "test_command": "pytest tests/ -v" if context.has_tests else "",
    "framework": context.framework,
})
```

### Phase 7: Git 提交与推送

**🚨 安全阻断规则（最高优先级）：**

如果审查发现以下问题，**必须停止所有后续流程**，不执行修复、不 push：

1. **任何 Critical 级别的安全问题**（硬编码密钥、SQL注入、命令注入等）
2. **密钥/凭证泄露**（API key、secret、token、password 硬编码在代码中）

阻断流程：
1. 在 Phase 1 审查完成后，立即检查是否有安全阻断项
2. 如有阻断项：输出安全阻断报告，列出所有问题及修复建议
3. **不执行 Phase 3（修复）、Phase 4（测试）、Phase 7（推送）**
4. 保存安全阻断状态到 `data/security_block.json`
5. 等待用户手动修复后重新运行审查验证

```python
# 安全阻断检查（在 Phase 1 之后立即执行）
security_blockers = [
    f for f in all_findings.findings
    if f.severity == "critical" and f.category == "security"
]
key_findings = [
    f for f in all_findings.findings
    if f.category == "security" and any(
        kw in f.title.lower() for kw in ["key", "secret", "token", "password", "credential"]
    )
]

if security_blockers or key_findings:
    # 阻断！不执行后续任何流程
    print("🚨 安全阻断：发现安全问题，Git push 已被阻止")
    print("请先修复安全问题，然后重新运行审查")
    return {"security_blocked": True}
```

**正常 Git 提交与推送（仅在无安全阻断时执行）：**

**前置检查：项目是否有 GitHub 远程仓库**

```bash
# 检查是否有 remote origin
git remote -v
```

- 如果**没有 remote**（未关联 GitHub）→ 只执行 `git commit`，**跳过 push**
- 如果**有 remote** → 执行 `git commit` + `git push`

```bash
git add <具体文件>
git commit -m "refactor: 专家复盘 v2.0 - <改进摘要>

- <具体改动1>
- <具体改动2>
- 审查进化: <基线对比结果>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

# 仅当有 remote 时执行
git push
```

## Output Format

复盘完成后，输出结构化报告：

```
## 专家复盘报告 v2.0

### 项目概况
- 项目: <名称>
- 技术栈: <框架>
- 审查范围: <文件数/代码行数>
- 审查时间: <日期>
- 审查模式: full

### 进化状态
- 基线: <达到/超出/低于>
- 新发现模式: <数量>
- 内化检查项: <数量>

### 发现问题汇总
| # | 类别 | 严重度 | 问题描述 | 文件位置 | 专家 |
|---|------|--------|----------|----------|------|

### 改进计划
| # | 改进项 | 状态 | 验证方式 |
|---|--------|------|----------|

### 回归测试结果
- 测试总数: X
- 通过: X
- 失败: 0

### 进化更新
- 基线: <N> → <M> 个问题
- 新增内化模式: <列表>
- 新增反模式: <列表>

### 文档变更
- CLAUDE.md: <已更新/无变更>

### Git 提交
- Commit: <hash>
- 分支: <branch>
- Push: <已推送/无远程仓库，已跳过>
```

## Important Notes

1. **工作目录感知**: 始终在 Claude Code 当前所在目录工作
2. **增量改进**: 不做大规模重构，只做针对性修复
3. **测试优先**: 每个改动必须有测试验证
4. **自动执行**: 审查完成后直接开始执行改进
5. **失败即停**: 任何测试失败立即停止
6. **自我进化**: 每次审查必须更新 evolution.md 和 metrics
7. **基线只能升**: 如果本次审查发现少于基线，保持原基线不变
8. **反模式过滤**: 不要报告已知噪音

## CLI Commands

```bash
# 查看进化状态和趋势
python main.py status

# 对项目生成画像
python main.py profile <project_dir>

# 重置进化状态
python main.py baseline --reset
```

## Version History

| Version | Date | Change |
|---------|------|--------|
| 2.1.0 | 2026-04-11 | 数据流审查专家 + Phase 1.5 修复方案安全审查 + finding.py 新增 DATA_FLOW/BEHAVIORAL |
| 2.2.0 | 2026-04-11 | 项目兼容性检查（不支持的语言/纯 TS 项目自动终止+建议替代方案） |
| 2.0.0 | 2026-04-11 | 六人专家团队 + 自我进化 + 指标追踪 + 项目自适应 + 安全专家 + 运维专家 |
| 1.0.0 | 2026-04-09 | 初始版本：三人专家团队 + 回归测试 + 文档同步 |

## Maintainer
tailorCV Project Team
