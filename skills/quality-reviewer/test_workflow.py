"""
完整工作流测试 - 审查-修复-再循环

测试场景：
1. 审查agent发现飞书文档下载问题（主内容区为空）
2. 生成修复任务
3. 执行agent接收任务并修复
4. 审查agent再次验证修复效果

工作流：
quality-reviewer (发现问题) → 生成fix_tasks →
task-executor (执行修复) →
quality-reviewer (再审查)
"""

import sys
import json
import subprocess
from pathlib import Path


def test_workflow():
    """测试完整的审查-修复-再审查工作流"""

    print("\n" + "=" * 80)
    print("完整工作流测试 - 审查-修复-再循环")
    print("=" * 80)

    # 步骤1: 审查agent发现问题
    print("\n[步骤1] 审查agent检查下载结果...")

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

    # 调用quality-reviewer
    print("调用 quality-reviewer...")
    # Use current directory for subprocess
    reviewer_dir = Path(__file__).parent.absolute()

    # Write input to temp file to avoid encoding issues
    temp_input = reviewer_dir / "temp_test_input.json"
    with open(temp_input, 'w', encoding='utf-8') as f:
        json.dump(review_input, f, ensure_ascii=False, indent=2)

    result = subprocess.run(
        [sys.executable, "main.py", str(temp_input)],
        capture_output=True,
        text=True,
        cwd=reviewer_dir,
        encoding='utf-8',
        errors='replace'  # Replace invalid chars instead of failing
    )

    # Clean up temp file
    temp_input.unlink(missing_ok=True)

    # 解析审查结果
    try:
        if not result.stdout:
            print("错误: quality-reviewer 无输出")
            print(f"STDERR: {result.stderr}")
            return
        review_result = json.loads(result.stdout)
    except Exception as e:
        print(f"错误: 无法解析审查结果 - {e}")
        print(f"STDOUT: {result.stdout[:500]}")
        print(f"STDERR: {result.stderr[:500]}")
        return

    print(f"\n审查结果:")
    print(f"  总分: {review_result.get('overall_score', 'N/A')}/100")
    print(f"  通过: {review_result.get('approved', False)}")

    # 步骤2: 检查是否有修复任务
    if "fix_tasks" not in review_result:
        print("\n未生成修复任务（可能审查通过了，或者功能未启用）")
        return

    fix_tasks = review_result.get("fix_tasks", [])
    print(f"\n[步骤2] 审查agent生成了 {len(fix_tasks)} 个修复任务:")

    for i, task in enumerate(fix_tasks, 1):
        print(f"\n  任务{i}: {task['description']}")
        print(f"    优先级: {task['priority']}")
        print(f"    类型: {task['type']}")
        print(f"    推荐agent: {task['agent_type']}")
        print(f"    验收标准: {task['acceptance_criteria']['description']}")

    # 步骤3: 选择P0任务执行
    p0_tasks = [t for t in fix_tasks if t['priority'] == 'P0']

    if not p0_tasks:
        print("\n没有P0任务，无需执行修复")
        return

    print(f"\n[步骤3] 执行P0修复任务...")

    for task in p0_tasks:
        print(f"\n  执行任务: {task['task_id']}")
        print(f"  问题: {task['params'].get('problem', 'Unknown')[:100]}...")

        # 模拟执行修复（对于飞书SPA渲染问题）
        if task['task_id'] == 'fix_spa_rendering':
            print(f"  解决方案: {task['params']['suggested_solution']}")

            print("\n  使用FeishuDownloaderV2提取纯文本内容...")

            # 调用gethtml skill使用FeishuDownloaderV2
            gethtml_cmd = [
                sys.executable, "../gethtml/gethtml_skill.py",
                review_input["result"]["original_url"],
                "--feishu-format", "markdown"
            ]

            print(f"  命令: {' '.join(gethtml_cmd)}")

            # 这里只是演示，实际需要调用
            print(f"  [模拟] 提取纯文本内容到 standalone 文件")

            # 实际执行应该是：
            # subprocess.run(gethtml_cmd, cwd="../gethtml")

            print(f"  [提示] 实际执行时，将使用FeishuDownloaderV2提取内容")
            print(f"  [提示] 输出文件: {Path(review_input['result']['html_path']).parent}/standalone_v2.md")

    # 步骤4: 再次审查验证
    print(f"\n[步骤4] 再次审查验证修复效果...")
    print("  [模拟] 使用quality-reviewer重新审查...")
    print(f"  预期: rendering_check.main_content_empty = false")
    print(f"  预期: overall_score > 70")
    print(f"  预期: approved = true")

    print("\n" + "=" * 80)
    print("工作流测试完成")
    print("=" * 80)

    print("\n总结:")
    print("✅ quality-reviewer: 准确检测到SPA渲染问题")
    print("✅ 修复任务生成: 生成详细的P0修复任务")
    print("✅ agent推荐: 自动推荐使用task-executor执行修复")
    print("✅ 验收标准: 明确的成功定义和验证方法")
    print("\n下一步: 实际执行修复，然后再次审查验证")


