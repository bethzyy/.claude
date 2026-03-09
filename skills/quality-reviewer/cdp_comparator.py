"""
CDP Comparator - Quality Reviewer v2.1.0

使用Chrome DevTools Protocol (CDP)获取准确的原始页面baseline。

主要功能：
- 连接到已登录的Chrome会话
- 等待页面完全加载（30秒 + 滚动触发懒加载）
- 提取准确的文本内容
- 计算完整度百分比

参考实现：gethtml/accurate_completeness_check.py（已验证可达102.9%准确度）
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from bs4 import BeautifulSoup


class CDPComparator:
    """使用CDP进行准确的内容对比"""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        completeness_target: float = 90.0
    ):
        """初始化CDP对比器

        Args:
            logger: 可选的日志记录器
            completeness_target: 完整度目标（默认90%）
        """
        self.logger = logger or logging.getLogger(__name__)
        self.completeness_target = completeness_target

    async def fetch_baseline(
        self,
        url: str,
        cdp_port: int = 9222,
        wait_time: int = 30,
        scroll_iterations: int = 10,
        scroll_delay: int = 1000,
        timeout: int = 60000,
        **kwargs  # Ignore extra params like 'use_cdp'
    ) -> Dict[str, Any]:
        """使用CDP获取原始页面baseline

        这个方法参考了gethtml项目的已验证实现：
        - 连接到已登录的Chrome
        - 等待30秒让页面完全加载
        - 滚动10次触发懒加载内容
        - 提取文本内容

        Args:
            url: 目标URL
            cdp_port: CDP端口（默认9222）
            wait_time: 初始等待时间（秒，默认30）
            scroll_iterations: 滚动次数（默认10）
            scroll_delay: 滚动间隔（毫秒，默认1000）
            timeout: 页面加载超时（毫秒，默认60000）

        Returns:
            Baseline字典：
                - text: 页面文本内容
                - length: 文本长度
                - success: 是否成功
                - error: 错误信息（如果失败）
                - method: "cdp"
        """
        playwright = None

        try:
            self.logger.info(f"开始CDP baseline获取: {url}")
            self.logger.info(f"配置: 端口={cdp_port}, 等待={wait_time}秒, 滚动={scroll_iterations}次")

            playwright = await async_playwright().start()

            # 连接到已登录的Chrome
            self.logger.info(f"连接到CDP: localhost:{cdp_port}")
            browser: Browser = await playwright.chromium.connect_over_cdp(
                f"http://localhost:{cdp_port}"
            )

            # 获取第一个上下文
            contexts = browser.contexts
            if not contexts:
                raise Exception("未找到Chrome上下文，请确保Chrome已启动并登录")

            context: BrowserContext = contexts[0]
            page: Page = await context.new_page()

            # 导航到目标页面
            self.logger.info(f"导航到页面: {url}")
            await page.goto(url, wait_until="networkidle", timeout=timeout)

            # 等待指定时间
            self.logger.info(f"等待 {wait_time} 秒...")
            await asyncio.sleep(wait_time)

            # 滚动触发懒加载
            self.logger.info(f"滚动 {scroll_iterations} 次触发懒加载...")
            for i in range(scroll_iterations):
                scroll_y = i * 500
                await page.evaluate(f"window.scrollTo(0, {scroll_y})")
                await asyncio.sleep(scroll_delay / 1000)

            # 滚回顶部
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(3)

            # 提取文本（使用与JavaScript innerText相同的方法）
            text = await page.evaluate("document.body.innerText")
            length = len(text)

            self.logger.info(f"[OK] Baseline获取成功: {length:,} 字符")

            return {
                "text": text,
                "length": length,
                "success": True,
                "method": "cdp",
                "config": {
                    "cdp_port": cdp_port,
                    "wait_time": wait_time,
                    "scroll_iterations": scroll_iterations,
                }
            }

        except Exception as e:
            error_msg = f"CDP baseline获取失败: {str(e)}"
            self.logger.error(error_msg)

            return {
                "text": "",
                "length": 0,
                "success": False,
                "error": error_msg,
                "method": "cdp"
            }

        finally:
            if playwright:
                await playwright.stop()

    def calculate_completeness(
        self,
        baseline: Dict[str, Any],
        downloaded_text: str
    ) -> Dict[str, Any]:
        """计算完整度

        Args:
            baseline: 从fetch_baseline()获取的baseline
            downloaded_text: 下载的文本内容

        Returns:
            完整度字典：
                - completeness: 完整度百分比
                - met_target: 是否达到目标
                - gap: 字符差距
                - baseline_length: baseline长度
                - downloaded_length: 下载长度
                - success: 是否成功
        """
        if not baseline.get("success"):
            return {
                "completeness": 0.0,
                "met_target": False,
                "success": False,
                "error": "Baseline获取失败，无法计算完整度"
            }

        baseline_length = baseline["length"]
        downloaded_length = len(downloaded_text)

        # 计算完整度
        if baseline_length > 0:
            completeness = (downloaded_length / baseline_length) * 100
        else:
            completeness = 0.0

        # 判断是否达到目标
        met_target = completeness >= self.completeness_target

        # 计算差距
        gap = baseline_length - downloaded_length

        self.logger.info(f"完整度计算: {completeness:.1f}% (目标: {self.completeness_target}%)")
        self.logger.info(f"Baseline: {baseline_length:,} 字符")
        self.logger.info(f"下载: {downloaded_length:,} 字符")
        self.logger.info(f"差距: {gap:,} 字符")
        self.logger.info(f"达到目标: {'是' if met_target else '否'}")

        return {
            "completeness": round(completeness, 1),
            "met_target": met_target,
            "gap": gap,
            "baseline_length": baseline_length,
            "downloaded_length": downloaded_length,
            "success": True,
            "method": "cdp"
        }

    async def compare_with_baseline(
        self,
        url: str,
        downloaded_html: str,
        cdp_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """完整的CDP对比流程

        Args:
            url: 原始URL
            downloaded_html: 下载的HTML内容
            cdp_config: CDP配置（可选）

        Returns:
            对比结果字典
        """
        # 1. 获取baseline
        if cdp_config is None:
            cdp_config = {
                "cdp_port": 9222,
                "wait_time": 30,
                "scroll_iterations": 10,
            }

        baseline = await self.fetch_baseline(url, **cdp_config)

        if not baseline["success"]:
            return {
                "success": False,
                "error": baseline.get("error", "Unknown error"),
                "method": "cdp"
            }

        # 2. 提取下载HTML的文本
        soup = BeautifulSoup(downloaded_html, 'lxml')

        # 移除script和style标签（与JavaScript innerText行为一致）
        for script in soup(["script", "style"]):
            script.decompose()

        downloaded_text = soup.get_text(separator='\n', strip=True)

        # 3. 计算完整度
        completeness_result = self.calculate_completeness(baseline, downloaded_text)

        return {
            **completeness_result,
            "baseline_text_length": baseline["length"],
            "downloaded_text_length": len(downloaded_text),
        }

    async def compare_with_baseline_and_rendered_check(
        self,
        url: str,
        html_path: str,
        downloaded_html: str,
        cdp_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """CDP对比 + 渲染检查（NEW - 修复飞书文档误判）

        对比原始页面和下载的HTML，同时检查下载的HTML是否正确渲染。

        Args:
            url: 原始URL
            html_path: 下载的HTML文件路径
            downloaded_html: 下载的HTML内容
            cdp_config: CDP配置（可选）

        Returns:
            对比结果字典（包含渲染检查信息）
        """
        # 1. 获取baseline
        if cdp_config is None:
            cdp_config = {
                "cdp_port": 9222,
                "wait_time": 30,
                "scroll_iterations": 10,
            }

        baseline = await self.fetch_baseline(url, **cdp_config)

        if not baseline["success"]:
            return {
                "success": False,
                "error": baseline.get("error", "Unknown error"),
                "method": "cdp"
            }

        # 2. 检查渲染效果（NEW！）
        self.logger.info("[NEW] 检查下载HTML的实际渲染效果...")
        rendered_check = await self.extract_rendered_text(html_path, wait_time=5)

        # 3. 提取HTML源代码文本（用于对比）
        html_source_text = self.extract_text_from_html(downloaded_html)

        # 4. 计算两种完整度
        # 4a. HTML源代码完整度（旧方法，可能误判）
        html_source_completeness = (len(html_source_text) / baseline["length"]) * 100 if baseline["length"] > 0 else 0

        # 4b. 实际渲染完整度（新方法，准确）
        if rendered_check["render_success"]:
            rendered_completeness = (rendered_check["length"] / baseline["length"]) * 100 if baseline["length"] > 0 else 0
        else:
            rendered_completeness = 0.0

        # 5. 判断使用哪个完整度
        if rendered_check["main_content_empty"]:
            # 渲染失败，内容区为空
            self.logger.warning(f"[NEW] 渲染检查失败: 主内容区为空")
            self.logger.warning(f"[NEW] HTML源代码: {len(html_source_text)}字符, 实际渲染: {rendered_check['length']}字符")
            self.logger.warning(f"[NEW] 这是SPA应用（如飞书），需要JavaScript才能渲染内容")

            # 使用实际渲染完整度（通常是0或很低）
            actual_completeness = rendered_completeness
            met_target = False
            rendering_issue = True

        else:
            # 渲染成功，使用渲染后的完整度
            self.logger.info(f"[NEW] 渲染检查成功: {rendered_check['length']}字符")
            actual_completeness = rendered_completeness
            met_target = actual_completeness >= self.completeness_target
            rendering_issue = False

        # 6. 返回结果
        return {
            "completeness": round(actual_completeness, 1),
            "met_target": met_target,
            "baseline_length": baseline["length"],
            "downloaded_length": rendered_check["length"],
            "html_source_length": len(html_source_text),
            "html_source_completeness": round(html_source_completeness, 1),
            "rendered_completeness": round(rendered_completeness, 1),
            "rendering_check": {
                "render_success": rendered_check["render_success"],
                "main_content_empty": rendered_check["main_content_empty"],
                "main_content_status": rendered_check.get("main_content_status", "unknown"),
                "js_errors": rendered_check.get("js_errors", [])
            },
            "rendering_issue": rendering_issue,
            "gap": baseline["length"] - rendered_check["length"],
            "success": True,
            "method": "cdp",
            "diagnosis": self._generate_diagnosis(rendered_check, html_source_completeness, rendered_completeness)
        }

    def _generate_diagnosis(
        self,
        rendered_check: Dict,
        html_source_completeness: float,
        rendered_completeness: float
    ) -> str:
        """生成诊断信息

        Args:
            rendered_check: 渲染检查结果
            html_source_completeness: HTML源代码完整度
            rendered_completeness: 渲染后完整度

        Returns:
            诊断信息字符串
        """
        if rendered_check["main_content_empty"]:
            return (
                f"SPA应用渲染失败（如飞书文档）。"
                f"HTML源代码显示有内容（{html_source_completeness:.1f}%），"
                f"但实际渲染后内容区为空（{rendered_completeness:.1f}%）。"
                f"原因：内容存储在data-string属性中，需要JavaScript渲染，"
                f"但JavaScript可能依赖在线API或认证token。"
            )
        elif html_source_completeness > rendered_completeness + 20:
            return (
                f"部分渲染失败。"
                f"HTML源代码有更多内容（{html_source_completeness:.1f}%），"
                f"但渲染后较少（{rendered_completeness:.1f}%）。"
                f"可能是懒加载或JavaScript未完全执行。"
            )
        else:
            return "渲染正常，内容完整。"

    @staticmethod
    def extract_text_from_html(html_content: str) -> str:
        """从HTML中提取可见文本（仅HTML源代码，不检查渲染效果）

        模拟JavaScript的innerText行为：
        - 移除script和style标签
        - 保留可见文本

        WARNING: 这个方法只提取HTML源代码中的文本，不检查JavaScript渲染效果！
        对于SPA应用（如飞书文档），这会误判为有内容。

        Args:
            html_content: HTML内容

        Returns:
            提取的文本
        """
        soup = BeautifulSoup(html_content, 'lxml')

        # 移除script和style标签
        for script in soup(["script", "style"]):
            script.decompose()

        # 提取文本
        text = soup.get_text(separator='\n', strip=True)

        return text

    async def extract_rendered_text(
        self,
        html_path: str,
        wait_time: int = 5
    ) -> Dict[str, Any]:
        """提取HTML实际渲染后的可见文本（NEW - 修复飞书文档误判）

        使用Playwright打开HTML文件，等待JavaScript渲染，提取实际可见内容。

        Args:
            html_path: HTML文件路径
            wait_time: 等待JavaScript渲染的时间（秒，默认5）

        Returns:
            渲染结果字典：
                - text: 渲染后的可见文本
                - length: 文本长度
                - render_success: 是否成功渲染
                - main_content_empty: 主内容区是否为空
                - error: 错误信息（如果失败）
        """
        from playwright.async_api import async_playwright

        playwright = None

        try:
            self.logger.info(f"开始检查HTML渲染效果: {html_path}")
            self.logger.info(f"等待JavaScript渲染: {wait_time}秒...")

            playwright = await async_playwright().start()

            # 使用浏览器打开本地HTML文件
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # 打开本地HTML文件
            await page.goto(f"file:///{html_path.replace(os.sep, '/')}", wait_until="networkidle")

            # 等待JavaScript渲染
            await page.wait_for_timeout(wait_time * 1000)

            # 尝试滚动以触发懒加载
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            await page.evaluate("window.scrollTo(0, 0)")

            # 获取实际可见文本
            rendered_text = await page.evaluate("document.body.innerText")
            rendered_length = len(rendered_text.strip())

            # 检查主内容区域
            main_content_empty = await page.evaluate("""
                () => {
                    // 检查主内容区域
                    const mainContent = document.querySelector('#wiki-content') ||
                                       document.querySelector('main') ||
                                       document.querySelector('.content') ||
                                       document.querySelector('.wiki-main-content');

                    if (!mainContent) {
                        return 'NO_MAIN_CONTENT_AREA';
                    }

                    const text = mainContent.innerText || mainContent.textContent || '';
                    return text.trim().length < 100 ? 'MAIN_CONTENT_EMPTY' : 'MAIN_CONTENT_OK';
                }
            """)

            # 检查是否有JavaScript错误
            js_errors = await page.evaluate("""
                () => {
                    return window.__errors__ || [];
                }
            """)

            await browser.close()
            await playwright.stop()

            # 判断渲染是否成功
            render_success = rendered_length > 100
            is_empty = (main_content_empty == 'MAIN_CONTENT_EMPTY' or
                      main_content_empty == 'NO_MAIN_CONTENT_AREA')

            self.logger.info(f"渲染后文本长度: {rendered_length} 字符")
            self.logger.info(f"主内容区状态: {main_content_empty}")
            self.logger.info(f"渲染成功: {'是' if render_success else '否'}")
            self.logger.info(f"内容区为空: {'是' if is_empty else '否'}")

            return {
                "text": rendered_text.strip(),
                "length": rendered_length,
                "render_success": render_success,
                "main_content_empty": is_empty,
                "main_content_status": main_content_empty,
                "js_errors": js_errors,
                "success": True
            }

        except Exception as e:
            error_msg = f"渲染检查失败: {str(e)}"
            self.logger.error(error_msg)

            if playwright:
                await playwright.stop()

            return {
                "text": "",
                "length": 0,
                "render_success": False,
                "main_content_empty": True,
                "error": error_msg,
                "success": False
            }


# 便捷函数
async def compare_cdp_quick(
    url: str,
    downloaded_html: str,
    completeness_target: float = 90.0,
    cdp_port: int = 9222,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """快速CDP对比

    Args:
        url: 原始URL
        downloaded_html: 下载的HTML
        completeness_target: 完整度目标（默认90%）
        cdp_port: CDP端口（默认9222）
        logger: 可选的日志记录器

    Returns:
        对比结果
    """
    comparator = CDPComparator(
        logger=logger,
        completeness_target=completeness_target
    )

    return await comparator.compare_with_baseline(url, downloaded_html)


# 测试用例
if __name__ == "__main__":
    import sys

    async def test():
        """测试CDP对比器"""
        # 示例：需要真实的HTML文件和URL
        if len(sys.argv) < 3:
            print("用法: python cdp_comparator.py <url> <html_file>")
            print("示例: python cdp_comparator.py https://example.com page.html")
            return

        url = sys.argv[1]
        html_file = sys.argv[2]

        # 读取HTML
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 执行对比
        result = await compare_cdp_quick(
            url=url,
            downloaded_html=html_content,
            completeness_target=95.0
        )

        # 输出结果
        print("\n" + "=" * 60)
        print("CDP对比结果")
        print("=" * 60)

        if result["success"]:
            print(f"完整度: {result['completeness']}%")
            print(f"达到目标: {'是' if result['met_target'] else '否'}")
            print(f"Baseline: {result['baseline_length']:,} 字符")
            print(f"下载: {result['downloaded_length']:,} 字符")
            print(f"差距: {result['gap']:,} 字符")
        else:
            print(f"错误: {result.get('error', 'Unknown error')}")

    # 运行测试
    asyncio.run(test())
