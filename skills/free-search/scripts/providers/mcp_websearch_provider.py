#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP WebSearch Provider
使用MCP websearch工具（智谱Coding Plan配额）
"""
import sys
import os

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from providers import SearchProvider


class MCPWebSearchProvider(SearchProvider):
    """MCP WebSearch Provider（使用智谱Coding Plan配额）"""

    def __init__(self):
        super().__init__("mcp_websearch")
        # MCP工具通过Skill tool调用，无需API key

    def is_available(self) -> bool:
        """
        检查MCP WebSearch是否可用

        MCP WebSearch只在Claude Code的Skill tool调用时可用，
        直接运行Python脚本时无法使用。
        """
        # 检测是否在Claude Code环境中运行
        # 方法1：检查Skill tool传入的环境变量
        if os.environ.get('SKILL_CALL') == '1':
            return True

        # 方法2：检查是否有Claude Code会话ID
        if os.environ.get('CLAUDE_CODE_SESSION_ID'):
            return True

        # 方法3：检查是否在Claude Code的Agent模式下
        if os.environ.get('CLAUDE_CODE_AGENT'):
            return True

        # CLI模式：不可用（直接跳过，避免浪费时间）
        return False

    def search(self, query: str, max_results: int = 5, **kwargs) -> dict:
        """
        使用MCP WebSearch进行搜索

        注意：此Provider需要通过Skill tool调用，
        直接使用Python代码无法调用MCP工具。

        Args:
            query: 搜索查询
            max_results: 最大结果数
            **kwargs: 其他参数

        Returns:
            搜索结果字典
        """
        # 此Provider只能通过Skill tool调用
        # 当search_engine尝试使用此provider时，返回"需要Skill调用"错误
        # 实际的MCP调用会在skill层面处理
        return {
            'success': False,
            'provider': self.name,
            'error': 'MCP_WEBSKILL_REQUIRED',
            'results': [],
            'content': '',
            'metadata': {
                'note': 'MCP WebSearch需要通过Skill tool调用',
                'use_command': f'/skill web-search "{query}"'
            }
        }

    @staticmethod
    def get_skill_command(query: str, max_results: int = 5) -> str:
        """
        获取调用MCP WebSearch的命令

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            Skill命令字符串
        """
        return f'/skill web-search "{query}" --max-results {max_results}'
