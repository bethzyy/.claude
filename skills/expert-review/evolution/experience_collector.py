"""
BugExperienceCollector v2 — Bug 修复经验收集与自动借鉴

基于业界最佳实践设计：
- 参考 CodeGuru/DeepCode 的经验复用架构
- 采用 CWE/SEI CERT 分类体系
- 结构化 prompt 注入（参考 SonarQube rule format）
- 智能去重 + 相关性排序 + 注入上限控制

核心闭环：git diff 提取 → 分类沉淀 → 审查自动加载 → 回归检查
"""

import re
import json
import os
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core._paths import SKILL_DIR, ensure_skill_path
ensure_skill_path()


# ============ CWE Reference Mapping ============
# 基于 CWE Top 25 (2024) + SEI CERT Python Rules
# 参考: https://cwe.mitre.org/top25/archive/2024/2024_cwe_top25.html

CWE_MAP = {
    # -- Security (OWASP/CWE Top 25) --
    "sql_injection": {"cwe": "CWE-89", "name": "SQL Injection", "severity": "critical"},
    "command_injection": {"cwe": "CWE-78", "name": "OS Command Injection", "severity": "critical"},
    "xss": {"cwe": "CWE-79", "name": "Cross-site Scripting", "severity": "high"},
    "path_traversal": {"cwe": "CWE-22", "name": "Path Traversal", "severity": "high"},
    "hardcoded_secret": {"cwe": "CWE-798", "name": "Hardcoded Credentials", "severity": "critical"},
    "weak_hash": {"cwe": "CWE-328", "name": "Weak Hash", "severity": "high"},
    "insecure_deserialize": {"cwe": "CWE-502", "name": "Insecure Deserialization", "severity": "high"},
    "ssrf": {"cwe": "CWE-918", "name": "SSRF", "severity": "high"},
    "auth_bypass": {"cwe": "CWE-287", "name": "Improper Authentication", "severity": "critical"},
    "session_fixation": {"cwe": "CWE-384", "name": "Session Fixation", "severity": "high"},
    "missing_auth": {"cwe": "CWE-306", "name": "Missing Authentication", "severity": "high"},
    "debug_mode": {"cwe": "CWE-489", "name": "Debug Code in Release", "severity": "medium"},
    "eval_usage": {"cwe": "CWE-95", "name": "Eval Injection", "severity": "high"},
    "cors_misconfig": {"cwe": "CWE-942", "name": "Overly Permissive CORS", "severity": "medium"},

    # -- Bug (SEI CERT + Common) --
    "null_pointer": {"cwe": "CWE-476", "name": "NULL Pointer Dereference", "severity": "high"},
    "index_out_of_bounds": {"cwe": "CWE-125", "name": "Out-of-bounds Read", "severity": "high"},
    "off_by_one": {"cwe": "CWE-193", "name": "Off-by-one Error", "severity": "medium"},
    "integer_overflow": {"cwe": "CWE-190", "name": "Integer Overflow", "severity": "high"},
    "race_condition": {"cwe": "CWE-362", "name": "Race Condition", "severity": "high"},
    "deadlock": {"cwe": "CWE-833", "name": "Deadlock", "severity": "high"},
    "type_error": {"cwe": "CWE-843", "name": "Type Confusion", "severity": "medium"},

    # -- Reliability --
    "resource_leak": {"cwe": "CWE-404", "name": "Resource Leak", "severity": "medium"},
    "unreleased_lock": {"cwe": "CWE-833", "name": "Unreleased Lock", "severity": "medium"},
    "missing_error_handling": {"cwe": "CWE-755", "name": "Improper Exception Handling", "severity": "medium"},
    "silent_exception": {"cwe": "CWE-390", "name": "Silent Exception", "severity": "medium"},

    # -- Performance --
    "n_plus_one_query": {"cwe": "CWE-1049", "name": "Excessive Database Query", "severity": "medium"},
    "memory_leak": {"cwe": "CWE-401", "name": "Memory Leak", "severity": "high"},

    # -- Input Validation --
    "missing_validation": {"cwe": "CWE-20", "name": "Improper Input Validation", "severity": "medium"},
    "missing_sanitization": {"cwe": "CWE-20", "name": "Missing Sanitization", "severity": "medium"},
    "encoding_error": {"cwe": "CWE-172", "name": "Encoding Error", "severity": "low"},
}

# ============ Fix Pattern Taxonomy (参考 Defects4J + Error Prone) ============
# Fix Type 维度 — 描述修复技巧的类型

FIX_TYPES = {
    "guard": "添加前置检查条件（if x is None: return）",
    "wrap": "添加 try/except/finally 包裹",
    "replace": "替换表达式/算法/方法调用",
    "remove": "删除死代码或冗余逻辑",
    "restructure": "重构代码结构（提取方法、移动职责）",
    "configure": "修改配置值或环境变量",
    "escape": "添加转义/编码处理",
    "lock": "添加锁/同步机制",
    "validate": "添加输入验证",
    "sanitize": "添加数据清理",
    "close": "添加资源释放（with/finally）",
    "log": "添加日志记录",
    "auth": "添加认证/授权保护",
}


