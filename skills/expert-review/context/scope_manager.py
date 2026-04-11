"""
ScopeManager — 审查范围管理

支持 full / incremental / targeted 三种审查模式。
"""

import subprocess
import os
from pathlib import Path
from typing import List, Optional, Dict


class ScopeManager:
    """审查范围管理"""

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)

    def get_files(
        self,
        mode: str = "full",
        focus_areas: List[str] = None,
        exclude_patterns: List[str] = None,
        since_ref: str = None,
        all_source_files: List[str] = None,
    ) -> List[str]:
        """
        根据审查模式获取要审查的文件列表。

        Args:
            mode: full | incremental | targeted
            focus_areas: 重点关注区域（如 ["security", "testing"]）
            exclude_patterns: 排除模式
            since_ref: 增量审查的起始点（git ref 或 "last_review"）
            all_source_files: 全量文件列表（如果已有，避免重复扫描）
        """
        if mode == "full":
            return self._full_scope(all_source_files, exclude_patterns)
        elif mode == "incremental":
            return self._incremental_scope(since_ref, all_source_files, exclude_patterns)
        elif mode == "targeted":
            return self._targeted_scope(focus_areas, all_source_files, exclude_patterns)
        else:
            return all_source_files or []

    def _full_scope(
        self,
        all_files: List[str] = None,
        exclude_patterns: List[str] = None,
    ) -> List[str]:
        """全量审查"""
        files = all_files or self._scan_source_files()
        return self._apply_excludes(files, exclude_patterns)

    def _incremental_scope(
        self,
        since_ref: str = None,
        all_files: List[str] = None,
        exclude_patterns: List[str] = None,
    ) -> List[str]:
        """增量审查 — 只审查变更文件"""
        changed = self._get_changed_files(since_ref)
        if not changed:
            return []

        # 如果提供了全量文件列表，取交集
        if all_files:
            changed = [f for f in changed if f in all_files]

        return self._apply_excludes(changed, exclude_patterns)

    def _targeted_scope(
        self,
        focus_areas: List[str] = None,
        all_files: List[str] = None,
        exclude_patterns: List[str] = None,
    ) -> List[str]:
        """定向审查 — 根据关注领域筛选"""
        files = all_files or self._scan_source_files()

        if not focus_areas:
            return self._apply_excludes(files, exclude_patterns)

        # 根据关注领域匹配文件
        targeted = []
        area_file_patterns = {
            "security": ["auth", "login", "password", "security", "token", "session", "crypto", "api"],
            "testing": ["test_", "_test.py", "tests/", "conftest.py"],
            "performance": ["query", "cache", "async", "worker", "batch"],
            "architecture": ["model", "service", "controller", "route", "config"],
            "documentation": ["README", "CHANGELOG", "CLAUDE", "docs/"],
        }

        for area in focus_areas:
            patterns = area_file_patterns.get(area.lower(), [])
            for f in files:
                if any(p.lower() in f.lower() for p in patterns):
                    if f not in targeted:
                        targeted.append(f)

        # 如果定向筛选结果为空，回退到全量
        if not targeted:
            targeted = files

        return self._apply_excludes(targeted, exclude_patterns)

    def _get_changed_files(self, since_ref: str = None) -> List[str]:
        """获取变更文件列表"""
        if not (self.project_dir / ".git").exists():
            return []

        try:
            if since_ref == "last_review":
                # 获取最近一次 commit 的 parent
                result = subprocess.run(
                    ["git", "log", "--oneline", "-1", "--pretty=%H"],
                    cwd=str(self.project_dir),
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    commit_hash = result.stdout.strip()
                    # 获取该 commit 与前一个 commit 的 diff
                    result = subprocess.run(
                        ["git", "diff", "--name-only", f"{commit_hash}^..{commit_hash}"],
                        cwd=str(self.project_dir),
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0:
                        return [f for f in result.stdout.strip().split("\n") if f]
            elif since_ref:
                result = subprocess.run(
                    ["git", "diff", "--name-only", since_ref],
                    cwd=str(self.project_dir),
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    return [f for f in result.stdout.strip().split("\n") if f]

            # 默认：最近一次 commit 的变更
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1..HEAD"],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return [f for f in result.stdout.strip().split("\n") if f]
        except (subprocess.TimeoutExpired, Exception):
            pass

        return []

    def _scan_source_files(self) -> List[str]:
        """扫描项目源文件"""
        extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java"}
        exclude_dirs = {
            "node_modules", ".git", "__pycache__", ".venv", "venv",
            "dist", "build", ".next", ".mypy_cache", ".pytest_cache",
            "test", "tests", "data", "static", "assets", "migrations",
        }

        files = []
        for root, dirs, filenames in os.walk(str(self.project_dir)):
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
            for f in filenames:
                if any(f.endswith(ext) for ext in extensions):
                    rel = str((Path(root) / f).relative_to(self.project_dir))
                    files.append(rel)
        return files

    def _apply_excludes(self, files: List[str], patterns: List[str] = None) -> List[str]:
        """应用排除模式"""
        if not patterns:
            return files

        import re
        result = []
        for f in files:
            excluded = False
            for pattern in patterns:
                if re.search(pattern, f, re.IGNORECASE):
                    excluded = True
                    break
            if not excluded:
                result.append(f)
        return result
