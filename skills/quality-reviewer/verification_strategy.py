"""
Verification Strategy Selector - Quality Reviewer v2.1.0

智能选择最佳验证策略，根据URL类型、CDP可用性和任务目标。

主要功能：
- 检测URL类型（飞书/登录页/静态网页）
- 检查CDP是否可用
- 智能选择验证方法（CDP/在线/静态）
"""

import re
import socket
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse


class VerificationStrategy:
    """验证策略选择器"""

    # URL模式
    FEISHU_PATTERNS = [
        r'feishu\.cn',
        r'feishu\.com',
        r'\.feishu\.cn',
        r'localhost\d+\.feishu\.cn',  # 租户模式
    ]

    LOGIN_REQUIRED_PATTERNS = [
        r'/login',
        r'/signin',
        r'/auth',
        r'/account',
        r'member\.',
        r'user\.',
        r'profile',
    ]

    def __init__(
        self,
        cdp_port: int = 9222,
        cdp_timeout: float = 0.5,
        logger: Optional[logging.Logger] = None
    ):
        """初始化策略选择器

        Args:
            cdp_port: CDP端口（默认9222）
            cdp_timeout: CDP检查超时（秒）
            logger: 可选的日志记录器
        """
        self.cdp_port = cdp_port
        self.cdp_timeout = cdp_timeout
        self.logger = logger or logging.getLogger(__name__)

        # 缓存CDP可用性
        self._cdp_available = None

    def select_strategy(
        self,
        url: str,
        task_goals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """智能选择验证策略

        决策树：
        1. 飞书URL + CDP可用 + 高目标(≥90%) → CDP方法
        2. 登录页 + CDP可用 → CDP方法
        3. 静态页 + 低目标(<90%) → 在线对比
        4. 无CDP → 静态分析（降级）

        Args:
            url: 目标URL
            task_goals: 任务目标（包含completeness_target等）

        Returns:
            策略字典：
                - method: 验证方法（"cdp" | "online" | "static"）
                - reason: 选择原因
                - config: 方法配置
                - confidence: 置信度（0-1）
        """
        # 1. 检测页面类型
        page_type = self._detect_page_type(url)
        self.logger.info(f"检测到页面类型: {page_type}")

        # 2. 检查CDP可用性
        cdp_available = self._check_cdp_available()
        self.logger.info(f"CDP可用性: {cdp_available}")

        # 3. 获取任务目标
        completeness_target = task_goals.get("completeness_target", 90.0)
        self.logger.info(f"完整度目标: {completeness_target}%")

        # 4. 决策逻辑
        if page_type == "feishu":
            return self._strategy_for_feishu(cdp_available, completeness_target)

        elif page_type == "login_required":
            return self._strategy_for_login(cdp_available, completeness_target)

        else:  # static
            return self._strategy_for_static(cdp_available, completeness_target)

    def _strategy_for_feishu(
        self,
        cdp_available: bool,
        completeness_target: float
    ) -> Dict[str, Any]:
        """飞书文档策略"""
        if cdp_available:
            return {
                "method": "cdp",
                "reason": "飞书文档需要登录态才能获取准确baseline，CDP可以提供已登录的Chrome会话",
                "config": {
                    "use_cdp": True,
                    "cdp_port": self.cdp_port,
                    "wait_time": 30,
                    "scroll_iterations": 10,
                    "scroll_delay": 1000,
                },
                "confidence": 0.95,
                "fallback": "online"
            }
        else:
            return {
                "method": "online",
                "reason": "CDP不可用，使用在线对比（可能无法访问完整内容）",
                "config": {
                    "timeout": 15000,
                    "wait_until": "networkidle"
                },
                "confidence": 0.40,
                "warning": "飞书文档需要登录态，建议启用CDP",
                "fallback": "static"
            }

    def _strategy_for_login(
        self,
        cdp_available: bool,
        completeness_target: float
    ) -> Dict[str, Any]:
        """登录页策略"""
        if cdp_available:
            return {
                "method": "cdp",
                "reason": "页面需要登录，CDP可以提供已登录的会话",
                "config": {
                    "use_cdp": True,
                    "cdp_port": self.cdp_port,
                    "wait_time": 20,
                    "scroll_iterations": 5,
                },
                "confidence": 0.90,
                "fallback": "static"
            }
        else:
            return {
                "method": "static",
                "reason": "CDP不可用且页面需要登录，无法进行在线对比，使用静态分析",
                "config": {
                    "html_only": True
                },
                "confidence": 0.50,
                "warning": "登录页无法准确验证，建议启用CDP"
            }

    def _strategy_for_static(
        self,
        cdp_available: bool,
        completeness_target: float
    ) -> Dict[str, Any]:
        """静态页策略"""
        if completeness_target >= 95.0 and cdp_available:
            # 高目标 + CDP可用 → 使用CDP确保准确
            return {
                "method": "cdp",
                "reason": f"完整度目标较高({completeness_target}%)，使用CDP确保准确baseline",
                "config": {
                    "use_cdp": True,
                    "cdp_port": self.cdp_port,
                    "wait_time": 15,
                    "scroll_iterations": 5,
                },
                "confidence": 0.85,
                "fallback": "online"
            }
        else:
            # 标准情况 → 在线对比
            return {
                "method": "online",
                "reason": "普通静态页面，使用在线对比即可",
                "config": {
                    "timeout": 15000,
                    "wait_until": "networkidle"
                },
                "confidence": 0.80,
                "fallback": "static"
            }

    def _detect_page_type(self, url: str) -> str:
        """检测页面类型

        Args:
            url: 目标URL

        Returns:
            页面类型："feishu" | "login_required" | "static"
        """
        # 1. 检查飞书
        for pattern in self.FEISHU_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return "feishu"

        # 2. 检查登录页模式
        for pattern in self.LOGIN_REQUIRED_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return "login_required"

        # 3. 默认为静态页
        return "static"

    def _check_cdp_available(self) -> bool:
        """检查CDP是否可用

        尝试连接到localhost:9222（Chrome DevTools Protocol）。

        Returns:
            CDP是否可用
        """
        # 使用缓存
        if self._cdp_available is not None:
            return self._cdp_available

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.cdp_timeout)
            result = sock.connect_ex(("localhost", self.cdp_port))
            sock.close()

            self._cdp_available = (result == 0)

            if self._cdp_available:
                self.logger.info(f"CDP可用 (端口 {self.cdp_port})")
            else:
                self.logger.info(f"CDP不可用 (端口 {self.cdp_port})")

            return self._cdp_available

        except Exception as e:
            self.logger.debug(f"CDP检查失败: {e}")
            self._cdp_available = False
            return False

    @staticmethod
    def is_feishu_url(url: str) -> bool:
        """检查是否为飞书URL

        Args:
            url: 目标URL

        Returns:
            是否为飞书URL
        """
        for pattern in VerificationStrategy.FEISHU_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def needs_login(url: str) -> bool:
        """检查URL是否可能需要登录

        Args:
            url: 目标URL

        Returns:
            是否可能需要登录
        """
        for pattern in VerificationStrategy.LOGIN_REQUIRED_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False


