#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从今日头条提取完整文章（含图片）并发布到小红书

Extract complete article with images from Toutiao and publish to Xiaohongshu.
"""

import sys
import time
import requests
import base64
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def download_image(url, output_path, referer):
    """下载图片"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': referer
        }
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True, len(response.content)
        return False, 0
    except Exception as e:
        return False, str(e)


def image_to_base64(image_path):
    """将图片转为base64"""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        base64_data = base64.b64encode(image_data).decode('utf-8')
        return base64_data
    except Exception as e:
        print(f"  [!] 图片转base64失败: {e}")
        return None


def main():
    print("=" * 60)
    print("从今日头条提取文章（含图片）")
    print("=" * 60)

    # 连接Chrome
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=options)

    url = "https://www.toutiao.com/article/7608531811392438824/"

    print(f"\n[1/5] 访问今日头条文章")
    print(f"  URL: {url}")
    driver.get(url)
    time.sleep(8)

    # 获取页面HTML
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # 提取标题
    print(f"\n[2/5] 提取标题和内容")
    title = soup.find('h1').get_text(strip=True)
    print(f"  标题: {title}")

    # 获取文章内容
    js_get_content = """
    var article = document.querySelector('article');
    if (article) {
        return article.innerText;
    }
    // 备选方案
    var divs = document.querySelectorAll('[class*="article"]');
    for (var i = 0; i < divs.length; i++) {
        if (divs[i].innerText.length > 500) {
            return divs[i].innerText;
        }
    }
    return "";
    """

    content = driver.execute_script(js_get_content)

    # 清理内容
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line and len(line) > 1:
            cleaned_lines.append(line)

    cleaned_content = '\n\n'.join(cleaned_lines)

    # 截断到1000字
    if len(cleaned_content) > 1000:
        cleaned_content = cleaned_content[:1000]
        print(f"  ⚠️  内容已截断到1000字（原{len(content)}字）")
    else:
        print(f"  内容长度: {len(cleaned_content)} 字")

    # 获取图片URL
    print(f"\n[3/5] 获取图片URL")
    js_get_images = """
    // 找到文章容器
    var article = document.querySelector('article') || document.querySelector('[class*="article"]') || document.body;
    var imgs = article.querySelectorAll('img');
    var urls = [];

    for (var i = 0; i < imgs.length; i++) {
        var src = imgs[i].src || imgs[i].getAttribute('data-src') || imgs[i].getAttribute('data-original');

        // 排除头像、图标、小图
        if (src) {
            var width = imgs[i].width || imgs[i].naturalWidth || 0;
            var height = imgs[i].height || imgs[i].naturalHeight || 0;

            // 只保留尺寸大于200的图片
            if (width > 200 || height > 200 || (!width && !height)) {
                // 排除头像和特殊标识
                if (src.indexOf('avatar') === -1 &&
                    src.indexOf('icon') === -1 &&
                    src.indexOf('logo') === -1) {
                    urls.push(src);
                }
            }
        }
    }
    return urls;
    """

    image_urls = driver.execute_script(js_get_images)
    print(f"  找到 {len(image_urls)} 张图片")

    # 下载图片
    print(f"\n[4/5] 下载图片（前5张）")
    output_dir = Path("C:/Users/yingy/Desktop/tmp/images")
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded_paths = []
    for i, img_url in enumerate(image_urls[:5]):
        img_path = output_dir / f"image_{i}.jpg"
        success, result = download_image(img_url, img_path, url)

        if success:
            print(f"  [{i+1}/5] ✅ 已下载: {result} bytes")
            downloaded_paths.append(str(img_path))
        else:
            print(f"  [{i+1}/5] ✗ 下载失败: {result}")

    driver.quit()

    # 创建HTML文件（包含base64图片）
    print(f"\n[5/5] 创建HTML文件")

    # 将图片转为base64
    base64_images = []
    for i, img_path in enumerate(downloaded_paths):
        print(f"  转换图片{i+1}为base64...")
        base64_data = image_to_base64(img_path)
        if base64_data:
            base64_images.append({
                'index': i,
                'format': 'jpeg',
                'data': base64_data
            })

    # 生成HTML
    images_html = ""
    for img in base64_images:
        images_html += f'<img src="data:image/jpeg;base64,{img["data"]}" alt="图片{img["index"]}"/>\n'

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
    <div class="content">
        <h1>{title}</h1>
        {images_html}
        <p>{cleaned_content.replace(chr(10) + chr(10), '</p><p>')}</p>
    </div>
</body>
</html>
"""

    output_file = Path("C:/Users/yingy/Desktop/tmp/七十二候的源头.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n{'=' * 60}")
    print(f"✅ 提取完成！")
    print(f"{'=' * 60}")
    print(f"标题: {title}")
    print(f"内容: {len(cleaned_content)} 字")
    print(f"图片: {len(base64_images)} 张 (base64)")
    print(f"HTML文件: {output_file}")
    print(f"{'=' * 60}")

    return str(output_file)


if __name__ == '__main__':
    main()