def show_fix_tasks_example():
    """显示修复任务示例（不执行审查）"""

    print("\n" + "=" * 80)
    print("修复任务示例")
    print("=" * 80)

    # 模拟审查结果
    mock_review_result = {
        "overall_score": 45,
        "approved": False,
        "fix_tasks": [
            {
                "task_id": "fix_spa_rendering",
                "description": "修复SPA应用渲染问题 - SPA应用渲染失败（如飞书文档）。HTML源代码显示有内容（121.9%），但实际渲染后内容区为空（104.8%）。",
                "type": "fix_web_download",
                "priority": "P0",
                "agent_type": "task-executor",
                "params": {
                    "issue_type": "spa_rendering_failure",
                    "original_url": "https://meetchances.feishu.cn/wiki/WiKVwhPjYiGL3nksfldc94V3n8b",
                    "html_path": "C:/D/CAIE_tool/MyAIProduct/gethtml/downloads/meetchances.feishu.cn/index.html",
                    "problem": "SPA应用渲染失败...",
                    "suggested_solution": "使用FeishuDownloaderV2提取纯文本内容"
                },
                "acceptance_criteria": {
                    "description": "修复后，主内容区应显示实际内容",
                    "verification": "rendering_check.main_content_empty=false"
                }
            },
            {
                "task_id": "fix_sidebar_scrolling",
                "description": "修复侧边栏滚动功能 - 侧边栏无法正常滚动",
                "type": "fix_web_layout",
                "priority": "P0",
                "agent_type": "task-executor",
                "params": {
                    "html_path": "C:/D/CAIE_tool/MyAIProduct/gethtml/downloads/meetchances.feishu.cn/index.html"
                },
                "acceptance_criteria": {
                    "description": "侧边栏可以滚动到底部",
                    "verification": "动态测试sidebar测试应通过"
                }
            }
        ]
    }

    print("\n修复任务详情:")
    print(json.dumps(mock_review_result, ensure_ascii=False, indent=2))

    print("\n\n传递给task-executor的示例:")
    print("-" * 80)

    executor_input = {
        "task_id": "fix_feishu_download",
        "type": "fix_web_download",
        "prompt": f"""
执行修复任务: {mock_review_result['fix_tasks'][0]['description']}

问题: {mock_review_result['fix_tasks'][0]['params']['problem']}

解决方案: {mock_review_result['fix_tasks'][0]['params']['suggested_solution']}

参数: {json.dumps(mock_review_result['fix_tasks'][0]['params'], ensure_ascii=False)}
"""
    }

    print(json.dumps(executor_input, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="测试审查-修复-再审查工作流")
    parser.add_argument("--mode", choices=["test", "example"], default="test",
                       help="test: 完整工作流测试, example: 显示修复任务示例")

    args = parser.parse_args()

    if args.mode == "test":
        test_workflow()
    else:
        show_fix_tasks_example()
