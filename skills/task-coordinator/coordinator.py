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
    """任务协调器 - 管理执行-审查-改进循环 (v2.0.0)"""

    def __init__(self, task_id: str, task_dir: Path, max_iterations: int = 3, quality_gates: Dict = None, reporting: Dict = None):
        self.task_id = task_id
        self.task_dir = task_dir
        self.max_iterations = max_iterations

        # v2.0.0: Quality gates configuration
        self.quality_gates = quality_gates or {
            "min_score": 70,
            "required_checks": []
        }

        # v2.0.0: Reporting configuration
        self.reporting = reporting or {
            "detailed_metrics": False,
            "include_recommendations": False
        }

        # 初始化executor和reviewer
        self.executor = ExecutorAgent(task_id, task_dir)
        self.reviewer = ReviewerAgent(task_id, task_dir)

        # 记录日志
        self.logs = []

        # v2.0.0: Performance metrics
        self.start_time = None
        self.executor_calls = 0
        self.reviewer_calls = 0
        self.scores_trajectory = []

    def process_task(self, task_config: Dict) -> Dict:
        """协调整个流程：执行 → 审查 → 改进 → 再审查 → ..."""
        self._log(f"开始处理任务: {task_config.get('type', 'unknown')}")

        # v2.0.0: Start performance tracking
        self.start_time = time.time()

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

            # v2.0.0: Track executor calls
            self.executor_calls += 1

            # 检查执行是否失败
            if result.get("status") == "failed":
                self._log(f"执行失败: {result.get('error')}")
                return self._final_failure(result, None, iteration)

            # Step 2: 审查结果
            review = self.reviewer.review_result(result, task_config)

            # v2.0.0: Track reviewer calls and scores
            self.reviewer_calls += 1
            current_score = review.get('overall_score', 0)
            self.scores_trajectory.append(current_score)

            self._log(f"审查得分: {current_score}/100")

            # v2.0.0: Check quality gates
            quality_gates_met = self._check_quality_gates(review)
            self._log(f"质量门禁: {'通过' if quality_gates_met else '未通过'}")

            # Step 3: 检查是否通过
            if quality_gates_met:
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

    def _check_quality_gates(self, review: Dict) -> bool:
        """v2.0.0: Check if quality gates are met"""
        # Check minimum score
        min_score = self.quality_gates.get("min_score", 70)
        current_score = review.get('overall_score', 0)

        if current_score < min_score:
            return False

        # Check required checks
        required_checks = self.quality_gates.get("required_checks", [])
        if required_checks:
            check_results = review.get('check_results', {})
            for check in required_checks:
                if check_results.get(check, {}).get('passed', False) is False:
                    return False

        # If no specific gates, use approved field
        return review.get("approved", current_score >= min_score)

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
        """生成成功结果 (v2.0.0 enhanced)"""
        base_result = {
            "success": True,
            "status": "completed",
            "task_id": self.task_id,
            "iterations": iteration,
            "result": result,
            "review": review,
            "timestamp": datetime.now().isoformat(),
            "logs": self.logs
        }

        # v2.0.0: Add enhanced metrics if reporting is enabled
        if self.reporting.get("detailed_metrics", False):
            base_result.update({
                "quality_metrics": self._generate_quality_metrics(review, iteration),
                "performance_metrics": self._generate_performance_metrics()
            })

        if self.reporting.get("include_recommendations", False):
            base_result["recommendations"] = self._generate_recommendations(iteration, review)

        return base_result

    def _final_failure(self, result: Dict, review: Optional[Dict], iteration: int) -> Dict:
        """生成失败结果 (v2.0.0 enhanced)"""
        base_result = {
            "success": False,
            "status": "failed",
            "task_id": self.task_id,
            "iterations": iteration,
            "result": result,
            "review": review,
            "error": result.get("error", "审查未通过"),
            "timestamp": datetime.now().isoformat(),
            "logs": self.logs
        }

        # v2.0.0: Add metrics even for failures
        if review and self.reporting.get("detailed_metrics", False):
            base_result.update({
                "final_score": review.get('overall_score', 0),
                "required_score": self.quality_gates.get("min_score", 70),
                "quality_metrics": self._generate_quality_metrics(review, iteration),
                "performance_metrics": self._generate_performance_metrics()
            })

        return base_result

    def _generate_quality_metrics(self, review: Dict, iteration: int) -> Dict:
        """v2.0.0: Generate quality metrics"""
        return {
            "total_iterations": iteration,
            "final_score": review.get('overall_score', 0),
            "improvement_trajectory": self.scores_trajectory.copy(),
            "quality_gates_met": True,
            "min_score_required": self.quality_gates.get("min_score", 70),
            "score_improvement": self.scores_trajectory[-1] - self.scores_trajectory[0] if len(self.scores_trajectory) > 1 else 0,
            "check_results": review.get('check_results', {})
        }

    def _generate_performance_metrics(self) -> Dict:
        """v2.0.0: Generate performance metrics"""
        total_time = time.time() - self.start_time if self.start_time else 0
        return {
            "total_time_seconds": round(total_time, 2),
            "executor_calls": self.executor_calls,
            "reviewer_calls": self.reviewer_calls,
            "avg_time_per_iteration": round(total_time / max(self.executor_calls, 1), 2)
        }

    def _generate_recommendations(self, iteration: int, review: Dict) -> list:
        """v2.0.0: Generate improvement recommendations"""
        recommendations = []

        # Iteration optimization
        if iteration < self.max_iterations:
            recommendations.append(f"Quality gates met after {iteration} iterations")

        # Score-based recommendations
        if self.scores_trajectory:
            avg_improvement = (self.scores_trajectory[-1] - self.scores_trajectory[0]) / max(len(self.scores_trajectory) - 1, 1)
            if avg_improvement > 20:
                recommendations.append("High improvement rate - consider more iterations for complex tasks")
            elif iteration == 1 and self.scores_trajectory[0] >= self.quality_gates.get("min_score", 70):
                recommendations.append("First attempt passed - consider reducing max_iterations to 1")

        # Performance-based recommendations
        total_time = time.time() - self.start_time if self.start_time else 0
        if total_time > 120:
            recommendations.append("Long execution time - consider breaking into smaller tasks")

        return recommendations

    def _log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.logs.append(log_message)
        print(log_message)

    def save_workflow_report(self, final_result: Dict):
        """保存完整的工作流报告 (v2.0.0 enhanced)"""
        # v2.0.0: Save both v1.0.0 and v2.0.0 formats
        report_file_v1 = self.task_dir / "workflow_report.json"
        report_file_v2 = self.task_dir / "workflow_report_v2.json"

        # v1.0.0 format (backward compatibility)
        report_v1 = {
            "task_id": self.task_id,
            "timestamp": datetime.now().isoformat(),
            "final_result": final_result,
            "execution_log": self.logs
        }

        # v2.0.0 format (enhanced metrics)
        report_v2 = {
            "task_id": self.task_id,
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "final_result": final_result,
            "execution_log": self.logs
        }

        # Add v2.0.0 specific fields if available
        if self.reporting.get("detailed_metrics", False) and "quality_metrics" in final_result:
            report_v2["quality_metrics"] = final_result["quality_metrics"]
            report_v2["performance_metrics"] = final_result["performance_metrics"]
            if "recommendations" in final_result:
                report_v2["recommendations"] = final_result["recommendations"]

        # Save both formats
        report_file_v1.parent.mkdir(parents=True, exist_ok=True)

        report_file_v1.write_text(
            json.dumps(report_v1, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        report_file_v2.write_text(
            json.dumps(report_v2, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        print(f"\n[工作流报告] 已保存: {report_file_v1}")
        print(f"[工作流报告 v2.0] 已保存: {report_file_v2}")
