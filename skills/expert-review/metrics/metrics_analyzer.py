"""
MetricsAnalyzer — 趋势分析器

分析审查指标趋势，生成洞察。
"""

import json
from typing import Dict, List, Optional

from core._paths import ensure_skill_path
ensure_skill_path()

from metrics.metrics_collector import MetricsCollector


class MetricsAnalyzer:
    """审查指标趋势分析器"""

    def __init__(self, skill_dir: str = None):
        self.collector = MetricsCollector(skill_dir)

    def analyze_project(self, project: str) -> Dict:
        """分析单个项目的审查趋势"""
        metrics = self.collector.load_project(project)
        if not metrics:
            return {"error": f"No reviews found for project '{project}'"}

        counts = [m["findings"]["total"] for m in metrics if "findings" in m]
        severities_over_time = []
        durations = []

        for m in metrics:
            if "findings" in m:
                severities_over_time.append(m["findings"].get("by_severity", {}))
            if "duration_seconds" in m:
                durations.append(m["duration_seconds"])

        # 趋势计算
        trend = "stable"
        if len(counts) >= 2:
            if counts[-1] > counts[0] * 1.2:
                trend = "improving"
            elif counts[-1] < counts[0] * 0.8:
                trend = "declining"

        # 严重度趋势
        severity_trends = {}
        for sev in ["critical", "high", "medium", "low"]:
            sev_counts = [s.get(sev, 0) for s in severities_over_time]
            if sev_counts:
                severity_trends[sev] = {
                    "latest": sev_counts[-1],
                    "average": round(sum(sev_counts) / len(sev_counts), 1),
                    "trend": "up" if len(sev_counts) >= 2 and sev_counts[-1] > sev_counts[0] else "down" if len(sev_counts) >= 2 and sev_counts[-1] < sev_counts[0] else "stable",
                }

        return {
            "project": project,
            "total_reviews": len(metrics),
            "total_issues": sum(counts),
            "average_issues": round(sum(counts) / max(len(counts), 1), 1),
            "trend": trend,
            "severity_trends": severity_trends,
            "average_duration": round(sum(durations) / max(len(durations), 1), 1) if durations else 0,
        }

    def compare_projects(self) -> Dict:
        """跨项目对比"""
        all_metrics = self.collector.load_all()
        if not all_metrics:
            return {"error": "No reviews found"}

        projects = {}
        for m in all_metrics:
            proj = m.get("project", "unknown")
            if proj not in projects:
                projects[proj] = {"reviews": 0, "issues": 0, "files": 0}
            projects[proj]["reviews"] += 1
            if "findings" in m:
                projects[proj]["issues"] += m["findings"]["total"]
            projects[proj]["files"] += m.get("files_scanned", 0)

        # 计算指标
        comparison = {}
        for proj, data in projects.items():
            comparison[proj] = {
                "reviews": data["reviews"],
                "total_issues": data["issues"],
                "avg_issues": round(data["issues"] / max(data["reviews"], 1), 1),
                "issue_density": round(data["issues"] / max(data["files"], 1), 3),
            }

        # 排序
        sorted_proj = sorted(comparison.items(), key=lambda x: x[1]["issue_density"], reverse=True)

        return {
            "total_projects": len(comparison),
            "ranking": [
                {"project": p, **d} for p, d in sorted_proj
            ],
        }

    def generate_insights(self) -> List[str]:
        """生成分析洞察"""
        all_metrics = self.collector.load_all()
        if not all_metrics:
            return ["暂无审查数据"]

        insights = []

        # 1. 总体趋势
        if len(all_metrics) >= 3:
            recent = all_metrics[-3:]
            early = all_metrics[:3]
            recent_avg = sum(m["findings"]["total"] for m in recent if "findings" in m) / len(recent)
            early_avg = sum(m["findings"]["total"] for m in early if "findings" in m) / len(early)

            if recent_avg > early_avg * 1.2:
                insights.append(f"📈 审查深度提升：近期平均发现 {recent_avg:.1f} 个问题 vs 早期 {early_avg:.1f}")
            elif recent_avg < early_avg * 0.8:
                insights.append(f"📉 审查深度下降：近期平均发现 {recent_avg:.1f} 个问题 vs 早期 {early_avg:.1f}")

        # 2. 最常见的问题类别
        all_categories = {}
        for m in all_metrics:
            for cat, count in m.get("findings", {}).get("by_category", {}).items():
                all_categories[cat] = all_categories.get(cat, 0) + count

        if all_categories:
            top_cat = max(all_categories.items(), key=lambda x: x[1])
            insights.append(f"🎯 最常见问题类别: {top_cat[0]} ({top_cat[1]} 次)")

        # 3. 项目健康度
        comparison = self.compare_projects()
        if "ranking" in comparison:
            for item in comparison["ranking"][:3]:
                density = item.get("issue_density", 0)
                if density > 0.5:
                    insights.append(f"⚠️ {item['project']} 问题密度较高 ({density}/文件)")

        if not insights:
            insights.append("审查数据正常，未发现异常趋势")

        return insights