class ExperienceCard:
    """
    单条经验卡片 — 参考 Error Prone BugPattern 格式设计

    结构: Pattern ID + CWE + Fix Type + Before/After + Context
    """

    def __init__(
        self,
        bug_pattern: str,           # 模式名（如 "missing null check"）
        bug_description: str,       # 问题描述
        fix_technique: str,         # 修复技巧描述
        fix_type: str = "guard",    # 修复类型（参考 FIX_TYPES）
        fix_code_example: str = "", # 修复代码示例
        before_code: str = "",      # 修复前的代码
        after_code: str = "",       # 修复后的代码
        file_path: str = "",        # 涉及的文件
        line_range: str = "",       # 行范围
        category: str = "bug",      # 分类
        severity: str = "high",     # 严重度
        cwe_id: str = "",           # CWE ID（如 CWE-476）
        cwe_name: str = "",         # CWE 名称
        scope: str = "project",     # universal | framework | project
        framework: str = "",        # 框架（scope=framework 时填写）
        project: str = "",          # 项目名
        discovered_at: str = "",    # 发现时间
        occurrence_count: int = 1,  # 出现次数
        confidence: float = 1.0,    # 提取置信度 (0-1)
        card_id: str = "",          # 可选：指定 ID（从文件加载时使用）
    ):
        self.id = card_id or f"EXP-{uuid.uuid4().hex[:8].upper()}"
        self.bug_pattern = bug_pattern
        self.bug_description = bug_description
        self.fix_technique = fix_technique
        self.fix_type = fix_type
        self.fix_code_example = fix_code_example
        self.before_code = before_code
        self.after_code = after_code
        self.file_path = file_path
        self.line_range = line_range
        self.category = category
        self.severity = severity
        self.cwe_id = cwe_id
        self.cwe_name = cwe_name
        self.scope = scope
        self.framework = framework
        self.project = project
        self.discovered_at = discovered_at or datetime.now().strftime("%Y-%m-%d")
        self.occurrence_count = occurrence_count
        self.confidence = confidence

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "bug_pattern": self.bug_pattern,
            "bug_description": self.bug_description,
            "fix_technique": self.fix_technique,
            "fix_type": self.fix_type,
            "fix_code_example": self.fix_code_example,
            "before_code": self.before_code,
            "after_code": self.after_code,
            "file_path": self.file_path,
            "line_range": self.line_range,
            "category": self.category,
            "severity": self.severity,
            "cwe_id": self.cwe_id,
            "cwe_name": self.cwe_name,
            "scope": self.scope,
            "framework": self.framework,
            "project": self.project,
            "discovered_at": self.discovered_at,
            "occurrence_count": self.occurrence_count,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ExperienceCard":
        card = cls(
            bug_pattern=d.get("bug_pattern", ""),
            bug_description=d.get("bug_description", ""),
            fix_technique=d.get("fix_technique", ""),
            fix_type=d.get("fix_type", "guard"),
            fix_code_example=d.get("fix_code_example", ""),
            before_code=d.get("before_code", ""),
            after_code=d.get("after_code", ""),
            file_path=d.get("file_path", ""),
            line_range=d.get("line_range", ""),
            category=d.get("category", "bug"),
            severity=d.get("severity", "high"),
            cwe_id=d.get("cwe_id", ""),
            cwe_name=d.get("cwe_name", ""),
            scope=d.get("scope", "project"),
            framework=d.get("framework", ""),
            project=d.get("project", ""),
            discovered_at=d.get("discovered_at", ""),
            occurrence_count=d.get("occurrence_count", 1),
            confidence=d.get("confidence", 1.0),
            card_id=d.get("id", ""),
        )
        return card

    def normalized_key(self) -> str:
        """用于去重的标准化 key — 去除变量名和字面量"""
        # 将 bug_pattern 标准化为小写 + 去除多余空格
        key = self.bug_pattern.lower().strip()
        # 将 file_path 只保留文件名（不含路径）
        return f"{key}|{self.category}"

    def relevance_score(self, context_extensions: List[str] = None,
                        context_modules: List[str] = None) -> float:
        """
        计算与当前审查的相关性分数 (0-1)
        用于 prompt 注入排序 — 参考 CodeGuru 的推荐排序机制
        """
        score = 0.0

        # 严重度权重
        severity_weights = {"critical": 0.3, "high": 0.2, "medium": 0.1, "low": 0.05}
        score += severity_weights.get(self.severity, 0.1)

        # 置信度权重
        score += self.confidence * 0.2

        # 出现次数权重（越多越重要）
        score += min(self.occurrence_count * 0.05, 0.15)

        # 文件扩展名匹配
        if context_extensions:
            for ext in context_extensions:
                if self.file_path.endswith(ext):
                    score += 0.1
                    break

        # 模块匹配
        if context_modules:
            for mod in context_modules:
                if mod and mod.lower() in self.file_path.lower():
                    score += 0.1
                    break

        return min(score, 1.0)

    def to_review_prompt(self) -> str:
        """
        生成注入到审查 prompt 的结构化条目
        格式参考 SonarQube rule format + CodeGuru recommendation format
        """
        severity_badge = {
            "critical": "CRITICAL", "high": "HIGH",
            "medium": "MEDIUM", "low": "LOW",
        }.get(self.severity, "MEDIUM")

        parts = [
            f"### [{severity_badge}] {self.id}: {self.bug_pattern}",
        ]

        if self.cwe_id:
            parts.append(f"- **CWE**: {self.cwe_id} ({self.cwe_name})")

        parts.append(f"- **Pattern (before)**: `{self.before_code or self.bug_description}`")
        parts.append(f"- **Fix**: {self.fix_technique}")
        if self.after_code:
            parts.append(f"- **Example (after)**: `{self.after_code}`")

        if self.occurrence_count > 1:
            parts.append(f"- **Recurrence**: {self.occurrence_count}x")

        if self.file_path:
            parts.append(f"- **Last seen**: `{self.file_path}`")

        return "\n".join(parts)

    def to_compact_prompt(self) -> str:
        """紧凑格式 — 用于低优先级 pattern 的单行展示"""
        cwe_prefix = f"[{self.cwe_id}] " if self.cwe_id else ""
        return f"- {cwe_prefix}{self.bug_pattern}: {self.fix_technique}"

    def to_markdown(self) -> str:
        """生成持久化 markdown"""
        lines = [
            f"### {self.id}: {self.bug_pattern}",
            f"- **Problem**: {self.bug_description}",
            f"- **Fix**: {self.fix_technique}",
            f"- **Fix Type**: {self.fix_type}",
        ]
        if self.cwe_id:
            lines.append(f"- **CWE**: {self.cwe_id} ({self.cwe_name})")
        if self.before_code:
            lines.append(f"- **Before**: ```\n{self.before_code}\n```")
        if self.after_code:
            lines.append(f"- **After**: ```\n{self.after_code}\n```")
        if self.file_path:
            lines.append(f"- **File**: `{self.file_path}:{self.line_range}`")
        lines.append(f"- **Category**: {self.category} | **Severity**: {self.severity}")
        scope_labels = {
            "universal": "Universal (cross-project)",
            "framework": f"Framework ({self.framework})",
            "project": f"Project-specific ({self.project})",
        }
        lines.append(f"- **Scope**: {scope_labels.get(self.scope, self.scope)}")
        lines.append(f"- **Discovered**: {self.discovered_at}")
        if self.occurrence_count > 1:
            lines.append(f"- **Recurrence**: {self.occurrence_count}x")
        return "\n".join(lines)


