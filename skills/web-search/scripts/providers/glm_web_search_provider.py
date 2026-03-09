#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GLM Web Search Provider
使用ZhipuAI GLM-4-flash模型的web_search工具能力
"""
import sys
import os

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from providers import SearchProvider
from config import get_zhipu_api_key


class GLMWebSearchProvider(SearchProvider):
    """GLM Web Search Provider（使用GLM-4-flash的web_search工具）"""

    def __init__(self):
        super().__init__("glm_web_search")
        # 优先级：3（MCP=1, Tavily=2, GLM=3, DuckDuckGo=4, AI知识库=5）

    def is_available(self) -> bool:
        """检查GLM Web Search是否可用"""
        api_key = get_zhipu_api_key()

        if not api_key:
            return False

        try:
            from zhipuai import ZhipuAI
            # 尝试创建客户端验证
            client = ZhipuAI(api_key=api_key)
            return True
        except Exception:
            return False

    def search(self, query: str, max_results: int = 5, **kwargs) -> dict:
        """
        使用GLM-4-flash的web_search工具进行搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数
            **kwargs: 其他参数

        Returns:
            搜索结果字典
        """
        api_key = get_zhipu_api_key()
        if not api_key:
            return {
                'success': False,
                'provider': self.name,
                'error': 'ZHIPU_API_KEY未配置',
                'results': [],
                'content': '',
                'metadata': {}
            }

        try:
            from zhipuai import ZhipuAI
        except ImportError:
            return {
                'success': False,
                'provider': self.name,
                'error': '未安装zhipuai库，请运行: pip install zhipuai',
                'results': [],
                'content': '',
                'metadata': {}
            }

        try:
            client = ZhipuAI(api_key=api_key)

            # 使用GLM-4-flash的web_search工具
            response = client.chat.completions.create(
                model="glm-4-flash",  # 使用flash版本（速度快、成本低）
                messages=[
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                tools=[
                    {
                        "type": "web_search",
                        "web_search": {
                            "enable": True,
                            "search_result": True
                        }
                    }
                ],
                temperature=0.7,
                max_tokens=4096
            )

            # 提取搜索结果
            if not response.choices:
                return {
                    'success': False,
                    'provider': self.name,
                    'error': 'GLM未返回搜索结果',
                    'results': [],
                    'content': '',
                    'metadata': {}
                }

            message = response.choices[0].message
            content = message.content or ""

            # 提取tool_calls中的搜索结果
            search_results = []
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call.type == "web_search" and hasattr(tool_call, 'web_search'):
                        web_search_data = tool_call.web_search
                        if hasattr(web_search_data, 'search_result'):
                            # 解析搜索结果
                            for item in web_search_data.search_result:
                                search_results.append({
                                    'title': item.get('title', ''),
                                    'url': item.get('url', ''),
                                    'snippet': item.get('content', '')  # GLM使用content字段
                                })

            # 如果没有提取到结构化结果，尝试从content中解析
            if not search_results and content:
                # GLM可能会在content中返回搜索结果的格式化文本
                # 这里我们简单返回整个content作为结果
                search_results = [{
                    'title': 'GLM Web Search结果',
                    'url': '',
                    'snippet': content[:500] + '...' if len(content) > 500 else content
                }]

            # 限制结果数量
            search_results = search_results[:max_results]

            return {
                'success': True,
                'provider': self.name,
                'results': search_results,
                'content': content,
                'metadata': {
                    'model': 'glm-4-flash',
                    'tool_type': 'web_search',
                    'total_results': len(search_results)
                }
            }

        except Exception as e:
            return {
                'success': False,
                'provider': self.name,
                'error': f'GLM Web Search失败: {str(e)}',
                'results': [],
                'content': '',
                'metadata': {}
            }
