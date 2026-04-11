#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理器 - MD5-based缓存系统
"""
import os
import sys
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Optional


class CacheManager:
    """搜索结果缓存管理器"""

    def __init__(self, cache_dir: str = 'search_cache', cache_days: int = 7):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录路径
            cache_days: 缓存过期天数
        """
        # 获取项目根目录
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        self.cache_dir = Path(base_dir) / cache_dir
        self.cache_days = cache_days
        self._init_cache_dir()

    def _init_cache_dir(self):
        """初始化缓存目录"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, query: str, max_results: int) -> str:
        """生成缓存键"""
        key_string = f"{query}:{max_results}"
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()

    def get(self, query: str, max_results: int) -> Optional[Dict]:
        """
        从缓存获取结果

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            缓存的结果，如果不存在或已过期则返回None
        """
        cache_key = self._get_cache_key(query, max_results)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 检查是否过期
            cache_time = data.get('timestamp', 0)
            if time.time() - cache_time > self.cache_days * 86400:
                # 删除过期缓存
                cache_file.unlink()
                return None

            return data.get('result')

        except Exception as e:
            print(f"[WARNING] 读取缓存失败: {e}")
            return None

    def set(self, query: str, max_results: int, result: Dict):
        """
        保存结果到缓存

        Args:
            query: 搜索查询
            max_results: 最大结果数
            result: 搜索结果
        """
        cache_key = self._get_cache_key(query, max_results)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            data = {
                'query': query,
                'max_results': max_results,
                'result': result,
                'timestamp': time.time()
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[WARNING] 保存缓存失败: {e}")

    def clear(self):
        """清空所有缓存"""
        try:
            for cache_file in self.cache_dir.glob('*.json'):
                cache_file.unlink()
            print(f"[INFO] 已清空缓存目录: {self.cache_dir}")
        except Exception as e:
            print(f"[WARNING] 清空缓存失败: {e}")

    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        try:
            cache_files = list(self.cache_dir.glob('*.json'))
            total_size = sum(f.stat().st_size for f in cache_files)

            # 统计过期缓存数量
            expired_count = 0
            current_time = time.time()
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if current_time - data.get('timestamp', 0) > self.cache_days * 86400:
                            expired_count += 1
                except Exception:
                    pass

            return {
                'total_files': len(cache_files),
                'total_size_mb': total_size / (1024 * 1024),
                'expired_files': expired_count,
                'cache_dir': str(self.cache_dir)
            }
        except Exception as e:
            return {
                'error': str(e)
            }