# 便捷函数
def select_strategy_quick(
    url: str,
    completeness_target: float = 90.0,
    cdp_port: int = 9222
) -> Dict[str, Any]:
    """快速选择策略

    Args:
        url: 目标URL
        completeness_target: 完整度目标（默认90%）
        cdp_port: CDP端口（默认9222）

    Returns:
        策略字典
    """
    selector = VerificationStrategy(cdp_port=cdp_port)
    task_goals = {"completeness_target": completeness_target}
    return selector.select_strategy(url, task_goals)


# 测试用例
if __name__ == "__main__":
    # 测试策略选择
    test_cases = [
        {
            "url": "https://meetchances.feishu.cn/wiki/test",
            "completeness_target": 95.0,
        },
        {
            "url": "https://example.com/member/profile",
            "completeness_target": 90.0,
        },
        {
            "url": "https://example.com/page",
            "completeness_target": 90.0,
        },
        {
            "url": "https://example.com/article",
            "completeness_target": 98.0,
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"URL: {case['url']}")
        print(f"完整度目标: {case['completeness_target']}%")

        strategy = select_strategy_quick(
            case["url"],
            case["completeness_target"]
        )

        print(f"验证方法: {strategy['method']}")
        print(f"原因: {strategy['reason']}")
        print(f"置信度: {strategy['confidence']}")
        if "warning" in strategy:
            print(f"警告: {strategy['warning']}")
