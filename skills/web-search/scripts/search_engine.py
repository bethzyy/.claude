#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索引擎 - 核心fallback逻辑

v2.6.0 - 移除GLM Web Search，进一步简化架构
"""
import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from providers import SearchProvider
from providers.zhipu_mcp_provider import ZhipuMCPProvider
from providers.tavily_provider import TavilyProvider
from providers.duckduckgo_provider import DuckDuckGoProvider
from providers.ai_knowledge_provider import AIKnowledgeProvider
from cache_manager import CacheManager
from typing import Dict, List, Optional


class WebSearchEngine:
    """
    多级fallback网络搜索引擎

    Fallback顺序（v2.6.0）：
    1. 智谱MCP（使用apikeyValue.txt）
    2. Tavily API（第三方服务，独立配额）
    3. DuckDuckGo（完全免费，无需API Key）
    4. AI知识库（最后手段，使用预训练知识）

    架构说明：
    - 简化为单配额设计，移除了配额2的自动切换逻辑
    - 当智谱MCP配额用尽时，直接fallback到Tavily
    - 移除了GLM Web Search provider以简化架构
    """

    def __init__(self, cache_days: int = 7):
        """
        初始化搜索引擎

        Args:
            cache_days: 缓存过期天数
        """
        # 初始化providers（按优先级顺序）
        self.providers = [
            ZhipuMCPProvider(),            # Priority 1: 智谱MCP（单配额）
            TavilyProvider(),               # Priority 2: 第三方服务，独立配额
            DuckDuckGoProvider(),           # Priority 3: 免费搜索
            AIKnowledgeProvider()           # Priority 4: 最后手段
        ]

        self.cache = CacheManager(cache_dir='search_cache', cache_days=cache_days)

    def search(
        self,
        query: str,
        max_results: int = 5,
        source: str = 'auto',
        timeout: int = 30,
        use_cache: bool = True
    ) -> Dict:
        """
        执行搜索（带自动fallback）

        Args:
            query: 搜索查询
            max_results: 最大结果数
            source: 指定搜索源 ('auto', 'tavily', 'duckduckgo', 'ai_knowledge')
            timeout: 超时时间（秒）
            use_cache: 是否使用缓存

        Returns:
            搜索结果字典
        """
        if not query or not query.strip():
            return {
                'success': False,
                'error': '搜索查询不能为空',
                'query': query,
                'attempts': [],
                'cached': False
            }

        # 1. 检查缓存
        if use_cache:
            cached = self.cache.get(query, max_results)
            if cached:
                print(f"[INFO] 使用缓存结果")
                cached['cached'] = True
                cached['query'] = query
                return cached

        # 2. 确定要尝试的providers
        if source == 'auto':
            providers_to_try = self.providers
        else:
            providers_to_try = [p for p in self.providers if p.name == source]
            if not providers_to_try:
                return {
                    'success': False,
                    'error': f'未找到指定的搜索源: {source}',
                    'query': query,
                    'attempts': [],
                    'cached': False
                }

        # 3. 依次尝试，直到成功
        attempts = []

        for provider in providers_to_try:
            print(f"[INFO] 尝试 {provider.name}...")

            # 检查provider是否可用
            if not provider.is_available():
                print(f"[WARNING] {provider.name} 不可用，尝试下一个...")
                attempts.append({
                    'provider': provider.name,
                    'success': False,
                    'error': 'Provider不可用'
                })
                continue

            try:
                result = provider.search(query, max_results, timeout=timeout)

                attempts.append({
                    'provider': provider.name,
                    'success': result['success'],
                    'error': result.get('error', '')
                })

                if result['success']:
                    print(f"[SUCCESS] {provider.name} 返回 {len(result['results'])} 条结果")

                    # 缓存结果
                    if use_cache:
                        self.cache.set(query, max_results, result)

                    return {
                        'success': True,
                        'query': query,
                        'provider_used': provider.name,
                        'results': result['results'],
                        'content': result['content'],
                        'metadata': result.get('metadata', {}),
                        'attempts': attempts,
                        'cached': False
                    }
                else:
                    # 检查错误类型
                    error = result.get('error', '')

                    # MCP WebSearch需要Skill调用，跳过
                    if error == 'MCP_WEBSKILL_REQUIRED':
                        print(f"[INFO] {provider.name} 需要通过Skill tool调用，尝试下一个...")
                    # 配额用尽
                    elif error == 'QUOTA_EXHAUSTED':
                        print(f"[WARNING] {provider.name} 配额已用尽，尝试下一个...")
                    else:
                        print(f"[WARNING] {provider.name} 失败: {error}")

            except Exception as e:
                print(f"[ERROR] {provider.name} 异常: {e}")
                attempts.append({
                    'provider': provider.name,
                    'success': False,
                    'error': str(e)
                })

        # 所有provider都失败
        return {
            'success': False,
            'error': '所有搜索方式都失败',
            'query': query,
            'attempts': attempts,
            'cached': False
        }

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()

    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        return self.cache.get_stats()
