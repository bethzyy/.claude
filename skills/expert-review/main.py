"""
专家复盘 Skill v2.0 — 入口文件

完整编排入口：项目画像 → 进化加载 → 并行专家审查 → 报告 → 进化更新
"""

import io
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import argparse
import json
from datetime import datetime
from pathlib import Path

from core._paths import SKILL_DIR, ensure_skill_path
ensure_skill_path()

SKILL_NAME = "expert-review"
SKILL_VERSION = "4.0.0"

# === 兼容性检查 ===

# 不支持的语言扩展名
UNSUPPORTED_LANGUAGES = {
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".r": "R",
    ".m": "Objective-C",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
}

# 支持但覆盖有限的语言
LIMITED_SUPPORT_LANGUAGES = {
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
}


def _check_compatibility(context) -> dict:
    """
    检查项目是否在专家复盘 Skill 的能力范围内。

    返回:
        {
            "compatible": True/False,
            "reason": str (仅 incompatible 时),
            "warning": str (仅 limited support 时),
            "suggestions": list[str],
        }
    """
    dist = context.language_distribution
    if not dist:
        return {"compatible": True}

    total = sum(dist.values())

    # 检查不支持的语言占比
    unsupported_count = 0
    unsupported_names = set()
    for ext, count in dist.items():
        if ext in UNSUPPORTED_LANGUAGES:
            unsupported_count += count
            unsupported_names.add(UNSUPPORTED_LANGUAGES[ext])

    if unsupported_count > 0:
        unsupported_ratio = unsupported_count / total
        # 不支持的语言超过 50% 或有超过 10 个文件
        if unsupported_ratio > 0.5 or unsupported_count > 10:
            return {
                "compatible": False,
                "reason": (
                    f"项目主要使用 {', '.join(sorted(unsupported_names))}，"
                    f"专家复盘 Skill 不支持这些语言（{unsupported_count}/{total} 个文件，"
                    f"占比 {unsupported_ratio:.0%}）。所有专家的检测模式均基于 Python 正则，"
                    f"无法有效审查其他语言的代码。"
                ),
                "suggestions": [
                    "对于 Python 项目，专家复盘能提供高质量的全面审查",
                    "对于 TypeScript/JavaScript 项目，仅数据流专家能提供有限覆盖",
                    "对于其他语言，建议使用对应语言的专用 lint 工具（如 ESLint、golangci-lint、rustfmt 等）",
                ],
            }

    # 检查有限支持的语言
    limited_count = 0
    limited_names = set()
    for ext, count in dist.items():
        if ext in LIMITED_SUPPORT_LANGUAGES:
            limited_count += count
            limited_names.add(LIMITED_SUPPORT_LANGUAGES[ext])

    py_count = dist.get(".py", 0)

    # TS/JS 文件占比判断
    limited_ratio = limited_count / total if total > 0 else 0
    py_ratio = py_count / total if total > 0 else 0

    if limited_count > 0 and limited_ratio > 0.5:
        # TS/JS 占主导（>50%）— 使用 TypeScript 审查分支（由 Claude Code 驱动）
        extra = ""
        if py_count > 0:
            extra = f"（含 {py_count} 个 Python 文件，不单独审查）"
        if limited_ratio > 0.8:
            return {
                "compatible": True,
                "project_type": "typescript",
                "reason": (
                    f"TypeScript/JavaScript 项目（{', '.join(sorted(limited_names))}），"
                    f"使用 TypeScript 审查分支（Claude Code 驱动）。{extra}"
                ),
            }
        return {
            "compatible": True,
            "project_type": "typescript",
            "warning": (
                f"混合项目以 {', '.join(sorted(limited_names))} 为主"
                f"（{limited_count}/{total} 个文件，{limited_ratio:.0%}），"
                f"使用 TypeScript 审查分支。{extra}"
            ),
        }

    # Python 占主导或纯 Python 项目
    if py_count > 0:
        return {"compatible": True, "project_type": "python"}

    return {"compatible": True, "project_type": "python"}


def get_skill_info():
    """返回 skill 元信息"""
    return {
        "name": SKILL_NAME,
        "version": SKILL_VERSION,
        "description": "六人专家团队智能代码审查+项目兼容性检查+自我进化+架构分析+测试评估+安全扫描+运维审查+改进+回归测试+文档同步+Git推送",
        "trigger_words": [
            "专家复盘", "expert review", "代码审查", "code review",
            "项目复盘", "project review", "全面检查", "整体审查",
            "代码体检", "code health check", "技术债清理",
        ],
    }


