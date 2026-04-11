---
name: expert-retro-autofix
description: "全自动化专家复盘 + 自动修复。ALWAYS use this skill when the user says: 复盘, 专家复盘, 自动复盘, 项目复盘, 代码复盘, 全面检查, 项目体检, retro, retrospective, expert retro, auto-fix, autofix, 自动改进, 自动优化, 全面审查+修复, project health check, code review and fix. Even if the user just says '复盘一下' or '帮我复盘', trigger this skill. Scans project → 3-expert roundtable → improvement plan → auto-fix loop → experience extraction. Fully automated until completion."
version: 1.0.0
author: Claude Code
tags: [retrospective, autofix, expert-review, quality, automation, zhipuai]
---

# Expert Retro AutoFix — 全自动化专家复盘 + 自动修复

**核心理念**: 定目标 → 追过程 → 拿结果。一条龙闭环：发现问题 → 专家讨论 → 制定方案 → 执行修复 → 经验沉淀。全程无需用户干预。

## 触发条件

当用户说以下任何关键词时触发：
- 复盘、专家复盘、自动复盘、项目复盘、代码复盘
- 全面检查、项目体检、代码体检
- retro, retrospective, expert retro, auto-fix, autofix
- 自动改进、自动优化、全面审查+修复
- project health check, code review and fix

---

## Phase 0: Bootstrap — 环境检查

在开始之前，验证所有依赖就绪。缺少任何一项都要报告并停止。

### 检查清单

使用 Bash 工具依次执行：

```bash
# 1. 检查 ZHIPU_API_KEY
python -c "import os; assert os.environ.get('ZHIPU_API_KEY'), 'ZHIPU_API_KEY not set'; print('ZHIPU_API_KEY: OK')"

# 2. 检查 zhipuai 包
python -c "import zhipuai; print('zhipuai:', zhipuai.__version__)"

# 3. 检查 pytest
python -c "import pytest; print('pytest:', pytest.__version__)" 2>/dev/null || echo "pytest: not installed"

# 4. 检查项目是否是 git 仓库
git rev-parse --is-inside-work-tree
```

如果 ZHIPU_API_KEY 缺失：告知用户设置环境变量，停止。
如果 zhipuai 缺失：运行 `pip install zhipuai`。
如果 pytest 缺失：继续但不执行测试验证。
如果不是 git 仓库：继续但不执行 checkpoint。

### 输出

向用户报告：
```
## Phase 0: 环境检查
- ZHIPU_API_KEY: ✅/❌
- zhipuai: ✅/❌
- pytest: ✅/❌
- git: ✅/❌
```

---

## Phase 1: Project Scan — 五层扫描

这是发现问题的地基。**颗粒度决定成败** — 扫描越全面，发现越精准。

### Layer 1: 结构扫描

```bash
# 列出所有 Python 源文件
find app/ -name "*.py" -not -path "*__pycache__*" -not -path "*migrations/*" | head -50
```

使用 Glob 工具扫描：
- `app/**/*.py` — 后端 Python
- `web/**/*.{vue,ts,js}` — 前端（如果存在）
- `*.{json,yml,yaml,toml,cfg,ini}` — 配置文件

对每个文件，记录：路径、行数（用 `wc -l`）。

### Layer 2: 模式扫描（Grep 搜索以下模式）

对每个模式，使用 Grep 工具搜索，收集匹配文件和行号：

| 模式 | 含义 |
|------|------|
| `TODO\|FIXME\|HACK\|XXX` | 遗留待办 |
| `except:` | 裸 except |
| `except.*:\s*pass` | 吞异常 |
| `print\(` | 调试打印残留 |
| `import \*` | 通配符导入 |
| `eval(\|exec(\|subprocess.*shell=True` | 危险函数 |
| `password\|secret\|token` | 可能的硬编码密钥 |
| `SELECT.*\|.*WHERE.*format\|f".*SELECT` | 潜在 SQL 注入 |
| `request\.(args\|form\|json)\[` | 未验证的用户输入 |
| `\.execute\(` | 直接 SQL 执行 |
| `open\(.*['\"]w` | 文件写入（检查是否关闭） |
| `conn\|cursor\|session` | 数据库连接（检查是否释放） |

### Layer 3: 架构扫描

1. **模块依赖**：读取所有 `import` 语句，构建依赖图
2. **路由-服务映射**：读取 `app/routes/` 中每个路由调用的服务
3. **配置使用**：读取 `config.py` 中的配置项，检查是否都被使用
4. **循环依赖检测**：检查是否有 A imports B imports A 的情况

### Layer 4: 测试扫描

