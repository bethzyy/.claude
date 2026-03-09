"""
合集分类器 - 使用AI判断文章应该加入哪个合集

Collection classifier - Use AI to determine which collection to add.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from zhipuai import ZhipuAI
    ZHIPUAI_AVAILABLE = True
except ImportError:
    ZHIPUAI_AVAILABLE = False


class CollectionClassifier:
    """合集分类器"""

    # 合集定义
    COLLECTIONS = {
        "美就是意义": {
            "description": "非遗、景色、色彩、美学相关内容",
            "keywords": ["非遗", "景色", "色彩", "美学", "传统色", "二十四节气",
                        "故宫", "艺术", "绘画", "摄影", "视觉", "设计", "文化"]
        },
        "饮食养生": {
            "description": "吃喝、养生、食材相关内容",
            "keywords": ["饮食", "养生", "美食", "吃", "喝", "食材", "烹饪",
                        "菜谱", "食谱", "营养", "健康", "食疗", "药膳", "节气饮食"]
        },
        "地方风物志": {
            "description": "包含地域信息的内容",
            "note": "需要检测标题中的地名"
        }
    }

    def __init__(self):
        """初始化分类器"""
        self.client = None
        if ZHIPUAI_AVAILABLE:
            api_key = os.environ.get('ZHIPU_API_KEY')
            if api_key:
                self.client = ZhipuAI(api_key=api_key)

    def classify(self, title: str, content: str) -> Optional[str]:
        """
        使用AI判断文章应该加入哪个合集

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            合集名称，如果无法判断则返回None
        """
        # 如果AI不可用，使用关键词匹配
        if not self.client:
            return self._keyword_match(title, content)

        # 使用AI判断
        return self._ai_classify(title, content)

    def _keyword_match(self, title: str, content: str) -> Optional[str]:
        """
        基于关键词的简单匹配（AI不可用时使用）

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            合集名称
        """
        title_lower = title.lower()
        content_lower = content.lower()
        combined = title_lower + " " + content_lower

        # 检查"美就是意义"
        beauty_keywords = self.COLLECTIONS["美就是意义"]["keywords"]
        if any(kw in combined for kw in beauty_keywords):
            return "美就是意义"

        # 检查"饮食养生"
        food_keywords = self.COLLECTIONS["饮食养生"]["keywords"]
        if any(kw in combined for kw in food_keywords):
            return "饮食养生"

        # 检查"地方风物志"（通过常见地名检测）
        regions = ["北京", "上海", "广州", "深圳", "成都", "杭州", "西安", "苏州",
                  "西藏", "新疆", "云南", "四川", "江南", "中原", "东北", "西北"]
        if any(region in title for region in regions):
            return "地方风物志"

        return None

    def _ai_classify(self, title: str, content: str) -> Optional[str]:
        """
        使用AI判断合集

        Args:
            title: 文章标题
            content: 文章内容（前500字）

        Returns:
            合集名称
        """
        if not self.client:
            return self._keyword_match(title, content)

        # 构建提示词
        prompt = f"""请判断以下文章应该加入哪个小红书合集：

标题：{title}

内容摘要：{content[:500]}

可选合集：
1. 美就是意义 - 适用于非遗、景色、色彩、美学相关内容
2. 饮食养生 - 适用于吃喝、养生、食材相关内容
3. 地方风物志 - 适用于包含地域信息的内容

请只回答合集名称（美就是意义/饮食养生/地方风物志），如果都不适合请回答"无"。

回答："""

        try:
            response = self.client.chat.completions.create(
                model="glm-4-flash",  # 使用快速模型
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 低温度，更确定性
                max_tokens=50
            )

            result = response.choices[0].message.content.strip()

            # 提取合集名称
            if "美就是意义" in result:
                return "美就是意义"
            elif "饮食养生" in result:
                return "饮食养生"
            elif "地方风物志" in result:
                return "地方风物志"
            else:
                # AI判断为无，尝试关键词匹配作为备选
                return self._keyword_match(title, content)

        except Exception as e:
            print(f"  [!] AI判断失败: {e}")
            # 降级到关键词匹配
            return self._keyword_match(title, content)

    def get_collection_suggestion(self, title: str, content: str) -> dict:
        """
        获取合集建议（包含详细信息）

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            包含collection, confidence, reason的字典
        """
        collection = self.classify(title, content)

        if not collection:
            return {
                'collection': None,
                'confidence': 0,
                'reason': '无法判断合适的合集'
            }

        # 生成理由
        reason = f"根据标题和内容判断，应加入「{collection}」合集"

        if collection == "美就是意义":
            reason = "内容涉及美学、色彩或传统文化"
        elif collection == "饮食养生":
            reason = "内容涉及美食、养生或饮食文化"
        elif collection == "地方风物志":
            reason = "标题包含地域信息"

        return {
            'collection': collection,
            'confidence': 0.8,  # AI判断的置信度
            'reason': reason
        }
