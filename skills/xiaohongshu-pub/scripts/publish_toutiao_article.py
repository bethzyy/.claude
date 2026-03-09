#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整流程：从今日头条提取文章并发布到小红书

Complete workflow: Extract from Toutiao and publish to Xiaohongshu.
"""

import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def wait_for_input_elements(driver, max_wait=20):
    """等待输入元素出现"""
    for i in range(max_wait):
        js_check = """
        var results = {
            inputs: document.querySelectorAll('input[type=\"text\"]'),
            textareas: document.querySelectorAll('textarea'),
            contenteditables: document.querySelectorAll('[contenteditable=\"true\"]')
        };
        results.inputCount = results.inputs.length;
        results.textareaCount = results.textareas.length;
        results.ceCount = results.contenteditables.length;
        return results;
        """

        elements = driver.execute_script(js_check)
        total = elements['inputCount'] + elements['ceCount']

        if total > 0:
            print(f"  [等待中...] {i+1}/{max_wait}秒 - 找到 {total} 个输入元素")
            return True
        else:
            print(f"  [等待中...] {i+1}/{max_wait}秒 - 未找到输入元素")
            time.sleep(1)

    return False


def publish_to_xiaohongshu(title, content):
    """发布到小红书"""
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=options)

    print("\n" + "=" * 60)
    print("开始发布到小红书")
    print("=" * 60)

    # 打开发布页面
    print("\n[1/6] 打开发布页面...")
    driver.get("https://creator.xiaohongshu.com/publish/publish")
    time.sleep(5)

    # 点击上传图文
    print("[2/6] 点击'上传图文'...")
    js_click = """
    var all = document.querySelectorAll('div, span, button');
    for (var i = 0; i < all.length; i++) {
        if (all[i].textContent.trim() === '上传图文') {
            all[i].click();
            return true;
        }
    }
    return false;
    """

    result = driver.execute_script(js_click)
    print(f"  点击结果: {result}")

    if result:
        print("  等待页面加载...")
        time.sleep(5)

        # 等待输入元素出现
        print("[3/6] 等待输入框出现...")
        if wait_for_input_elements(driver, max_wait=15):
            time.sleep(2)

            # 填写标题
            print("[4/6] 填写标题...")
            js_fill_title = f"""
            var inputs = document.querySelectorAll('input[type=\"text\"]');
            for (var i = 0; i < inputs.length; i++) {{
                var placeholder = inputs[i].placeholder || '';
                if (placeholder.indexOf('标题') >= 0 || placeholder === '' || inputs[i].className.indexOf('title') >= 0) {{
                    inputs[i].value = '{title}';
                    inputs[i].dispatchEvent(new Event('input', {{bubbles: true}}));
                    break;
                }}
            }}
            return true;
            """

            driver.execute_script(js_fill_title)
            print(f"  ✅ 标题已填写")

            # 填写内容
            print("[5/6] 填写内容...")
            js_fill_content = """
            var ce = document.querySelectorAll('[contenteditable="true"]');
            if (ce.length > 0) {
                ce[0].click();
                ce[0].focus();
                document.execCommand('insertText', false, 'TITLE_PLACEHOLDER');
            }
            """

            # 先用占位符，然后替换
            time.sleep(1)
            js_replace_content = f"""
            var ce = document.querySelectorAll('[contenteditable="true"]');
            if (ce.length > 0) {{
                ce[0].innerHTML = '<p>{content}</p>';
            }} else {{
                var tas = document.querySelectorAll('textarea');
                if (tas.length > 0) {{
                    tas[0].value = '{content}';
                }}
            }}
            return true;
            """

            driver.execute_script(js_replace_content)
            print(f"  ✅ 内容已填写")

            # 点击发布
            print("[6/6] 点击发布...")
            js_publish = """
            var all = document.querySelectorAll('button, div, span');
            for (var i = 0; i < all.length; i++) {
                if (all[i].textContent.trim() === '发布' && all[i].offsetParent !== null) {
                    all[i].click();
                    return true;
                }
            }
            return false;
            """

            publish_result = driver.execute_script(js_publish)
            print(f"  发布点击结果: {publish_result}")

            time.sleep(5)

            # 检查结果
            current_url = driver.current_url
            print(f"\n当前URL: {current_url}")

            if 'published' in current_url or 'success' in current_url:
                print("\n✅ 发布成功！")
            else:
                print("\n⚠️  请在浏览器中手动确认发布状态")

        else:
            print("  ❌ 超时：未能找到输入元素")
            print("\n建议：请手动在浏览器中填写内容并发布")

    driver.quit()
    print("=" * 60)


# 提取文章内容
print("从已保存的HTML读取内容...")

html_file = Path("C:/Users/yingy/Desktop/tmp/七十二候的源头_完整版.html")

with open(html_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

from bs4 import BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

title = soup.find('h1').get_text(strip=True)
content_div = soup.find('div', class_='content')

if content_div:
    # 移除标签获取文本
    import re
    for tag in content_div.find_all(['h1', 'script', 'style']):
        tag.decompose()
    content_text = content_div.get_text(strip=True)
else:
    content_text = "无法提取内容"

print(f"标题: {title}")
print(f"内容: {content_text[:200]}...")

# 发布
publish_to_xiaohongshu(title, content_text)
