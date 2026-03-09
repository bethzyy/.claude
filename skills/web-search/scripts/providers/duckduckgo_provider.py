#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckDuckGo搜索Provider
使用duckduckgo-search库进行免费搜索
"""
import sys
import os

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from providers import SearchProvider


class DuckDuckGoProvider(SearchProvider):
    """DuckDuckGo搜索Provider（完全免费，无需API Key）"""

    def __init__(self):
        super().__init__("duckduckgo")

    def is_available(self) -> bool:
        """检查DuckDuckGo是否可用（始终可用）"""
        try:
            from duckduckgo_search import DDGS
            return True
        except ImportError:
            return False

    def search(self, query: str, max_results: int = 5, **kwargs) -> dict:
        """
        使用DuckDuckGo进行搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数
            **kwargs: 其他参数（timeout等）

        Returns:
            搜索结果字典
        """
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return {
                'success': False,
                'provider': self.name,
                'error': '未安装duckduckgo-search库，请运行: pip install duckduckgo-search',
                'results': [],
                'content': '',
                'metadata': {}
            }

        try:
            results = []
            with DDGS() as ddgs:
                search_results = list(ddgs.text(
                    query,
                    max_results=max_results
                ))

                for r in search_results:
                    results.append({
                        'title': r.get('title', ''),
                        'url': r.get('href', ''),
                        'snippet': r.get('body', '')[:300]
                    })

            if results:
                # 格式化内容
                content = '\n\n'.join([
                    f"【{r['title']}】\n{r['snippet']}\n来源: {r['url']}"
                    for r in results
                ])

                return {
                    'success': True,
                    'provider': self.name,
                    'results': results,
                    'content': content,
                    'error': '',
                    'metadata': {
                        'num_results': len(results)
                    }
                }
            else:
                return {
                    'success': False,
                    'provider': self.name,
                    'error': '未找到搜索结果',
                    'results': [],
                    'content': '',
                    'metadata': {}
                }

        except Exception as e:
            return {
                'success': False,
                'provider': self.name,
                'error': f'搜索异常: {e}',
                'results': [],
                'content': '',
                'metadata': {}
            }
