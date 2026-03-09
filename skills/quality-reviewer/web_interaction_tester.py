#!/usr/bin/env python3
"""
Web Interaction Tester - Playwright-based dynamic testing for downloaded webpages.

Provides automated testing for:
- Scrolling functionality (sidebar, main content)
- Click interactions (navigation, links)
- Layout comparison (original vs downloaded)
- Screenshot-based visual diff
"""

import os
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from difflib import SequenceMatcher

from playwright.async_api import async_playwright, Browser, Page, BrowserContext


class WebInteractionTester:
    """
    Test downloaded webpages with Playwright.

    Uses async/await pattern compatible with gethtml's WebpageDownloader.
    """

    def __init__(self, logger=None, screenshot_dir: str = None):
        """
        Initialize WebInteractionTester.

        Args:
            logger: Logger instance (optional)
            screenshot_dir: Directory for screenshots (default: test/screenshots)
        """
        self.logger = logger or self._default_logger()
        self.screenshot_dir = Path(screenshot_dir or "test/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    def _default_logger(self):
        """Create a simple logger if none provided"""
        import logging
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def test_local_html(
        self,
        html_path: str,
        tests: List[str] = None
    ) -> Dict[str, Any]:
        """
        Test a local HTML file with multiple checks.

        Args:
            html_path: Path to local HTML file
            tests: List of tests to run (default: all tests)
                   Available: ["scrolling", "sidebar", "click_interactions"]

        Returns:
            Dict with test results
        """
        if tests is None:
            tests = ["scrolling", "sidebar", "click_interactions"]

        html_path = Path(html_path).resolve()
        if not html_path.exists():
            return {
                "success": False,
                "error": f"HTML file not found: {html_path}",
                "tests": {}
            }

        self.logger.info(f"Testing local HTML: {html_path}")

        # Use async context manager
        async with self:
            page = await self.context.new_page()

            # Navigate to local file
            file_url = f"file:///{html_path.as_posix()}"
            try:
                await page.goto(file_url, wait_until='networkidle', timeout=10000)
                await page.wait_for_timeout(2000)  # Wait for JS rendering
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to load HTML: {e}",
                    "tests": {}
                }

            results = {}

            # Run requested tests
            if "scrolling" in tests:
                results["scrolling"] = await self.test_scrolling(page)

            if "sidebar" in tests:
                results["sidebar"] = await self.test_sidebar(page)

            if "click_interactions" in tests:
                results["click_interactions"] = await self.test_click_interactions(page)

            # Take screenshot for visual inspection
            screenshot_path = self.screenshot_dir / f"{html_path.stem}_test.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            results["screenshot"] = str(screenshot_path)

        return {
            "success": True,
            "html_path": str(html_path),
            "tests": results,
            "timestamp": datetime.now().isoformat()
        }

    async def test_scrolling(self, page: Page) -> Dict[str, Any]:
        """
        Test if the page is scrollable and bottom content is accessible.

        Returns:
            Dict with scroll test results
        """
        try:
            # Get page dimensions
            scroll_height = await page.evaluate("() => document.body.scrollHeight")
            client_height = await page.evaluate("() => window.innerHeight")

            self.logger.info(f"Page dimensions: scroll_height={scroll_height}, client_height={client_height}")

            # Try to scroll to bottom
            await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(500)

            # Check if we successfully scrolled
            final_scroll_y = await page.evaluate("() => window.scrollY")

            # Try to get text at bottom (Feishu-specific)
            bottom_text = await page.evaluate("""
                () => {
                    const bottomElements = document.querySelectorAll('.wiki-ssr-sidebar__wrapper *:last-child');
                    return bottomElements.length > 0 ? bottomElements[0].textContent : '';
                }
            """)

            scrollable = scroll_height > client_height
            reached_bottom = final_scroll_y > 0

            return {
                "passed": scrollable and reached_bottom,
                "scrollable": scrollable,
                "reached_bottom": reached_bottom,
                "scroll_height": scroll_height,
                "client_height": client_height,
                "bottom_text_accessible": len(bottom_text) > 0,
                "bottom_text_sample": bottom_text[:100] if bottom_text else ""
            }
        except Exception as e:
            self.logger.error(f"Scroll test failed: {e}")
            return {
                "passed": False,
                "error": str(e)
            }

    async def test_sidebar(self, page: Page) -> Dict[str, Any]:
        """
        Test Feishu sidebar scrolling functionality.

        Returns:
            Dict with sidebar test results
        """
        selectors_to_try = [
            ".wiki-ssr-sidebar__wrapper",  # Feishu wiki sidebar
            ".wiki-sidebar",                # Alternative selector
            "[role='navigation']"           # Generic navigation
        ]

        results = []

        for selector in selectors_to_try:
            try:
                element = await page.query_selector(selector)
                if not element:
                    results.append({
                        "selector": selector,
                        "found": False,
                        "reason": "Element not found"
                    })
                    continue

                # Get scroll dimensions
                scroll_height = await element.evaluate("el => el.scrollHeight")
                client_height = await element.evaluate("el => el.clientHeight")
                scroll_top = await element.evaluate("el => el.scrollTop")

                # Try to scroll to bottom
                await element.evaluate("el => el.scrollTop = el.scrollHeight")
                await page.wait_for_timeout(500)

                # Check if scroll worked
                final_scroll_top = await element.evaluate("el => el.scrollTop")

                scrollable = scroll_height > client_height
                can_scroll_bottom = final_scroll_top > scroll_top

                results.append({
                    "selector": selector,
                    "found": True,
                    "scrollable": scrollable,
                    "can_scroll_to_bottom": can_scroll_bottom,
                    "scroll_height": scroll_height,
                    "client_height": client_height,
                    "initial_scroll_top": scroll_top,
                    "final_scroll_top": final_scroll_top
                })

                # If found and working, don't try other selectors
                if scrollable and can_scroll_bottom:
                    break

            except Exception as e:
                results.append({
                    "selector": selector,
                    "found": False,
                    "error": str(e)
                })

        # Check if any selector worked
        working_results = [r for r in results if r.get("found") and r.get("scrollable")]

        return {
            "passed": len(working_results) > 0,
            "results": results,
            "working_selector": working_results[0]["selector"] if working_results else None
        }

    async def test_click_interactions(self, page: Page) -> Dict[str, Any]:
        """
        Test basic click interactions (links, buttons).

        Returns:
            Dict with click test results
        """
        click_tests = []

        # Test 1: Check if links are present
        try:
            links = await page.query_selector_all("a[href]")
            click_tests.append({
                "test": "links_present",
                "passed": len(links) > 0,
                "count": len(links),
                "description": f"Found {len(links)} links"
            })
        except Exception as e:
            click_tests.append({
                "test": "links_present",
                "passed": False,
                "error": str(e)
            })

        # Test 2: Check if buttons are present
        try:
            buttons = await page.query_selector_all("button")
            click_tests.append({
                "test": "buttons_present",
                "passed": len(buttons) > 0,
                "count": len(buttons),
                "description": f"Found {len(buttons)} buttons"
            })
        except Exception as e:
            click_tests.append({
                "test": "buttons_present",
                "passed": False,
                "error": str(e)
            })

        # Test 3: Try clicking a sidebar item (Feishu-specific)
        try:
            sidebar_item = await page.query_selector(".wiki-ssr-sidebar__wrapper a")
            if sidebar_item:
                # Get href before click
                href = await sidebar_item.get_attribute("href")

                # Try clicking (don't navigate, just check if clickable)
                is_clickable = await sidebar_item.is_enabled()
                is_visible = await sidebar_item.is_visible()

                click_tests.append({
                    "test": "sidebar_item_clickable",
                    "passed": is_clickable and is_visible,
                    "href": href,
                    "description": f"Sidebar item is clickable and visible"
                })
            else:
                click_tests.append({
                    "test": "sidebar_item_clickable",
                    "passed": False,
                    "reason": "No sidebar item found"
                })
        except Exception as e:
            click_tests.append({
                "test": "sidebar_item_clickable",
                "passed": False,
                "error": str(e)
            })

        passed_tests = sum(1 for t in click_tests if t.get("passed", False))

        return {
            "passed": passed_tests > 0,
            "total_tests": len(click_tests),
            "passed_tests": passed_tests,
            "tests": click_tests
        }

    async def compare_pages(
        self,
        original_url: str,
        downloaded_html: str
    ) -> Dict[str, Any]:
        """
        Compare original webpage with downloaded version.

        Args:
            original_url: Original webpage URL
            downloaded_html: Path to downloaded HTML file

        Returns:
            Dict with comparison results
        """
        self.logger.info(f"Comparing {original_url} with {downloaded_html}")

        downloaded_html = Path(downloaded_html).resolve()
        if not downloaded_html.exists():
            return {
                "success": False,
                "error": f"Downloaded HTML not found: {downloaded_html}"
            }

        async with self:
            # Open original page
            try:
                page1 = await self.context.new_page()
                await page1.goto(original_url, wait_until='networkidle', timeout=15000)
                await page1.wait_for_timeout(2000)

                original_text = await page1.evaluate("""
                    () => {
                        // Remove scripts and styles from text extraction
                        const clone = document.body.cloneNode(true);
                        clone.querySelectorAll('script, style').forEach(el => el.remove());
                        return clone.innerText;
                    }
                """)
                original_title = await page1.title()

                # Screenshot original
                original_screenshot = self.screenshot_dir / f"{downloaded_html.stem}_original.png"
                await page1.screenshot(path=str(original_screenshot), full_page=True)

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to load original page: {e}"
                }

            # Open downloaded version
            try:
                page2 = await self.context.new_page()
                file_url = f"file:///{downloaded_html.as_posix()}"
                await page2.goto(file_url, wait_until='networkidle', timeout=10000)
                await page2.wait_for_timeout(2000)

                downloaded_text = await page2.evaluate("""
                    () => {
                        const clone = document.body.cloneNode(true);
                        clone.querySelectorAll('script, style').forEach(el => el.remove());
                        return clone.innerText;
                    }
                """)

                # Screenshot downloaded
                downloaded_screenshot = self.screenshot_dir / f"{downloaded_html.stem}_downloaded.png"
                await page2.screenshot(path=str(downloaded_screenshot), full_page=True)

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to load downloaded HTML: {e}"
                }

            # Calculate similarity
            similarity = self._calculate_text_similarity(original_text, downloaded_text)

            # Count images
            original_images = await page1.query_selector_all("img")
            downloaded_images = await page2.query_selector_all("img")

            return {
                "success": True,
                "original_url": original_url,
                "downloaded_html": str(downloaded_html),
                "text_similarity": similarity,
                "original_length": len(original_text),
                "downloaded_length": len(downloaded_text),
                "acceptable": similarity >= 0.90,
                "image_count": {
                    "original": len(original_images),
                    "downloaded": len(downloaded_images)
                },
                "screenshots": {
                    "original": str(original_screenshot),
                    "downloaded": str(downloaded_screenshot)
                }
            }

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using SequenceMatcher.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        return SequenceMatcher(None, text1, text2).ratio()

    async def take_screenshot(
        self,
        page: Page,
        path: str,
        full_page: bool = True
    ) -> str:
        """
        Take a screenshot of the current page.

        Args:
            page: Playwright page object
            path: Screenshot save path
            full_page: Capture full scrollable page

        Returns:
            Absolute path to screenshot
        """
        screenshot_path = Path(path).resolve()
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)

        await page.screenshot(path=str(screenshot_path), full_page=full_page)

        self.logger.info(f"Screenshot saved: {screenshot_path}")
        return str(screenshot_path)


# Convenience function for quick testing
async def quick_test_html(html_path: str) -> Dict:
    """
    Quick test a local HTML file with all checks.

    Args:
        html_path: Path to HTML file

    Returns:
        Test results dict
    """
    tester = WebInteractionTester()
    return await tester.test_local_html(html_path)


if __name__ == "__main__":
    # Test command
    import sys

    if len(sys.argv) < 2:
        print("Usage: python web_interaction_tester.py <html_path>")
        sys.exit(1)

    html_path = sys.argv[1]
    results = asyncio.run(quick_test_html(html_path))

    print(json.dumps(results, indent=2, ensure_ascii=False))