def _add_finding_safe(findings_list, finding_list_obj, **kwargs):
    """安全地添加 Finding 到两个列表"""
    from core.finding import Finding, Severity, Category
    sev_map = {"critical": Severity.CRITICAL, "high": Severity.HIGH,
               "medium": Severity.MEDIUM, "low": Severity.LOW}
    cat_map = {
        "security": Category.SECURITY, "bug": Category.BUG,
        "performance": Category.PERFORMANCE, "maintainability": Category.MAINTAINABILITY,
        "architecture": Category.ARCHITECTURE, "testing": Category.TESTING,
        "documentation": Category.DOCUMENTATION, "configuration": Category.CONFIGURATION,
        "reliability": Category.RELIABILITY, "style": Category.STYLE,
        "data_flow": Category.DATA_FLOW, "behavioral": Category.BEHAVIORAL,
    }
    severity = sev_map.get(kwargs.pop("severity", "medium"), Severity.MEDIUM)
    category = cat_map.get(kwargs.pop("category", "maintainability"), Category.MAINTAINABILITY)
    finding = Finding(severity=severity, category=category, **kwargs)
    findings_list.append(finding)
    finding_list_obj.add(finding)


def _run_auto_fix(all_findings, context, project_dir: str, plan_only: bool = False):
    """
    Phase 2.7: 自动改进闭环。

    生成改进方案 → 逐批执行修复 → 验证 → 回归审查。
    """
    from autofix.llm_client import LLMClient
    from autofix.plan_generator import PlanGenerator
    from autofix.fix_executor import FixExecutor
    from autofix.verifier import Verifier

    print(f"\n{'='*60}")
    print(f"  Phase 2.7: 自动改进闭环")
    print(f"{'='*60}")

    # 初始化
    try:
        llm = LLMClient()
    except RuntimeError as e:
        print(f"  ❌ LLM 初始化失败: {e}")
        print(f"  请设置 ZHIPU_API_KEY 环境变量")
        return

    executor = FixExecutor(llm, project_dir)
    verifier = Verifier(project_dir)
    generator = PlanGenerator()

    # 2.7.1 生成改进方案
    print("\n[Phase 2.7.1] 生成改进方案...")
    findings_list = [f.to_dict() if hasattr(f, "to_dict") else f for f in all_findings.findings]

    plan = generator.generate(
        findings=findings_list,
        project_dir=project_dir,
        project_context={
            "project_name": context.project_name,
            "framework": context.framework,
            "total_files": context.total_files,
        },
        use_llm=True,
        llm_client=llm,
    )

    if not plan.batches:
        print("  无可操作的发现（所有发现缺少修复建议）")
        return

    print(f"  改进方案: {plan.total_batches} 个批次, {plan.total_findings} 个发现")
    for batch in plan.batches:
        priority_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(batch.priority, "⚪")
        print(f"    {priority_icon} 批次 {batch.id}: {batch.summary} ({batch.complexity})")

    if plan_only:
        print(f"\n  --plan-only 模式，不执行修复")
        return

    # 2.7.2 逐批执行
    print(f"\n[Phase 2.7.2] 逐批执行修复...")
    success_count = 0
    fail_count = 0

    for batch in plan.batches:
        print(f"\n  --- 批次 {batch.id}/{plan.total_batches}: {batch.summary} ---")

        result = executor.execute_batch(batch)

        if not result.success:
            print(f"  ❌ 失败: {result.error or '未知错误'}")
            if result.checkpoint_sha:
                executor.rollback(result.checkpoint_sha)
            fail_count += 1
            continue

        # 2.7.3 验证
        print(f"  修复文件: {result.modified_files}")
        if result.failed_files:
            print(f"  跳过文件: {result.failed_files}")

        # 语法检查
        syntax_ok_files = []
        for fp in result.modified_files:
            if verifier.validate_syntax(fp):
                syntax_ok_files.append(fp)
            else:
                print(f"  ⚠️ 语法错误: {fp}")

        if not syntax_ok_files:
            print(f"  ⚠️ 所有修复文件语法验证失败，回滚")
            executor.rollback(result.checkpoint_sha)
            fail_count += 1
            continue

        # 测试执行
        test_result = verifier.run_tests()
        if test_result.passed:
            print(f"  ✅ 测试通过")
        elif test_result.total == 0:
            print(f"  ℹ️ 无测试，跳过测试验证")
        else:
            print(f"  ⚠️ 测试失败 ({test_result.failed}/{test_result.total})，回滚")
            executor.rollback(result.checkpoint_sha)
            fail_count += 1
            continue

        success_count += 1
        print(f"  ✅ 批次 {batch.id} 完成")

    # 2.7.4 回归审查
    if executor.all_modified_files:
        print(f"\n[Phase 2.7.4] 回归审查 ({len(executor.all_modified_files)} 个修改文件)...")
        max_iterations = 5

        for iteration in range(max_iterations):
            new_findings = verifier.re_review(executor.all_modified_files)
            if not new_findings:
                print(f"  ✅ 回归审查通过，无新 Critical/High 问题")
                break

            print(f"  回归第 {iteration+1} 轮: 发现 {len(new_findings)} 个新问题")

            # 构建修复批次
            from autofix.plan_generator import FixBatch
            file_groups = {}
            for f in new_findings:
                fp = f.get("file_path", "")
                if fp not in file_groups:
                    file_groups[fp] = []
                file_groups[fp].append(f)

            for fp, fp_findings in file_groups.items():
                print(f"  修复: {fp} ({len(fp_findings)} 个问题)")
                checkpoint = executor._checkpoint(f"auto-fix: regression iteration {iteration+1}")
                if not checkpoint:
                    continue

                modified = executor._fix_file(fp, fp_findings)
                if not modified:
                    executor.rollback(checkpoint)
                    continue

                if not verifier.validate_syntax(fp):
                    print(f"  ⚠️ 回归修复语法错误，回滚: {fp}")
                    executor.rollback(checkpoint)
                    continue

                test_result = verifier.run_tests()
                if not test_result.passed and test_result.total > 0:
                    print(f"  ⚠️ 回归修复测试失败，回滚: {fp}")
                    executor.rollback(checkpoint)
                    continue

                print(f"  ✅ 回归修复成功: {fp}")
        else:
            print(f"  ⚠️ 达到最大回归轮次 ({max_iterations})")

    # 最终 git commit
    if executor.all_modified_files:
        final_sha = executor._checkpoint("auto-fix: all fixes applied")
        if final_sha:
            print(f"\n  📦 最终提交: {final_sha}")

    # 汇总
    print(f"\n{'='*60}")
    print(f"  自动改进完成")
    print(f"  成功批次: {success_count}/{plan.total_batches}")
    print(f"  修改文件: {len(executor.all_modified_files)}")
    if fail_count:
        print(f"  失败批次: {fail_count} (已回滚)")
    print(f"{'='*60}\n")


