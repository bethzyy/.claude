"""
日志管理模块 - 提供统一的日志接口

Logger module - Unified logging interface.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def get_logger(name: str = "xiaohongshu-pub", level: int = logging.INFO) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别

    Returns:
        配置好的Logger实例
    """
    logger = logging.getLogger(name)

    # 避免重复配置
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


class ProgressLogger:
    """进度日志记录器"""

    def __init__(self, total_steps: int = 4):
        """
        初始化进度记录器

        Args:
            total_steps: 总步骤数
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = datetime.now()

    def step(self, message: str):
        """
        记录一个步骤

        Args:
            message: 步骤描述
        """
        self.current_step += 1
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n[步骤{self.current_step}/{self.total_steps}] {message} (已用时: {elapsed:.1f}秒)")

    def complete(self, message: str = "完成"):
        """
        记录完成状态

        Args:
            message: 完成消息
        """
        total_elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{'=' * 60}")
        print(f"[{message}] 总用时: {total_elapsed:.1f}秒")
        print(f"{'=' * 60}")
