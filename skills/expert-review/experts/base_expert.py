"""
BaseExpert — 专家基类

所有审查专家的统一接口和公共逻辑。
"""

import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional

from core._paths import SKILL_DIR, ensure_skill_path
ensure_skill_path()

from core.finding import Finding, FindingList, Severity, Category
from core.review_context import ReviewContext
from evolution.evolution_store import EvolutionState


class BaseExpert(ABC):
    """审查专家基类"""

    # 子类必须定义
    name: str = ""
    name_cn: str = ""
    description: str = ""

    # 重点关注的安全/质量模式
    PATTERNS: Dict[str, Dict] = {}

    def __init__(
        self,
        context: ReviewContext,
        evolution: Optional[EvolutionState] = None,
        prompt_deltas: Optional[List[str]] = None,
        experience_cards: Optional[dict] = None,
    ):
        self.context = context
        self.evolution = evolution
        self.prompt_deltas = prompt_deltas or []
        self.experience_cards = experience_cards or {}
        self.findings = FindingList()

    @abstractmethod
    def review(self, source_files: List[str] = None) -> FindingList:
        """
        执行审查。

        Args:
            source_files: 要审查的文件列表，None 表示全量审查

        Returns:
            FindingList: 审查发现
        """
        pass

    def get_prompt_context(self) -> str:
        """生成注入到 prompt 的完整上下文"""
        parts = []

        # 项目上下文
        parts.append(self.context.to_prompt_context())

        # 进化上下文
        if self.evolution:
            evo_parts = []
            if self.evolution.baseline:
                evo_parts.append(
                    f"## 审查基线\n"
                    f"上次审查发现 {self.evolution.baseline.get('issues_found', 'N/A')} 个问题。"
                    f"这是你的最低标准。"
                )
            if self.evolution.internalized_patterns:
                evo_parts.append("## 必查项（已内化）")
                for p in self.evolution.internalized_patterns:
                    evo_parts.append(f"- [{p.get('category', '?')}] {p['description']}")
            if self.evolution.anti_patterns:
                evo_parts.append("## 已知噪音（不要报告）")
                for ap in self.evolution.anti_patterns:
                    evo_parts.append(f"- {ap['description']}")

            if evo_parts:
                parts.append("\n".join(evo_parts))

        # Prompt deltas
        if self.prompt_deltas:
            parts.append("## 本次审查新增检查项（来自进化）")
            for delta in self.prompt_deltas:
                parts.append(f"- {delta}")

        # Experience injection (from past bug fixes)
        if self.experience_cards:
            from evolution.experience_collector import BugExperienceCollector
            collector = BugExperienceCollector()
            # 提取文件扩展名和模块用于相关性排序
            extensions = list(set(
                f.split(".")[-1] for f in (self.context.source_files or [])
                if "." in f
            ))
            modules = list(set(
                f.replace("\\", "/").split("/")[0] if "/" in f.replace("\\", "/") else ""
                for f in (self.context.source_files or [])
            ))
            experience_prompt = collector.get_review_prompt(
                project_dir=self.context.project_dir,
                context_extensions=extensions,
                context_modules=modules,
            )
            if experience_prompt:
                parts.append(experience_prompt)

        return "\n".join(parts)

    def add_finding(
        self,
        title: str,
        severity: Severity,
        category: Category,
        file_path: str = "",
        line_range: str = None,
        code_snippet: str = None,
        description: str = "",
        fix_suggestion: str = None,
        fix_code_example: str = None,
        effort: str = None,
        references: List[str] = None,
    ) -> Finding:
        """便捷方法：添加一个 Finding"""
        finding = Finding(
            severity=severity,
            category=category,
            expert=self.name,
            title=title,
            description=description,
            file_path=file_path,
            line_range=line_range,
            code_snippet=code_snippet,
            fix_suggestion=fix_suggestion,
            fix_code_example=fix_code_example,
            effort=effort,
            references=references or [],
        )
        self.findings.add(finding)
        return finding

    def read_file(self, file_path: str) -> Optional[str]:
        """安全读取项目文件，优先从缓存获取"""
        # 优先从 context 缓存读取
        cached = self.context.get_content(file_path)
        if cached is not None:
            return cached

        # Fallback: 磁盘读取 + 写入缓存
        full_path = (Path(self.context.project_dir) / file_path).resolve()
        project_root = Path(self.context.project_dir).resolve()
        if not str(full_path).startswith(str(project_root)):
            return None  # Path traversal attempt
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            self.context._content_cache[file_path] = content
            self.context._lines_cache[file_path] = content.split("\n")
            return content
        except Exception:
            return None

    def _in_docstring(self, lines: List[str], line_no: int) -> bool:
        """Check if line is inside a triple-quote docstring by counting all quotes from file start"""
        in_docstring = False
        for i in range(line_no + 1):
            line = lines[i]
            for quote in ['"""', "'''"]:
                count = line.count(quote)
                for _ in range(count):
                    in_docstring = not in_docstring
        return in_docstring

    def read_file_lines(self, file_path: str) -> Optional[List[str]]:
        """读取文件为行列表，优先从缓存获取"""
        cached = self.context.get_lines(file_path)
        if cached is not None:
            return cached
        content = self.read_file(file_path)
        if content is None:
            return None
        return content.split("\n")

    def find_pattern_in_file(self, file_path: str, pattern: str) -> List[Dict]:
        """在文件中搜索正则模式，返回匹配结果"""
        lines = self.read_file_lines(file_path)
        if not lines:
            return []

        results = []
        regex = re.compile(pattern)
        for i, line in enumerate(lines, 1):
            match = regex.search(line)
            if match:
                results.append({
                    "line": i,
                    "content": line.strip(),
                    "match": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })
        return results

    def scan_all_files(self, source_files: List[str] = None) -> List[str]:
        """获取要扫描的文件列表"""
        if source_files:
            return source_files
        return self.context.source_files

    def filter_by_extension(self, files: List[str], extensions: List[str]) -> List[str]:
        """按扩展名过滤文件"""
        return [f for f in files if any(f.endswith(ext) for ext in extensions)]
