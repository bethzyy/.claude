#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI知识库搜索Provider
使用ZhipuAI GLM模型的知识库作为最后手段
"""
import sys
import os

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from providers import SearchProvider
from config import get_zhipu_api_key


class AIKnowledgeProvider(SearchProvider):
    """AI知识库Provider（最后手段，使用预训练知识）"""

    def __init__(self):
        super().__init__("ai_knowledge")

    def is_available(self) -> bool:
        """检查AI知识库是否可用"""
        api_key = get_zhipu_api_key()
        return bool(api_key)

    def search(self, query: str, max_results: int = 5, **kwargs) -> dict:
        """
        使用AI知识库进行搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数（AI知识库不使用此参数）
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

            # 构建提示词
            prompt = f"""请提供关于"{query}"的信息。

注意：这是基于AI预训练知识的回答，可能不是最新的实时信息。如果需要最新信息，请使用网络搜索功能。

请提供：
1. 相关的基本信息和定义
2. 主要特点和要点
3. 常见应用或场景

请用清晰的格式回答。"""

            response = client.chat.completions.create(
                model='glm-4-flash',  # 使用最快的模型
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                max_tokens=2000
            )

            content = response.choices[0].message.content

            return {
                'success': True,
                'provider': self.name,
                'results': [{
                    'title': f'AI知识库: {query}',
                    'url': '',
                    'snippet': content[:200] + '...' if len(content) > 200 else content
                }],
                'content': f"【AI知识库回答 - {query}】\n\n{content}",
                'error': '',
                'metadata': {
                    'model': 'glm-4-flash',
                    'disclaimer': '来自AI预训练知识，可能不是最新信息'
                }
            }

        except Exception as e:
            return {
                'success': False,
                'provider': self.name,
                'error': f'AI知识库查询失败: {e}',
                'results': [],
                'content': '',
                'metadata': {}
            }
