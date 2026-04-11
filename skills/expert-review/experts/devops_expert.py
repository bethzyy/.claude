"""
DevOpsExpert — 运维分析师

审查错误处理、配置管理、资源清理、部署就绪。
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


class DevOpsExpert(BaseExpert):
    """运维分析师 — 错误处理、配置管理、资源清理、部署就绪"""

    name = "devops"
    name_cn = "运维分析师"
    description = "审查错误处理完整性、配置管理、资源泄漏、部署就绪"

    def review(self, source_files: List[str] = None) -> FindingList:
        files = self.scan_all_files(source_files)
        py_files = self.filter_by_extension(files, [".py"])

        self._check_error_handling(py_files)
        self._check_resource_management(py_files)
        self._check_configuration_management(files)
        self._check_deployment_readiness()
        self._check_logging(py_files)
        self._check_health_checks()

        return self.findings

    def _check_error_handling(self, files: List[str]):
        """检查错误处理完整性"""
        for file_path in files:
            content = self.read_file(file_path)
            if not content:
                continue

            lines = content.split("\n")

            # 检查裸 except
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("except:"):
                    self.add_finding(
                        title="Bare except clause",
                        severity=Severity.MEDIUM,
                        category=Category.RELIABILITY,
                        file_path=file_path,
                        line_range=str(i),
                        code_snippet=stripped,
                        description="裸 except 会捕获所有异常，包括 KeyboardInterrupt",
                        fix_suggestion="捕获具体异常类型，如 except Exception: 或 except ValueError:",
                        effort="small",
                    )

            # 检查 HTTP 请求是否处理错误
            if "requests." in content:
                has_error_handling = any(
                    kw in content for kw in [".raise_for_status()", "try:", "except", "status_code"]
                )
                if not has_error_handling:
                    self.add_finding(
                        title="HTTP requests without error handling",
                        severity=Severity.MEDIUM,
                        category=Category.RELIABILITY,
                        file_path=file_path,
                        description="使用 requests 但没有错误处理",
                        fix_suggestion="添加 try/except 和 .raise_for_status() 或检查 status_code",
                        effort="small",
                    )

            # 检查数据库操作是否有错误处理
            if "execute(" in content or ".commit(" in content:
                db_lines = [(i, l) for i, l in enumerate(lines, 1) if "execute(" in l or ".commit(" in l]
                if db_lines:
                    # 检查附近是否有 try/except
                    has_try = any("try:" in lines[max(0, i-5):i+1] for i, _ in db_lines)
                    if not has_try:
                        self.add_finding(
                            title="Database operations without error handling",
                            severity=Severity.HIGH,
                            category=Category.RELIABILITY,
                            file_path=file_path,
                            description="数据库操作没有 try/except 保护",
                            fix_suggestion="用 try/except 包裹数据库操作，失败时 rollback",
                            effort="small",
                        )

    def _check_resource_management(self, files: List[str]):
        """检查资源管理"""
        for file_path in files:
            content = self.read_file(file_path)
            if not content:
                continue

            # 检查 open() 是否使用 with
            open_matches = re.finditer(r"(\w+)\s*=\s*open\(", content)
            for match in open_matches:
                var_name = match.group(1)
                # 检查是否在 with 语句中
                line_num = content[:match.start()].count("\n") + 1
                # 简单检查：如果前面有 with，说明在 with 块中
                nearby = content[max(0, match.start()-100):match.start()]
                if "with " not in nearby:
                    self.add_finding(
                        title=f"File handle not using 'with' statement",
                        severity=Severity.MEDIUM,
                        category=Category.RELIABILITY,
                        file_path=file_path,
                        line_range=str(line_num),
                        code_snippet=match.group()[:60],
                        description=f"变量 {var_name} 使用 open() 但未在 with 块中",
                        fix_suggestion="使用 with open(...) as f: 确保文件正确关闭",
                        effort="small",
                    )

            # 检查是否有全局数据库连接
            if "create_engine" in content or "connect(" in content:
                global_conn = re.search(
                    r"^(engine|conn|db|connection)\s*=\s*(create_engine|connect)",
                    content,
                    re.MULTILINE,
                )
                if global_conn:
                    self.add_finding(
                        title="Global database connection at module level",
                        severity=Severity.MEDIUM,
                        category=Category.RELIABILITY,
                        file_path=file_path,
                        description="数据库连接在模块级别创建，可能导致连接泄漏",
                        fix_suggestion="使用连接池或应用工厂模式管理数据库连接",
                        effort="medium",
                    )

    def _check_configuration_management(self, files: List[str]):
        """检查配置管理"""
        # 检查是否有硬编码配置
        hardcoded_configs = {
            "host": r"(HOST|host|server|SERVER)\s*=\s*['\"]localhost['\"]",
            "port": r"(PORT|port)\s*=\s*['\"]?\d{4,5}['\"]?",
            "database_url": r"(DATABASE_URL|DB_URL|SQLALCHEMY_DATABASE_URI)\s*=\s*['\"][^'\"]+['\"]",
            "debug": r"DEBUG\s*=\s*True",
        }

        config_files = ["config.py", "settings.py", "app.py", "server.py", "main.py"]
        for config_file in config_files:
            content = self.read_file(config_file)
            if not content:
                continue

            for config_name, pattern in hardcoded_configs.items():
                matches = self.find_pattern_in_file(config_file, pattern)
                for match in matches:
                    self.add_finding(
                        title=f"Hardcoded configuration: {config_name}",
                        severity=Severity.MEDIUM,
                        category=Category.CONFIGURATION,
                        file_path=config_file,
                        line_range=str(match["line"]),
                        code_snippet=match["content"][:60],
                        description=f"配置项 {config_name} 被硬编码",
                        fix_suggestion="使用环境变量或 .env 文件管理配置",
                        effort="small",
                    )

    def _check_deployment_readiness(self):
        """检查部署就绪性"""
        # 检查是否有 Dockerfile
        has_dockerfile = self.read_file("Dockerfile") is not None
        has_docker_compose = self.read_file("docker-compose.yml") is not None

        if not has_dockerfile and self.context.total_files > 10:
            self.add_finding(
                title="No Dockerfile found",
                severity=Severity.LOW,
                category=Category.CONFIGURATION,
                file_path="",
                description="项目没有 Dockerfile，可能影响部署一致性",
                fix_suggestion="添加 Dockerfile 实现容器化部署",
                effort="medium",
            )

        # 检查是否有 requirements.txt 或 pyproject.toml
        has_requirements = (
            self.read_file("requirements.txt") is not None
            or self.read_file("pyproject.toml") is not None
        )
        if not has_requirements and self.context.total_files > 5:
            self.add_finding(
                title="No dependency file found",
                severity=Severity.HIGH,
                category=Category.CONFIGURATION,
                file_path="",
                description="缺少依赖管理文件（requirements.txt 或 pyproject.toml）",
                fix_suggestion="创建 requirements.txt 并固定版本号",
                effort="small",
            )

        # 检查是否有 .gitignore
        has_gitignore = self.read_file(".gitignore") is not None
        if not has_gitignore:
            self.add_finding(
                title="No .gitignore file",
                severity=Severity.MEDIUM,
                category=Category.CONFIGURATION,
                file_path="",
                description="缺少 .gitignore 文件",
                fix_suggestion="创建 .gitignore，排除 __pycache__、.env、*.pyc 等",
                effort="small",
            )

    def _check_logging(self, files: List[str]):
        """检查日志记录"""
        for file_path in files:
            content = self.read_file(file_path)
            if not content:
                continue

            # 统计 print vs logging
            print_count = len(re.findall(r"\bprint\s*\(", content))
            logging_count = len(re.findall(r"\b(logging|logger|log)\.(info|warning|error|debug|critical)\s*\(", content))

            if print_count > 5 and logging_count == 0:
                self.add_finding(
                    title=f"Using print() instead of logging ({print_count} occurrences)",
                    severity=Severity.LOW,
                    category=Category.RELIABILITY,
                    file_path=file_path,
                    description=f"发现 {print_count} 处 print() 调用，建议使用 logging 模块",
                    fix_suggestion="将 print() 替换为 logging.info/warning/error()",
                    effort="medium",
                )

    def _check_health_checks(self):
        """检查健康检查端点"""
        # 如果是 Web 项目，检查是否有健康检查
        if self.context.framework in ("Flask", "FastAPI", "Django"):
            has_health = False
            for f in self.context.source_files:
                content = self.read_file(f)
                if content and any(kw in content.lower() for kw in ["/health", "/ping", "/status", "healthcheck"]):
                    has_health = True
                    break

            if not has_health:
                self.add_finding(
                    title="No health check endpoint",
                    severity=Severity.LOW,
                    category=Category.RELIABILITY,
                    file_path="",
                    description=f"{self.context.framework} 项目没有健康检查端点",
                    fix_suggestion="添加 /health 端点用于容器编排和监控",
                    effort="small",
                )
