#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serper.dev搜索Provider
使用Google搜索结果API (Serper.dev)进行搜索
"""
import requests
from typing import Dict
import sys
import os

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from providers import SearchProvider
from config import get_serper_api_key


class SerperProvider(SearchProvider):
    """Serper.dev API搜索Provider (Google搜索结果)"""

    def __init__(self):
        super().__init__("serper")
        self.api_url = "https://google.serper.dev/search"

    def is_available(self) -> bool:
        """检查Serper API是否可用"""
        api_key = get_serper_api_key()
        return bool(api_key)

    def search(self, query: str, max_results: int = 5, **kwargs) -> Dict:
        """
        使用Serper API进行搜索

        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            **kwargs: 其他参数（timeout等）

        Returns:
            搜索结果字典
        """
        api_key = get_serper_api_key()
        if not api_key:
            return {
                'success': False,
                'provider': self.name,
                'error': 'SERPER_API_KEY未配置',
                'results': [],
                'content': '',
                'metadata': {}
            }

        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }

        # Serper API payload - 支持中文搜索
        payload = {
            "q": query,
            "hl": "zh-cn",
            "gl": "cn"
        }

        timeout = kwargs.get('timeout', 30)

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=timeout
            )

            # 检查配额用尽
            if response.status_code == 429:
                return {
                    'success': False,
                    'provider': self.name,
                    'error': 'QUOTA_EXHAUSTED',
                    'results': [],
                    'content': '',
                    'metadata': {'status_code': 429}
                }

            # 检查权限错误
            if response.status_code == 403:
                return {
                    'success': False,
                    'provider': self.name,
                    'error': 'QUOTA_EXHAUSTED',
                    'results': [],
                    'content': '',
                    'metadata': {'status_code': 403}
                }

            response.raise_for_status()
            result = response.json()

            # 解析 organic 结果
            results = []
            organic = result.get("organic", [])
            for item in organic[:max_results]:
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', '')[:300]
                })

            # 格式化内容
            content = self._format_content(result, results)

            return {
                'success': True,
                'provider': self.name,
                'results': results,
                'content': content,
                'error': '',
                'metadata': {
                    'num_results': len(results),
                    'search_parameters': result.get('searchParameters', {})
                }
            }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'provider': self.name,
                'error': '搜索超时',
                'results': [],
                'content': '',
                'metadata': {}
            }
        except requests.exceptions.RequestException as e:
            # 检查是否是配额错误
            error_str = str(e).lower()
            if 'quota' in error_str or '429' in error_str or '403' in error_str:
                return {
                    'success': False,
                    'provider': self.name,
                    'error': 'QUOTA_EXHAUSTED',
                    'results': [],
                    'content': '',
                    'metadata': {'exception': str(e)}
                }
            return {
                'success': False,
                'provider': self.name,
                'error': f'搜索请求失败: {e}',
                'results': [],
                'content': '',
                'metadata': {}
            }
        except Exception as e:
            return {
                'success': False,
                'provider': self.name,
                'error': f'未知错误: {e}',
                'results': [],
                'content': '',
                'metadata': {}
            }

    def _format_content(self, raw_result: dict, results: list) -> str:
        """格式化搜索结果为文本"""
        content_parts = []

        # 添加搜索结果
        if results:
            content_parts.append("【Google搜索结果】")
            for i, r in enumerate(results, 1):
                content_parts.append(
                    f"\n{i}. {r['title']}\n"
                    f"   {r['snippet']}\n"
                    f"   来源: {r['url']}"
                )

        # 添加知识图谱信息（如果有）
        kg = raw_result.get('knowledgeGraph', {})
        if kg:
            content_parts.append(f"\n【知识图谱】")
            if kg.get('title'):
                content_parts.append(f"标题: {kg.get('title')}")
            if kg.get('description'):
                content_parts.append(f"描述: {kg.get('description')}")

        return '\n'.join(content_parts)
