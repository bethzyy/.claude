"""
PatternDetector — 跨审查模式检测

检测跨多次审查的重复模式，支持内化建议。
"""

from collections import Counter
from typing import List, Dict, Optional, Tuple

from core._paths import ensure_skill_path
ensure_skill_path()

from core.finding import Finding, FindingList


class PatternDetector:
    """跨审查模式检测器"""

    def __init__(self, internalize_threshold: int = 3):
        self.internalize_threshold = internalize_threshold

    def detect_recurring(
        self,
        current_findings: FindingList,
        historical_findings: List[Finding] = None,
    ) -> Dict:
        """
        检测重复出现的模式。

        Returns:
            {
                "recurring_patterns": [...],  # 可内化的模式
                "new_patterns": [...],        # 首次出现的模式
                "category_distribution": {...}, # 类别分布变化
            }
        """
        historical = historical_findings or []
        all_findings = historical + current_findings.findings

        # 按 category + title 关键词聚合
        pattern_counter = Counter()
        current_patterns = set()
        historical_pattern_set = set()

        # 标记历史模式
        for f in historical:
            key = self._pattern_key(f)
            pattern_counter[key] += 1
            historical_pattern_set.add(key)

        # 标记当前模式
        for f in current_findings.findings:
            key = self._pattern_key(f)
            pattern_counter[key] += 1
            current_patterns.add(key)

            # 新模式
            if key not in historical_pattern_set:
                f.is_new_pattern = True

        # 超过阈值的模式 → 可内化
        recurring = []
        for (category, title_prefix), count in pattern_counter.items():
            if count >= self.internalize_threshold:
                recurring.append({
                    "category": category,
                    "description": f"检查 {category} 类问题: {title_prefix}",
                    "occurrence_count": count,
                    "confidence": min(count / self.internalize_threshold, 1.0),
                })

        # 新模式
        new_patterns = []
        for f in current_findings.findings:
            if f.is_new_pattern:
                new_patterns.append({
                    "id": f.id,
                    "category": f.category.value,
                    "title": f.title,
                })

        # 类别分布
        cat_dist = Counter()
        for f in current_findings.findings:
            cat_dist[f.category.value] += 1

        return {
            "recurring_patterns": recurring,
            "new_patterns": new_patterns,
            "category_distribution": dict(cat_dist),
            "total_patterns": len(pattern_counter),
            "unique_in_session": len(current_patterns),
        }

    def analyze_expert_effectiveness(
        self,
        findings: FindingList,
    ) -> Dict[str, Dict]:
        """
        分析各专家的有效性。

        Returns:
            {expert_name: {"count": N, "severity_avg": X, "actionable_pct": Y}}
        """
        expert_stats: Dict[str, Dict] = {}

        for f in findings.findings:
            if f.expert not in expert_stats:
                expert_stats[f.expert] = {
                    "count": 0,
                    "critical": 0,
                    "high": 0,
                    "actionable": 0,
                }
            expert_stats[f.expert]["count"] += 1
            if f.severity.value in ("critical", "high"):
                expert_stats[f.expert][f.severity.value] += 1
            if f.fix_suggestion:
                expert_stats[f.expert]["actionable"] += 1

        # 计算百分比
        for name, stats in expert_stats.items():
            stats["actionable_pct"] = round(
                stats["actionable"] / max(stats["count"], 1) * 100, 1
            )

        return expert_stats

    def detect_quality_drift(
        self,
        current_stats: Dict,
        historical_stats: List[Dict],
    ) -> Dict:
        """
        检测审查质量漂移（发现数突然下降或上升）。

        Returns:
            {"drift_detected": bool, "direction": "up"/"down"/"stable", "details": str}
        """
        if len(historical_stats) < 2:
            return {"drift_detected": False, "direction": "stable", "details": "数据不足"}

        recent_counts = [s.get("total", 0) for s in historical_stats[-5:]]
        current_count = current_stats.get("total", 0)

        if len(recent_counts) >= 2:
            avg_recent = sum(recent_counts) / len(recent_counts)
            if current_count < avg_recent * 0.5:
                return {
                    "drift_detected": True,
                    "direction": "down",
                    "details": f"当前发现数 ({current_count}) 显著低于近期平均 ({avg_recent:.1f})",
                }
            elif current_count > avg_recent * 1.5:
                return {
                    "drift_detected": True,
                    "direction": "up",
                    "details": f"当前发现数 ({current_count}) 显著高于近期平均 ({avg_recent:.1f})",
                }

        return {"drift_detected": False, "direction": "stable", "details": "正常范围"}

    def _pattern_key(self, finding: Finding) -> Tuple[str, str]:
        """生成模式 key（用于去重和计数）"""
        return (finding.category.value, finding.title[:30])
