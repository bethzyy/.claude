"""
PromptEvolver — Prompt 自动进化

分析审查结果，自动生成 prompt 改进建议（delta 文件）。
下次审查时自动应用，形成正向飞轮。
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from core._paths import ensure_skill_path
ensure_skill_path()

from core.finding import FindingList


class PromptEvolver:
    """Prompt 自动进化器"""

    def __init__(self, skill_dir: str = None):
        if skill_dir:
            self.deltas_dir = Path(skill_dir) / "data" / "prompt_deltas"
        else:
            self.deltas_dir = Path(__file__).parent.parent / "data" / "prompt_deltas"
        self.deltas_dir.mkdir(parents=True, exist_ok=True)

    def generate_deltas(
        self,
        findings: FindingList,
        expert_name: str,
        project_name: str = "",
    ) -> List[str]:
        """
        基于审查结果生成 prompt delta。

        分析逻辑：
        1. 发现了新类别的问题 → 建议添加对应检查
        2. 某个类别发现问题很多 → 建议加强该类检查
        3. 某个类别没有发现问题 → 可能是盲区，建议添加
        """
        stats = findings.statistics()
        deltas = []

        # 按专家筛选发现
        expert_findings = findings.by_expert(expert_name)
        if not expert_findings:
            return deltas

        # 只关注 High+ 级别的发现用于进化，Low 级别不生成 delta
        high_value_findings = [
            f for f in expert_findings
            if f.severity.value in ("critical", "high")
        ]

        # 1. 新发现模式 → 生成加强建议（仅 High+）
        new_patterns = [f for f in high_value_findings if f.is_new_pattern]
        for f in new_patterns[:5]:  # 限制每个专家最多5个
            delta_text = (
                f"[{expert_name}] 加强 {f.category.value} 类检查: "
                f"发现 {f.title}，建议在类似代码中主动检查此模式"
            )
            deltas.append(delta_text)

        # 2. 某类别发现密集 → 建议深化（仅 High+）
        category_counts: Dict[str, int] = {}
        for f in high_value_findings:
            cat = f.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        for cat, count in category_counts.items():
            if count >= 3:
                delta_text = (
                    f"[{expert_name}] {cat} 类问题密集 ({count}个)，"
                    f"建议对该类别进行更深入审查"
                )
                deltas.append(delta_text)

        # 3. 安全专家特殊处理 — 如果发现硬编码密钥，建议加强密钥检测
        if expert_name == "security":
            secret_findings = [f for f in high_value_findings if "secret" in f.title.lower() or "key" in f.title.lower()]
            if secret_findings:
                deltas.append(
                    f"[security] 加强密钥检测: 发现 {len(secret_findings)} 个密钥相关问题，"
                    f"建议检查 .env 文件和配置文件中的密钥管理"
                )

        # 4. 测试专家特殊处理 — 如果覆盖率缺口大，建议优先级提升
        if expert_name == "testing":
            high_severity_tests = [f for f in high_value_findings if f.severity.value == "high"]
            if high_severity_tests:
                deltas.append(
                    f"[testing] 发现 {len(high_severity_tests)} 个高严重度测试缺口，"
                    f"建议在审查报告中优先标记测试缺失的关键模块"
                )

        # 保存 delta 文件
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        for i, delta_text in enumerate(deltas):
            filename = f"{timestamp}-{expert_name}-{i+1}.md"
            filepath = self.deltas_dir / filename

            content = f"""---
target_expert: {expert_name}
project: {project_name}
generated_at: {datetime.now().isoformat()}
category: auto_evolution
---

## Prompt Delta

{delta_text}

### Source
- Review findings: {stats['total']} total
- Expert findings: {len(expert_findings)}
- Categories: {', '.join(category_counts.keys())}
"""
            filepath.write_text(content, encoding="utf-8")

        return deltas

    def load_pending_deltas(self, expert_name: str = None) -> List[str]:
        """加载待应用的 prompt delta"""
        deltas = []
        for f in sorted(self.deltas_dir.glob("*.md")):
            try:
                content = f.read_text(encoding="utf-8")
                # 解析 frontmatter
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        meta = parts[1]
                        body = parts[2].strip()

                        # 按专家过滤
                        if expert_name and f"target_expert: {expert_name}" not in meta:
                            continue

                        # 提取 delta 文本
                        for line in body.split("\n"):
                            if line.startswith("[") and "加强" in line:
                                deltas.append(line)
            except Exception:
                continue

        return deltas

    def count_pending(self) -> int:
        """统计待应用的 delta 数量"""
        return len(list(self.deltas_dir.glob("*.md")))

    def should_consolidate(self, threshold: int = 5) -> bool:
        """判断是否应该将 delta 合并到 SKILL.md"""
        return self.count_pending() >= threshold

    def get_consolidation_suggestion(self) -> Optional[str]:
        """生成合并建议"""
        if not self.should_consolidate():
            return None

        count = self.count_pending()
        deltas = self.load_pending_deltas()

        # 按专家分组
        expert_groups: Dict[str, List[str]] = {}
        for delta in deltas:
            if delta.startswith("["):
                expert = delta.split("]")[0][1:]
                expert_groups[expert] = expert_groups.get(expert, [])
                expert_groups[expert].append(delta)

        lines = [f"已积累 {count} 个 prompt delta，建议合并到 SKILL.md：\n"]
        for expert, items in expert_groups.items():
            lines.append(f"### {expert} ({len(items)} 个)")
            for item in items[:5]:
                lines.append(f"- {item}")
            if len(items) > 5:
                lines.append(f"- ... 还有 {len(items) - 5} 个")

        return "\n".join(lines)
