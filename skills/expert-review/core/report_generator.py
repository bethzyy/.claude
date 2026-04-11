"""
ReportGenerator — 审查报告生成器

生成结构化的 Markdown 审查报告。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

from core._paths import SKILL_DIR, ensure_skill_path
ensure_skill_path()

from core.finding import FindingList, Severity
from core.review_context import ReviewContext
from evolution.evolution_store import EvolutionState


class ReportGenerator:
    """审查报告生成器"""

    SEVERITY_EMOJI = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }

    def __init__(self, skill_dir: str = None):
        if skill_dir:
            self.reports_dir = Path(skill_dir) / "reports"
        else:
            self.reports_dir = Path(__file__).parent.parent / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        findings: FindingList,
        context: ReviewContext,
        evolution: Optional[EvolutionState] = None,
        baseline_result: Optional[Dict] = None,
        regression_result: Optional[Dict] = None,
    ) -> str:
        """生成完整审查报告"""
        parts = []

        # Header
        parts.append(f"# 专家复盘报告 v2.0")
        parts.append(f"")
        parts.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
        parts.append(f"")

        # 项目概况
        parts.append("## 项目概况")
        parts.append(f"- 项目: **{context.project_name}**")
        parts.append(f"- 技术栈: {', '.join(context.tech_stack) or '未检测到'}")
        parts.append(f"- 框架: {context.framework or '未检测到'}")
        parts.append(f"- 审查范围: {context.total_files} 个源文件, {context.total_lines} 行代码")
        parts.append(f"- Git: {'是 (' + context.git_branch + ')' if context.is_git_repo else '否'}")
        if context.has_tests:
            parts.append(f"- 测试: {len(context.test_files)} 个测试文件")
        else:
            parts.append(f"- 测试: **无**")
        parts.append("")

        # 进化状态
        if evolution:
            parts.append("## 进化状态")
            if baseline_result:
                status_emoji = {
                    "exceeded": "📈 超出基线",
                    "met": "✅ 达到基线",
                    "below": "⚠️ 低于基线",
                    "baseline_established": "🆕 建立基线",
                }
                parts.append(f"- 基线状态: {status_emoji.get(baseline_result.get('status', ''), baseline_result.get('status', ''))}")
                if baseline_result.get("message"):
                    parts.append(f"- 详情: {baseline_result['message']}")
            parts.append(f"- 累计审查: {evolution.total_reviews} 次")
            parts.append(f"- 内化检查项: {len(evolution.internalized_patterns)} 个")
            parts.append(f"- 已知反模式: {len(evolution.anti_patterns)} 个")
            parts.append("")

        # 发现问题汇总
        stats = findings.statistics()
        parts.append("## 发现问题汇总")
        parts.append(f"")
        parts.append(f"**总计: {stats['total']} 个问题** | "
                     f"🔴 Critical: {stats['by_severity'].get('critical', 0)} | "
                     f"🟠 High: {stats['by_severity'].get('high', 0)} | "
                     f"🟡 Medium: {stats['by_severity'].get('medium', 0)} | "
                     f"🟢 Low: {stats['by_severity'].get('low', 0)}")
        parts.append(f"")
        parts.append(f"可操作性: {stats['actionability_score']}%")

        # 按严重度分组的问题列表
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            severity_findings = findings.by_severity(severity)
            if not severity_findings:
                continue

            parts.append(f"")
            parts.append(f"### {self.SEVERITY_EMOJI[severity.value]} {severity.value.upper()} ({len(severity_findings)})")
            parts.append(f"")

            for i, f in enumerate(severity_findings, 1):
                parts.append(f"**{f.id}**: {f.title}")
                if f.file_path:
                    parts.append(f"- 文件: `{f.file_path}`" + (f":{f.line_range}" if f.line_range else ""))
                if f.expert:
                    parts.append(f"- 专家: {f.expert}")
                if f.fix_suggestion:
                    parts.append(f"- 修复: {f.fix_suggestion}")
                if f.code_snippet:
                    parts.append(f"- 代码: `{f.code_snippet[:80]}`")
                if f.is_new_pattern:
                    parts.append(f"- 🆕 **新发现模式**")
                parts.append("")

        # 按专家统计
        parts.append("### 按专家分布")
        for expert, count in stats.get("by_expert", {}).items():
            parts.append(f"- {expert}: {count} 个问题")
        parts.append("")

        # 回归测试结果
        if regression_result:
            parts.append("## 回归测试结果")
            parts.append(f"- 总数: {regression_result.get('total', 'N/A')}")
            parts.append(f"- 通过: {regression_result.get('passed', 'N/A')}")
            parts.append(f"- 失败: {regression_result.get('failed', 'N/A')}")
            parts.append(f"- 通过率: {regression_result.get('pass_rate', 'N/A')}%")
            parts.append("")

        # 进化更新建议
        if evolution and baseline_result:
            parts.append("## 进化更新")
            if baseline_result.get("status") == "exceeded":
                parts.append("- 基线已更新（超出上次）")
            elif baseline_result.get("status") == "met":
                parts.append("- 基线保持不变（达到标准）")
            elif baseline_result.get("status") == "below":
                parts.append("- ⚠️ 基线保持不变（未达到标准，不降低）")
            parts.append("")

        report = "\n".join(parts)

        # 保存报告
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        filename = f"{timestamp}-{context.project_name}.md"
        filepath = self.reports_dir / filename
        filepath.write_text(report, encoding="utf-8")

        return report

    def generate_json_report(
        self,
        findings: FindingList,
        context: ReviewContext,
        extra: Dict = None,
    ) -> str:
        """生成 JSON 格式报告"""
        data = {
            "report_version": "2.0",
            "generated_at": datetime.now().isoformat(),
            "project": context.project_name,
            "context": {
                "tech_stack": context.tech_stack,
                "framework": context.framework,
                "total_files": context.total_files,
                "total_lines": context.total_lines,
                "has_tests": context.has_tests,
                "test_files_count": len(context.test_files),
            },
            "findings": {
                "total": len(findings.findings),
                "statistics": findings.statistics(),
                "items": [f.to_dict() for f in findings.findings],
            },
        }
        if extra:
            data.update(extra)

        return json.dumps(data, ensure_ascii=False, indent=2)
