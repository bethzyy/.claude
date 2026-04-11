#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一的MCP WebSearch Provider - 自动切换配额

智能管理两个智谱Coding Plan配额：
1. 配额1：apikeyValue.txt
2. 配额2：apikeyValue2.txt

当配额1用尽时，自动切换到配额2
当配额2也用尽时，标记MCP不可用，fallback到Tavily
"""
import sys
import os
from typing import Dict, Any

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from providers import SearchProvider


class UnifiedMCPWebSearchProvider(SearchProvider):
    """
    统一的MCP WebSearch Provider

    智能管理两个API key的切换：
    - 优先使用配额1
    - 配额1用尽（错误1310）时切换到配额2
    - 配额2也用尽时标记为不可用
    """

    # 配额用尽的错误码
    QUOTA_ERROR_CODE = 1310

    def __init__(self):
        super().__init__("mcp_websearch")

        # 两个API key的文件路径
        self.api_key_files = [
            r"C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue.txt",      # 配额1
            r"C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue2.txt"      # 配额2
        ]

        # 配额状态
        self.quota_exhausted = [False, False]  # [配额1用尽, 配额2用尽]

        # 当前使用的配额索引（0或1）
        self.current_quota = 0

        # 在Skill模式下，MCP工具可用
        self.mcp_available = self._check_mcp_available()

    def _check_mcp_available(self) -> bool:
        """
        检查MCP工具是否可用

        在Claude Desktop的Skill模式下，MCP工具可用
        在CLI模式下，MCP工具不可用
        """
        if os.environ.get('SKILL_CALL') == '1':
            return True

        if os.environ.get('CLAUDE_CODE_SESSION_ID'):
            return True

        if os.environ.get('CLAUDE_CODE_AGENT'):
            return True

        return False

    def is_available(self) -> bool:
        """
        检查provider是否可用

        可用条件：
        1. MCP工具可用（Skill模式）
        2. 至少有一个配额未用尽
        """
        # CLI模式：不可用
        if not self.mcp_available:
            return False

        # Skill模式：检查是否还有可用配额
        return not (self.quota_exhausted[0] and self.quota_exhausted[1])

    def _get_api_key(self, quota_index: int) -> str:
        """
        读取指定配额的API key

        Args:
            quota_index: 配额索引（0或1）

        Returns:
            API key字符串
        """
        if quota_index < 0 or quota_index >= len(self.api_key_files):
            return ""

        api_key_file = self.api_key_files[quota_index]

        if os.path.exists(api_key_file):
            try:
                with open(api_key_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"[WARNING] 读取API key文件失败（配额{quota_index + 1}）: {e}")
                return ""

        return ""

    def _switch_quota(self) -> bool:
        """
        切换到下一个可用配额

        Returns:
            是否成功切换到可用配额
        """
        # 尝试从当前配额切换
        for i in range(len(self.api_key_files)):
            if not self.quota_exhausted[i]:
                if i != self.current_quota:
                    print(f"[INFO] 切换到配额{i + 1}")
                    self.current_quota = i
                    return True

        return False

    def _mark_quota_exhausted(self, quota_index: int):
        """
        标记某个配额已用尽

        Args:
            quota_index: 配额索引（0或1）
        """
        if 0 <= quota_index < len(self.quota_exhausted):
            if not self.quota_exhausted[quota_index]:
                self.quota_exhausted[quota_index] = True
                print(f"[WARNING] 配额{quota_index + 1}已用尽（错误码{self.QUOTA_ERROR_CODE}）")

                # 尝试切换到下一个配额
                self._switch_quota()

    def search(self, query: str, max_results: int = 5, **kwargs) -> Dict:
        """
        执行搜索（带自动配额切换）

        Args:
            query: 搜索查询
            max_results: 最大结果数
            **kwargs: 其他参数

        Returns:
            搜索结果字典
        """
        # CLI模式或MCP不可用：返回错误
        if not self.mcp_available:
            return {
                'success': False,
                'provider': self.name,
                'error': 'MCP_NOT_AVAILABLE',
                'results': [],
                'content': '',
                'metadata': {
                    'note': 'MCP WebSearch在CLI模式下不可用，请使用Tavily',
                    'use_command': f'直接使用Tavily或DuckDuckGo'
                }
            }

        # Skill模式：通过MCP工具调用
        return {
            'success': False,
            'provider': self.name,
            'error': 'MCP_WEBSKILL_REQUIRED',
            'results': [],
            'content': '',
            'metadata': {
                'note': 'MCP WebSearch需要通过Skill tool调用',
                'use_command': f'/skill web-search "{query}"',
                'current_quota': self.current_quota + 1,
                'quota_status': {
                    '配额1': '已用尽' if self.quota_exhausted[0] else '可用',
                    '配额2': '已用尽' if self.quota_exhausted[1] else '可用'
                }
            }
        }

    def report_quota_error(self, quota_index: int = None):
        """
        外部报告配额用尽

        当MCP工具返回错误1310时，可以调用此方法

        Args:
            quota_index: 配额索引（如果为None，使用当前配额）
        """
        if quota_index is None:
            quota_index = self.current_quota

        self._mark_quota_exhausted(quota_index)

    def get_status(self) -> Dict:
        """
        获取当前状态

        Returns:
            状态字典
        """
        return {
            'provider': self.name,
            'mcp_available': self.mcp_available,
            'current_quota': self.current_quota + 1,
            'quota_status': {
                '配额1': {
                    'file': self.api_key_files[0],
                    'status': '已用尽' if self.quota_exhausted[0] else '可用'
                },
                '配额2': {
                    'file': self.api_key_files[1],
                    'status': '已用尽' if self.quota_exhausted[1] else '可用'
                }
            },
            'available': self.is_available()
        }


# 创建全局实例（供search_engine使用）
_unified_provider_instance = None

def get_unified_mcp_provider() -> UnifiedMCPWebSearchProvider:
    """获取统一的MCP provider单例"""
    global _unified_provider_instance
    if _unified_provider_instance is None:
        _unified_provider_instance = UnifiedMCPWebSearchProvider()
    return _unified_provider_instance
