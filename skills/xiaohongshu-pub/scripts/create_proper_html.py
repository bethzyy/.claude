#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建格式正确的HTML文件用于小红书发布

Create properly formatted HTML for Xiaohongshu publishing.
"""

import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def main():
    print("=" * 60)
    print("提取并创建格式正确的HTML")
    print("=" * 60)

    # 连接Chrome
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=options)

    url = "https://www.toutiao.com/article/7608531811392438824/"
    print(f"\n[1/4] 访问今日头条文章")
    driver.get(url)

    import time
    time.sleep(8)

    # 获取内容
    print(f"[2/4] 提取文章内容")

    js_get_all = """
    function getAllContent() {
        // 标题
        var titleElem = document.querySelector('h1');
        var title = titleElem ? titleElem.innerText : document.title.split('-')[0];

        // 正文
        var article = document.querySelector('article');
        var content = '';

        if (article) {
            // 移除不需要的元素
            var clone = article.cloneNode(true);
            var scripts = clone.querySelectorAll('script, style, [class*=\"ad\"], [class*=\"comment\"], [class*=\"recommend\"]');
            for (var i = 0; i < scripts.length; i++) {
                scripts[i].parentNode.removeChild(scripts[i]);
            }

            // 获取文本，保留段落结构
            var paragraphs = [];
            var paras = clone.querySelectorAll('p');
            for (var i = 0; i < paras.length; i++) {
                var text = paras[i].innerText.trim();
                if (text && text.length > 10) {
                    paragraphs.push(text);
                }
            }

            content = paragraphs.join('\\n\\n');
        }

        return {title: title, content: content};
    }

    return getAllContent();
    """

    result = driver.execute_script(js_get_all)
    title = result['title']
    content = result['content']

    print(f"  标题: {title}")
    print(f"  内容: {len(content)} 字")

    # 截断到1000字
    if len(content) > 1000:
        content = content[:1000]
        print(f"  [WARNING] 内容已截断到1000字")

    driver.quit()

    # 创建HTML文件（使用成功案例的格式）
    print(f"\n[3/4] 创建HTML文件")

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', 'PingFang SC', Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            background: #fff;
            padding: 20px;
            max-width: 750px;
            margin: 0 auto;
        }}

        .content {{
            margin: 20px 0;
        }}

        h1 {{
            font-size: 24px;
            font-weight: bold;
            line-height: 1.4;
            margin-bottom: 15px;
            color: #000;
        }}

        p {{
            margin-bottom: 15px;
            text-align: justify;
            line-height: 1.8;
        }}
    </style>
</head>
<body>
    <div class="content">
        <h1>{title}</h1>
        {chr(10).join([f'<p>{p}</p>' for p in content.split(chr(10) + chr(10))])}
    </div>
</body>
</html>
"""

    output_file = Path("C:/Users/yingy/Desktop/tmp/七十二候的源头_标准版.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"  [OK] 已保存: {output_file}")

    # 验证HTML格式
    print(f"\n[4/4] 验证HTML格式")
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        print(f"  总行数: {len(lines)}")
        doctype_ok = '[OK]' if '<!DOCTYPE html>' in content else '[X]'
        html_ok = '[OK]' if '<html' in content else '[X]'
        body_ok = '[OK]' if '<body>' in content else '[X]'
        div_ok = '[OK]' if '<div class="content">' in content else '[X]'
        print(f"  DOCTYPE声明: {doctype_ok}")
        print(f"  html标签: {html_ok}")
        print(f"  body标签: {body_ok}")
        print(f"  div.content: {div_ok}")

    print("\n" + "=" * 60)
    print(f"[OK] HTML文件已创建")
    print(f"文件: {output_file}")
    print(f"标题: {title}")
    print(f"内容: {len(content)} 字")
    print(f"=" * 60)

    return str(output_file)


if __name__ == '__main__':
    main()
