#!/usr/bin/env python3
"""
执行Agent Skill入口
"""
import sys
import json
import time
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from executor import ExecutorAgent


def main():
    """Skill入口函数"""
    # 1. 解析输入
    if len(sys.argv) > 1:
        # 命令行参数
        try:
            task_config = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            # 如果不是JSON，当作简单提示处理
            task_config = {
                "type": "code_generation",
                "prompt": " ".join(sys.argv[1:])
            }
    else:
        # 标准输入
        input_data = sys.stdin.read().strip()
        if not input_data:
            # 默认任务
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
    task_id = task_config.get("task_id", f"task_{int(time.time())}")

    # 3. 创建执行器
    task_dir = Path("test") / "skill-evals" / "task-executor" / task_id
    executor = ExecutorAgent(task_id, task_dir)

    # 4. 执行任务
    result = executor.execute_task(task_config)

    # 5. 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
