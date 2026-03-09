#!/usr/bin/env python3
"""
测试 fix_tasks 生成
"""
import json
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from reviewer import ReviewerAgent

def main():
    # 准备测试数据
    review_input = {
        "task_id": "feishu_download_review",
        "result": {
            "type": "web-download",
            "html_path": "C:/D/CAIE_tool/MyAIProduct/gethtml/downloads/meetchances.feishu.cn/index.html",
            "original_url": "https://meetchances.feishu.cn/wiki/WiKVwhPjYiGL3nksfldc94V3n8b"
        },
        "task": {
            "description": "飞书文档下载质量审查，要求95%内容完整度"
        }
    }

    # 创建审查器
    task_dir = Path("test") / "skill-evals" / "quality-reviewer" / review_input["task_id"]
    reviewer = ReviewerAgent(review_input["task_id"], task_dir)

    # 执行审查
    review = reviewer.review_result(
        review_input["result"],
        review_input["task"]
    )

    # 检查是否有 fix_tasks
    print("=" * 80)
    print("测试结果")
    print("=" * 80)
    print(f"\nOverall Score: {review.get('overall_score', 'N/A')}/100")
    print(f"Approved: {review.get('approved', False)}")
    print(f"\nFix Tasks Found: {'fix_tasks' in review}")

    if 'fix_tasks' in review:
        fix_tasks = review['fix_tasks']
        print(f"Total Fix Tasks: {len(fix_tasks)}")

        print("\n" + "=" * 80)
        print("Fix Tasks:")
        print("=" * 80)

        for i, task in enumerate(fix_tasks, 1):
            print(f"\n{i}. [{task['priority']}] {task['description']}")
            print(f"   Type: {task['type']}")
            print(f"   Agent: {task['agent_type']}")
            print(f"   Acceptance: {task['acceptance_criteria']['description']}")
    else:
        print("\n[WARNING] No fix_tasks found in review output!")
        print("Available keys:", list(review.keys()))

if __name__ == "__main__":
    main()
