"""
CodeQualityExpert — 代码质量审查员

审查 bug、性能瓶颈、错误处理、输入验证、代码规范。
"""

import re
import os
from typing import List, Dict, Optional

from core._paths import SKILL_DIR, ensure_skill_path
ensure_skill_path()

from experts.base_expert import BaseExpert
from core.finding import Finding, FindingList, Severity, Category
from core.review_context import ReviewContext
from evolution.evolution_store import EvolutionState


class CodeQualityExpert(BaseExpert):
    """代码质量审查员 — Bug、性能、错误处理"""

    name = "code_quality"
    name_cn = "代码质量审查员"
    description = "审查 bug、性能瓶颈、错误处理完整性、输入验证、代码规范"

    # 性能反模式
    PERFORMANCE_PATTERNS = {
        "N+1 query": {
            "pattern": r"(for\s+\w+\s+in\s+.*?:\s*\n\s*\n*.+query|\.filter\(.*for\s+\w+\s+in)",
            "severity": Severity.HIGH,
            "category": Category.PERFORMANCE,
            "suggestion": "使用 JOIN 或预加载避免 N+1 查询",
        },
        "bare except": {
            "pattern": r"except\s*:",
            "severity": Severity.MEDIUM,
            "category": Category.BUG,
            "suggestion": "捕获具体异常类型，不要用裸 except",
        },
        "mutable default arg": {
            "pattern": r"def\s+\w+\(.*=\s*(\[\]|\{\}|set\(\))",
            "severity": Severity.MEDIUM,
            "category": Category.BUG,
            "suggestion": "使用 None 作为默认值，在函数体内初始化",
        },
    }

    # 安全反模式（基础检查，不替代 security_expert）
    SECURITY_PATTERNS = {
        "hardcoded password": {
            "pattern": r'(password\s*=\s*["\'][^"\']+["\']|pwd\s*=\s*["\'][^"\']+["\'])',
            "severity": Severity.CRITICAL,
            "category": Category.SECURITY,
            "suggestion": "密码应存储在环境变量或 .env 文件中",
        },
        "hardcoded secret": {
            "pattern": r'(secret\s*=\s*["\'][^"\']+["\']|api_key\s*=\s*["\'][^"\']+["\']|token\s*=\s*["\'][^"\']+["\'])',
            "severity": Severity.CRITICAL,
            "category": Category.SECURITY,
            "suggestion": "密钥应存储在环境变量中，不要硬编码",
            "skip_comments": True,  # 跳过注释中的示例
        },
        "eval usage": {
            "pattern": r"\beval\s*\(",
            "severity": Severity.HIGH,
            "category": Category.SECURITY,
            "suggestion": "避免使用 eval()，存在代码注入风险",
        },
        "sql injection risk": {
            "pattern": r'(execute\s*\(\s*["\'].*%|execute\s*\(\s*f["\'].*\{|\.format\s*\(.*execute)',
            "severity": Severity.CRITICAL,
            "category": Category.SECURITY,
            "suggestion": "使用参数化查询，不要拼接 SQL",
        },
        "debug mode": {
            "pattern": r"(DEBUG\s*=\s*True|app\.debug\s*=\s*True)",
            "severity": Severity.HIGH,
            "category": Category.SECURITY,
            "suggestion": "生产环境必须关闭 DEBUG 模式",
        },
    }

    # 错误处理反模式
    ERROR_PATTERNS = {
        "silent except": {
            "pattern": r"except.*:\s*\n\s*pass\s*$",
            "severity": Severity.MEDIUM,
            "category": Category.BUG,
            "suggestion": "至少记录日志，不要静默吞掉异常",
        },
        "missing finally": {
            "pattern": r"with\s+open\s*\(",
            "severity": Severity.LOW,
            "category": Category.RELIABILITY,
            "suggestion": "使用 with 语句自动管理资源",
        },
    }

    def review(self, source_files: List[str] = None) -> FindingList:
        files = self.scan_all_files(source_files)
        py_files = self.filter_by_extension(files, [".py"])

        for file_path in py_files:
            self._check_patterns(file_path, self.PERFORMANCE_PATTERNS)
            self._check_patterns(file_path, self.SECURITY_PATTERNS)
            self._check_patterns(file_path, self.ERROR_PATTERNS)
            self._check_complexity(file_path)
            self._check_input_validation(file_path)

        return self.findings

    def _check_patterns(self, file_path: str, patterns: Dict[str, Dict]):
        """检查文件中的反模式"""
        lines = self.read_file_lines(file_path)
        if not lines:
            return

        for pattern_name, config in patterns.items():
            matches = self.find_pattern_in_file(file_path, config["pattern"])
            for match in matches:
                # 过滤已内化的反模式
                if self._is_suppressed(config["category"], pattern_name):
                    continue

                # 跳过注释行
                line_no = match["line"] - 1
                if line_no < len(lines):
                    raw_line = lines[line_no].strip()
                    if raw_line.startswith("#") or raw_line.startswith("//") or raw_line.startswith("*"):
                        continue
                    # 跳过文档字符串中的示例（三引号内）
                    if self._in_docstring(lines, line_no):
                        continue

                # 过滤明显的占位符/示例值
                matched_value = match["match"]
                if self._is_placeholder(matched_value):
                    continue

                self.add_finding(
                    title=f"{pattern_name}: {match['content'][:80]}",
                    severity=config["severity"],
                    category=config["category"],
                    file_path=file_path,
                    line_range=str(match["line"]),
                    code_snippet=match["content"],
                    description=f"在 {file_path}:{match['line']} 发现 {pattern_name}",
                    fix_suggestion=config["suggestion"],
                )

    def _is_suppressed(self, category: Category, keyword: str) -> bool:
        """检查是否被反模式抑制"""
        if not self.evolution:
            return False
        for ap in self.evolution.anti_patterns:
            if ap.get("category", "").lower() == category.value.lower():
                if keyword.lower() in ap.get("description", "").lower():
                    return True
        return False

    def _is_placeholder(self, value: str) -> bool:
        """检查匹配到的值是否是占位符/示例"""
        placeholders = [
            "xxx", "xxxx", "example", "test", "dummy", "placeholder",
            "your-", "not-needed", "none", "null", "false", "true",
            "changeme", "todo", "fixme",
            "123456", "abc123", "sk-xxx", "sk-test",
            '"sk-', "'sk-",
        ]
        value_lower = value.lower().strip("'\"")
        if len(value_lower) < 6:
            return True  # 太短的不可能是真实密钥
        for p in placeholders:
            if p in value_lower:
                return True
        return False

    def _check_complexity(self, file_path: str):
        """检查函数复杂度（简单的行数 + 嵌套深度检查）"""
        lines = self.read_file_lines(file_path)
        if not lines:
            return

        # 检查过长函数（>50行）
        func_start = None
        func_lines = 0
        func_indent = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("async def "):
                if func_start and func_lines > 50:
                    self.add_finding(
                        title=f"Long function ({func_lines} lines)",
                        severity=Severity.MEDIUM,
                        category=Category.MAINTAINABILITY,
                        file_path=file_path,
                        line_range=f"{func_start}-{i-1}",
                        description=f"函数从第 {func_start} 行开始，共 {func_lines} 行",
                        fix_suggestion="拆分为更小的函数，每个函数只做一件事",
                        effort="medium",
                    )
                func_start = i
                func_lines = 0
                func_indent = len(line) - len(line.lstrip())
            elif func_start:
                if stripped and not stripped.startswith("#"):
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= func_indent and stripped and not stripped.startswith((")", "]", "}", "'", '"')):
                        # Function ended, don't report here (reported when next def found)
                        func_start = None
                        func_lines = 0
                    else:
                        func_lines += 1

        # 最后一个函数
        if func_start and func_lines > 50:
            self.add_finding(
                title=f"Long function ({func_lines} lines)",
                severity=Severity.MEDIUM,
                category=Category.MAINTAINABILITY,
                file_path=file_path,
                line_range=f"{func_start}-{len(lines)}",
                fix_suggestion="拆分为更小的函数",
                effort="medium",
            )

    def _check_input_validation(self, file_path: str):
        """检查输入验证"""
        lines = self.read_file_lines(file_path)
        if not lines:
            return

        content = "\n".join(lines)

        # Flask 路由参数未验证
        if "@app.route" in content or "@router" in content:
            # 检查是否有 request.args 或 request.form 但没有验证
            if "request.args" in content or "request.form" in content:
                if "validate" not in content.lower() and "int(" not in content:
                    # 不报太细，只在文件级别报一次
                    pass  # 避免噪音

        # 检查 int() 转换是否安全
        if "int(" in content:
            matches = self.find_pattern_in_file(file_path, r"int\s*\(\s*(request|params|args)")
            for match in matches:
                self.add_finding(
                    title=f"Unsafe int conversion from user input",
                    severity=Severity.MEDIUM,
                    category=Category.BUG,
                    file_path=file_path,
                    line_range=str(match["line"]),
                    code_snippet=match["content"],
                    description=f"用户输入直接转 int 可能抛出 ValueError",
                    fix_suggestion="使用 try/except 或自定义验证函数",
                )
