"""
FeedbackCollector — 审查反馈收集

收集用户对审查结果的确认/否决，用于校准审查质量。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class FeedbackCollector:
    """审查反馈收集器"""

    def __init__(self, skill_dir: str = None):
        if skill_dir:
            self.feedback_dir = Path(skill_dir) / "data" / "feedback"
        else:
            self.feedback_dir = Path(__file__).parent.parent / "data" / "feedback"
        self.feedback_dir.mkdir(parents=True, exist_ok=True)

    def record_feedback(
        self,
        review_id: str,
        finding_id: str,
        action: str,  # "confirm" | "reject" | "wont_fix"
        reason: str = "",
    ):
        """记录单个发现的反馈"""
        entry = {
            "review_id": review_id,
            "finding_id": finding_id,
            "action": action,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        }

        filepath = self.feedback_dir / f"{review_id}.json"
        existing = []

        if filepath.exists():
            try:
                existing = json.loads(filepath.read_text(encoding="utf-8"))
            except Exception:
                existing = []

        existing.append(entry)
        filepath.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_feedback_summary(self, review_id: str) -> Dict:
        """获取某次审查的反馈摘要"""
        filepath = self.feedback_dir / f"{review_id}.json"
        if not filepath.exists():
            return {"total": 0}

        try:
            entries = json.loads(filepath.read_text(encoding="utf-8"))
        except Exception:
            return {"total": 0}

        confirmed = sum(1 for e in entries if e["action"] == "confirm")
        rejected = sum(1 for e in entries if e["action"] == "reject")
        wont_fix = sum(1 for e in entries if e["action"] == "wont_fix")

        return {
            "total": len(entries),
            "confirmed": confirmed,
            "rejected": rejected,
            "wont_fix": wont_fix,
            "false_positive_rate": round(rejected / max(len(entries), 1) * 100, 1),
        }

    def get_rejection_reasons(self) -> List[Dict]:
        """获取所有被否决的原因（用于改进）"""
        reasons = []
        for f in sorted(self.feedback_dir.glob("*.json")):
            try:
                entries = json.loads(f.read_text(encoding="utf-8"))
                for e in entries:
                    if e["action"] == "reject" and e.get("reason"):
                        reasons.append({
                            "finding_id": e["finding_id"],
                            "reason": e["reason"],
                            "review_id": e["review_id"],
                        })
            except Exception:
                continue
        return reasons

    def generate_feedback_prompt(self, review_id: str) -> str:
        """生成反馈收集 prompt（用于审查后询问用户）"""
        summary = self.get_feedback_summary(review_id)
        if summary["total"] == 0:
            return ""

        return (
            f"审查反馈摘要:\n"
            f"- 确认有效: {summary['confirmed']}\n"
            f"- 误报否决: {summary['rejected']}\n"
            f"- 暂不修复: {summary['wont_fix']}\n"
            f"- 误报率: {summary['false_positive_rate']}%\n"
        )
