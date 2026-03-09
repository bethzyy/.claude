"""
Task Goal Parser - Quality Reviewer v2.1.0

解析用户任务目标，提取验证标准和成功条件。

主要功能：
- 从任务描述中提取完整度目标（"95%完整度" → 95.0）
- 支持多种表达格式（中文/英文，百分比/小数）
- 提供默认值和回退策略
"""

import re
import logging
from typing import Dict, Any, Optional


class TaskGoalParser:
    """任务目标解析器"""

    # 支持的完整度表达模式
    COMPLETENESS_PATTERNS = [
        # 中文模式
        r'(\d+(?:\.\d+)?)\s*%\s*完整度',
        r'完整度\s*[≥>=]\s*(\d+(?:\.\d+)?)\s*%',
        r'完整度\s*[≥>=]\s*(\d+(?:\.\d+)?)',
        r'内容完整度\s*[≥>=]\s*(\d+(?:\.\d+)?)\s*%',

        # 英文模式
        r'completeness\s*[≥>=]\s*(\d+(?:\.\d+)?)\s*%',
        r'(\d+(?:\.\d+)?)\s*%\s*completeness',

        # 混合模式
        r'(\d{2,3})\s*%',  # 纯数字百分比（在明确上下文中）
    ]

    # 默认值
    DEFAULT_COMPLETENESS_TARGET = 90.0
    MIN_COMPLETENESS_TARGET = 50.0
    MAX_COMPLETENESS_TARGET = 100.0

    def __init__(self, logger: Optional[logging.Logger] = None):
        """初始化解析器

        Args:
            logger: 可选的日志记录器
        """
        self.logger = logger or logging.getLogger(__name__)

    @staticmethod
    def parse(task: Dict[str, Any]) -> Dict[str, Any]:
        """解析任务目标

        从任务描述和要求中提取验证目标。

        Args:
            task: 任务字典，包含以下字段：
                - description: 任务描述
                - requirements: 任务要求（可选）
                - success_criteria: 成功标准（可选）
                - custom_goals: 自定义目标（可选）

        Returns:
            目标字典，包含：
                - completeness_target: 完整度目标（0-100）
                - quality_targets: 质量目标列表
                - custom_goals: 自定义目标
                - raw_input: 原始输入（用于调试）
        """
        parser = TaskGoalParser()

        # 合并所有文本字段
        text_context = ""
        if "description" in task:
            text_context += task["description"] + " "
        if "requirements" in task:
            text_context += task["requirements"] + " "
        if "success_criteria" in task:
            text_context += str(task["success_criteria"]) + " "

        # 解析完整度目标
        completeness_target = parser._parse_completeness_target(text_context, task)

        # 解析其他质量目标
        quality_targets = parser._parse_quality_targets(text_context, task)

        # 提取自定义目标
        custom_goals = task.get("custom_goals", {})

        return {
            "completeness_target": completeness_target,
            "quality_targets": quality_targets,
            "custom_goals": custom_goals,
            "raw_input": {
                "description": task.get("description", ""),
                "requirements": task.get("requirements", ""),
                "text_context": text_context.strip()
            }
        }

    def _parse_completeness_target(
        self,
        text_context: str,
        task: Dict[str, Any]
    ) -> float:
        """从文本中提取完整度目标

        Args:
            text_context: 合并后的任务文本
            task: 原始任务字典

        Returns:
            完整度目标（0-100）
        """
        # 方法1：从文本中提取
        for pattern in self.COMPLETENESS_PATTERNS:
            match = re.search(pattern, text_context, re.IGNORECASE)
            if match:
                target = float(match.group(1))

                # 验证范围
                if self.MIN_COMPLETENESS_TARGET <= target <= self.MAX_COMPLETENESS_TARGET:
                    self.logger.info(f"从文本提取完整度目标: {target}%")
                    return target
                else:
                    self.logger.warning(
                        f"完整度目标超出范围 [{target}%], "
                        f"使用默认值 {self.DEFAULT_COMPLETENESS_TARGET}%"
                    )

        # 方法2：从成功标准中提取
        if "success_criteria" in task:
            criteria = task["success_criteria"]
            if isinstance(criteria, dict):
                if "completeness" in criteria:
                    target = float(criteria["completeness"])
                    if self.MIN_COMPLETENESS_TARGET <= target <= self.MAX_COMPLETENESS_TARGET:
                        self.logger.info(f"从成功标准提取完整度目标: {target}%")
                        return target

        # 方法3：使用默认值
        self.logger.info(
            f"未找到完整度目标，使用默认值: {self.DEFAULT_COMPLETENESS_TARGET}%"
        )
        return self.DEFAULT_COMPLETENESS_TARGET

    def _parse_quality_targets(self, text_context: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """解析其他质量目标

        Args:
            text_context: 任务文本
            task: 任务字典

        Returns:
            质量目标字典
        """
        targets = {
            "accessibility": False,  # 可访问性检查
            "performance": False,    # 性能检查
            "seo": False,           # SEO检查
            "security": True,       # 安全检查（默认开启）
        }

        # 检测关键词
        keywords = {
            "accessibility": ["可访问性", "accessibility", "无障碍", "a11y"],
            "performance": ["性能", "performance", "速度", "加载时间", "speed"],
            "seo": ["SEO", "搜索引擎", "search engine", "优化"],
        }

        text_lower = text_context.lower()

        for target_name, terms in keywords.items():
            if any(term in text_lower for term in terms):
                targets[target_name] = True
                self.logger.info(f"启用质量目标: {target_name}")

        # 从任务字典中读取明确设置
        if "quality_checks" in task:
            for check, enabled in task["quality_checks"].items():
                if check in targets:
                    targets[check] = enabled

        return targets

    @staticmethod
    def validate_target(completeness: float) -> bool:
        """验证完整度目标是否有效

        Args:
            completeness: 完整度目标

        Returns:
            是否有效
        """
        return TaskGoalParser.MIN_COMPLETENESS_TARGET <= completeness <= TaskGoalParser.MAX_COMPLETENESS_TARGET


# 便捷函数
def parse_completeness_target(task: Dict[str, Any]) -> float:
    """快速提取完整度目标

    Args:
        task: 任务字典

    Returns:
        完整度目标（0-100）
    """
    goals = TaskGoalParser.parse(task)
    return goals["completeness_target"]


# 测试用例
if __name__ == "__main__":
    # 测试解析器
    test_cases = [
        {
            "description": "下载飞书文档，要求95%内容完整度",
        },
        {
            "description": "网页下载任务",
            "requirements": "completeness ≥ 90%"
        },
        {
            "description": "简单下载任务",
        },
        {
            "description": "高完整度要求",
            "success_criteria": {"completeness": 98.0}
        },
    ]

    for i, task in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"描述: {task.get('description', '')}")

        goals = TaskGoalParser.parse(task)
        print(f"完整度目标: {goals['completeness_target']}%")
        print(f"质量目标: {goals['quality_targets']}")