class BugExperienceCollector:
    """
    Bug 修复经验收集器 v2

    改进点（基于 CodeGuru/DeepCode/SonarQube 最佳实践）:
    1. 三档分类: universal / framework / project
    2. CWE 映射: 每个 pattern 关联 CWE ID
    3. 智能去重: 按 normalized pattern + category
    4. 相关性排序: 注入前按 relevance_score 排序
    5. 注入上限: 15 universal + 10 project（防止 context dilution）
    6. 完整上下文: 捕获 before/after hunks
    """

    # Git commit message 中 bug fix 关键词（带置信度）
    BUG_FIX_KEYWORDS = [
        # 高置信度 (>0.9) — 明确的 bug fix
        (r"fix\s+", 0.95),
        (r"bug\s*fix", 0.95),
        (r"bugfix", 0.95),
        (r"hotfix", 0.95),
        (r"修复", 0.95),
        (r"修正", 0.95),
        (r"security\s*fix", 0.95),
        (r"cve-\d+", 0.95),
        (r"vuln", 0.90),
        (r"xss", 0.90),
        (r"sqli", 0.90),
        # 中置信度 (0.7-0.9) — 可能是 bug fix
        (r"resolve", 0.85),
        (r"patch", 0.85),
        (r"prevent\s+\w+", 0.80),
        (r"guard\s+against", 0.85),
        (r"handle\s+error", 0.75),
        (r"catch\s+exception", 0.80),
        (r"inject", 0.80),
        (r"leak", 0.80),
        (r"overflow", 0.80),
        (r"crash", 0.80),
        (r"race\s+condition", 0.85),
        (r"deadlock", 0.85),
        (r"null\s+pointer", 0.85),
        (r"index\s*out.of.bounds", 0.85),
        (r"type\s+error", 0.75),
        # 低置信度 (0.5-0.7) — 可能有其他含义
        (r"解决", 0.70),
        (r"改进", 0.50),
        (r"优化", 0.40),
        (r"refactor", 0.30),
        (r"update", 0.20),
        (r"clean", 0.20),
    ]

    # Diff 修复模式（参考 Error Prone + CERT Python）
    # 格式: (regex, fix_type, cwe_key, description, universal)
    DIFF_FIX_PATTERNS = [
        # -- 安全类 (通常 universal) --
        (r"except\s*\(\s*\w*\s*\)\s*:", "wrap", "missing_error_handling", "添加异常捕获", True),
        (r"try\s*:", "wrap", "missing_error_handling", "添加 try/except", True),
        (r"finally\s*:", "wrap", "resource_leak", "添加 finally 清理", True),
        (r"re\.escape\(", "escape", "xss", "添加正则转义", True),
        (r"html\.escape\(", "escape", "xss", "添加 HTML 转义", True),
        (r"@login_required|@auth", "auth", "missing_auth", "添加认证保护", True),
        (r"@permission|@role", "auth", "auth_bypass", "添加授权检查", True),
        (r"validate|validation", "validate", "missing_validation", "添加输入验证", True),
        (r"sanitize|clean", "sanitize", "missing_sanitization", "添加数据清理", True),
        (r"str\(\s*.*\s*\)\s*\.encode|\.decode", "replace", "encoding_error", "添加编码处理", True),
        (r"int\(", "guard", "type_error", "添加类型转换保护", True),
        (r"Lock\(|lock\(", "lock", "race_condition", "添加锁", True),

        # -- 可靠性类 (通常 universal) --
        (r"if\s+\w+\s+is\s+None\s*:", "guard", "null_pointer", "添加 None 检查", True),
        (r"if\s+not\s+\w+\s*:", "guard", "null_pointer", "添加空值检查", True),
        (r"==\s*None\s+", "guard", "null_pointer", "添加 None 比较", True),
        (r"len\(.*\)\s*[><=]", "guard", "off_by_one", "添加长度/边界检查", True),
        (r"\.close\(\)", "close", "resource_leak", "添加资源释放", True),
        (r"with\s+open\s*\(", "close", "resource_leak", "使用 with 管理资源", True),
        (r"logger\.\w+\(", "log", "silent_exception", "添加日志记录", True),
    ]

    # 注入上限（参考 CodeGuru: ~20 recommendations per review）
    MAX_UNIVERSAL_INJECT = 15
    MAX_PROJECT_INJECT = 10

    def __init__(self, skill_dir: str = None):
        if skill_dir:
            self.skill_dir = Path(skill_dir)
        else:
            self.skill_dir = Path(__file__).parent.parent
        self.universal_file = self.skill_dir / "data" / "cross_project_patterns.md"
        self.universal_file.parent.mkdir(parents=True, exist_ok=True)

    def collect_from_session(self, project_dir: str) -> List[ExperienceCard]:
        """
        从当前 session 的 git diff 中提取 bug fix 经验。

        改进（参考 GitBug/Defects4J）:
        - 带置信度的 commit 分类（不只是 true/false）
        - 捕获完整 before/after hunk context
        - 自动映射 CWE ID
        """
        project_path = Path(project_dir)
        project_name = project_path.name
        experiences = []

        session_diffs = self._get_session_diffs(project_dir)
        if not session_diffs:
            return experiences

        for commit in session_diffs:
            message = commit.get("message", "")
            files_changed = commit.get("files", [])

            # 带置信度的 bug fix 判断
            confidence = self._is_bug_fix_commit(message)
            if confidence < 0.5:
                continue

            for file_info in files_changed:
                diff_content = file_info.get("patch", "")
                if not diff_content:
                    continue

                cards = self._extract_experience_from_diff(
                    diff_content=diff_content,
                    file_path=file_info.get("file", ""),
                    commit_message=message,
                    project_name=project_name,
                    commit_confidence=confidence,
                )
                experiences.extend(cards)

        # 智能去重
        experiences = self._deduplicate(experiences)

        # 合并相似 pattern 的 occurrence_count
        experiences = self._merge_similar(experiences)

        # 分类 scope
        for card in experiences:
            card.scope = self._classify_scope(card, project_dir)

        return experiences

    def _get_session_diffs(self, project_dir: str) -> List[Dict]:
        """获取当前 session 的 git commits"""
        project_path = Path(project_dir)

        if not (project_path / ".git").exists():
            return []

        try:
            today = datetime.now().strftime("%Y-%m-%d")
            result = subprocess.run(
                ["git", "log", f"--since={today}", "--pretty=format:%H|%s", "--name-only"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return []

            commits = []
            current_hash = None
            current_msg = None
            current_files = []

            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue

                if "|" in line and not line.startswith(" "):
                    # 保存上一个 commit
                    if current_hash and current_files:
                        commits.append({
                            "hash": current_hash,
                            "message": current_msg,
                            "files": current_files,
                        })

                    parts = line.split("|", 1)
                    current_hash = parts[0]
                    current_msg = parts[1] if len(parts) > 1 else ""
                    current_files = []
                elif current_hash:
                    current_files.append({"file": line})

            # 最后一个 commit
            if current_hash and current_files:
                commits.append({
                    "hash": current_hash,
                    "message": current_msg,
                    "files": current_files,
                })

            # 为每个文件获取 patch 内容
            for commit in commits:
                for file_info in commit["files"]:
                    file_info["patch"] = self._get_commit_diff(
                        project_dir, commit["hash"], file_info["file"]
                    )

            return commits
        except Exception:
            return []

    def _get_commit_diff(self, project_dir: str, commit_hash: str, file_path: str) -> str:
        """获取某个 commit 中某个文件的完整 diff"""
        try:
            result = subprocess.run(
                ["git", "show", f"{commit_hash}^..{commit_hash}", "--", file_path],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout if result.returncode == 0 else ""
        except Exception:
            return ""

    def _is_bug_fix_commit(self, message: str) -> float:
        """
        判断 commit 是否是 bug fix，返回置信度 (0-1)
        参考 GitBug 的多信号方法，但简化为关键词匹配 + 置信度
        """
        message_lower = message.lower()
        max_confidence = 0.0

        for pattern, confidence in self.BUG_FIX_KEYWORDS:
            if re.search(pattern, message_lower):
                max_confidence = max(max_confidence, confidence)

        return max_confidence

    def _extract_experience_from_diff(
        self,
        diff_content: str,
        file_path: str,
        commit_message: str,
        project_name: str,
        commit_confidence: float = 1.0,
    ) -> List[ExperienceCard]:
        """
        从 diff 中提取经验卡片

        改进: 捕获完整 hunk context（before/after），不只是单行
        """
        cards = []
        lines = diff_content.split("\n")

        # 解析 hunks — 每个 hunk 保存完整的 before/after
        hunks = []
        current_hunk = None

        for line in lines:
            if line.startswith("@@"):
                if current_hunk:
                    hunks.append(current_hunk)
                current_hunk = {"header": line, "deletions": [], "additions": []}
                continue

            if current_hunk is None:
                continue

            if line.startswith("+") and not line.startswith("+++"):
                current_hunk["additions"].append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                current_hunk["deletions"].append(line[1:])

        if current_hunk:
            hunks.append(current_hunk)

        # 从每个 hunk 提取经验
        for hunk in hunks:
            additions_text = "\n".join(hunk["additions"])
            deletions_text = "\n".join(hunk["deletions"])

            for pattern, fix_type, cwe_key, description, is_universal in self.DIFF_FIX_PATTERNS:
                # 在 additions 中检测修复模式
                if not re.search(pattern, additions_text):
                    continue

                # 获取 CWE 信息
                cwe_info = CWE_MAP.get(cwe_key, {})
                severity = cwe_info.get("severity", "medium")

                # 构造 before/after context（最多 3 行）
                before_code = "\n".join(hunk["deletions"][-3:]) if hunk["deletions"] else ""
                after_code = "\n".join(hunk["additions"][:3]) if hunk["additions"] else ""

                # 清理过长代码
                before_code = before_code[:200]
                after_code = after_code[:200]

                card = ExperienceCard(
                    bug_pattern=description,
                    bug_description=self._infer_bug_from_deletions(hunk["deletions"], pattern),
                    fix_technique=description,
                    fix_type=fix_type,
                    fix_code_example=after_code,
                    before_code=before_code,
                    after_code=after_code,
                    file_path=file_path,
                    category=self._guess_category(file_path, cwe_key),
                    severity=severity,
                    cwe_id=cwe_info.get("cwe", ""),
                    cwe_name=cwe_info.get("name", ""),
                    project=project_name,
                    discovered_at=datetime.now().strftime("%Y-%m-%d"),
                    confidence=commit_confidence * 0.8,  # pattern match 降低置信度
                )
                cards.append(card)

        return cards

    def _infer_bug_from_deletions(self, deletions: List[str], fix_pattern: str) -> str:
        """从被删除的代码行推断原始 bug"""
        if not deletions:
            return "Code issue (see fix for details)"

        relevant = [d.strip() for d in deletions if d.strip()]
        if relevant:
            last_line = relevant[-1]
            if len(last_line) > 100:
                last_line = last_line[:100] + "..."
            return f"Before fix: `{last_line}`"
        return "Code issue (see fix for details)"

    def _guess_category(self, file_path: str, cwe_key: str) -> str:
        """根据 CWE key 和文件路径猜测分类"""
        # 优先使用 CWE 映射的分类
        security_cwe = {
            "sql_injection", "command_injection", "xss", "path_traversal",
            "hardcoded_secret", "weak_hash", "insecure_deserialize", "ssrf",
            "auth_bypass", "session_fixation", "missing_auth", "debug_mode",
            "eval_usage", "cors_misconfig", "missing_sanitization",
        }
        if cwe_key in security_cwe:
            return "security"

        reliability_cwe = {
            "resource_leak", "unreleased_lock", "missing_error_handling", "silent_exception",
        }
        if cwe_key in reliability_cwe:
            return "reliability"

        performance_cwe = {"n_plus_one_query", "memory_leak"}
        if cwe_key in performance_cwe:
            return "performance"

        # 回退到文件路径判断
        path_lower = file_path.lower()
        if any(kw in path_lower for kw in ["test", "spec", "fixture"]):
            return "testing"
        if any(kw in path_lower for kw in ["config", "setting", "env"]):
            return "configuration"

        return "bug"

    def _classify_scope(self, card: ExperienceCard, project_dir: str = "") -> str:
        """
        三档分类: universal / framework / project
        参考 CodeGuru 的 universal vs custom recommendations 分法
        """
        # 安全类 → 大部分是 universal
        if card.category == "security":
            return "universal"

        # 通用可靠性模式 → universal
        universal_fix_types = {
            "guard", "wrap", "close", "lock", "escape",
            "validate", "sanitize", "log",
        }
        if card.fix_type in universal_fix_types:
            return "universal"

        # 检测是否是框架相关
        framework_patterns = {
            "flask": ["@app.route", "@router", "request.args", "request.form", "flask"],
            "django": ["@login_required", "HttpResponse", "models.Model", "django"],
            "fastapi": ["@app.get", "@app.post", "Depends(", "fastapi"],
            "sqlalchemy": ["session.query", "db.session", "Column(", "sqlalchemy"],
            "pytest": ["@pytest.fixture", "pytest.raises", "conftest"],
        }

        # 简单检测（用 file_path 和 before/after code）
        code_context = f"{card.before_code} {card.after_code} {card.file_path}".lower()
        for framework, patterns in framework_patterns.items():
            for p in patterns:
                if p.lower() in code_context:
                    card.framework = framework
                    return "framework"

        return "project"

    def _deduplicate(self, cards: List[ExperienceCard]) -> List[ExperienceCard]:
        """
        智能去重 — 按 normalized pattern + category
        改进: 不再按 (pattern, file_path) 去重（太细），按 pattern 语义去重
        """
        seen = set()
        unique = []
        for card in cards:
            key = card.normalized_key()
            if key not in seen:
                seen.add(key)
                unique.append(card)
        return unique

    def _merge_similar(self, cards: List[ExperienceCard]) -> List[ExperienceCard]:
        """合并相似 pattern，累加 occurrence_count"""
        merged = {}
        for card in cards:
            key = card.normalized_key()
            if key in merged:
                merged[key].occurrence_count += 1
                # 保留置信度更高的
                merged[key].confidence = max(merged[key].confidence, card.confidence)
            else:
                merged[key] = card
        return list(merged.values())

    def persist(self, experiences: List[ExperienceCard], project_dir: str = ""):
        """
        持久化经验 — 双存储:
        - universal → data/cross_project_patterns.md
        - framework → data/cross_project_patterns.md (标注框架)
        - project → <project>/EXPERIENCE.md
        """
        universal = [c for c in experiences if c.scope == "universal"]
        framework = [c for c in experiences if c.scope == "framework"]
        project_specific = [c for c in experiences if c.scope == "project"]

        # 1. 保存通用 + 框架经验到 skill 目录
        cross_project = universal + framework
        if cross_project:
            self._persist_cross_project(cross_project)

        # 2. 保存项目特有经验
        if project_specific and project_dir:
            self._persist_project_specific(project_specific, project_dir)

    def _persist_cross_project(self, cards: List[ExperienceCard]):
        """持久化跨项目经验"""
        # 加载已有数据
        existing_cards = []
        if self.universal_file.exists():
            existing_cards = self._parse_cards_from_file(
                self.universal_file.read_text(encoding="utf-8")
            )

        # 合并: 已有的保留，新的追加
        existing_keys = {c.normalized_key() for c in existing_cards}
        for card in cards:
            key = card.normalized_key()
            if key in existing_keys:
                # 更新已有卡片的 occurrence_count
                for ec in existing_cards:
                    if ec.normalized_key() == key:
                        ec.occurrence_count += card.occurrence_count
                        ec.discovered_at = card.discovered_at  # 更新时间
                        break
            else:
                existing_cards.append(card)

        # 写入
        header = (
            f"# Cross-Project Experience Patterns\n\n"
            f"Universal bug fix experiences, auto-injected into every review.\n"
            f"Based on CWE/SEI CERT taxonomy.\n"
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"Total: {len(existing_cards)} patterns\n"
        )

        content = header + "\n---\n\n"
        # 按 category 分组
        by_category = {}
        for card in existing_cards:
            by_category.setdefault(card.category, []).append(card)

        for category, category_cards in sorted(by_category.items()):
            content += f"## {category.upper()}\n\n"
            for card in category_cards:
                content += card.to_markdown() + "\n\n"

        self._atomic_write(self.universal_file, content)

    def _persist_project_specific(self, cards: List[ExperienceCard], project_dir: str):
        """持久化项目特有经验"""
        project_path = Path(project_dir)
        exp_file = project_path / "EXPERIENCE.md"

        # 加载已有数据
        existing_cards = []
        if exp_file.exists():
            existing_cards = self._parse_cards_from_file(
                exp_file.read_text(encoding="utf-8")
            )

        # 合并
        existing_keys = {c.normalized_key() for c in existing_cards}
        for card in cards:
            key = card.normalized_key()
            if key in existing_keys:
                for ec in existing_cards:
                    if ec.normalized_key() == key:
                        ec.occurrence_count += card.occurrence_count
                        break
            else:
                existing_cards.append(card)

        header = (
            f"# {project_path.name} Bug Fix Experience\n\n"
            f"Project-specific bug fix experience. Auto-loaded during reviews.\n"
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"Total: {len(existing_cards)} patterns\n"
        )

        content = header + "\n---\n\n"
        for card in existing_cards:
            content += card.to_markdown() + "\n\n"

        self._atomic_write(exp_file, content)

    def load_experiences(self, project_dir: str = "") -> Dict:
        """
        加载经验，返回可直接注入 prompt 的内容。

        Returns:
            {
                "universal_cards": [ExperienceCard, ...],
                "project_cards": [ExperienceCard, ...],
                "total_available": int,
            }
        """
        result = {
            "universal_cards": [],
            "project_cards": [],
            "total_available": 0,
        }

        # 加载通用经验
        if self.universal_file.exists():
            content = self.universal_file.read_text(encoding="utf-8")
            result["universal_cards"] = self._parse_cards_from_file(content)

        # 加载项目特有经验
        if project_dir:
            exp_file = Path(project_dir) / "EXPERIENCE.md"
            if exp_file.exists():
                content = exp_file.read_text(encoding="utf-8")
                result["project_cards"] = self._parse_cards_from_file(content)

        result["total_available"] = (
            len(result["universal_cards"]) + len(result["project_cards"])
        )

        return result

    def get_review_prompt(
        self,
        project_dir: str = "",
        context_extensions: List[str] = None,
        context_modules: List[str] = None,
    ) -> str:
        """
        生成注入到审查 prompt 的经验内容。

        核心逻辑:
        1. 加载所有经验
        2. 按相关性排序
        3. 限制数量: 15 universal + 10 project
        4. 高优先级用完整格式，低优先级用紧凑格式
        """
        experiences = self.load_experiences(project_dir)
        parts = []

        # --- Universal patterns ---
        universal = experiences["universal_cards"]
        if universal:
            # 按相关性排序
            universal.sort(
                key=lambda c: c.relevance_score(context_extensions, context_modules),
                reverse=True,
            )
            # 限制数量
            top_universal = universal[:self.MAX_UNIVERSAL_INJECT]
            remaining_universal = universal[self.MAX_UNIVERSAL_INJECT:]

            parts.append(f"## Regression Prevention Checklist (from past fixes)")
            parts.append(f"Total universal patterns: {len(universal)}. "
                         f"Showing top {len(top_universal)} by relevance.\n")

            # 前 5 个用完整格式（最重要）
            for card in top_universal[:5]:
                parts.append(card.to_review_prompt())
                parts.append("")

            # 剩余用紧凑格式
            if len(top_universal) > 5:
                parts.append("### Additional patterns:")
                for card in top_universal[5:]:
                    parts.append(card.to_compact_prompt())

            if remaining_universal:
                parts.append(f"\n_... and {len(remaining_universal)} more (suppressed for context)_")

        # --- Project-specific patterns ---
        project = experiences["project_cards"]
        if project:
            project.sort(
                key=lambda c: c.relevance_score(context_extensions, context_modules),
                reverse=True,
            )
            top_project = project[:self.MAX_PROJECT_INJECT]

            parts.append(f"\n## Project-Specific Patterns ({Path(project_dir).name if project_dir else 'unknown'})")
            parts.append(f"Total: {len(project)}. Showing top {len(top_project)}.\n")

            # 前 3 个用完整格式
            for card in top_project[:3]:
                parts.append(card.to_review_prompt())
                parts.append("")

            if len(top_project) > 3:
                parts.append("### Additional project patterns:")
                for card in top_project[3:]:
                    parts.append(card.to_compact_prompt())

        return "\n".join(parts) if parts else ""

    def get_regression_check_prompt(self, project_dir: str = "") -> str:
        """
        生成回归检查 prompt — 让专家检查已修复的问题是否复现
        与 get_review_prompt 共用逻辑，但只关注 regression 场景
        """
        experiences = self.load_experiences(project_dir)
        parts = []

        all_cards = []
        all_cards.extend(experiences["universal_cards"])
        all_cards.extend(experiences["project_cards"])

        if not all_cards:
            return ""

        # 只选 HIGH+ 的经验进行回归检查
        regression_cards = [
            c for c in all_cards
            if c.severity in ("critical", "high")
        ]

        if not regression_cards:
            return ""

        parts.append("## Regression Check (high-priority past fixes)")
        parts.append("The following issues appeared in past reviews. Verify they haven't recurred:\n")

        for card in regression_cards[:10]:
            parts.append(card.to_review_prompt())
            parts.append("")

        return "\n".join(parts)

    def _parse_cards_from_file(self, content: str) -> List[ExperienceCard]:
        """从 markdown 文件解析 ExperienceCard"""
        cards = []
        current_card = {}

        for line in content.split("\n"):
            stripped = line.strip()

            # 匹配 ### EXP-001: pattern name 或 ### pattern name
            if stripped.startswith("### "):
                if current_card:
                    cards.append(ExperienceCard.from_dict(current_card))
                current_card = {}

                # 尝试解析 ID
                header_text = stripped[4:]
                if header_text.startswith("EXP-"):
                    parts = header_text.split(": ", 1)
                    current_card["id"] = parts[0].strip()
                    current_card["bug_pattern"] = parts[1].strip() if len(parts) > 1 else header_text
                else:
                    current_card["bug_pattern"] = header_text

            elif stripped.startswith("- **Problem**:") and current_card:
                current_card["bug_description"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("- **Fix**:") and current_card:
                current_card["fix_technique"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("- **Fix Type**:") and current_card:
                current_card["fix_type"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("- **CWE**:") and current_card:
                cwe_text = stripped.split(":", 1)[1].strip()
                # 解析 "CWE-476 (Name)"
                m = re.match(r"(CWE-\d+)\s*\((.+)\)", cwe_text)
                if m:
                    current_card["cwe_id"] = m.group(1)
                    current_card["cwe_name"] = m.group(2)
            elif stripped.startswith("- **Before**:") and current_card:
                current_card["before_code"] = stripped.split(":", 1)[1].strip().strip("`")
            elif stripped.startswith("- **After**:") and current_card:
                current_card["after_code"] = stripped.split(":", 1)[1].strip().strip("`")
            elif stripped.startswith("- **File**:") and current_card:
                file_text = stripped.split(":", 1)[1].strip().strip("`")
                # 解析 "path:line"
                if ":" in file_text:
                    current_card["file_path"], current_card["line_range"] = file_text.rsplit(":", 1)
                else:
                    current_card["file_path"] = file_text
            elif stripped.startswith("- **Category**:") and current_card:
                cat_text = stripped.split(":", 1)[1].strip()
                # 解析 "bug | Severity: high"
                parts = cat_text.split("|")
                current_card["category"] = parts[0].strip()
                if len(parts) > 1 and "Severity:" in parts[1]:
                    current_card["severity"] = parts[1].split(":")[-1].strip()
            elif stripped.startswith("- **Scope**:") and current_card:
                scope_text = stripped.split(":", 1)[1].strip()
                if "Universal" in scope_text or "universal" in scope_text.lower():
                    current_card["scope"] = "universal"
                elif "Framework" in scope_text or "framework" in scope_text.lower():
                    current_card["scope"] = "framework"
                    # 提取框架名
                    m = re.search(r"\((\w+)\)", scope_text)
                    if m:
                        current_card["framework"] = m.group(1)
                else:
                    current_card["scope"] = "project"
            elif stripped.startswith("- **Discovered**:") and current_card:
                current_card["discovered_at"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("- **Recurrence**:") and current_card:
                count_text = stripped.split(":", 1)[1].strip().replace("x", "")
                try:
                    current_card["occurrence_count"] = int(count_text)
                except ValueError:
                    pass

        if current_card and current_card.get("bug_pattern"):
            cards.append(ExperienceCard.from_dict(current_card))

        return cards

    def _append_to_file(self, file_path: Path, header: str, sections: List[str]):
        """追加内容到文件"""
        content = header + "\n---\n\n"
        content += "\n\n".join(sections)
        file_path.write_text(content, encoding="utf-8")

    def _atomic_write(self, file_path: Path, content: str):
        """原子写入：先写临时文件再 rename，防止并发写入损坏"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(file_path.parent),
            suffix=".tmp",
            prefix="exp_",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            if os.name == "nt" and file_path.exists():
                file_path.unlink()
            os.rename(tmp_path, str(file_path))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
