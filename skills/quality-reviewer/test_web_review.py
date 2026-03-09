#!/usr/bin/env python3
"""
Test script for web-download review functionality.
"""
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from reviewer import ReviewerAgent


def create_mock_web_result(html_path: str = None):
    """Create a mock web-download result for testing."""
    if html_path is None:
        # Create a temporary test HTML
        html_path = Path(__file__).parent / "test_temp.html"
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
            <link rel="stylesheet" href="styles.css">
        </head>
        <body>
            <div class="wiki-ssr-sidebar__wrapper">
                <a href="#section1">Section 1</a>
                <a href="#section2">Section 2</a>
                <a href="#section3">Section 3</a>
            </div>
            <div class="content">
                <h1>Test Content</h1>
                <p>This is a test page with sufficient content.</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
                <img src="image1.jpg" alt="Test Image">
            </div>
        </body>
        </html>
        """
        html_path.write_text(html_content, encoding='utf-8')

    # Read HTML content
    html_content = Path(html_path).read_text(encoding='utf-8')

    return {
        "type": "web-download",
        "html_path": str(html_path),
        "original_url": "https://example.com/test",
        "html_content": html_content,
        "assets_dir": None  # No assets for this test
    }


def test_static_checks():
    """Test static checks (no Playwright required)."""
    print("=" * 60)
    print("TEST: Static Checks (HTML Structure + Custom CSS)")
    print("=" * 60)

    # Create reviewer agent
    task_dir = Path(__file__).parent / "test_output"
    agent = ReviewerAgent("test_001", task_dir)

    # Test 1: Clean HTML (should pass)
    print("\n[Test 1] Clean HTML - Should Pass")
    result1 = create_mock_web_result()
    review1 = agent._review_web_download(result1)

    print(f"  Overall Score: {review1['overall_score']}")
    print(f"  Approved: {review1['approved']}")
    print(f"  Custom CSS Passed: {review1['static_checks']['custom_css']['passed']}")
    print(f"  HTML Structure Passed: {review1['static_checks']['html_structure']['passed']}")

    assert review1['static_checks']['custom_css']['passed'], "Clean HTML should pass custom CSS check"
    assert review1['static_checks']['html_structure']['passed'], "Clean HTML should pass structure check"
    print("  [OK] PASSED")

    # Test 2: HTML with dangerous CSS (should fail)
    print("\n[Test 2] HTML with Dangerous CSS - Should Fail P0 Check")
    dangerous_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dangerous Page</title>
        <style>
            body {
                height: 100vh;
                overflow-y: auto !important;
            }
        </style>
    </head>
    <body>
        <h1>Dangerous Content</h1>
    </body>
    </html>
    """

    dangerous_path = Path(__file__).parent / "test_temp_dangerous.html"
    dangerous_path.write_text(dangerous_html, encoding='utf-8')

    result2 = {
        "type": "web-download",
        "html_path": str(dangerous_path),
        "original_url": "https://example.com/dangerous",
        "html_content": dangerous_html,
        "assets_dir": None
    }

    review2 = agent._review_web_download(result2)

    print(f"  Overall Score: {review2['overall_score']}")
    print(f"  Approved: {review2['approved']}")
    print(f"  Custom CSS Passed: {review2['static_checks']['custom_css']['passed']}")
    print(f"  P0 Issues Found: {review2['static_checks']['custom_css']['p0_count']}")
    print(f"  Issues: {len(review2['static_checks']['custom_css']['issues'])}")

    assert not review2['static_checks']['custom_css']['passed'], "Dangerous CSS should fail"
    assert review2['static_checks']['custom_css']['p0_count'] > 0, "Should find P0 issues"
    assert not review2['approved'], "Should not approve with P0 issues"
    print("  [OK] PASSED")

    # Cleanup
    if Path(result1['html_path']).exists():
        Path(result1['html_path']).unlink()
    if Path(result2['html_path']).exists():
        Path(result2['html_path']).unlink()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED [OK]")
    print("=" * 60)


def test_review_result_integration():
    """Test the main review_result() method with web-download type."""
    print("\n" + "=" * 60)
    print("TEST: Integration - review_result() with web-download")
    print("=" * 60)

    task_dir = Path(__file__).parent / "test_output_integration"
    agent = ReviewerAgent("test_integration", task_dir)

    result = create_mock_web_result()
    report = agent.review_result(result)

    print(f"\nReport Generated:")
    print(f"  Type: {report['review_type']}")
    print(f"  Overall Score: {report['overall_score']}")
    print(f"  Approved: {report['approved']}")
    print(f"  Suggestions: {len(report['suggestions'])}")
    print(f"  Issues: {len(report['issues'])}")

    assert report['review_type'] == "web_download_review", "Should return web_download_review type"
    assert 'overall_score' in report, "Should include overall_score"
    assert 'approved' in report, "Should include approved flag"
    assert 'static_checks' in report['checks'], "Should include static_checks"

    # Check report file was saved
    report_file = task_dir / "review_report.json"
    assert report_file.exists(), "Should save report to file"

    print("\n  [OK] PASSED")
    print(f"  Report saved to: {report_file}")

    # Cleanup
    if Path(result['html_path']).exists():
        Path(result['html_path']).unlink()

    print("\n" + "=" * 60)
    print("INTEGRATION TEST PASSED [OK]")
    print("=" * 60)


def main():
    """Run all tests."""
    print("\n[TEST] Quality-Reviewer Web-Download Tests")
    print("=" * 60)

    try:
        # Test 1: Static checks
        test_static_checks()

        # Test 2: Integration
        test_review_result_integration()

        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("=" * 60)
        print("\n[OK] Web-download review functionality is working correctly.")
        print("[OK] Static checks (HTML structure, custom CSS) are working.")
        print("[OK] Integration with review_result() is working.")
        print("\n[INFO] Note: Dynamic tests (scrolling, sidebar) require Playwright.")
        print("       To test dynamic functionality, install Playwright and use a real HTML file.")

        return 0

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
