"""
TestingExpert — 测试评估员

审查测试基础设施、覆盖率、集成测试、回归测试有效性。
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional

from core._paths import SKILL_DIR, ensure_skill_path
ensure_skill_path()

from experts.base_expert import BaseExpert
from core.finding import Finding, FindingList, Severity, Category
from core.review_context import ReviewContext
from evolution.evolution_store import EvolutionState


class TestingExpert(BaseExpert):
    """测试评估员 — 测试基础设施、覆盖率、有效性"""

    name = "testing"
    name_cn = "测试评估员"
    description = "审查测试基础设施完整性、覆盖率、集成测试、回归测试"

    def review(self, source_files: List[str] = None) -> FindingList:
        # 检查项目是否有测试
        if not self.context.has_tests:
            self.add_finding(
                title="No test directory found",
                severity=Severity.HIGH,
                category=Category.TESTING,
                file_path="",
                description="项目没有测试目录（tests/ 或 test/），缺少任何测试",
                fix_suggestion="创建 tests/ 目录，添加基础测试框架（pytest推荐）和关键路径测试",
                effort="large",
            )
            return self.findings

        self._check_test_infrastructure()
        self._check_coverage_gaps(source_files)
        self._check_test_quality()
        self._check_test_fixtures()
        self._check_edge_case_coverage()

        return self.findings

    def _check_test_infrastructure(self):
        """检查测试基础设施"""
        # 检查 conftest.py
        has_conftest = any("conftest.py" in f for f in self.context.test_files)
        if not has_conftest:
            self.add_finding(
                title="Missing conftest.py",
                severity=Severity.MEDIUM,
                category=Category.TESTING,
                file_path=f"{self.context.test_dir}/",
                description="缺少 conftest.py，无法共享 fixtures",
                fix_suggestion="创建 conftest.py，定义通用 fixtures（如 app、client、db session）",
                effort="small",
            )

        # 检查测试框架配置
        if self.context.test_framework == "pytest":
            has_config = any(
                f in ["pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"]
                for f in self.context.config_files
            )
            if not has_config:
                self.add_finding(
                    title="Missing pytest configuration",
                    severity=Severity.LOW,
                    category=Category.TESTING,
                    file_path="",
                    description="没有 pytest 配置文件（pytest.ini 或 pyproject.toml [tool.pytest]）",
                    fix_suggestion="创建 pytest.ini 或在 pyproject.toml 中添加 [tool.pytest.ini_options]",
                    effort="small",
                )

    def _check_coverage_gaps(self, source_files: List[str] = None):
        """检查测试覆盖率缺口"""
        source = self.filter_by_extension(
            source_files or self.context.source_files, [".py"]
        )
        # 排除测试文件自身
        source = [f for f in source if not f.startswith("test") and "tests/" not in f]

        test_modules = set()
        for tf in self.context.test_files:
            # test_xxx.py -> xxx
            base = os.path.basename(tf)
            if base.startswith("test_"):
                test_modules.add(base[5:].replace(".py", ""))

        # 检查每个源文件是否有对应测试
        checked = set()
        for src_file in source:
            base = os.path.basename(src_file).replace(".py", "")
            if base in checked:
                continue
            checked.add(base)

            # 检查同名测试文件
            has_test = any(
                Path(tf).stem in (f"test_{base}", f"{base}_test")
                for tf in self.context.test_files
            )

            # 关键模块必须有测试
            is_critical = any(kw in base.lower() for kw in [
                "auth", "payment", "user", "security", "login",
                "api", "route", "handler", "service", "model",
            ])

            if not has_test and is_critical:
                self.add_finding(
                    title=f"Missing tests for critical module: {base}",
                    severity=Severity.HIGH,
                    category=Category.TESTING,
                    file_path=src_file,
                    description=f"关键模块 {base} 没有对应测试文件",
                    fix_suggestion=f"创建 tests/test_{base}.py，至少覆盖主要功能和错误场景",
                    effort="medium",
                )
            elif not has_test and len(source) > 5:
                # 非关键模块也报告，但严重度低
                self.add_finding(
                    title=f"Missing tests: {base}",
                    severity=Severity.LOW,
                    category=Category.TESTING,
                    file_path=src_file,
                    description=f"模块 {base} 没有对应测试文件",
                    fix_suggestion=f"考虑创建 tests/test_{base}.py",
                    effort="small",
                )

    def _check_test_quality(self):
        """检查测试质量"""
        for test_file in self.context.test_files:
            content = self.read_file(test_file)
            if not content:
                continue

            # 检查是否有实际断言
            assertion_count = 0
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped.startswith("assert ") or stripped.startswith("self.assert"):
                    assertion_count += 1

            if assertion_count == 0:
                self.add_finding(
                    title=f"No assertions in test file: {test_file}",
                    severity=Severity.HIGH,
                    category=Category.TESTING,
                    file_path=test_file,
                    description=f"测试文件 {test_file} 没有任何断言",
                    fix_suggestion="添加 assert 语句验证预期行为",
                    effort="small",
                )

            # 检查是否有空的测试函数
            empty_tests = re.findall(
                r"def\s+(test_\w+)\s*\([^)]*\)\s*:\s*\n\s*pass",
                content
            )
            if empty_tests:
                self.add_finding(
                    title=f"Empty test functions in {test_file}: {', '.join(empty_tests[:3])}",
                    severity=Severity.MEDIUM,
                    category=Category.TESTING,
                    file_path=test_file,
                    description=f"发现 {len(empty_tests)} 个空测试函数（只有 pass）",
                    fix_suggestion="为每个测试函数添加实际测试逻辑",
                    effort="small",
                )

            # 检查测试是否只测正常路径（缺少异常测试）
            has_error_test = any(
                kw in content.lower()
                for kw in ["error", "exception", "invalid", "missing", "empty", "none", "timeout"]
            )
            if not has_error_test and assertion_count > 3:
                self.add_finding(
                    title=f"No error/edge case tests in {test_file}",
                    severity=Severity.MEDIUM,
                    category=Category.TESTING,
                    file_path=test_file,
                    description="测试只覆盖正常路径，缺少异常场景测试",
                    fix_suggestion="添加异常输入、边界条件、空值等测试用例",
                    effort="medium",
                )

    def _check_test_fixtures(self):
        """检查测试 fixtures"""
        conftest_path = f"{self.context.test_dir}/conftest.py"
        conftest = self.read_file(conftest_path)

        if conftest:
            # 检查 fixture 是否使用了 scope
            fixtures = re.findall(r"@pytest\.fixture\s*\(([^)]*)\)", conftest)
            for fixture_args in fixtures:
                if "scope" not in fixture_args:
                    self.add_finding(
                        title="Fixture without explicit scope",
                        severity=Severity.LOW,
                        category=Category.TESTING,
                        file_path=conftest_path,
                        description="Fixture 没有指定 scope，默认为 function 级别",
                        fix_suggestion="根据需要设置 scope（module/class/session）以提高效率",
                        effort="small",
                    )

    def _check_edge_case_coverage(self):
        """检查边界条件覆盖"""
        if not self.context.source_files:
            return

        # 收集源代码中的关键模式
        critical_patterns = {
            "file operations": [r"open\(", r"\.read\(\)", r"\.write\("],
            "database": [r"execute\(", r"commit\(", r"query\("],
            "network": [r"requests\.", r"urllib", r"httpx\."],
            "json parsing": [r"json\.loads", r"json\.load"],
        }

        # 检查测试是否 mock 了外部依赖
        test_content = ""
        for tf in self.context.test_files:
            content = self.read_file(tf)
            if content:
                test_content += content + "\n"

        has_mock = "mock" in test_content.lower() or "patch" in test_content.lower() or "MagicMock" in test_content
        has_parametrize = "@pytest.mark.parametrize" in test_content

        if not has_mock and len(self.context.source_files) > 10:
            self.add_finding(
                title="No mock/patch usage in tests",
                severity=Severity.MEDIUM,
                category=Category.TESTING,
                file_path="",
                description="测试中没有使用 mock/patch，可能存在外部依赖耦合",
                fix_suggestion="使用 unittest.mock.patch 隔离外部依赖（数据库、API、文件系统）",
                effort="medium",
            )

        if not has_parametrize and len(self.context.test_files) > 3:
            self.add_finding(
                title="No parametrized tests found",
                severity=Severity.LOW,
                category=Category.TESTING,
                file_path="",
                description="没有使用 @pytest.mark.parametrize，可能缺少边界值测试",
                fix_suggestion="对关键函数使用参数化测试覆盖多种输入组合",
                effort="small",
            )
