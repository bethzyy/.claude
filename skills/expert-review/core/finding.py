"""
Finding 数据模型 — 审查发现的问题

每个 Finding 代表审查中发现的一个问题，包含分类、严重度、修复建议等。
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, List
import uuid
import json


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def rank(self) -> int:
        return {"critical": 0, "high": 1, "medium": 2, "low": 3}[self.value]


class Category(Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    RELIABILITY = "reliability"
    STYLE = "style"
    DATA_FLOW = "data_flow"          # 跨模块数据流问题（状态不同步、引用断裂）
    BEHAVIORAL = "behavioral"         # 行为正确性（逻辑与预期不符）


class FindingStatus(Enum):
    OPEN = "open"
    FIXED = "fixed"
    FALSE_POSITIVE = "false_positive"
    WONT_FIX = "wont_fix"


@dataclass
class Finding:
    """审查发现的问题"""

    # 基本信息
    id: str = field(default_factory=lambda: f"FND-{uuid.uuid4().hex[:6].upper()}")
    severity: Severity = Severity.MEDIUM
    category: Category = Category.MAINTAINABILITY
    expert: str = ""  # 哪个专家发现的

    # 描述
    title: str = ""
    description: str = ""

    # 位置
    file_path: str = ""
    line_range: Optional[str] = None
    code_snippet: Optional[str] = None

    # 修复建议
    fix_suggestion: Optional[str] = None
    fix_code_example: Optional[str] = None
    effort: Optional[str] = None  # small / medium / large

    # 引用
    references: List[str] = field(default_factory=list)

    # 状态追踪
    status: FindingStatus = FindingStatus.OPEN
    resolution: Optional[str] = None
    resolved_at: Optional[str] = None

    # 进化追踪
    is_new_pattern: bool = False  # 首次出现的模式
    pattern_occurrence_count: int = 1  # 该模式出现次数
    was_suppressed_by_anti_pattern: bool = False  # 是否被反模式抑制

    # 时间
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value
        d["category"] = self.category.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Finding":
        d = d.copy()
        d["severity"] = Severity(d.get("severity", "medium"))
        d["category"] = Category(d.get("category", "maintainability"))
        d["status"] = FindingStatus(d.get("status", "open"))
        return cls(**d)

    def __str__(self) -> str:
        emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        return f"{emoji.get(self.severity.value, '⚪')} [{self.severity.value.upper()}] {self.id}: {self.title}"


class FindingList:
    """Finding 集合，提供筛选和统计"""

    def __init__(self, findings: List[Finding] = None):
        self.findings = findings or []

    def add(self, finding: Finding):
        self.findings.append(finding)

    def by_severity(self, severity: Severity) -> List[Finding]:
        return [f for f in self.findings if f.severity == severity]

    def by_category(self, category: Category) -> List[Finding]:
        return [f for f in self.findings if f.category == category]

    def by_expert(self, expert: str) -> List[Finding]:
        return [f for f in self.findings if f.expert == expert]

    def critical_and_high(self) -> List[Finding]:
        return [f for f in self.findings if f.severity.rank <= Severity.HIGH.rank]

    def open_items(self) -> List[Finding]:
        return [f for f in self.findings if f.status == FindingStatus.OPEN]

    def statistics(self) -> dict:
        severity_dist = {}
        for s in Severity:
            severity_dist[s.value] = len(self.by_severity(s))

        category_dist = {}
        for c in Category:
            count = len(self.by_category(c))
            if count > 0:
                category_dist[c.value] = count

        expert_dist = {}
        for f in self.findings:
            expert_dist[f.expert] = expert_dist.get(f.expert, 0) + 1

        actionability = 0
        for f in self.findings:
            if f.fix_suggestion:
                actionability += 1

        return {
            "total": len(self.findings),
            "by_severity": severity_dist,
            "by_category": category_dist,
            "by_expert": expert_dist,
            "actionable": actionability,
            "actionability_score": round(actionability / max(len(self.findings), 1) * 100, 1),
            "new_patterns": sum(1 for f in self.findings if f.is_new_pattern),
        }

    def deduplicate(self) -> "FindingList":
        """按 file_path + title 去重"""
        seen = set()
        unique = []
        for f in self.findings:
            key = (f.file_path, f.title)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return FindingList(unique)

    def filter_by_anti_patterns(self, anti_patterns: List[dict]) -> "FindingList":
        """过滤掉匹配反模式的发现"""
        if not anti_patterns:
            return self

        filtered = []
        for f in self.findings:
            suppressed = False
            for ap in anti_patterns:
                if ap.get("category") == f.category.value and ap.get("keyword", "").lower() in f.title.lower():
                    f.was_suppressed_by_anti_pattern = True
                    suppressed = True
                    break
            if not suppressed:
                filtered.append(f)
        return FindingList(filtered)

    def to_json(self) -> str:
        return json.dumps([f.to_dict() for f in self.findings], ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "FindingList":
        data = json.loads(json_str)
        return cls([Finding.from_dict(d) for d in data])
