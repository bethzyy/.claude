"""
KPITracker — KPI 追踪

追踪审查质量的关键性能指标。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from core._paths import SKILL_DIR, ensure_skill_path
ensure_skill_path()

from metrics.metrics_collector import MetricsCollector


class KPITracker:
    """KPI 追踪器"""

    # KPI 定义
    KPI_DEFS = {
        "issues_per_file": {
            "name": "问题发现率",
            "description": "发现问题数 / 审查文件数",
            "target": "> 0.5/文件",
            "direction": "higher_is_better",
        },
        "actionability_score": {
            "name": "可操作性",
            "description": "有修复建议的问题占比",
            "target": "> 80%",
            "direction": "higher_is_better",
        },
        "false_positive_rate": {
            "name": "误报率",
            "description": "被否决的问题占比",
            "target": "< 15%",
            "direction": "lower_is_better",
        },
        "baseline_trend": {
            "name": "基线趋势",
            "description": "近5次审查移动平均",
            "target": "先升后稳",
            "direction": "stable_target",
        },
        "new_pattern_rate": {
            "name": "新模式发现率",
            "description": "首次出现的类别占比",
            "target": "> 10%",
            "direction": "higher_is_better",
        },
    }

    def __init__(self, skill_dir: str = None):
        self.collector = MetricsCollector(skill_dir)

    def calculate_kpis(self, review_metrics: Dict) -> Dict:
        """计算单次审查的 KPI"""
        kpis = {}

        findings = review_metrics.get("findings", {})
        total_issues = findings.get("total", 0)
        files_scanned = review_metrics.get("files_scanned", 1)

        # 1. 问题发现率
        issues_per_file = total_issues / max(files_scanned, 1)
        kpis["issues_per_file"] = {
            "value": round(issues_per_file, 2),
            "target": 0.5,
            "met": issues_per_file >= 0.5,
        }

        # 2. 可操作性
        actionability = review_metrics.get("actionability", {})
        score = actionability.get("actionability_score", 0)
        kpis["actionability_score"] = {
            "value": score,
            "target": 80,
            "met": score >= 80,
        }

        # 3. 新模式发现率
        new_patterns = review_metrics.get("new_patterns", 0)
        new_rate = new_patterns / max(total_issues, 1) * 100
        kpis["new_pattern_rate"] = {
            "value": round(new_rate, 1),
            "target": 10,
            "met": new_rate >= 10,
        }

        # 4. 审查效率（问题数/分钟）
        duration = review_metrics.get("duration_seconds", 0)
        if duration > 0:
            issues_per_min = total_issues / (duration / 60)
            kpis["issues_per_minute"] = {
                "value": round(issues_per_min, 2),
                "target": 1.0,
                "met": issues_per_min >= 1.0,
            }

        return kpis

    def calculate_trend_kpis(self) -> Dict:
        """计算趋势 KPI"""
        all_metrics = self.collector.load_all()
        if len(all_metrics) < 2:
            return {"trend": "insufficient_data"}

        recent = all_metrics[-5:]
        recent_counts = [m["findings"]["total"] for m in recent if "findings" in m]

        if len(recent_counts) < 2:
            return {"trend": "insufficient_data"}

        # 移动平均
        moving_avg = sum(recent_counts) / len(recent_counts)

        # 趋势方向
        if recent_counts[-1] > recent_counts[0] * 1.2:
            direction = "improving"
        elif recent_counts[-1] < recent_counts[0] * 0.8:
            direction = "declining"
        else:
            direction = "stable"

        return {
            "trend": direction,
            "moving_average": round(moving_avg, 1),
            "recent_counts": recent_counts,
            "direction": direction,
        }

    def generate_kpi_report(self) -> str:
        """生成 KPI 报告"""
        lines = ["## KPI Dashboard", ""]

        # 最新一次审查的 KPI
        latest = self.collector.get_latest()
        if latest:
            kpis = self.calculate_kpis(latest)
            lines.append("### Latest Review KPIs")
            for kpi_name, kpi_data in kpis.items():
                kpi_def = self.KPI_DEFS.get(kpi_name, {})
                status = "✅" if kpi_data.get("met") else "❌"
                lines.append(
                    f"- {status} **{kpi_def.get('name', kpi_name)}**: "
                    f"{kpi_data['value']} (target: {kpi_def.get('target', 'N/A')})"
                )
            lines.append("")

        # 趋势
        trend = self.calculate_trend_kpis()
        lines.append("### Trend Analysis")
        direction_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️", "insufficient_data": "❓"}
        lines.append(f"- Direction: {direction_emoji.get(trend.get('direction', ''), '')} {trend.get('direction', trend.get('trend', 'N/A'))}")

        if trend.get("moving_average"):
            lines.append(f"- Moving Average (5 reviews): {trend['moving_average']} issues")

        return "\n".join(lines)
