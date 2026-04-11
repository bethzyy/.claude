"""
EvolutionStore v2 — 进化状态管理

核心改进（基于安全审计）:
1. JSON 作为主存储格式，杜绝 markdown 解析数据丢失
2. 向后兼容：自动迁移旧 .md 文件
3. 原子写入：write-to-temp + rename，防止并发写入损坏
4. 安全读取：校验 JSON schema，拒绝恶意注入
"""

import json
import re
import os
import tempfile
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict


@dataclass
class EvolutionState:
    """进化状态数据模型"""

    # 统计
    total_reviews: int = 0
    total_issues_found: int = 0
    avg_issues_per_review: float = 0.0
    last_review_date: str = ""
    last_review_project: str = ""

    # 当前基线
    baseline: Optional[Dict] = None

    # 内化模式（出现 3+ 次后自动加入必查列表）
    internalized_patterns: List[Dict] = field(default_factory=list)

    # 反模式（已知噪音，不报告）
    anti_patterns: List[Dict] = field(default_factory=list)

    # 项目特定知识
    project_knowledge: Dict[str, str] = field(default_factory=dict)

    # 本次会话应用的 prompt delta
    prompt_deltas_applied: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> "EvolutionState":
        # 只接受已知字段，拒绝未知注入
        safe = {}
        for f in cls.__dataclass_fields__:
            if f in d:
                safe[f] = d[f]
            else:
                # 使用默认值
                safe[f] = cls.__dataclass_fields__[f].default
                if isinstance(safe[f], type(field)):
                    safe[f] = safe[f].default_factory()
        return cls(**safe)

    def validate(self) -> bool:
        """校验数据完整性"""
        if self.total_reviews < 0:
            return False
        if self.total_issues_found < 0:
            return False
        if self.avg_issues_per_review < 0:
            return False
        if self.baseline is not None:
            if not isinstance(self.baseline, dict):
                return False
        for p in self.internalized_patterns:
            if not isinstance(p, dict) or "description" not in p:
                return False
        for ap in self.anti_patterns:
            if not isinstance(ap, dict) or "description" not in ap:
                return False
        return True


