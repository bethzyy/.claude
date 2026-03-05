#!/usr/bin/env python3
"""
审查Agent Skill入口
"""
import sys
import json
import time
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from reviewer import ReviewerAgent


def main():
    """Skill入口函数"""
    # 1. 解析输入
    if len(sys.argv) > 1:
        try:
            input_data = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            print(json.dumps({
                "status": "error",
                "message": "输入必须是有效的JSON"
            }, ensure_ascii=False))
            sys.exit(1)
    else:
        input_data = json.loads(sys.stdin.read())

    # 2. 提取任务ID和结果
    task_id = input_data.get("task_id", f"review_{int(time.time())}")
    result = input_data.get("result", {})
    task = input_data.get("task", {})

    # 3. 创建审查器
    task_dir = Path("test") / "skill-evals" / "quality-reviewer" / task_id
    reviewer = ReviewerAgent(task_id, task_dir)

    # 4. 执行审查
    review = reviewer.review_result(result, task)

    # 5. 输出结果
    print(json.dumps(review, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
