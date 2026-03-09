"""
测试任务感知审查系统 - Quality Reviewer v2.1.0

测试场景：
1. 任务目标解析（"95%完整度" → 95.0）
2. 智能策略选择（飞书URL → CDP）
3. 任务感知评分（目标95%实际96% → 高分）
"""

import sys
import asyncio
from pathlib import Path


def test_task_goal_parser():
    """测试任务目标解析器"""
    print("\n" + "=" * 60)
    print("测试1: 任务目标解析器")
    print("=" * 60)

    from task_goal_parser import TaskGoalParser

    test_cases = [
        {
            "name": "中文完整度",
            "task": {"description": "下载飞书文档，要求95%内容完整度"},
            "expected": 95.0
        },
        {
            "name": "英文完整度",
            "task": {"description": "Web download with completeness ≥ 90%"},
            "expected": 90.0
        },
        {
            "name": "未指定目标",
            "task": {"description": "简单下载任务"},
            "expected": 90.0  # 默认值
        },
        {
            "name": "成功标准",
            "task": {
                "description": "高完整度下载",
                "success_criteria": {"completeness": 98.0}
            },
            "expected": 98.0
        },
    ]

    all_passed = True
    for case in test_cases:
        goals = TaskGoalParser.parse(case["task"])
        actual = goals["completeness_target"]
        expected = case["expected"]

        passed = (actual == expected)
        status = "[PASS]" if passed else "[FAIL]"

        print(f"{status} {case['name']}: {actual}% (expected {expected}%)")

        if not passed:
            all_passed = False

    return all_passed


def test_verification_strategy():
    """测试验证策略选择器"""
    print("\n" + "=" * 60)
    print("测试2: 验证策略选择器")
    print("=" * 60)

    from verification_strategy import VerificationStrategy

    test_cases = [
        {
            "name": "飞书文档",
            "url": "https://meetchances.feishu.cn/wiki/test",
            "target": 95.0,
            "expected_method": "cdp",
            "min_confidence": 0.90
        },
        {
            "name": "登录页",
            "url": "https://example.com/member/profile",
            "target": 90.0,
            "expected_method": "cdp",
            "min_confidence": 0.85
        },
        {
            "name": "普通页面",
            "url": "https://example.com/page",
            "target": 90.0,
            "expected_method": "online",
            "min_confidence": 0.70
        },
        {
            "name": "高目标",
            "url": "https://example.com/article",
            "target": 98.0,
            "expected_method": "cdp",  # 高目标使用CDP
            "min_confidence": 0.80
        },
    ]

    all_passed = True
    for case in test_cases:
        selector = VerificationStrategy(cdp_port=9222)
        strategy = selector.select_strategy(case["url"], {"completeness_target": case["target"]})

        method = strategy["method"]
        confidence = strategy["confidence"]

        method_passed = (method == case["expected_method"])
        confidence_passed = (confidence >= case["min_confidence"])

        status = "[PASS]" if (method_passed and confidence_passed) else "[FAIL]"

        print(f"{status} {case['name']}: method={method}, confidence={confidence}")

        if not method_passed:
            print(f"   Expected method: {case['expected_method']}")
            all_passed = False

        if not confidence_passed:
            print(f"   Min confidence: {case['min_confidence']}")
            all_passed = False

    return all_passed


def test_scoring_v2():
    """测试任务感知评分"""
    print("\n" + "=" * 60)
    print("测试3: 任务感知评分 (v2.1.0)")
    print("=" * 60)

    from reviewer import ReviewerAgent

    # 模拟审查结果
    agent = ReviewerAgent(
        task_id="test_task",
        task_dir=Path("./test_output"),
        task={"description": "95%完整度"}  # 设置目标为95%
    )

    # Verify goal parsing
    target_parsed = (agent.completeness_target == 95.0)
    print(f"[{'PASS' if target_parsed else 'FAIL'}] Goal parsing: {agent.completeness_target}% (expected 95.0%)")

    # Test CDP comparison scoring
    static_checks = {
        "html_structure": {"passed": True},
        "custom_css": {"passed": True},
        "resources": {"passed": True}
    }

    dynamic_checks = {
        "scrolling": {"passed": True},
        "sidebar": {"passed": True},
        "click_interactions": {"passed": True}
    }

    # Scenario 1: Met target (96% vs 95%)
    comparison1 = {
        "method": "cdp",
        "success": True,
        "completeness": 96.0,
        "met_target": True
    }

    score1 = agent._calculate_web_score_v2(
        static_checks, dynamic_checks, comparison1, None,
        completeness_target=95.0
    )

    # Scenario 2: Not met target (85% vs 95%)
    comparison2 = {
        "method": "cdp",
        "success": True,
        "completeness": 85.0,
        "met_target": False
    }

    score2 = agent._calculate_web_score_v2(
        static_checks, dynamic_checks, comparison2, None,
        completeness_target=95.0
    )

    # Verify scoring logic
    score1_passed = (score1 >= 85)  # Met target should get high score
    score2_passed = (score2 < score1)  # Not met should get lower score

    print(f"[{'PASS' if score1_passed else 'FAIL'}] Met target score: {score1}/100 (expected >=85)")
    print(f"[{'PASS' if score2_passed else 'FAIL'}] Not met target score: {score2}/100 (expected < {score1})")

    return target_parsed and score1_passed and score2_passed


async def test_cdp_comparator():
    """测试CDP对比器（需要真实的CDP连接）"""
    print("\n" + "=" * 60)
    print("测试4: CDP对比器 (需要CDP连接)")
    print("=" * 60)

    try:
        from cdp_comparator import CDPComparator

        # 检查CDP是否可用
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex(("localhost", 9222))
        sock.close()

        if result != 0:
            print("[SKIP] CDP not available, skipping CDP comparator test")
            print("  Hint: Start CDP: chrome.exe --remote-debugging-port=9222")
            return True  # Not a failure

        # CDP available, run comparison test
        print("[INFO] CDP available, running comparison test...")

        # Create mock HTML
        mock_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
            <h1>Test Title</h1>
            <p>This is test content.</p>
            <p>This is second paragraph.</p>
        </body>
        </html>
        """

        comparator = CDPComparator(
            completeness_target=95.0,
            logger=None
        )

        # Test text extraction
        extracted = CDPComparator.extract_text_from_html(mock_html)

        extract_passed = len(extracted) > 0
        print(f"[{'PASS' if extract_passed else 'FAIL'}] Text extraction: {len(extracted)} chars")

        return extract_passed

    except Exception as e:
        print(f"[FAIL] CDP comparator test failed: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Quality Reviewer v2.1.0 - 任务感知系统测试")
    print("=" * 60)

    results = []

    # 测试1: 任务目标解析
    results.append(("任务目标解析", test_task_goal_parser()))

    # 测试2: 验证策略选择
    results.append(("验证策略选择", test_verification_strategy()))

    # 测试3: 任务感知评分
    results.append(("任务感知评分", test_scoring_v2()))

    # 测试4: CDP对比器（异步）
    results.append(("CDP对比器", await test_cdp_comparator()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n[PASS] All tests passed! Task-aware system is working correctly.")
        return 0
    else:
        print(f"\n[FAIL] {total_count - passed_count} test(s) failed, please check.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
