"""
FreeSearchBridge — 桥接 free-search skill

为专家提供实时搜索能力：CVE 查询、框架最佳实践、安全公告。
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List


class FreeSearchBridge:
    """桥接 free-search 搜索引擎"""

    def __init__(self):
        self._engine = None
        self._available = False
        self._error = None
        self._init_bridge()

    def _init_bridge(self):
        """尝试初始化 free-search 的 WebSearchEngine"""
        try:
            search_engine_path = (
                Path(__file__).parent.parent.parent
                / "free-search"
                / "scripts"
                / "search_engine.py"
            )
            if not search_engine_path.exists():
                self._error = "search_engine.py not found"
                return

            import importlib.util
            scripts_dir = str(search_engine_path.parent)
            if scripts_dir not in sys.path:
                sys.path.insert(0, scripts_dir)

            spec = importlib.util.spec_from_file_location(
                "search_engine", str(search_engine_path)
            )
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                self._engine = mod.WebSearchEngine(cache_days=3)
                self._available = True
        except Exception as e:
            self._error = str(e)

    @property
    def available(self) -> bool:
        return self._available

    def get_error(self) -> Optional[str]:
        return self._error

    def search(self, query: str, max_results: int = 3, timeout: int = 15) -> Dict:
        """执行搜索查询"""
        if not self._available:
            return {"success": False, "error": self._error}
        try:
            return self._engine.search(query, max_results=max_results, timeout=timeout)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_cve(self, package: str, version: str = "") -> str:
        """搜索依赖包的 CVE 漏洞信息"""
        query = f"{package} {version} CVE vulnerability 2025 2026"
        result = self.search(query, max_results=3)
        if result.get("success"):
            results = result.get("results", [])
            if results:
                lines = []
                for r in results[:3]:
                    title = r.get("title", "")
                    snippet = r.get("snippet", "") or r.get("content", "")[:120]
                    lines.append(f"- {title}: {snippet}")
                return "\n".join(lines)
        return ""

    def search_best_practice(self, framework: str, topic: str) -> str:
        """搜索框架最佳实践"""
        query = f"{framework} {topic} best practices security 2025 2026"
        result = self.search(query, max_results=3)
        if result.get("success"):
            results = result.get("results", [])
            if results:
                lines = []
                for r in results[:3]:
                    title = r.get("title", "")
                    snippet = r.get("snippet", "") or r.get("content", "")[:120]
                    lines.append(f"- {title}: {snippet}")
                return "\n".join(lines)
        return ""
