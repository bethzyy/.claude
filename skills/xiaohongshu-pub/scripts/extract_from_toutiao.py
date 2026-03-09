#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从今日头条URL提取文章并发布到小红书

Extract article from Toutiao URL and publish to Xiaohongshu.
"""

import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def extract_toutiao_article(url: str) -> dict:
    """
    从今日头条URL提取文章内容

    Args:
        url: 今日头条文章URL

    Returns:
        包含title, content的字典
    """
    # 连接到Chrome
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=options)

    print(f"[1/3] 访问今日头条文章...")
    print(f"  URL: {url}")
    driver.get(url)
    time.sleep(5)

    # 获取页面HTML
    page_html = driver.page_source
    soup = BeautifulSoup(page_html, 'html.parser')

    # 提取标题
    title = None
    title_selectors = [
        'h1.article-title',
        'h1.title',
        '.article-title',
        '[class*="title"]'
    ]

    for selector in title_selectors:
        title_elem = soup.select_one(selector)
        if title_elem:
            title = title_elem.get_text(strip=True)
            break

    if not title:
        title = driver.title.split('_')[0].split('-')[0].strip()

    print(f"  标题: {title}")

    # 提取正文内容
    print(f"[2/3] 提取文章内容...")

    content_selectors = [
        'article',
        '.article-content',
        '[class*="article-content"]',
        '[class*="content"]'
    ]

    content_text = ""
    for selector in content_selectors:
        content_elem = soup.select_one(selector)
        if content_elem:
            # 移除script和style标签
            for tag in content_elem.find_all(['script', 'style', 'noscript']):
                tag.decompose()
            content_text = content_elem.get_text(separator='\n', strip=True)
            if len(content_text) > 100:
                break

    # 如果还是找不到，使用JavaScript获取
    if not content_text or len(content_text) < 100:
        js_get_content = """
        var article = document.querySelector('article') || document.body;
        var clone = article.cloneNode(true);
        var scripts = clone.querySelectorAll('script, style, noscript');
        for (var i = 0; i < scripts.length; i++) {
            scripts[i].parentNode.removeChild(scripts[i]);
        }
        return clone.innerText || clone.textContent;
        """
        content_text = driver.execute_script(js_get_content)

    # 清理内容
    lines = content_text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line and len(line) > 1:
            cleaned_lines.append(line)

    cleaned_content = '\n\n'.join(cleaned_lines)

    # 截断到1000字（小红书限制）
    if len(cleaned_content) > 1000:
        cleaned_content = cleaned_content[:1000]
        print(f"  ⚠️  内容已截断到1000字（原{len(content_text)}字）")

    print(f"  内容长度: {len(cleaned_content)} 字")

    # 保存为HTML文件
    print(f"[3/3] 保存HTML文件...")

    paragraphs = cleaned_content.split('\n\n')
    paragraph_html = '\n'.join([f'<p>{p}</p>' for p in paragraphs])

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
    <div class="content">
        <h1>{title}</h1>
        {paragraph_html}
    </div>
</body>
</html>
"""

    output_file = Path("C:/Users/yingy/Desktop/tmp/toutiao_extracted.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"  ✅ 已保存到: {output_file}")

    driver.quit()

    return {
        'title': title,
        'content': cleaned_content,
        'html_file': str(output_file)
    }


if __name__ == '__main__':
    url = 'https://www.toutiao.com/article/7608531811392438824/'

    result = extract_toutiao_article(url)

    print(f"\n{'='*60}")
    print(f"提取完成！")
    print(f"标题: {result['title']}")
    print(f"内容: {result['content'][:200]}...")
    print(f"HTML文件: {result['html_file']}")
    print(f"{'='*60}")