```bash
# 运行现有测试
python -m pytest tests/ -v --tb=short 2>&1 | tail -30
```

记录：通过/失败/跳过数量，失败测试详情。

### Layer 5: 依赖扫描

```bash
# 检查 requirements.txt
cat requirements.txt
```

检查是否有明显过时或已知有漏洞的包版本。

### 构建项目快照 JSON

将以上所有扫描结果整理为 JSON 格式：

```json
{
  "project_name": "hotel",
  "framework": "Flask + Nuxt.js",
  "total_files": 0,
  "file_tree": ["app/routes/comparison.py:245", "..."],
  "pattern_findings": [
    {"pattern": "bare_except", "file": "app/routes/...", "line": 42, "content": "...", "severity": "high"}
  ],
  "architecture": {
    "imports": {"module.a": ["module.b", "module.c"]},
    "route_service_map": {"/api/search": "hotel_provider"},
    "circular_deps": []
  },
  "test_results": "...",
  "dependencies": "...",
  "key_snippets": [
    {"file": "...", "start": 1, "end": 50, "language": "python", "content": "..."}
  ]
}
```

将快照保存到临时文件：`test/temp/project_snapshot.json`

---

## Phase 2: Expert Roundtable — 三人专家圆桌

调用 `expert_roundtable.py` 脚本，让三位专家讨论项目问题。

### 执行命令

```bash
cd PROJECT_DIR && python ".claude/skills/expert-retro-autofix/scripts/expert_roundtable.py" "test/temp/project_snapshot.json"
```

将 stdout 输出保存为 `test/temp/roundtable_results.json`。

### 输出格式

脚本输出包含：
- `findings[]` — 去重后的所有发现
- `batches[]` — 分批执行计划
- `stats` — 统计信息

### 如果脚本失败

回退方案：Claude Code 直接根据 Phase 1 扫描结果生成 findings。逐个读取 Phase 1 发现的模式问题，自行评估严重级别并生成 findings JSON。

### 向用户报告

```
## Phase 2: 专家圆桌讨论完成
- Round 1（独立分析）: X 个发现
- Round 2（交叉审查）: Y 个补充
- Round 3（综合分析）: Z 个最终发现
- 分为 N 个执行批次
- 严重级别: critical: X, high: Y, medium: Z, low: W
```

---

## Phase 3: Plan Review — 方案审核

在执行修复前，向用户展示改进方案并征求确认（仅首次）。

### 展示内容

列出所有 findings，按严重级别排序：

```
| # | 级别 | 文件 | 问题 | 建议 |
|---|------|------|------|------|
| 1 | critical | ... | ... | ... |
```

列出执行批次：

```
| 批次 | 优先级 | 文件 | 问题数 | 复杂度 |
|------|--------|------|--------|--------|
| 1 | critical | ... | 3 | medium |
```

**重要**：仅第一次迭代需要确认。后续自动迭代循环中直接执行，不再打断用户。

---

## Phase 4: Auto-Fix Loop — 自动修复循环

**这是闭环的核心**。逐批执行修复，每批都有 checkpoint 保护。

### 迭代变量

```
current_iteration = 1
MAX_ITERATIONS = 5
last_finding_count = 0
stagnation_count = 0
```

### 外层循环（最多 MAX_ITERATIONS 轮）

```
while current_iteration <= MAX_ITERATIONS:
    execute_all_batches()
    run_regression_tests()
    write_experience_cards()
    check_termination()
    current_iteration += 1
```

### 单批次执行流程

对每个 batch（按 batches 数组顺序）：

**Step 1: Git Checkpoint**

```bash
git add -A
git commit -m "auto-fix: checkpoint before batch {batch.id}" --allow-empty
```

记录 commit SHA。

**Step 2: 读取目标文件**

对 batch 中的每个文件，使用 Read 工具读取当前内容。

**Step 3: 调用 LLM 生成修复**

使用 Python 脚本调用 ZhipuAI 修复代码：

```bash
python -c "
import sys, json
sys.path.insert(0, '.claude/skills/expert-review')
from autofix.llm_client import LLMClient

llm = LLMClient()
file_content = open('{file_path}', encoding='utf-8').read()
findings = json.loads('''{batch.findings_json}''')
result = llm.fix_code(file_content, '{file_path}', '{language}', findings)
if result:
    print(result)
else:
    print('FIX_FAILED')
"
```

**Step 4: AST 验证**

```bash
python -c "import ast; ast.parse(open('{file_path}', encoding='utf-8').read()); print('AST: OK')"
```

如果 AST 失败：跳过此文件，标记为 failed。

**Step 5: 写入修复**

使用 Edit 工具（如果是局部修改）或 Write 工具（如果是整体重写）写入修复后的文件。

