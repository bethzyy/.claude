"""
Verifier — 修复验证器

职责：
1. AST 语法检查
2. pytest 执行
3. 回归审查（复用现有 expert 类，对修改文件重新扫描）
"""

import ast
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """测试结果"""
    passed: bool
    total: int = 0
    failed: int = 0
    error: Optional[str] = None


class Verifier:
    """修复验证器"""

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)

    def validate_syntax(self, file_path: str) -> bool:
        """
        AST 语法检查。

        Args:
            file_path: 相对或绝对路径

        Returns:
            True if syntax is valid
        """
        full_path = self.project_dir / file_path if not Path(file_path).is_absolute() else Path(file_path)
        if not full_path.exists():
            logger.warning(f"验证文件不存在: {file_path}")
            return False

        ext = full_path.suffix.lower()
        if ext != ".py":
            # 非 Python 文件跳过 AST 检查
            return True

        try:
            source = full_path.read_text(encoding="utf-8")
            ast.parse(source)
            return True
        except SyntaxError as e:
            logger.error(f"语法错误 {file_path}: {e}")
            return False

    def run_tests(self, test_dir: str = "tests", timeout: int = 120) -> TestResult:
        """
        执行 pytest。

        Args:
            test_dir: 测试目录（相对于 project_dir）
            timeout: 超时秒数

        Returns:
            TestResult
        """
        test_path = self.project_dir / test_dir
        if not test_path.exists():
            logger.info(f"测试目录不存在: {test_path}，跳过测试")
            return TestResult(passed=True, total=0, failed=0)

        try:
            result = subprocess.run(
                ["python", "-m", "pytest", str(test_path), "-x", "--tb=short", "-q"],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = result.stdout + result.stderr

            # 解析 pytest 输出
            total = 0
            failed = 0
            for line in output.splitlines():
                # 匹配 "X passed, Y failed"
                import re
                m = re.search(r"(\d+) passed", line)
                if m:
                    total = int(m.group(1))
                m = re.search(r"(\d+) failed", line)
                if m:
                    failed = int(m.group(1))

            passed = result.returncode == 0 and failed == 0
            error = None if passed else output[-500:]  # 最后 500 字符

            if not passed:
                logger.warning(f"测试失败: {failed}/{total} failed")
                if error:
                    logger.debug(f"测试输出:\n{error}")

            return TestResult(passed=passed, total=total, failed=failed, error=error)

        except subprocess.TimeoutExpired:
            logger.error(f"测试超时 ({timeout}s)")
            return TestResult(passed=False, total=0, failed=0, error=f"Timeout after {timeout}s")
        except Exception as e:
            logger.error(f"测试执行异常: {e}")
            return TestResult(passed=False, total=0, failed=0, error=str(e))

    def re_review(self, modified_files: list[str]) -> list[dict]:
        """
        对修改过的文件重新执行专家审查。

        复用现有 expert 类进行快速模式匹配扫描，
        只返回 Critical 和 High 级别的新发现。

        Args:
            modified_files: 修改过的文件相对路径列表

        Returns:
            新发现的 finding dict 列表
        """
        if not modified_files:
            return []

        new_findings = []

        try:
            # 导入现有专家（在 skill 目录下执行）
            import sys
            skill_dir = Path(__file__).resolve().parent.parent
            if str(skill_dir) not in sys.path:
                sys.path.insert(0, str(skill_dir))

            from experts.security_expert import SecurityExpert
            from experts.code_quality_expert import CodeQualityExpert

            experts = [
                ("security", SecurityExpert(self.project_dir)),
                ("code_quality", CodeQualityExpert(self.project_dir)),
            ]

            for expert_name, expert in experts:
                try:
                    expert.review_files(modified_files)
                    if hasattr(expert, "findings"):
                        for f in expert.findings:
                            sev = getattr(f, "severity", None)
                            sev_val = sev.value if hasattr(sev, "value") else str(sev)
                            if sev_val in ("critical", "high"):
                                f_dict = f.to_dict() if hasattr(f, "to_dict") else {}
                                f_dict["expert"] = f"re_review_{expert_name}"
                                new_findings.append(f_dict)
                except Exception as e:
                    logger.debug(f"回归审查 {expert_name} 跳过: {e}")

        except ImportError as e:
            logger.warning(f"无法导入专家模块进行回归审查: {e}")

        return new_findings
