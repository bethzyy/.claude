#!/usr/bin/env python3
"""
任务协调器 - 管理执行-审查循环
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# 添加父目录到路径以导入其他agent
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "task-executor"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "quality-reviewer"))

from executor import ExecutorAgent
from reviewer import ReviewerAgent


class TaskCoordinator:
    """任务协调器 - 管理执行-审查-改进循环"""

    def __init__(self, task_id: str, task_dir: Path, max_iterations: int = 3):
        self.task_id = task_id
        self.task_dir = task_dir
        self.max_iterations = max_iterations

        # 初始化executor和reviewer
        self.executor = ExecutorAgent(task_id, task_dir)
        self.reviewer = ReviewerAgent(task_id, task_dir)

        # 记录日志
        self.logs = []

    def process_task(self, task_config: Dict) -> Dict:
        """协调整个流程：执行 → 审查 → 改进 → 再审查 → ..."""
        self._log(f"开始处理任务: {task_config.get('type', 'unknown')}")

        iteration = 0
        result = None
        review = None

        while iteration < self.max_iterations:
            iteration += 1
            self._log(f"\n[迭代 {iteration}/{self.max_iterations}]")

            # Step 1: 执行任务
            if iteration == 1:
                result = self.executor.execute_task(task_config)
            else:
                # 使用反馈改进
                result = self.executor.improve(task_config, review)

            # 检查执行是否失败
            if result.get("status") == "failed":
                self._log(f"执行失败: {result.get('error')}")
                return self._final_failure(result, None, iteration)

            # Step 2: 审查结果
            review = self.reviewer.review_result(result, task_config)

            self._log(f"审查得分: {review.get('overall_score', 0)}/100")
            self._log(f"是否通过: {review.get('approved', False)}")

            # Step 3: 检查是否通过
            if review.get("approved", False):
                self._log(f"[OK] 任务完成！")
                return self._final_success(result, review, iteration)

            # Step 4: 准备下一轮迭代
            if iteration < self.max_iterations:
                self._log(f"审查未通过，准备改进...")
                self._log(f"建议: {', '.join(review.get('suggestions', [])[:3])}")

                # 更新任务配置，添加反馈
                task_config = self._prepare_retry(task_config, review)

        # 达到最大迭代次数仍未通过
        self._log(f"达到最大迭代次数，任务失败")
        return self._final_failure(result, review, iteration)

    def _prepare_retry(self, task_config: Dict, review: Dict) -> Dict:
        """准备重试任务"""
        # 复制配置
        new_config = task_config.copy()

        # 添加审查反馈
        new_config["_review_feedback"] = {
            "suggestions": review.get("suggestions", []),
            "issues": review.get("issues", []),
            "score": review.get("overall_score", 0)
        }

        # 增加迭代计数
        new_config["iteration"] = task_config.get("iteration", 0) + 1

        return new_config

    def _final_success(self, result: Dict, review: Dict, iteration: int) -> Dict:
        """生成成功结果"""
        return {
            "status": "completed",
            "task_id": self.task_id,
            "iterations": iteration,
            "result": result,
            "review": review,
            "timestamp": datetime.now().isoformat(),
            "logs": self.logs
        }

    def _final_failure(self, result: Dict, review: Optional[Dict], iteration: int) -> Dict:
        """生成失败结果"""
        return {
            "status": "failed",
            "task_id": self.task_id,
            "iterations": iteration,
            "result": result,
            "review": review,
            "error": result.get("error", "审查未通过"),
            "timestamp": datetime.now().isoformat(),
            "logs": self.logs
        }

    def _log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.logs.append(log_message)
        print(log_message)

    def save_workflow_report(self, final_result: Dict):
        """保存完整的工作流报告"""
        report_file = self.task_dir / "workflow_report.json"

        report = {
            "task_id": self.task_id,
            "timestamp": datetime.now().isoformat(),
            "final_result": final_result,
            "execution_log": self.logs
        }

        report_file.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        print(f"\n[工作流报告] 已保存: {report_file}")
