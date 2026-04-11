"""
ReviewContext — 审查上下文管理

收集项目信息、技术栈、历史审查结果，为专家提供上下文。
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict


@dataclass
class ReviewContext:
    """审查上下文 — 描述被审查项目的状态"""

    # 项目基本信息
    project_name: str = ""
    project_dir: str = ""
    is_git_repo: bool = False
    git_branch: str = ""

    # 技术栈检测
    tech_stack: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    language_distribution: Dict[str, int] = field(default_factory=dict)  # 扩展名 → 文件数
    framework: str = ""
    test_framework: str = ""
    package_manager: str = ""

    # 文件统计
    source_files: List[str] = field(default_factory=list)
    total_files: int = 0
    total_lines: int = 0

    # 测试基础设施
    has_tests: bool = False
    test_dir: str = ""
    test_files: List[str] = field(default_factory=list)

    # 关键路径
    entry_points: List[str] = field(default_factory=list)
    api_routes: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    database_files: List[str] = field(default_factory=list)

    # 历史审查（从 evolution.md 加载）
    previous_review_count: int = 0
    previous_findings_count: int = 0
    unresolved_previous_findings: int = 0

    # 审查配置
    review_mode: str = "full"  # full | incremental | targeted
    focus_areas: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)

    # 文件内容缓存（由 ContextProfiler 预加载，供专家共享）
    _content_cache: Dict[str, str] = field(default_factory=dict)
    _lines_cache: Dict[str, list] = field(default_factory=list)

    def get_content(self, file_path: str) -> Optional[str]:
        """获取文件内容，优先从缓存读取"""
        if file_path in self._content_cache:
            return self._content_cache[file_path]
        return None

    def get_lines(self, file_path: str) -> Optional[List[str]]:
        """获取文件行列表，优先从缓存读取"""
        if file_path in self._lines_cache:
            return self._lines_cache[file_path]
        return None

    def to_prompt_context(self) -> str:
        """生成注入到专家 prompt 的上下文文本"""
        parts = []

        parts.append(f"## 项目上下文")
        parts.append(f"- 项目: {self.project_name}")
        parts.append(f"- 技术栈: {', '.join(self.tech_stack) or '未检测到'}")
        parts.append(f"- 框架: {self.framework or '未检测到'}")
        parts.append(f"- 测试框架: {self.test_framework or '未检测到'}")
        parts.append(f"- 源文件数: {self.total_files}")
        parts.append(f"- 代码行数: {self.total_lines}")
        parts.append(f"- Git: {'是 (' + self.git_branch + ')' if self.is_git_repo else '否'}")

        if self.has_tests:
            parts.append(f"- 测试: 有 ({len(self.test_files)} 个测试文件, 目录: {self.test_dir})")
        else:
            parts.append(f"- 测试: 无 (⚠️ 项目缺少测试)")

        if self.entry_points:
            parts.append(f"- 入口文件: {', '.join(self.entry_points[:5])}")
        if self.api_routes:
            parts.append(f"- API 路由: {', '.join(self.api_routes[:5])}")

        if self.previous_review_count > 0:
            parts.append(f"\n## 历史审查记录")
            parts.append(f"- 已完成 {self.previous_review_count} 次审查")
            parts.append(f"- 上次发现 {self.previous_findings_count} 个问题")
            if self.unresolved_previous_findings > 0:
                parts.append(f"- ⚠️ {self.unresolved_previous_findings} 个问题未解决，请复查")

        if self.review_mode != "full":
            parts.append(f"\n## 审查模式: {self.review_mode}")
            if self.focus_areas:
                parts.append(f"- 重点关注: {', '.join(self.focus_areas)}")

        return "\n".join(parts)


class ContextProfiler:
    """项目画像 — 自动检测项目特征"""

    # Python 项目特征文件
    PYTHON_MARKERS = {
        "requirements.txt": ("pip", "Python"),
        "pyproject.toml": ("pip/poetry", "Python"),
        "setup.py": ("pip/setuptools", "Python"),
        "setup.cfg": ("pip/setuptools", "Python"),
        "Pipfile": ("pipenv", "Python"),
    }

    # JS/TS 项目特征文件
    JS_MARKERS = {
        "package.json": ("npm/yarn/pnpm", "JavaScript/TypeScript"),
        "yarn.lock": ("yarn", "JavaScript/TypeScript"),
        "pnpm-lock.yaml": ("pnpm", "JavaScript/TypeScript"),
    }

    # 框架检测
    FRAMEWORK_PATTERNS = {
        "Flask": ["flask", "Flask"],
        "FastAPI": ["fastapi", "FastAPI"],
        "Django": ["django", "Django"],
        "Express": ["express", "Express"],
        "React": ["react", "React"],
        "Vue": ["vue", "Vue"],
        "Next.js": ["next", "Next"],
    }

    # 测试框架检测
    TEST_FRAMEWORK_PATTERNS = {
        "pytest": ["pytest", "conftest.py", "test_"],
        "unittest": ["unittest", "TestCase"],
        "jest": ["jest", "__tests__"],
        "vitest": ["vitest"],
    }

    # Python 源文件扩展名
    SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java"}

    # 排除目录
    EXCLUDE_DIRS = {
        "node_modules", ".git", "__pycache__", ".venv", "venv",
        "dist", "build", ".next", ".mypy_cache", ".pytest_cache",
        "test", "tests", "data", "static", "assets", "migrations",
    }

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.context = ReviewContext(project_dir=str(self.project_dir))

    def profile(self) -> ReviewContext:
        """执行完整的项目画像"""
        self._detect_project_name()
        self._detect_git()
        self._detect_tech_stack()
        self._detect_framework()
        self._detect_test_framework()
        self._scan_source_files()
        self._detect_entry_points()
        self._detect_config_files()
        self._preload_source_contents()

        return self.context

    def _detect_project_name(self):
        name = self.project_dir.name
        # 尝试从 pyproject.toml 或 package.json 获取更准确的名字
        for marker_file in ["pyproject.toml", "package.json"]:
            p = self.project_dir / marker_file
            if p.exists():
                name = p.stem.replace(".toml", "").replace(".json", "")
                break
        self.context.project_name = name

    def _detect_git(self):
        git_dir = self.project_dir / ".git"
        self.context.is_git_repo = git_dir.exists()

    def _detect_tech_stack(self):
        # 检查 Python 标记
        for marker, (pm, lang) in self.PYTHON_MARKERS.items():
            if (self.project_dir / marker).exists():
                self.context.package_manager = pm
                if "Python" not in self.context.languages:
                    self.context.languages.append("Python")
                if pm not in self.context.tech_stack:
                    self.context.tech_stack.append(pm)
                break

        # 检查 JS/TS 标记
        for marker, (pm, lang) in self.JS_MARKERS.items():
            if (self.project_dir / marker).exists():
                if not self.context.package_manager:
                    self.context.package_manager = pm
                if "JavaScript" not in self.context.languages:
                    self.context.languages.append(lang)
                if pm not in self.context.tech_stack:
                    self.context.tech_stack.append(pm)
                break

    def _detect_framework(self):
        # 在 requirements.txt 或 pyproject.toml 中搜索
        for req_file in ["requirements.txt", "pyproject.toml"]:
            p = self.project_dir / req_file
            if not p.exists():
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="ignore").lower()
                for framework, patterns in self.FRAMEWORK_PATTERNS.items():
                    for pattern in patterns:
                        if pattern.lower() in content:
                            self.context.framework = framework
                            return
            except Exception:
                continue

        # 检查 package.json 的 dependencies
        pkg = self.project_dir / "package.json"
        if pkg.exists():
            try:
                import json
                data = json.loads(pkg.read_text(encoding="utf-8"))
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                for framework, patterns in self.FRAMEWORK_PATTERNS.items():
                    for pattern in patterns:
                        if pattern.lower() in deps:
                            self.context.framework = framework
                            return
            except Exception:
                pass

    def _detect_test_framework(self):
        # 检查测试目录
        for test_dir in ["tests", "test", "__tests__"]:
            p = self.project_dir / test_dir
            if p.exists() and p.is_dir():
                self.context.has_tests = True
                self.context.test_dir = test_dir
                break

        if self.context.has_tests:
            # 扫描测试文件确定框架
            test_path = self.project_dir / self.context.test_dir
            for root, dirs, files in os.walk(str(test_path)):
                for f in files:
                    if not any(f.endswith(ext) for ext in self.SOURCE_EXTENSIONS):
                        continue
                    self.context.test_files.append(str((Path(root) / f).relative_to(self.project_dir)))

            # 检测测试框架
            for framework, patterns in self.TEST_FRAMEWORK_PATTERNS.items():
                for pattern in patterns:
                    # 检查文件名
                    for tf in self.context.test_files:
                        if pattern in tf:
                            self.context.test_framework = framework
                            return
                    # 检查 requirements
                    for req_file in ["requirements.txt", "pyproject.toml"]:
                        p = self.project_dir / req_file
                        if p.exists():
                            try:
                                content = p.read_text(encoding="utf-8", errors="ignore").lower()
                                if pattern.lower() in content:
                                    self.context.test_framework = framework
                                    return
                            except Exception:
                                continue

    def _scan_source_files(self):
        """扫描源文件统计"""
        count = 0
        lines = 0
        for root, dirs, files in os.walk(str(self.project_dir)):
            # 排除目录
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS and not d.startswith(".")]

            for f in files:
                if not any(f.endswith(ext) for ext in self.SOURCE_EXTENSIONS):
                    continue
                rel = str((Path(root) / f).relative_to(self.project_dir))
                self.context.source_files.append(rel)
                count += 1
                # 统计语言分布
                _, ext = os.path.splitext(f)
                ext_lower = ext.lower()
                self.context.language_distribution[ext_lower] = self.context.language_distribution.get(ext_lower, 0) + 1
                # 统计行数
                try:
                    file_lines = (Path(root) / f).read_text(encoding="utf-8", errors="ignore").count("\n")
                    lines += file_lines
                except Exception:
                    lines += 0

        self.context.total_files = count
        self.context.total_lines = lines

    def _detect_entry_points(self):
        """检测入口文件"""
        common_entries = [
            "main.py", "app.py", "server.py", "run.py", "manage.py",
            "index.js", "index.ts", "server.js", "app.js",
        ]
        for entry in common_entries:
            if (self.project_dir / entry).exists():
                self.context.entry_points.append(entry)

        # 检查 Flask/FastAPI app 对象
        for py_file in ["app.py", "server.py", "main.py"]:
            p = self.project_dir / py_file
            if p.exists():
                try:
                    content = p.read_text(encoding="utf-8", errors="ignore")
                    if "app.route" in content or "app.get" in content or "@router" in content:
                        self.context.api_routes.append(py_file)
                except Exception:
                    continue

    def _detect_config_files(self):
        """检测配置文件"""
        config_patterns = [
            ".env", ".env.local", "config.py", "config.json", "config.yaml",
            "settings.py", "docker-compose.yml", "Dockerfile", "Makefile",
            "tsconfig.json", ".eslintrc", ".prettierrc",
        ]
        for pattern in config_patterns:
            if (self.project_dir / pattern).exists():
                self.context.config_files.append(pattern)

    def _preload_source_contents(self):
        """预加载所有源文件内容到缓存，供专家共享读取"""
        for rel_path in self.context.source_files:
            full_path = self.project_dir / rel_path
            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                self.context._content_cache[rel_path] = content
                self.context._lines_cache[rel_path] = content.split("\n")
            except Exception:
                pass
