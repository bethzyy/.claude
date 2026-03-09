"""
发布验证模块 - 验证发布状态

Publish validator module - Validate publishing status.
"""

import re
from typing import Dict, Optional
from selenium import webdriver

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PUBLISH_SUCCESS_KEYWORDS


class PublishValidator:
    """发布验证器"""

    def __init__(self, driver: webdriver.Chrome):
        """
        初始化验证器

        Args:
            driver: Selenium WebDriver实例
        """
        self.driver = driver

    def validate(self) -> Dict:
        """
        验证发布状态

        Returns:
            包含success, note_url, page_text的字典
        """
        current_url = self.driver.current_url

        result = {
            'success': self._check_success_by_url(current_url),
            'note_url': self._extract_note_url(current_url),
            'current_url': current_url,
            'page_text': self._get_page_text(),
            'keywords_found': self._find_success_keywords()
        }

        return result

    def _check_success_by_url(self, url: str) -> bool:
        """
        通过URL判断是否发布成功

        Args:
            url: 当前URL

        Returns:
            是否成功
        """
        # URL中包含成功关键词
        for keyword in ['success', 'published=true', 'publish/success']:
            if keyword in url:
                return True

        # URL中不再包含publish（可能跳转到详情页）
        if 'publish' not in url and 'xiaohongshu.com' in url:
            return True

        return False

    def _extract_note_url(self, url: str) -> Optional[str]:
        """
        提取笔记URL

        Args:
            url: 当前URL

        Returns:
            笔记URL，如果无法确定则返回None
        """
        # 如果URL包含笔记ID模式，提取笔记URL
        # 例如：https://www.xiaohongshu.com/explore/123456789
        if 'xiaohongshu.com' in url and 'publish' not in url:
            return url

        return None

    def _get_page_text(self, max_length: int = 500) -> str:
        """
        获取页面文本

        Args:
            max_length: 最大长度

        Returns:
            页面文本
        """
        try:
            body = self.driver.find_element('tag name', 'body')
            text = body.text
            return text[:max_length] if len(text) > max_length else text
        except:
            return ""

    def _find_success_keywords(self) -> list:
        """
        在页面中查找成功关键词

        Returns:
            找到的关键词列表
        """
        page_text = self._get_page_text(1000).lower()

        found = []
        for keyword in PUBLISH_SUCCESS_KEYWORDS:
            if keyword.lower() in page_text:
                found.append(keyword)

        return found

    def get_note_info(self) -> Dict:
        """
        获取笔记详细信息

        Returns:
            包含title, note_id等的字典
        """
        js_get_info = """
        var result = {
            title: '',
            noteId: '',
            links: []
        };

        // 查找标题
        var titleElements = document.querySelectorAll('[class*="title"], h1, h2, h3');
        for (var i = 0; i < titleElements.length; i++) {
            var text = titleElements[i].textContent.trim();
            if (text && text.length < 100 && text !== '发布笔记') {
                result.title = text;
                break;
            }
        }

        // 查找所有xiaohongshu链接
        var links = document.querySelectorAll('a[href*="xiaohongshu.com"]');
        for (var i = 0; i < links.length; i++) {
            result.links.push({
                text: links[i].textContent.trim(),
                href: links[i].href
            });
        }

        return result;
        """

        return self.driver.execute_script(js_get_info)

    def print_result(self, result: Dict):
        """
        打印验证结果

        Args:
            result: validate()返回的结果
        """
        print(f"\n{'=' * 60}")
        print(f"发布状态验证")
        print(f"{'=' * 60}")

        print(f"\n当前URL: {result['current_url']}")

        if result['success']:
            print(f"\n✅ 发布状态: 成功")

            if result['note_url']:
                print(f"笔记链接: {result['note_url']}")
        else:
            print(f"\n⚠️  发布状态: 待确认")

        if result['keywords_found']:
            print(f"找到关键词: {', '.join(result['keywords_found'])}")

        print(f"\n页面内容（前200字）:")
        print(f"{result['page_text'][:200]}")

        print(f"\n{'=' * 60}")