def run_review(project_dir: str = ".", mode: str = "full", focus_areas: list = None, no_evolve: bool = False, auto_fix: bool = False, plan_only: bool = False):
    """
    执行完整审查流程。

    Args:
        project_dir: 项目目录
        mode: full | incremental | targeted
        focus_areas: 重点关注领域
        no_evolve: 跳过进化更新
    """
    project_path = Path(project_dir).resolve()
    if not project_path.is_dir():
        print(f"Error: Not a directory: {project_dir}")
        return {"error": f"Not a directory: {project_dir}"}

    from core.review_context import ContextProfiler
    from evolution.evolution_store import EvolutionStore
    from evolution.baseline_manager import BaselineManager
    from evolution.prompt_evolver import PromptEvolver
    from evolution.pattern_detector import PatternDetector
    from evolution.experience_collector import BugExperienceCollector
    from metrics.metrics_collector import MetricsCollector
    from metrics.kpi_tracker import KPITracker
    from context.scope_manager import ScopeManager
    from core.report_generator import ReportGenerator
    from experts.code_quality_expert import CodeQualityExpert
    from experts.architecture_expert import ArchitectureExpert
    from experts.testing_expert import TestingExpert
    from experts.security_expert import SecurityExpert
    from experts.devops_expert import DevOpsExpert
    from experts.data_flow_expert import DataFlowExpert

    print(f"\n{'='*60}")
    print(f"  专家复盘 Expert Review v{SKILL_VERSION}")
    print(f"{'='*60}\n")

    # === Phase 0: 加载上下文和进化状态 ===
    print("[Phase 0] 加载上下文和进化状态...")

    profiler = ContextProfiler(project_dir)
    context = profiler.profile()

    store = EvolutionStore(str(SKILL_DIR))
    evolution = store.load()

    # 加载 pending prompt deltas
    evolver = PromptEvolver(str(SKILL_DIR))
    prompt_deltas = evolver.load_pending_deltas()

    # 确定审查范围
    scope_mgr = ScopeManager(project_dir)
    source_files = scope_mgr.get_files(
        mode=mode,
        focus_areas=focus_areas,
        all_source_files=context.source_files,
    )

    print(f"  项目: {context.project_name}")
    print(f"  技术栈: {', '.join(context.tech_stack) or '未检测到'}")
    print(f"  框架: {context.framework or '未检测到'}")
    print(f"  源文件: {context.total_files} 个 ({context.total_lines} 行)")
    print(f"  审查模式: {mode}")
    print(f"  审查范围: {len(source_files)} 个文件")

    # 空项目早期退出
    if context.total_files == 0:
        print(f"\n  未发现可审查的源文件，审查终止。")
        return {"findings_count": 0, "message": "No source files found"}

    # === 兼容性检查 ===
    compatibility = _check_compatibility(context)
    if compatibility["compatible"] is False:
        print(f"\n{'!'*60}")
        print(f"  ⚠️  项目兼容性检查未通过")
        print(f"{'!'*60}")
        print(f"\n  {compatibility['reason']}\n")
        print(f"  当前项目语言分布:")
        for ext, cnt in sorted(context.language_distribution.items(), key=lambda x: -x[1]):
            print(f"    {ext}: {cnt} 个文件")
        print(f"\n  专家复盘 Skill 当前支持:")
        print(f"    ✅ Python (.py) — 5/6 专家完整支持")
        print(f"    ✅ TypeScript/JavaScript (.ts/.tsx/.js/.jsx) — Claude Code 驱动审查")
        print(f"    ❌ Java, Go, Rust, C#, Ruby, PHP 等 — 不支持\n")
        for suggestion in compatibility.get("suggestions", []):
            print(f"    - {suggestion}")
        print(f"\n{'!'*60}")
        print(f"  审查已终止。")
        print(f"{'!'*60}\n")
        return {"findings_count": 0, "message": compatibility["reason"]}

    # === TypeScript 项目 → 混合审查或 TS 专用分支 ===
    if compatibility.get("project_type") == "typescript":
        py_count = context.language_distribution.get(".py", 0)
        limited_count = sum(
            context.language_distribution.get(ext, 0)
            for ext in [".ts", ".tsx", ".js", ".jsx"]
        )

        if py_count > 0:
            # 混合项目：对 .py 文件执行完整 Python 专家审查
            print(f"\n{'='*60}")
            print(f"  混合项目: {py_count} Python + {limited_count} TypeScript/JS 文件")
            print(f"{'='*60}")
            print(f"\n  Python 专家审查: 对 {py_count} 个 .py 文件执行六人专家审查")
            print(f"  TypeScript 审查: DataFlowExpert 对 TS/JS 文件执行数据流检查")
            print(f"  （完整 TS 审查请按 SKILL.md Section A 手动执行）\n")

            # 过滤 source_files 只保留 .py 文件给 Python 专家
            source_files = [f for f in source_files if f.endswith(".py")]
            # 跳过 TS early return，继续下面的 Python 审查流程
        else:
            # 纯 TypeScript 项目
            print(f"\n{'='*60}")
            print(f"  TypeScript/JavaScript 项目检测到")
            print(f"  框架: {context.framework or '未知'}")
            print(f"  技术栈: {', '.join(context.tech_stack) or '未检测到'}")
            print(f"  源文件: {context.total_files} 个 ({context.total_lines} 行)")
            print(f"  审查模式: {mode}")
            print(f"{'='*60}")
            if compatibility.get("warning"):
                print(f"\n  ⚠️  {compatibility['warning']}")
            print(f"\n  ⚡ TypeScript 项目使用 Claude Code 驱动审查")
            print(f"  请按照 SKILL.md 中「Section A: TypeScript/Electron Review」")
            print(f"  的审查流程执行 6 阶段审查。")
            print(f"  审查完成后，将发现保存到 reports/ 目录。\n")
            return {
                "project_type": "typescript",
                "framework": context.framework,
                "total_files": context.total_files,
                "total_lines": context.total_lines,
            }

    # === 以下为 Python 项目流程（不变）===
    if compatibility.get("warning"):
        print(f"\n  ⚠️  {compatibility['warning']}")

    if evolution.baseline:
        print(f"  基线: {evolution.baseline.get('issues_found', 'N/A')} 个问题")
    if prompt_deltas:
        print(f"  Prompt deltas: {len(prompt_deltas)} 个待应用")
    print()

    # 启动指标采集
    collector = MetricsCollector(str(SKILL_DIR))
    collector.start_review(context.project_name, mode=mode)

    # === 外部集成状态 ===
    from integrations.skill_integrator import SkillIntegrator
    integrator = SkillIntegrator()
    integration_status = integrator.get_integration_status()
    available_integrations = [k for k, v in integration_status.items() if v.get("available")]
    if available_integrations:
        print(f"  外部集成: {', '.join(available_integrations)}")
    print()

    # === Phase 1: 并行专家审查 ===
    print("[Phase 1] 六人专家团队并行审查...")

    # 加载经验库（自动注入到专家 prompt）
    exp_collector = BugExperienceCollector(str(SKILL_DIR))
    experience_data = exp_collector.load_experiences(project_dir)
    if experience_data["total_available"] > 0:
        print(f"  经验库: {len(experience_data['universal_cards'])} 通用 + "
              f"{len(experience_data['project_cards'])} 项目特有")

    experts = [
        CodeQualityExpert(context, evolution, prompt_deltas, experience_data),
        ArchitectureExpert(context, evolution, prompt_deltas, experience_data),
        TestingExpert(context, evolution, prompt_deltas, experience_data),
        SecurityExpert(context, evolution, prompt_deltas, experience_data),
        DevOpsExpert(context, evolution, prompt_deltas, experience_data),
        DataFlowExpert(context, evolution, prompt_deltas, experience_data),
    ]

    all_findings_list = []
    for expert in experts:
        print(f"  审查中: {expert.name_cn} ({expert.name})...")
        collector.start_phase(expert.name)
        findings = expert.review(source_files)
        collector.end_phase(expert.name)
        all_findings_list.extend(findings.findings)
        collector.record_expert(expert.name)
        print(f"    发现: {len(findings.findings)} 个问题")

    # 合并和去重
    from core.finding import FindingList
    all_findings = FindingList(all_findings_list)
    all_findings = all_findings.deduplicate()
    all_findings = all_findings.filter_by_anti_patterns(
        [{"category": ap.get("category", ""), "keyword": ap.get("description", "")}
         for ap in evolution.anti_patterns]
    )

    stats = all_findings.statistics()
    print(f"\n  去重后总计: {stats['total']} 个问题")
    print(f"    🔴 Critical: {stats['by_severity'].get('critical', 0)}")
    print(f"    🟠 High: {stats['by_severity'].get('high', 0)}")
    print(f"    🟡 Medium: {stats['by_severity'].get('medium', 0)}")
    print(f"    🟢 Low: {stats['by_severity'].get('low', 0)}")
    print(f"    可操作性: {stats['actionability_score']}%")
    print()

    # === Phase 1.1: 混合项目 TS/JS 数据流审查 ===
    ts_js_files = [f for f in context.source_files if f.endswith((".ts", ".tsx", ".js", ".jsx"))]
    if ts_js_files:
        print(f"[Phase 1.1] 数据流审查 (TS/JS): {len(ts_js_files)} 个文件...")
        try:
            from experts.data_flow_expert import DataFlowExpert as TSDataFlowExpert
            ts_flow_expert = TSDataFlowExpert(context, evolution, prompt_deltas, experience_data)
            ts_findings = ts_flow_expert.review(ts_js_files)
            if ts_findings.findings:
                all_findings_list.extend(ts_findings.findings)
                print(f"    TS/JS 发现: {len(ts_findings.findings)} 个问题")
            else:
                print(f"    TS/JS 发现: 0 个问题")
        except Exception as e:
            print(f"    TS/JS 审查跳过: {e}")

    # === Phase 1.5: 安全阻断检查 ===
    security_blockers = [
        f for f in all_findings.findings
        if f.severity.value == "critical" and f.category.value == "security"
    ]
    key_findings = [
        f for f in all_findings.findings
        if f.category.value == "security" and any(
            kw in f.title.lower() for kw in ["key", "secret", "token", "password", "credential"]
        )
    ]

    if security_blockers or key_findings:
        all_security = security_blockers + key_findings
        print(f"\n{'!'*60}")
        print(f"  🚨 安全阻断: 发现 {len(all_security)} 个安全/密钥问题")
        print(f"{'!'*60}\n")

        # 按文件分组显示
        by_file = {}
        for f in all_security:
            fp = f.file_path or "unknown"
            by_file.setdefault(fp, []).append(f)

        for fp, issues in by_file.items():
            print(f"  📁 {fp}")
            for issue in issues:
                severity_tag = "🔴" if issue.severity.value == "critical" else "🟠"
                print(f"    {severity_tag} [{issue.id}] {issue.title}")
                if issue.fix_suggestion:
                    print(f"       修复: {issue.fix_suggestion}")

        print(f"\n{'!'*60}")
        print(f"  ⚠️  必须先修复以上安全问题，才能继续后续流程。")
        print(f"  Git push 已被自动阻止。")
        print(f"  请手动修复后重新运行审查验证。")
        print(f"{'!'*60}\n")

        # 记录安全阻断状态
        security_report = {
            "blocked": True,
            "blockers": len(all_security),
            "critical": len(security_blockers),
            "key_issues": len(key_findings),
            "details": [f.to_dict() for f in all_security],
        }
        # 保存安全阻断报告
        security_report_path = Path(SKILL_DIR) / "data" / "security_block.json"
        security_report_path.write_text(
            json.dumps(security_report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return {
            "findings_count": stats["total"],
            "security_blocked": True,
            "security_blockers": len(all_security),
            "message": "安全阻断：必须先修复安全问题才能继续",
        }

    # === Phase 1.6: 修复方案数据流安全审查 ===
    print("[Phase 1.6] 修复方案数据流安全审查...")
    critical_high = all_findings.critical_and_high()
    df_risks_found = 0
    for finding in critical_high:
        if not finding.fix_suggestion:
            continue
        fix_text = finding.fix_suggestion.lower()
        risks = []
        if any(kw in fix_text for kw in ["copy", "clone", "slice", "spread", "assign"]):
            risks.append("修复涉及拷贝/赋值 — 验证深浅拷贝正确性")
        if any(kw in fix_text for kw in ["return", "yield", "async"]):
            risks.append("修复改变返回值 — 验证调用方是否正确处理")
        if any(kw in fix_text for kw in ["global", "nonlocal", "class", "self."]):
            risks.append("修复涉及共享状态 — 验证无副作用传播")
        if any(kw in fix_text for kw in ["delete", "remove", "pop", "clear"]):
            risks.append("修复涉及删除操作 — 验证引用方不会访问已删除数据")
        if risks:
            _add_finding_safe(
                all_findings_list, all_findings,
                title=f"数据流风险: {finding.title}",
                severity="medium",
                category="data_flow",
                expert="data_flow_phase1_6",
                file_path=finding.file_path,
                line_range=finding.line_range,
                description="; ".join(risks),
                fix_suggestion="验证修复方案不会引入数据流不一致",
            )
            df_risks_found += 1
    if df_risks_found:
        print(f"  发现 {df_risks_found} 个数据流风险")
    else:
        print(f"  未发现数据流风险")

    # === Phase 1.8: 需求交叉引用 ===
    requirement_context = None
    try:
        from integrations.requirement_trace_bridge import RequirementTraceBridge
        req_bridge = RequirementTraceBridge(project_dir)
        if req_bridge.has_requirements:
            print("[Phase 1.8] 需求交叉引用...")
            findings_dicts = [f.to_dict() for f in all_findings.findings]
            requirement_context = req_bridge.cross_reference(findings_dicts)
            if requirement_context.get("has_requirements"):
                related_count = len(requirement_context.get("related_findings", []))
                print(f"  需求文档: {requirement_context.get('total_requirements', 0)} 个需求项")
                print(f"  相关发现: {related_count} 个")
    except Exception:
        pass  # 需求追踪不可用时静默跳过

    # === Phase 2: 生成报告 ===
    print("[Phase 2] 生成审查报告...")

    # 对比基线
    baseline_mgr = BaselineManager(evolution.baseline)
    baseline_result = baseline_mgr.compare(all_findings)

    # 检测模式
    detector = PatternDetector()
    pattern_result = detector.detect_recurring(all_findings)

    # 记录指标
    collector.record_findings(all_findings, {
        "total_files": context.total_files,
        "total_lines": context.total_lines,
    })
    collector.record_evolution(
        baseline_met=baseline_result["status"] in ("met", "exceeded", "baseline_established"),
        new_patterns=len(pattern_result.get("new_patterns", [])),
    )

    # 生成报告
    reporter = ReportGenerator(str(SKILL_DIR))
    report = reporter.generate(all_findings, context, evolution, baseline_result,
                                 requirement_result=requirement_context)
    print(f"  报告已保存到 reports/ 目录")
    print()

    # === Phase 2.7: 自动改进闭环（仅 --auto-fix 模式） ===
    if auto_fix:
        _run_auto_fix(all_findings, context, project_dir)

    # === Phase 2.5: 反馈收集与反模式校准 ===

    # === Phase 2.5: 反馈收集与反模式校准 ===
    from evolution.feedback_collector import FeedbackCollector
    feedback_collector = FeedbackCollector(str(SKILL_DIR))
    review_id = f"{context.project_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    feedback_prompt = feedback_collector.generate_feedback_prompt(review_id)
    if feedback_prompt:
        print("[Phase 2.5] 审查反馈校准...")
        print(f"  {feedback_prompt}")
        summary = feedback_collector.get_feedback_summary(review_id)
        if summary["false_positive_rate"] > 30:
            print(f"  ⚠️ 误报率 {summary['false_positive_rate']}%，自动添加反模式")
            rejection_reasons = feedback_collector.get_rejection_reasons()
            for reason in rejection_reasons[:5]:
                store.add_anti_pattern(
                    description=reason["reason"],
                    category="auto_feedback",
                    reason=f"用户否决 (finding {reason['finding_id']})",
                )

    # === Phase 3: KPI 计算 ===
    print("[Phase 3] KPI 计算...")
    review_metrics = collector.finish_review()
    kpi_tracker = KPITracker(str(SKILL_DIR))
    kpis = kpi_tracker.calculate_kpis(review_metrics)
    kpi_report = kpi_tracker.generate_kpi_report()
    print(kpi_report)
    print()

    # === Phase 4: 进化更新 ===
    if not no_evolve:
        print("[Phase 4] 进化更新...")

        # 更新基线
        if baseline_mgr.should_update_baseline(baseline_result):
            print(f"  基线更新: {baseline_result['status']}")

        # 内化重复模式
        for pattern in pattern_result.get("recurring_patterns", []):
            store.add_internalized_pattern(
                description=pattern["description"],
                category=pattern["category"],
                occurrence_count=pattern["occurrence_count"],
            )
            print(f"  内化模式: {pattern['description']}")

        # 生成 prompt deltas
        for expert in experts:
            deltas = evolver.generate_deltas(
                findings=all_findings,
                expert_name=expert.name,
                project_name=context.project_name,
            )
            if deltas:
                print(f"  生成 {len(deltas)} 个 prompt delta ({expert.name})")

        # 检查是否需要合并
        if evolver.should_consolidate():
            suggestion = evolver.get_consolidation_suggestion()
            print(f"  ⚠️ 建议合并 prompt deltas 到 SKILL.md")

        # 保存进化状态
        store.update_after_review({
            "total": stats["total"],
            "by_severity": stats["by_severity"],
            "project": context.project_name,
            "duration_seconds": review_metrics.get("duration_seconds", 0),
            "actionability_score": stats["actionability_score"],
            "test_command": "pytest tests/ -v" if context.has_tests else "",
            "framework": context.framework,
        })
        print(f"  进化状态已保存")

        # 收集本次 session 的 bug fix 经验
        print("  收集 bug fix 经验...")
        new_experiences = exp_collector.collect_from_session(project_dir)
        if new_experiences:
            exp_collector.persist(new_experiences, project_dir)
            universal_count = sum(1 for c in new_experiences if c.scope == "universal")
            project_count = sum(1 for c in new_experiences if c.scope == "project")
            print(f"  新增经验: {len(new_experiences)} 条 "
                  f"({universal_count} 通用, {project_count} 项目特有)")
        else:
            print("  未发现新的 bug fix 经验")

        # 审查发现 → bug-retro 四维度经验沉淀（通过共享模块）
        print("  审查发现→经验沉淀...")
        from shared.experience_writer import write_experience_cards
        experience_dicts = exp_collector.findings_to_experience_dicts(
            all_findings.critical_and_high(),
            project_dir,
        )
        if experience_dicts:
            # 1. 持久化到 skill data（跨项目注入）
            exp_collector.persist(
                exp_collector.extract_from_findings(all_findings.critical_and_high(), project_dir),
                project_dir,
            )
            # 2. 写入项目 memory + 更新 MEMORY.md 索引（通过共享模块）
            written_paths = write_experience_cards(experience_dicts, project_dir)
            print(f"  审查发现→经验: {len(experience_dicts)} 条"
                  f"{f' (含 {len(written_paths)} 条写入项目 memory + 索引)' if written_paths else ''}")
        else:
            print("  无 Critical/High 发现需要沉淀")
        print()

    # === 输出报告摘要 ===
    print(f"{'='*60}")
    print(f"  审查完成: {stats['total']} 个问题")
    if baseline_result.get("message"):
        print(f"  基线: {baseline_result['message']}")
    print(f"  详细报告: reports/{Path(reporter.reports_dir).name}/")
    print(f"{'='*60}\n")

    return {
        "findings_count": stats["total"],
        "baseline_result": baseline_result,
        "report_path": str(reporter.reports_dir),
    }


# ============ CLI 命令 ============

def cmd_status(args):
    """查看进化状态和趋势"""
    from evolution.evolution_store import EvolutionStore
    from metrics.metrics_collector import MetricsCollector
    from metrics.kpi_tracker import KPITracker
    from evolution.prompt_evolver import PromptEvolver
    from metrics.metrics_analyzer import MetricsAnalyzer

    store = EvolutionStore(str(SKILL_DIR))
    state = store.load()

    print("=" * 60)
    print(f"  专家复盘 Expert Review v{SKILL_VERSION}")
    print("=" * 60)
    print()

    # 进化状态
    print("## 进化状态")
    print(f"  累计审查: {state.total_reviews} 次")
    print(f"  累计发现: {state.total_issues_found} 个问题")
    print(f"  平均每次: {state.avg_issues_per_review:.1f} 个问题")
    print(f"  上次审查: {state.last_review_date or 'N/A'}")
    print(f"  上次项目: {state.last_review_project or 'N/A'}")
    print()

    # 基线
    print("## 当前基线")
    if state.baseline:
        print(f"  问题数: {state.baseline.get('issues_found', 'N/A')}")
        print(f"  严重度: critical={state.baseline.get('critical', 0)}, "
              f"high={state.baseline.get('high', 0)}, "
              f"medium={state.baseline.get('medium', 0)}, "
              f"low={state.baseline.get('low', 0)}")
        print(f"  可操作性: {state.baseline.get('actionability_score', 'N/A')}%")
    else:
        print("  _尚未建立基线_")
    print()

    # 内化模式
    print(f"## 内化模式: {len(state.internalized_patterns)} 个")
    for p in state.internalized_patterns:
        print(f"  - [{p.get('category', '?')}] {p['description']}")
    if not state.internalized_patterns:
        print("  _暂无_")
    print()

    # 反模式
    print(f"## 反模式: {len(state.anti_patterns)} 个")
    for ap in state.anti_patterns:
        print(f"  - [{ap.get('category', '?')}] {ap['description']}")
    if not state.anti_patterns:
        print("  _暂无_")
    print()

    # Prompt deltas
    evolver = PromptEvolver(str(SKILL_DIR))
    pending = evolver.count_pending()
    print(f"## Prompt Deltas: {pending} 个待应用")
    if pending > 0 and evolver.should_consolidate():
        print("  ⚠️ 已积累足够多 delta，建议合并到 SKILL.md")
    print()

    # KPI
    kpi_tracker = KPITracker(str(SKILL_DIR))
    print(kpi_tracker.generate_kpi_report())
    print()

    # 趋势
    collector = MetricsCollector(str(SKILL_DIR))
    print(collector.generate_trend_summary())
    print()

    # 洞察
    analyzer = MetricsAnalyzer(str(SKILL_DIR))
    insights = analyzer.generate_insights()
    print("## 分析洞察")
    for insight in insights:
        print(f"  {insight}")


def cmd_profile(args):
    """对指定项目生成画像"""
    from core.review_context import ContextProfiler

    project_dir = args.project or "."
    profiler = ContextProfiler(project_dir)
    context = profiler.profile()

    print("=" * 60)
    print(f"  项目画像: {context.project_name}")
    print("=" * 60)
    print()
    print(context.to_prompt_context())


def cmd_baseline(args):
    """管理基线"""
    from evolution.evolution_store import EvolutionStore

    store = EvolutionStore(str(SKILL_DIR))
    state = store.load()

    if args.reset:
        state.baseline = None
        state.total_reviews = 0
        state.total_issues_found = 0
        state.avg_issues_per_review = 0.0
        state.internalized_patterns = []
        state.anti_patterns = []
        store._save(state)
        print("✅ 进化状态已重置。")
    elif args.show:
        if state.baseline:
            print(f"当前基线: {state.baseline['issues_found']} 个问题")
            print(f"  严重度分布: {state.baseline.get('by_severity', {})}")
        else:
            print("尚未建立基线。")


def cmd_feedback(args):
    """记录审查反馈"""
    from evolution.feedback_collector import FeedbackCollector
    collector = FeedbackCollector(str(SKILL_DIR))
    collector.record_feedback(
        review_id=args.review_id,
        finding_id=args.finding_id,
        action=args.action,
        reason=args.reason or "",
    )
    print(f"✅ 反馈已记录: {args.action} for finding {args.finding_id}")


def cmd_review(args):
    """执行审查"""
    run_review(
        project_dir=args.project or ".",
        mode=args.mode or "full",
        focus_areas=args.focus.split(",") if args.focus else None,
        no_evolve=args.no_evolve,
        auto_fix=args.auto_fix,
        plan_only=args.plan_only,
    )


def main():
    parser = argparse.ArgumentParser(
        prog="expert-review",
        description=f"专家复盘 Expert Review v{SKILL_VERSION} — 六人专家团队智能代码审查"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # status
    sub_status = subparsers.add_parser("status", help="查看进化状态和趋势")
    sub_status.set_defaults(func=cmd_status)

    # profile
    sub_profile = subparsers.add_parser("profile", help="对项目生成画像")
    sub_profile.add_argument("project", nargs="?", default=".", help="项目目录路径")
    sub_profile.set_defaults(func=cmd_profile)

    # baseline
    sub_baseline = subparsers.add_parser("baseline", help="管理审查基线")
    sub_baseline.add_argument("--reset", action="store_true", help="重置基线")
    sub_baseline.add_argument("--show", action="store_true", help="显示当前基线")
    sub_baseline.set_defaults(func=cmd_baseline)

    # feedback
    sub_feedback = subparsers.add_parser("feedback", help="记录审查反馈")
    sub_feedback.add_argument("--review-id", required=True, help="审查 ID")
    sub_feedback.add_argument("--finding-id", required=True, help="Finding ID")
    sub_feedback.add_argument("--action", required=True, choices=["confirm", "reject", "wont_fix"], help="反馈动作")
    sub_feedback.add_argument("--reason", default="", help="原因说明")
    sub_feedback.set_defaults(func=cmd_feedback)

    # review
    sub_review = subparsers.add_parser("review", help="执行代码审查")
    sub_review.add_argument("project", nargs="?", default=".", help="项目目录路径")
    sub_review.add_argument("--mode", choices=["full", "incremental", "targeted"], default="full", help="审查模式")
    sub_review.add_argument("--focus", help="重点关注领域（逗号分隔）")
    sub_review.add_argument("--no-evolve", action="store_true", help="跳过进化更新")
    sub_review.add_argument("--auto-fix", action="store_true", help="自动执行改进（审查→修复→验证闭环）")
    sub_review.add_argument("--plan-only", action="store_true", help="只生成改进方案，不执行修复")
    sub_review.set_defaults(func=cmd_review)

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        info = get_skill_info()
        print(f"Skill: {info['name']} v{info['version']}")
        print(f"Description: {info['description']}")
        print(f"Triggers: {', '.join(info['trigger_words'])}")
        print()
        print("Commands:")
        print("  status              查看进化状态和趋势")
        print("  profile <dir>       对项目生成画像")
        print("  feedback            记录审查反馈")
        print("  review <dir>        执行代码审查")
        print("    --mode full|incremental|targeted")
        print("    --focus security,testing")
        print("    --no-evolve        跳过进化更新")
        print("  baseline [--reset|--show]")


if __name__ == "__main__":
    main()
