"""
MetricsCollector — 审查指标采集

采集每次审查的关键指标，持久化为 JSON，支持趋势分析。
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

from core._paths import SKILL_DIR, ensure_skill_path
ensure_skill_path()

from core.finding import FindingList


class MetricsCollector:
    """审查指标采集器"""

    def __init__(self, skill_dir: str = None):
        if skill_dir:
            self.metrics_dir = Path(skill_dir) / "data" / "metrics"
        else:
            self.metrics_dir = Path(__file__).parent.parent / "data" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        self._start_time: Optional[float] = None
        self._phase_timings: Dict[str, float] = {}

    def start_review(self, project: str, mode: str = "full"):
        """审查开始时调用"""
        self._start_time = time.time()
        self._current = {
            "review_id": f"review-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "project": project,
            "review_mode": mode,
            "experts_used": [],
            "phase_timings": {},
        }

    def start_phase(self, phase_name: str):
        """阶段开始"""
        self._phase_timings[phase_name] = time.time()

    def end_phase(self, phase_name: str):
        """阶段结束"""
        if phase_name in self._phase_timings:
            elapsed = time.time() - self._phase_timings[phase_name]
            self._current["phase_timings"][phase_name] = round(elapsed, 1)

    def record_findings(self, findings: FindingList, context_info: Dict = None):
        """记录审查发现"""
        stats = findings.statistics()
        self._current.update({
            "files_scanned": context_info.get("total_files", 0) if context_info else 0,
            "lines_of_code": context_info.get("total_lines", 0) if context_info else 0,
            "findings": {
                "total": stats["total"],
                "by_severity": stats["by_severity"],
                "by_category": stats["by_category"],
                "by_expert": stats["by_expert"],
            },
            "actionability": {
                "actionable": stats["actionable"],
                "actionability_score": stats["actionability_score"],
            },
            "new_patterns": stats["new_patterns"],
        })

    def record_expert(self, expert_name: str):
        """记录使用的专家"""
        if "experts_used" not in self._current:
            self._current["experts_used"] = []
        if expert_name not in self._current["experts_used"]:
            self._current["experts_used"].append(expert_name)

    def record_evolution(self, baseline_met: bool, new_patterns: int = 0, anti_patterns_triggered: int = 0):
        """记录进化相关指标"""
        self._current["evolution"] = {
            "baseline_met": baseline_met,
            "new_patterns_found": new_patterns,
            "anti_patterns_triggered": anti_patterns_triggered,
        }

    def record_regression(self, total: int, passed: int, failed: int):
        """记录回归测试结果"""
        self._current["regression"] = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / max(total, 1) * 100, 1),
        }

    def finish_review(self) -> Dict:
        """审查结束，保存指标"""
        if self._start_time:
            self._current["duration_seconds"] = round(time.time() - self._start_time, 1)

        # 保存到文件
        filename = f"{self._current['review_id']}.json"
        filepath = self.metrics_dir / filename
        filepath.write_text(json.dumps(self._current, ensure_ascii=False, indent=2), encoding="utf-8")

        # 更新聚合文件
        self._update_aggregated()

        return self._current

    def _update_aggregated(self):
        """更新聚合指标文件"""
        all_metrics = self.load_all()
        if not all_metrics:
            return

        aggregated = {
            "total_reviews": len(all_metrics),
            "projects_reviewed": list(set(m["project"] for m in all_metrics)),
            "total_issues_found": sum(m["findings"]["total"] for m in all_metrics if "findings" in m),
            "avg_issues_per_review": round(
                sum(m["findings"]["total"] for m in all_metrics if "findings" in m)
                / max(len(all_metrics), 1), 1
            ),
            "avg_duration": round(
                sum(m.get("duration_seconds", 0) for m in all_metrics)
                / max(len(all_metrics), 1), 1
            ),
            "latest_reviews": all_metrics[-10:],  # 最近10次
        }

        filepath = self.metrics_dir / "aggregated.json"
        filepath.write_text(json.dumps(aggregated, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_all(self) -> List[Dict]:
        """加载所有历史指标"""
        metrics = []
        for f in sorted(self.metrics_dir.glob("review-*.json")):
            try:
                metrics.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                continue
        return metrics

    def load_project(self, project: str) -> List[Dict]:
        """加载特定项目的历史指标"""
        return [m for m in self.load_all() if m.get("project") == project]

    def get_latest(self) -> Optional[Dict]:
        """获取最近一次审查指标"""
        all_metrics = self.load_all()
        return all_metrics[-1] if all_metrics else None

    def generate_trend_summary(self) -> str:
        """生成趋势摘要文本"""
        all_metrics = self.load_all()
        if not all_metrics:
            return "暂无历史审查数据。"

        lines = ["## 审查趋势摘要", ""]

        # 基本统计
        total_reviews = len(all_metrics)
        total_issues = sum(m["findings"]["total"] for m in all_metrics if "findings" in m)
        lines.append(f"- 累计审查: {total_reviews} 次")
        lines.append(f"- 累计发现: {total_issues} 个问题")
        lines.append(f"- 平均每次: {total_issues / max(total_reviews, 1):.1f} 个问题")

        # 最近趋势（最近5次）
        recent = all_metrics[-5:]
        if len(recent) >= 2:
            recent_counts = [m["findings"]["total"] for m in recent if "findings" in m]
            if recent_counts:
                trend = "↑" if recent_counts[-1] > recent_counts[0] else "↓" if recent_counts[-1] < recent_counts[0] else "→"
                lines.append(f"- 近期趋势: {trend} ({recent_counts[0]} → {recent_counts[-1]})")

        # 按项目分组
        projects = {}
        for m in all_metrics:
            proj = m.get("project", "unknown")
            projects[proj] = projects.get(proj, 0) + 1
        lines.append("")
        lines.append("### 按项目分布")
        for proj, count in sorted(projects.items(), key=lambda x: -x[1]):
            lines.append(f"- {proj}: {count} 次审查")

        return "\n".join(lines)
