#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智谱MCP WebSearch Provider - 真实API调用

这个provider直接调用智谱API，不依赖MCP工具
使用单个配额（apikeyValue2.txt）
"""
import sys
import os
from typing import Dict, Any, List

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None
    print("[WARNING] 未安装zhipuai库，请运行: pip install zhipuai")


class ZhipuMCPProvider:
    """
    智谱MCP WebSearch Provider

    直接调用智谱API，使用单个配额
    """

    # 配额用尽的错误码
    QUOTA_ERROR_CODE = 1310

    def __init__(self):
        self.name = "zhipu_mcp"

        # API key文件路径
        self.api_key_file = r"C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue2.txt"

        # 配额状态
        self.quota_exhausted = False

        # 环境变量
        self.env_key = "ZHIPU_API_KEY"

    def is_available(self) -> bool:
        """
        检查provider是否可用

        可用条件：
        1. zhipuai库已安装
        2. 有API key且配额未用尽
        """
        if ZhipuAI is None:
            return False

        return self._get_api_key() != ""

    def _get_api_key(self) -> str:
        """
        获取API key

        Returns:
            API key字符串
        """
        # 优先从环境变量读取
        key = os.environ.get(self.env_key, "")
        if key:
            return key

        # 从文件读取
        if os.path.exists(self.api_key_file):
            try:
                with open(self.api_key_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception:
                pass

        return ""

    def _mark_quota_exhausted(self, error_code: int = None):
        """
        标记配额已用尽

        Args:
            error_code: 错误码（如果是1310，确认是配额用尽）
        """
        if error_code and error_code != self.QUOTA_ERROR_CODE:
            # 不是配额用尽错误，不标记
            return

        if not self.quota_exhausted:
            self.quota_exhausted = True
            print(f"[WARNING] 配额已用尽（错误码{error_code or 'UNKNOWN'}）")

    def search(self, query: str, max_results: int = 5, timeout: int = 30, **kwargs) -> Dict:
        """
        执行搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数
            timeout: 超时时间
            **kwargs: 其他参数

        Returns:
            搜索结果字典
        """
        if not self.is_available():
            return {
                'success': False,
                'provider': self.name,
                'error': 'Provider不可用（缺少zhipuai库或API key）',
                'results': [],
                'content': ''
            }

        # 如果配额已用尽，直接返回失败
        if self.quota_exhausted:
            return {
                'success': False,
                'provider': self.name,
                'error': 'QUOTA_EXHAUSTED',
                'results': [],
                'content': ''
            }

        # 获取API key
        api_key = self._get_api_key()
        if not api_key:
            return {
                'success': False,
                'provider': self.name,
                'error': 'API key不存在',
                'results': [],
                'content': ''
            }

        # 调用API
        try:
            print(f"[DEBUG] 调用API: {api_key[:15]}...")

            result = self._call_zhipu_api(
                api_key=api_key,
                query=query,
                max_results=max_results,
                timeout=timeout
            )

            if result['success']:
                # 成功！
                result['provider'] = self.name
                result['metadata'] = result.get('metadata', {})
                print(f"[SUCCESS] {self.name} 返回结果")
                return result
            else:
                # 失败，检查是否是配额用尽
                error_code = result.get('error_code')

                if error_code == self.QUOTA_ERROR_CODE:
                    # 配额用尽
                    self._mark_quota_exhausted(error_code)
                    return {
                        'success': False,
                        'provider': self.name,
                        'error': 'QUOTA_EXHAUSTED',
                        'results': [],
                        'content': ''
                    }
                else:
                    # 其他错误，直接返回
                    return result

        except Exception as e:
            # 异常处理
            error_str = str(e)
            if str(self.QUOTA_ERROR_CODE) in error_str:
                # 配额用尽
                self._mark_quota_exhausted(self.QUOTA_ERROR_CODE)
                return {
                    'success': False,
                    'provider': self.name,
                    'error': 'QUOTA_EXHAUSTED',
                    'results': [],
                    'content': ''
                }
            else:
                # 其他异常
                return {
                    'success': False,
                    'provider': self.name,
                    'error': error_str,
                    'results': [],
                    'content': ''
                }

    def _call_zhipu_api(self, api_key: str, query: str, max_results: int = 5, timeout: int = 30) -> Dict:
        """
        调用智谱API

        Args:
            api_key: API key
            query: 搜索查询
            max_results: 最大结果数
            timeout: 超时时间

        Returns:
            API调用结果
        """
        try:
            client = ZhipuAI(api_key=api_key)

            # 调用带web_search的API
            response = client.chat.completions.create(
                model="glm-4-flash",
                tools=[
                    {
                        "type": "web_search",
                        "web_search": {
                            "search_query": query,
                            "top_k": max_results
                        }
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": f"请搜索：{query}，并返回搜索结果摘要。"
                    }
                ],
                timeout=timeout,
                stream=False
            )

            # 检查响应
            if response.choices:
                content = response.choices[0].message.content

                # 检测是否真正使用了web_search
                # 通过检测内容中的关键词判断
                failed_keywords = [
                    '无法进行网络搜索',
                    '无法直接搜索',
                    '我无法直接',
                    '作为一个AI，我无法',
                    '知识更新时间',
                    '截至我知识',
                    '预训练知识'
                ]

                is_knowledge_only = any(keyword in content for keyword in failed_keywords)

                if is_knowledge_only:
                    # 返回的是预训练知识，web_search不可用
                    print(f"[DEBUG] 返回预训练知识（包含关键词: {[k for k in failed_keywords if k in content]}）")
                    return {
                        'success': False,
                        'error': 'web_search配额用尽（返回预训练知识）',
                        'error_code': self.QUOTA_ERROR_CODE
                    }

                # 返回的是实时搜索结果
                return {
                    'success': True,
                    'results': [
                        {
                            'title': f"搜索结果{i+1}",
                            'url': '',
                            'snippet': content
                        }
                        for i in range(min(3, max_results))
                    ],
                    'content': content,
                    'metadata': {
                        'model': 'glm-4-flash',
                        'usage': {
                            'prompt_tokens': response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                            'completion_tokens': response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                            'total_tokens': response.usage.total_tokens if hasattr(response, 'usage') else 0
                        }
                    }
                }
            else:
                return {
                    'success': False,
                    'error': '未返回搜索结果'
                }

        except Exception as e:
            error_str = str(e)

            # 检查是否是配额用尽错误
            if str(self.QUOTA_ERROR_CODE) in error_str:
                return {
                    'success': False,
                    'error': '配额用尽',
                    'error_code': self.QUOTA_ERROR_CODE
                }
            else:
                return {
                    'success': False,
                    'error': error_str
                }

    def get_status(self) -> Dict:
        """
        获取当前状态

        Returns:
            状态字典
        """
        return {
            'provider': self.name,
            'quota_status': {
                'file': self.api_key_file,
                'status': '已用尽' if self.quota_exhausted else '可用',
                'has_key': bool(self._get_api_key())
            },
            'available': self.is_available()
        }
