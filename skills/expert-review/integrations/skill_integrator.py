"""
SkillIntegrator — 统一跨 skill 调用接口

发现并调用其他 skill，所有依赖可选。
基于审查实际 skill 代码后的真实集成。
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List


class SkillIntegrator:
    """统一跨 skill 调用接口"""

    SKILLS_DIR = Path(__file__).parent.parent.parent

    def __init__(self):
        self._bridges = {}
        self._discover_skills()

        # 预创建桥接实例（延迟加载）
        self._qr_bridge = None
        self._tc_bridge = None

    def _discover_skills(self):
        """发现可用的 skill"""
        skills_dir = self.SKILLS_DIR
        if not skills_dir.exists():
            return

        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                continue
            main_file = skill_dir / "main.py"
            if main_file.exists():
                self._bridges[skill_dir.name] = main_file

    def list_available(self) -> List[str]:
        """列出所有可用的 skill"""
        return list(self._bridges.keys())

    def is_available(self, skill_name: str) -> bool:
        """检查 skill 是否可用"""
        return skill_name in self._bridges

    def get_skill_info(self, skill_name: str) -> Optional[Dict]:
        """获取 skill 元信息"""
        if skill_name not in self._bridges:
            return {"error": f"Skill '{skill_name}' not found"}

        main_file = self._bridges[skill_name]
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(skill_name, str(main_file))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "get_skill_info"):
                    return mod.get_skill_info()
        except Exception as e:
            return {"error": str(e)}

        return None

    def get_quality_reviewer_bridge(self):
        """获取 quality-reviewer 桥接（单例缓存）"""
        if self._qr_bridge is None:
            from integrations.quality_reviewer_bridge import QualityReviewerBridge
            self._qr_bridge = QualityReviewerBridge()
        return self._qr_bridge

    def get_task_coordinator_bridge(self):
        """获取 task-coordinator 桥接（单例缓存）"""
        if self._tc_bridge is None:
            from integrations.task_coordinator_bridge import TaskCoordinatorBridge
            self._tc_bridge = TaskCoordinatorBridge()
        return self._tc_bridge

    def get_requirement_trace_bridge(self, project_dir: str):
        """获取 requirement-trace 桥接"""
        from integrations.requirement_trace_bridge import RequirementTraceBridge
        return RequirementTraceBridge(project_dir)

    def get_free_search_bridge(self):
        """获取 free-search 桥接（单例缓存）"""
        if not hasattr(self, '_fs_bridge') or self._fs_bridge is None:
            from integrations.free_search_bridge import FreeSearchBridge
            self._fs_bridge = FreeSearchBridge()
        return self._fs_bridge

    def get_integration_status(self) -> Dict:
        """获取所有集成的状态"""
        status = {}

        # quality-reviewer
        qr = self.get_quality_reviewer_bridge()
        status["quality_reviewer"] = {
            "available": qr.available,
            "error": qr.get_error(),
        }

        # task-coordinator
        tc = self.get_task_coordinator_bridge()
        status["task_coordinator"] = {
            "available": tc.available,
            "error": tc.get_error(),
            "dependencies": tc.check_dependencies() if tc.available else None,
        }

        # requirement-trace (不指定项目，只检查 skill 本身)
        rt_path = self.SKILLS_DIR / "requirement-trace" / "scripts" / "requirement_manager.py"
        status["requirement_trace"] = {
            "available": rt_path.exists(),
            "path": str(rt_path),
        }

        # free-search
        fs = self.get_free_search_bridge()
        status["free_search"] = {
            "available": fs.available,
            "error": fs.get_error(),
        }

        return status