class EvolutionStore:
    """进化状态读写器 — JSON 持久化 + 向后兼容 .md"""

    def __init__(self, skill_dir: str = None):
        if skill_dir:
            self.data_dir = Path(skill_dir) / "data"
        else:
            self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.json_file = self.data_dir / "evolution.json"
        self.md_file = self.data_dir / "evolution.md"

        # 如果 JSON 不存在但 .md 存在，自动迁移
        if not self.json_file.exists():
            md_source = None
            if self.md_file.exists():
                md_source = self.md_file
            elif self.md_file.with_suffix(".md.bak").exists():
                md_source = self.md_file.with_suffix(".md.bak")
            if md_source:
                self._migrate_from_md(md_source)

        self.state: EvolutionState = self._load_or_create()

    def _migrate_from_md(self, md_source: Path = None):
        """从旧 .md 格式迁移到 JSON（一次性操作）"""
        try:
            source = md_source or self.md_file
            content = source.read_text(encoding="utf-8")
            state = self._parse_md(content)
            if state.validate():
                self._save_json(state)
                # 不删除源文件，只是标记已迁移
            else:
                self._save_json(EvolutionState())
        except Exception:
            self._save_json(EvolutionState())

    def _parse_md(self, content: str) -> EvolutionState:
        """向后兼容：解析旧 markdown 格式"""
        state = EvolutionState()
        lines = content.split("\n")
        current_section = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith("## Statistics"):
                current_section = "stats"
            elif stripped.startswith("## Current Baseline"):
                current_section = "baseline"
            elif stripped.startswith("## Internalized Patterns"):
                current_section = "internalized"
            elif stripped.startswith("## Anti-Patterns"):
                current_section = "anti_patterns"
            elif stripped.startswith("## Project-Specific Knowledge"):
                current_section = "knowledge"
            elif stripped.startswith("## Prompt Deltas"):
                current_section = "deltas"
            elif stripped.startswith("# ") and not stripped.startswith("## "):
                current_section = None
            else:
                if current_section == "stats":
                    if "Total reviews conducted:" in stripped:
                        state.total_reviews = self._extract_number(stripped)
                    elif "Total issues found:" in stripped:
                        state.total_issues_found = self._extract_number(stripped)
                    elif "Average issues per review:" in stripped:
                        state.avg_issues_per_review = self._extract_float(stripped)
                    elif "Last review:" in stripped:
                        state.last_review_date = stripped.split(":", 1)[1].strip()
                    elif "Last project:" in stripped:
                        state.last_review_project = stripped.split(":", 1)[1].strip()

                elif current_section == "baseline" and state.baseline is None:
                    if "Issues found:" in stripped:
                        state.baseline = {}
                        state.baseline["issues_found"] = self._extract_number(stripped)
                    elif state.baseline is not None:
                        if "critical=" in stripped:
                            state.baseline["critical"] = self._extract_number(stripped)
                        elif "high=" in stripped:
                            state.baseline["high"] = self._extract_number(stripped)
                        elif "Duration:" in stripped:
                            state.baseline["duration_seconds"] = self._extract_number(stripped)
                        elif "Actionability:" in stripped:
                            state.baseline["actionability_score"] = self._extract_float(stripped)

                elif current_section == "internalized" and stripped.startswith("- "):
                    item_text = stripped[2:]
                    # 尝试解析: [category] description (internalized date, after N appearances)
                    pattern = self._parse_internalized_item(item_text)
                    state.internalized_patterns.append(pattern)

                elif current_section == "anti_patterns" and stripped.startswith("- "):
                    item_text = stripped[2:]
                    if item_text.startswith("_") and item_text.endswith("_"):
                        continue  # 跳过占位符
                    pattern = self._parse_anti_pattern_item(item_text)
                    state.anti_patterns.append(pattern)

                elif current_section == "knowledge" and stripped.startswith("- "):
                    text = stripped[2:]
                    if ": " in text:
                        key, value = text.split(": ", 1)
                        state.project_knowledge[key] = value

        # 去重
        state.internalized_patterns = self._deduplicate_patterns(state.internalized_patterns)
        state.anti_patterns = self._deduplicate_patterns(state.anti_patterns)

        return state

    def _parse_internalized_item(self, text: str) -> Dict:
        """解析内化模式条目，提取所有元数据"""
        item = {"description": text, "category": "", "internalized_date": "", "occurrence_count": 1}

        # 提取 category: [xxx] 或 [?] [xxx]
        cat_match = re.search(r'\[(\w+)\]', text)
        if cat_match:
            item["category"] = cat_match.group(1)

        # 提取日期: (internalized 2026-04-11
        date_match = re.search(r'internalized\s+(\d{4}-\d{2}-\d{2})', text)
        if date_match:
            item["internalized_date"] = date_match.group(1)

        # 提取次数: after N appearances
        count_match = re.search(r'after\s+(\d+)\s+appearances', text)
        if count_match:
            item["occurrence_count"] = int(count_match.group(1))

        # 清理 description：去除元数据部分
        desc = text
        # 去掉最后的 (internalized ...) 括号
        desc = re.sub(r'\s*\(internalized\s+\d{4}-\d{2}-\d{2}.*?\)\s*$', '', desc)
        # 去掉 [xxx] 前缀
        desc = re.sub(r'^\[(\w+)\]\s*', '', desc)
        # 去掉重复的 "(internalized ..., after ...)" 后缀
        desc = re.sub(r'\s*\(internalized\s+\?.*?\)\s*$', '', desc)
        desc = desc.strip()
        if desc:
            item["description"] = desc

        return item

    def _parse_anti_pattern_item(self, text: str) -> Dict:
        """解析反模式条目"""
        item = {"description": text, "category": "", "reason": "", "added_date": ""}

        cat_match = re.search(r'\[(\w+)\]', text)
        if cat_match:
            item["category"] = cat_match.group(1)

        # reason: -- reason text (added date)
        reason_match = re.search(r'--\s*(.+?)\s*\(added\s+(\d{4}-\d{2}-\d{2})\)', text)
        if reason_match:
            item["reason"] = reason_match.group(1).strip()
            item["added_date"] = reason_match.group(2)

        # 清理 description
        desc = text
        desc = re.sub(r'\s*--\s*.+$', '', desc)
        desc = re.sub(r'^\[(\w+)\]\s*', '', desc)
        desc = desc.strip()
        if desc:
            item["description"] = desc

        return item

    def _deduplicate_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """按 description 去重，保留最完整的版本"""
        seen = {}
        for p in patterns:
            # 标准化 key：去掉所有前缀和元数据后缀，只保留核心描述
            desc = p.get("description", "")
            # 去掉 [xxx] 前缀
            desc = re.sub(r'^\[[\w\?]+\]\s*', '', desc)
            # 去掉 "检查 xxx 类问题:" 前缀
            desc = re.sub(r'^[\w\s]+类问题:\s*', '', desc)
            # 去掉 (internalized ...) 后缀
            desc = re.sub(r'\s*\(internalized\s+\d{4}-\d{2}-\d{2}.*?\)\s*$', '', desc)
            key = desc.lower().strip()[:60]

            if key in seen:
                existing = seen[key]
                if p.get("occurrence_count", 0) > existing.get("occurrence_count", 0):
                    seen[key] = p
            else:
                seen[key] = p
        return list(seen.values())

    def _load_or_create(self) -> EvolutionState:
        """加载或创建初始进化状态"""
        if self.json_file.exists():
            return self._load_json()
        else:
            state = EvolutionState()
            self._save_json(state)
            return state

    def _load_json(self) -> EvolutionState:
        """从 JSON 加载"""
        try:
            content = self.json_file.read_text(encoding="utf-8")
            data = json.loads(content)
            state = EvolutionState.from_dict(data)
            if not state.validate():
                # 数据损坏，重置
                return EvolutionState()
            return state
        except (json.JSONDecodeError, KeyError, TypeError):
            # JSON 损坏，尝试从 .md.bak 恢复
            backup = self.md_file.with_suffix(".md.bak")
            if backup.exists():
                try:
                    content = backup.read_text(encoding="utf-8")
                    state = self._parse_md(content)
                    if state.validate():
                        self._save_json(state)
                        return state
                except Exception:
                    pass
            return EvolutionState()

    def _save_json(self, state: EvolutionState):
        """原子写入 JSON：先写临时文件，再 rename"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        content = json.dumps(state.to_dict(), ensure_ascii=False, indent=2)

        # 原子写入：write to temp → rename
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self.data_dir),
            suffix=".tmp",
            prefix="evolution_",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            # 原子替换
            if os.name == "nt":
                # Windows: rename 需要先删除目标
                if self.json_file.exists():
                    self.json_file.unlink()
            os.rename(tmp_path, str(self.json_file))
        except Exception:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def _save_md_view(self, state: EvolutionState):
        """生成人类可读的 markdown 视图（只读，不用于加载）"""
        lines = [
            "# Expert Review Evolution State",
            "",
            "> 此文件由 expert-review skill 自动生成，仅供阅读。",
            "> 实际数据存储在 evolution.json 中。",
            "",
            "## Statistics",
            "",
            f"- Total reviews: {state.total_reviews}",
            f"- Total issues found: {state.total_issues_found}",
            f"- Average per review: {state.avg_issues_per_review:.1f}",
            f"- Last review: {state.last_review_date or 'N/A'}",
            f"- Last project: {state.last_review_project or 'N/A'}",
            "",
        ]

        # Baseline
        lines.append("## Current Baseline")
        lines.append("")
        if state.baseline:
            lines.append(f"- Issues found: {state.baseline.get('issues_found', 'N/A')}")
            lines.append(f"- Critical: {state.baseline.get('critical', 0)}")
            lines.append(f"- High: {state.baseline.get('high', 0)}")
            lines.append(f"- Medium: {state.baseline.get('medium', 0)}")
            lines.append(f"- Low: {state.baseline.get('low', 0)}")
            lines.append(f"- Duration: {state.baseline.get('duration_seconds', 'N/A')}s")
            lines.append(f"- Actionability: {state.baseline.get('actionability_score', 'N/A')}%")
        else:
            lines.append("_No baseline set._")
        lines.append("")

        # Internalized patterns
        lines.append("## Internalized Patterns")
        lines.append("")
        if state.internalized_patterns:
            for p in state.internalized_patterns:
                cat = p.get("category", "?")
                desc = p.get("description", "")
                date = p.get("internalized_date", "")
                count = p.get("occurrence_count", "?")
                lines.append(f"- [{cat}] {desc} (since {date}, {count}x)")
        else:
            lines.append("_None._")
        lines.append("")

        # Anti-patterns
        lines.append("## Anti-Patterns")
        lines.append("")
        if state.anti_patterns:
            for ap in state.anti_patterns:
                cat = ap.get("category", "?")
                desc = ap.get("description", "")
                reason = ap.get("reason", "")
                lines.append(f"- [{cat}] {desc} — {reason}")
        else:
            lines.append("_None._")
        lines.append("")

        # Knowledge
        lines.append("## Project Knowledge")
        lines.append("")
        if state.project_knowledge:
            for k, v in state.project_knowledge.items():
                lines.append(f"- {k}: {v}")
        else:
            lines.append("_None._")
        lines.append("")

        self.md_file.write_text("\n".join(lines), encoding="utf-8")

    def _extract_number(self, line: str) -> int:
        match = re.search(r'(\d+)', line)
        return int(match.group(1)) if match else 0

    def _extract_float(self, line: str) -> float:
        match = re.search(r'([\d.]+)', line)
        return float(match.group(1)) if match else 0.0

    # ============ 公共接口 ============

    def update_after_review(self, review_stats: dict, findings_by_category: Dict[str, int] = None):
        """审查结束后更新进化状态"""
        state = self.state
        now = datetime.now()

        state.total_reviews += 1
        issues_found = review_stats.get("total", 0)
        state.total_issues_found += issues_found
        state.avg_issues_per_review = state.total_issues_found / state.total_reviews
        state.last_review_date = now.strftime("%Y-%m-%d %H:%M")
        state.last_review_project = review_stats.get("project", "")

        # 更新基线（只能升不能降）
        new_baseline = {
            "issues_found": issues_found,
            "by_severity": review_stats.get("by_severity", {}),
            "duration_seconds": review_stats.get("duration_seconds", 0),
            "actionability_score": review_stats.get("actionability_score", 0),
        }
        new_baseline.update(review_stats.get("by_severity", {}))

        if state.baseline is None:
            state.baseline = new_baseline
        elif issues_found > state.baseline.get("issues_found", 0):
            state.baseline = new_baseline

        # 更新项目知识
        if review_stats.get("project"):
            state.project_knowledge["project_name"] = review_stats["project"]
        if review_stats.get("test_command"):
            state.project_knowledge["test_command"] = review_stats["test_command"]
        if review_stats.get("framework"):
            state.project_knowledge["framework"] = review_stats["framework"]

        self._save(state)

    def get_prompt_additions(self) -> str:
        """生成注入到专家 prompt 的进化上下文"""
        state = self.state
        parts = []

        if state.baseline:
            parts.append("## 审查基线")
            parts.append(f"上次审查发现 {state.baseline.get('issues_found', 'N/A')} 个问题。")
            parts.append("这是你的最低标准，不能低于这个深度。")
            parts.append("")

        if state.internalized_patterns:
            parts.append("## 必查项（已内化）")
            for p in state.internalized_patterns:
                parts.append(f"- [{p.get('category', '?')}] {p['description']}")
            parts.append("")

        if state.anti_patterns:
            parts.append("## 已知噪音（不要报告）")
            for ap in state.anti_patterns:
                parts.append(f"- [{ap.get('category', '?')}] {ap['description']} — 原因: {ap.get('reason', '?')}")
            parts.append("")

        if state.total_reviews > 0:
            parts.append("## 历史统计")
            parts.append(f"累计审查 {state.total_reviews} 次，平均每次发现 {state.avg_issues_per_review:.1f} 个问题。")

        return "\n".join(parts) if parts else ""

    def add_internalized_pattern(self, description: str, category: str, occurrence_count: int):
        """添加内化模式"""
        for p in self.state.internalized_patterns:
            if p["description"] == description:
                p["occurrence_count"] = max(p.get("occurrence_count", 1), occurrence_count)
                self._save(self.state)
                return
        self.state.internalized_patterns.append({
            "description": description,
            "category": category,
            "internalized_date": datetime.now().strftime("%Y-%m-%d"),
            "occurrence_count": occurrence_count,
        })
        self._save(self.state)

    def add_anti_pattern(self, description: str, category: str, reason: str):
        """添加反模式"""
        for ap in self.state.anti_patterns:
            if ap["description"] == description:
                return
        self.state.anti_patterns.append({
            "description": description,
            "category": category,
            "reason": reason,
            "added_date": datetime.now().strftime("%Y-%m-%d"),
        })
        self._save(self.state)

    def _save(self, state: EvolutionState):
        """保存状态：JSON 主存储 + markdown 视图"""
        self._save_json(state)
        self._save_md_view(state)

    def load(self) -> EvolutionState:
        return self.state
