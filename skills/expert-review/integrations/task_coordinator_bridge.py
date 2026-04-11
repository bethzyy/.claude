"""
TaskCoordinatorBridge — 桥接 task-coordinator skill

将修复任务委托给 task-coordinator 的 execute→review→improve 循环。
基于审查 task-coordinator/coordinator.py 的真实 API 设计。

TaskCoordinator 真实签名:
  __init__(self, task_id: str, task_dir: Path, max_iterations: int = 3,
           quality_gates: Dict = None, reporting: Dict = None)
  process_task(self, task_config: Dict) -> Dict

  process_task 输入: {"type": "code_generation", "prompt": "...", "context": {...}}
  process_task 输出: {"success": bool, "status": str, "iterations": int, "result": {...},
                     "review": {...}, "quality_metrics": {...}, "performance_metrics": {...}}

  注意: TaskCoordinator 依赖 ExecutorAgent (task-executor) 和 ReviewerAgent (quality-reviewer)
  这两个必须通过 sys.path 可导入。
"""

import sys
import tempfile
import traceback
from pathlib import Path
from typing import Dict, Optional


class TaskCoordinatorBridge:
    """桥接 task-coordinator 的修复循环"""

    def __init__(self):
        self._coordinator_class = None
        self._available = False
        self._error = None
        self._init_bridge()

    def _init_bridge(self):
        """尝试初始化 task-coordinator 桥接"""
        try:
            coordinator_path = (
                Path(__file__).parent.parent.parent
                / "task-coordinator"
                / "coordinator.py"
            )
            if not coordinator_path.exists():
                self._error = f"coordinator.py not found at {coordinator_path}"
                return

            # task-coordinator 需要能导入 sibling skills
            skills_root = coordinator_path.parent.parent
            for skill_dir in ["task-executor", "quality-reviewer"]:
                skill_path = skills_root / skill_dir
                if skill_path.exists() and str(skill_path) not in sys.path:
                    sys.path.insert(0, str(skill_path))

            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "task_coordinator_module", str(coordinator_path)
            )
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                # 直接查找 TaskCoordinator 类
                if hasattr(mod, "TaskCoordinator"):
                    self._coordinator_class = mod.TaskCoordinator
                    self._available = True
                else:
                    self._error = "TaskCoordinator class not found in coordinator.py"
        except Exception as e:
            self._error = f"Import failed: {str(e)}"
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def get_error(self) -> Optional[str]:
        return self._error

    def delegate_fix(
        self,
        issue_id: str,
        description: str,
        file_path: str = "",
        code_snippet: str = "",
        fix_suggestion: str = "",
        max_iterations: int = 2,
    ) -> Dict:
        """
        委托修复任务给 task-coordinator。

        构造 task_config 传入 process_task()。

        Returns:
            {"delegated": bool, "reason": str, "result": {...} | None}
        """
        if not self._available:
            return {
                "delegated": False,
                "reason": self._error or "task-coordinator not available",
                "result": None,
            }

        try:
            task_dir = Path(tempfile.mkdtemp(prefix="expert_review_tc_"))

            coordinator = self._coordinator_class(
                task_id=f"fix_{issue_id}",
                task_dir=task_dir,
                max_iterations=max_iterations,
                quality_gates={"min_score": 80},
                reporting={"detailed_metrics": False},
            )

            # 构造 task_config
            prompt_parts = [f"Fix the following issue:\n{description}"]
            if file_path:
                prompt_parts.append(f"\nFile: {file_path}")
            if code_snippet:
                prompt_parts.append(f"\nCurrent code:\n```\n{code_snippet}\n```")
            if fix_suggestion:
                prompt_parts.append(f"\nSuggested fix: {fix_suggestion}")

            task_config = {
                "type": "code_generation",
                "prompt": "\n".join(prompt_parts),
                "context": {
                    "issue_id": issue_id,
                    "file_path": file_path,
                    "auto_fix": True,
                },
            }

            # 执行
            result = coordinator.process_task(task_config)

            return {
                "delegated": True,
                "reason": None,
                "result": result,
            }
        except Exception as e:
            return {
                "delegated": False,
                "reason": f"Execution failed: {str(e)}",
                "result": None,
                "traceback": traceback.format_exc(),
            }

    def check_dependencies(self) -> Dict:
        """
        检查 task-coordinator 的依赖是否可用。

        task-coordinator 依赖:
          - ExecutorAgent from task-executor/executor.py
          - ReviewerAgent from quality-reviewer/reviewer.py
        """
        deps = {}

        # 检查 task-executor
        executor_path = (
            Path(__file__).parent.parent.parent
            / "task-executor"
            / "executor.py"
        )
        deps["task_executor"] = {
            "path": str(executor_path),
            "exists": executor_path.exists(),
        }

        # 检查 quality-reviewer
        reviewer_path = (
            Path(__file__).parent.parent.parent
            / "quality-reviewer"
            / "reviewer.py"
        )
        deps["quality_reviewer"] = {
            "path": str(reviewer_path),
            "exists": reviewer_path.exists(),
        }

        deps["all_available"] = all(d["exists"] for d in deps.values())

        return deps