**Step 6: 运行测试**

```bash
python -m pytest tests/ -x --tb=short 2>&1 | tail -20
```

- 如果通过：commit 修复，标记 batch 为 FIXED
- 如果失败：rollback 到 checkpoint，标记 batch 为 FAILED

**Step 7: 回滚（如果测试失败）**

```bash
git reset --soft {checkpoint_sha}
git checkout -- .
```

**Step 8: Commit 成功修复**

```bash
git add -A
git commit -m "auto-fix: batch {batch.id} - {batch.summary}"
```

### 向用户报告每批次结果

```
### Batch {id}: {summary}
- 状态: ✅ FIXED / ❌ FAILED
- 修改文件: file1.py, file2.py
- 测试: ✅ 全部通过 / ❌ X 个失败
```

---

## Phase 5: Retrospective — 经验沉淀

每轮迭代结束后，将修复经验写入项目 memory。

### 经验卡片生成

对每个 FIXED 或 FAILED 的 finding，生成经验卡片：

```json
{
  "problem_pattern": "描述问题模式",
  "root_cause": "Category — Specific cause",
  "solution_techniques": ["技巧1", "技巧2"],
  "reusable_insight": "一句话可复用洞察",
  "keywords": ["keyword1", "keyword2"],
  "date": "2026-04-11",
  "source": "expert-retro-autofix",
  "file_path": "相关文件路径"
}
```

### 写入经验卡片

使用 Python 脚本调用 `experience_writer`：

```bash
python -c "
import sys, json
sys.path.insert(0, '.claude/skills/expert-review')
from shared.experience_writer import write_experience_cards

cards = json.loads('''{cards_json}''')
written = write_experience_cards(cards, '{project_dir}')
print(f'Written {len(written)} cards')
"
```

---

## 终止条件检查

每轮迭代结束后检查三个终止条件：

### 条件 1: 所有 finding 已处理

```
if 所有 finding 状态为 FIXED 或 WONT_FIX:
    输出最终报告 → 结束
```

### 条件 2: 迭代上限

```
if current_iteration >= MAX_ITERATIONS:
    输出最终报告（标记未完成项）→ 结束
```

### 条件 3: 停滞检测

```
current_finding_count = count(findings 状态 != FIXED)
if current_finding_count == last_finding_count:
    stagnation_count += 1
else:
    stagnation_count = 0
    last_finding_count = current_finding_count

if stagnation_count >= 2:
    输出最终报告（标记为停滞）→ 结束
```

### 不终止则重新扫描

如果未满足任何终止条件：
1. 重新运行 Phase 1 扫描（快速版：只扫描已修改文件）
2. 将新发现的 findings 合并到待处理列表
3. 重新进入 Phase 4

---

## Phase 6: Final Report — 最终报告

### 报告格式

```
## 专家复盘完成 — 最终报告

### 执行统计
- 总迭代: {iterations}/{MAX_ITERATIONS}
- 总发现: {total_findings}
- 已修复: {fixed_count}
- 修复失败: {failed_count}
- 跳过: {skipped_count}
- Git commits: {commit_count}

### 修复详情
| 文件 | 问题数 | 状态 |
|------|--------|------|
| ... | ... | ✅/❌ |

### 经验沉淀
- 新增 {cards_count} 张经验卡片到 memory 目录

### 建议（未修复项）
1. [建议1]
2. [建议2]
```

### 清理

```bash
# 清理临时文件
rm -f test/temp/project_snapshot.json test/temp/roundtable_results.json
```

---

## 重要约束

1. **首次确认，后续自动**：Phase 3 首次展示方案时征求用户确认，之后自动循环
2. **Checkpoint 保护**：每个 batch 执行前必须 git commit，失败时必须回滚
3. **AST 验证**：所有 Python 文件修改后必须通过 ast.parse()
4. **测试回归**：每批修复后运行 pytest，失败则回滚
5. **经验沉淀**：每轮迭代结束写经验卡片，不允许跳过
6. **终止保障**：三重终止条件，不会无限循环
7. **中文交流**：全程使用中文与用户沟通

## 错误处理

| 场景 | 处理 |
|------|------|
| ZhipuAI API 失败 | 重试 3 次（LLMClient 内置），仍失败则标记 finding 为 WONT_FIX |
| Git 操作失败 | 跳过 checkpoint，直接修改（无保护模式） |
| AST 验证失败 | 丢弃修复，保留原文件 |
| pytest 失败 | 回滚到 checkpoint |
| 快照文件过大 | 截断到 8000 token 以内 |
| 经验卡片写入失败 | 记录错误但不中断流程 |
