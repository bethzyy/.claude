"""
BaselineManager — 基线追踪

管理审查基线，确保审查质量只能升不能降。
"""

from typing import Dict, Optional, List
from collections import Counter

from core._paths import ensure_skill_path
ensure_skill_path()

from core.finding import Finding, FindingList


class BaselineManager:
    """基线管理 — 追踪审查质量趋势"""

    def __init__(self, current_baseline: Optional[Dict] = None):
        self.current_baseline = current_baseline

    def compare(self, new_findings: FindingList) -> Dict:
        """对比新审查结果与基线"""
        stats = new_findings.statistics()

        if not self.current_baseline:
            return {
                "status": "baseline_established",
                "message": "首次审查，建立基线",
                "baseline": self._extract_baseline(stats),
                "comparison": None,
            }

        old_count = self.current_baseline.get("issues_found", 0)
        new_count = stats["total"]

        result = {
            "status": "met",
            "baseline": self.current_baseline,
            "new_stats": stats,
            "comparison": {
                "issues_found": {"old": old_count, "new": new_count, "delta": new_count - old_count},
                "actionability": {
                    "old": self.current_baseline.get("actionability_score", 0),
                    "new": stats["actionability_score"],
                },
            },
        }

        if new_count > old_count:
            result["status"] = "exceeded"
            result["message"] = f"超出基线！发现 {new_count} 个问题（基线 {old_count}），+{new_count - old_count}"
        elif new_count == old_count:
            result["message"] = f"达到基线。发现 {new_count} 个问题（基线 {old_count}）"
        else:
            result["status"] = "below"
            result["message"] = f"⚠️ 低于基线！发现 {new_count} 个问题（基线 {old_count}），-{old_count - new_count}"

        return result

    def _extract_baseline(self, stats: Dict) -> Dict:
        """从审查统计中提取基线"""
        return {
            "issues_found": stats["total"],
            "by_severity": stats.get("by_severity", {}),
            "actionability_score": stats.get("actionability_score", 0),
        }

    def should_update_baseline(self, comparison_result: Dict) -> bool:
        """判断是否应该更新基线"""
        status = comparison_result.get("status", "")
        return status in ("baseline_established", "exceeded")

    def detect_recurring_patterns(
        self,
        current_findings: FindingList,
        historical_findings: List[Finding],
        threshold: int = 3
    ) -> List[Dict]:
        """检测重复出现的模式（跨多次审查）

        Returns:
            超过阈值的模式列表，适合升级为内化模式
        """
        # 按类别+标题关键词聚合
        pattern_counter = Counter()

        for finding in historical_findings + current_findings.findings:
            # 用 category + title 的前10个字符作为模式 key
            key = (finding.category.value, finding.title[:30])
            pattern_counter[key] += 1

        recurring = []
        for (category, title_prefix), count in pattern_counter.items():
            if count >= threshold:
                recurring.append({
                    "category": category,
                    "description": f"检查 {category} 类问题: {title_prefix}",
                    "occurrence_count": count,
                })

        return recurring

    def generate_improvement_suggestions(self, findings: FindingList) -> List[Dict]:
        """基于审查结果生成改进建议

        分析哪些类型的检查最有价值，哪些可能需要加强。
        """
        stats = findings.statistics()
        suggestions = []

        # 1. 如果某个严重度级别为空，建议加强
        severity_map = {"critical": "安全/崩溃风险", "high": "功能缺陷", "medium": "代码质量", "low": "代码风格"}
        for sev, label in severity_map.items():
            if stats["by_severity"].get(sev, 0) == 0:
                suggestions.append({
                    "type": "coverage_gap",
                    "severity": sev,
                    "message": f"未发现 {sev} ({label}) 级别问题，建议加强此类检查",
                })

        # 2. 如果某个专家发现问题很少，建议调整
        for expert, count in stats.get("by_expert", {}).items():
            if count < 2:
                suggestions.append({
                    "type": "expert_underperformance",
                    "expert": expert,
                    "message": f"专家 {expert} 仅发现 {count} 个问题，可能需要调整检查策略",
                })

        # 3. 可操作性分数低时建议改进
        if stats["actionability_score"] < 70:
            suggestions.append({
                "type": "actionability",
                "message": f"可操作性分数 {stats['actionability_score']}% < 70%，建议为更多发现提供修复建议",
            })

        return suggestions
