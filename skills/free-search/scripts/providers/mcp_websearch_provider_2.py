#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP WebSearch Provider 2
使用第二个智谱Coding Plan配额（apikeyValue2.txt）
"""
import sys
import os

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from providers import SearchProvider


class MCPWebSearchProvider2(SearchProvider):
    """MCP WebSearch Provider 2（使用第二个智谱Coding Plan配额）"""

    def __init__(self):
        super().__init__("mcp_websearch_2")
        # MCP工具通过Skill tool调用，无需API key

    def is_available(self) -> bool:
        """
        检查第二个MCP WebSearch是否可用

        检查逻辑与第一个provider相同，
        但使用第二个API key的配额。
        """
        # 检测是否在Claude Code环境中运行
        if os.environ.get('SKILL_CALL') == '1':
            return True

        if os.environ.get('CLAUDE_CODE_SESSION_ID'):
            return True

        if os.environ.get('CLAUDE_CODE_AGENT'):
            return True

        # CLI模式：不可用
        return False

    def search(self, query: str, max_results: int = 5, **kwargs) -> dict:
        """
        使用第二个MCP WebSearch配额进行搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数
            **kwargs: 其他参数

        Returns:
            搜索结果字典
        """
        # 此Provider也需要通过Skill tool调用
        # 但使用第二个API key的配额
        return {
            'success': False,
            'provider': self.name,
            'error': 'MCP_WEBSKILL_REQUIRED',
            'results': [],
            'content': '',
            'metadata': {
                'note': 'MCP WebSearch 2 需要通过Skill tool调用，使用第二个API key配额',
                'use_command': f'/skill web-search "{query}"',
                'api_key_source': 'apikeyValue2.txt'
            }
        }

    @staticmethod
    def get_skill_command(query: str, max_results: int = 5) -> str:
        """
        获取调用第二个MCP WebSearch的命令

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            Skill命令字符串
        """
        return f'/skill web-search "{query}" --max-results {max_results} --source mcp_websearch_2'
