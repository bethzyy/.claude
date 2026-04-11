"""
RequirementTraceBridge — 桥接 requirement-trace skill

检查项目是否有需求文档，交叉引用审查发现。
基于审查 requirement-trace/scripts/requirement_manager.py 的真实 API 设计。

RequirementManager 真实签名:
  __init__(self, project_dir: str)
  get_statistics(self) -> Dict
  list_requirements(self, status=None, type=None, priority=None, blocked=None) -> str
  search_requirements(self, query: str) -> str
  get_requirement(self, req_id: str) -> Optional[str]

  注意: RequirementManager 在 scripts/requirement_manager.py，不在根目录。
  需求文件默认是 REQUIREMENTS.md。
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List


class RequirementTraceBridge:
    """桥接 requirement-trace 需求追踪"""

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.requirements_file = self.project_dir / "REQUIREMENTS.md"
        self._manager = None
        self._available = False
        self._error = None
        self._init_bridge()

    def _init_bridge(self):
        """尝试导入 RequirementManager"""
        try:
            # RequirementManager 在 scripts/requirement_manager.py
            manager_path = (
                Path(__file__).parent.parent.parent
                / "requirement-trace"
                / "scripts"
                / "requirement_manager.py"
            )
            if not manager_path.exists():
                self._error = f"requirement_manager.py not found at {manager_path}"
                return

            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "requirement_manager", str(manager_path)
            )
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                if hasattr(mod, "RequirementManager"):
                    self._manager = mod.RequirementManager(str(self.project_dir))
                    self._available = True
                else:
                    self._error = "RequirementManager class not found"
        except Exception as e:
            self._error = f"Import failed: {str(e)}"
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def get_error(self) -> Optional[str]:
        return self._error

    @property
    def has_requirements(self) -> bool:
        """检查项目是否有需求文档"""
        return self.requirements_file.exists()

    def get_statistics(self) -> Optional[Dict]:
        """获取需求统计（通过 RequirementManager.get_statistics()）"""
        if not self._available:
            # 降级：手动解析
            return self._parse_statistics_fallback()

        try:
            return self._manager.get_statistics()
        except Exception as e:
            self._error = f"get_statistics failed: {str(e)}"
            return self._parse_statistics_fallback()

    def _parse_statistics_fallback(self) -> Dict:
        """降级：手动解析 REQUIREMENTS.md"""
        if not self.requirements_file.exists():
            return {"has_requirements": False}

        try:
            content = self.requirements_file.read_text(encoding="utf-8")
            total = 0
            completed = 0
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped.startswith("- [x]"):
                    completed += 1
                    total += 1
                elif stripped.startswith("- [ ]"):
                    total += 1
            return {
                "has_requirements": True,
                "total": total,
                "completed": completed,
                "pending": total - completed,
            }
        except Exception:
            return {"has_requirements": False}

    def search_requirements(self, query: str) -> Optional[str]:
        """搜索需求（通过 RequirementManager.search_requirements()）"""
        if not self._available:
            return None

        try:
            return self._manager.search_requirements(query)
        except Exception:
            return None

    def cross_reference(self, findings: List[Dict]) -> Dict:
        """交叉引用审查发现与需求"""
        requirements = self._get_all_requirements()
        if not requirements:
            return {"has_requirements": False}

        req_texts = [r["text"] for r in requirements if not r.get("is_heading")]

        # 检查哪些发现与需求相关
        related = []
        for finding in findings:
            title = finding.get("title", "").lower()
            desc = finding.get("description", "").lower()
            for req in req_texts:
                req_lower = req.lower()
                # 关键词匹配
                keywords = set(title.split() + desc.split())
                req_keywords = set(req_lower.split())
                overlap = keywords & req_keywords
                if len(overlap) >= 2:
                    related.append({
                        "finding": finding.get("id"),
                        "requirement": req[:80],
                        "overlap_keywords": list(overlap)[:5],
                    })

        stats = self.get_statistics()
        return {
            "has_requirements": True,
            "statistics": stats,
            "total_requirements": len([r for r in requirements if not r.get("is_heading")]),
            "completed_requirements": len([r for r in requirements if r.get("completed")]),
            "related_findings": related,
        }

    def _get_all_requirements(self) -> Optional[List[Dict]]:
        """获取所有需求项"""
        if not self.requirements_file.exists():
            return None

        try:
            content = self.requirements_file.read_text(encoding="utf-8")
            requirements = []
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped.startswith("- [") or stripped.startswith("* ["):
                    is_checked = "[x]" in stripped.lower()
                    req_text = stripped.split("]", 1)[1].strip() if "]" in stripped else stripped
                    requirements.append({
                        "text": req_text,
                        "completed": is_checked,
                    })
                elif stripped.startswith("#"):
                    requirements.append({
                        "text": stripped,
                        "is_heading": True,
                    })
            return requirements
        except Exception:
            return None
