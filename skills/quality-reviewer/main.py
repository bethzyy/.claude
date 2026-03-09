#!/usr/bin/env python3
"""
审查Agent Skill入口
"""
import sys
import json
import time
import os
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from reviewer import ReviewerAgent


def main():
    """Skill入口函数"""
    # 1. 解析输入
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        # Check if it's a file path
        input_path = Path(arg)
        if input_path.exists():
            # Read from file
            with open(input_path, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
        else:
            # Parse as JSON string
            try:
                input_data = json.loads(arg)
            except json.JSONDecodeError:
                sys.stderr.write(json.dumps({
                    "status": "error",
                    "message": "输入必须是有效的JSON或文件路径"
                }, ensure_ascii=False))
                sys.stderr.write('\n')
                sys.exit(1)
    else:
        input_data = json.loads(sys.stdin.read())

    # 2. 提取任务ID和结果
    task_id = input_data.get("task_id", f"review_{int(time.time())}")
    result = input_data.get("result", {})
    task = input_data.get("task", {})

    # 3. 创建审查器 (logging will go to stderr via StreamHandler(sys.stderr))
    task_dir = Path("test") / "skill-evals" / "quality-reviewer" / task_id
    reviewer = ReviewerAgent(task_id, task_dir)

    # 4. 执行审查 (logs go to stderr)
    review = reviewer.review_result(result, task)

    # 5. 输出结果 to stdout
    print(json.dumps(review, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
