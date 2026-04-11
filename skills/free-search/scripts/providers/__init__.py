#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索Provider基类
所有搜索provider实现统一接口
"""
from abc import ABC, abstractmethod
from typing import Dict, List


class SearchProvider(ABC):
    """搜索Provider基类"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def search(self, query: str, max_results: int = 5, **kwargs) -> Dict:
        """
        执行搜索，返回统一格式的结果

        Args:
            query: 搜索查询
            max_results: 最大结果数
            **kwargs: 其他参数

        Returns:
            dict: {
                'success': bool,
                'provider': str,
                'results': List[Dict],  # 每个结果包含title, url, snippet
                'content': str,         # 格式化的文本内容
                'error': str,           # 失败时的错误信息
                'metadata': Dict        # 额外元数据
            }
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查provider是否可用"""
        pass
