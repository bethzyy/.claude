#!/usr/bin/env python3
"""
任务协调器Skill入口
"""
import sys
import json
import time
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from coordinator import TaskCoordinator


def main():
    """Skill入口函数"""
    # 1. 解析输入
    if len(sys.argv) > 1:
        try:
            task_config = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            # 简单提示
            task_config = {
                "type": "code_generation",
                "prompt": " ".join(sys.argv[1:])
            }
    else:
        input_data = sys.stdin.read().strip()
        if not input_data:
            task_config = {
                "type": "code_generation",
                "prompt": "Hello World"
            }
        else:
            try:
                task_config = json.loads(input_data)
            except json.JSONDecodeError:
                task_config = {
                    "type": "code_generation",
                    "prompt": input_data
                }

    # 2. 生成任务ID
    task_id = task_config.get("task_id", f"coordinated_task_{int(time.time())}")

    # 3. 创建协调器 (v2.0.0: 支持quality_gates和reporting参数)
    task_dir = Path("test") / "skill-evals" / "task-coordinator" / task_id
    max_iterations = task_config.get("max_iterations", 3)

    # v2.0.0: Parse quality gates configuration
    quality_gates = task_config.get("quality_gates", {
        "min_score": 70,
        "required_checks": []
    })

    # v2.0.0: Parse reporting configuration
    reporting = task_config.get("reporting", {
        "detailed_metrics": False,
        "include_recommendations": False
    })

    coordinator = TaskCoordinator(
        task_id=task_id,
        task_dir=task_dir,
        max_iterations=max_iterations,
        quality_gates=quality_gates,
        reporting=reporting
    )

    # 4. 执行完整工作流
    result = coordinator.process_task(task_config)

    # 5. 保存工作流报告
    coordinator.save_workflow_report(result)

    # 6. 输出结果
    print("\n" + "="*50)
    print("最终结果:")
    print("="*50)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
