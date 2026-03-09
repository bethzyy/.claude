#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Toutiao Article Creator - 简化版
===============================
根据主题生成今日头条文章

Usage:
    python create_article.py "元宵节风俗" --output-dir "./output"
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
import re

# 添加路径以导入config
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'post'))

try:
    from config import get_zhipu_anthropic_client
except ImportError:
    print("[错误] 无法导入配置，请确保 config.py 存在")
    sys.exit(1)


def search_topic_info(topic):
    """使用网络搜索获取主题相关信息"""

    print(f"  [搜索] 正在搜索关于'{topic}'的最新信息...")

    try:
        # 尝试使用 web-search skill
        import subprocess
        result = subprocess.run(
            ['python', 'C:/D/CAIE_tool/MyAIProduct/skills/web-search/main.py', topic],
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8'
        )

        if result.returncode == 0 and result.stdout:
            # 提取搜索结果（取前2000字符）
            search_info = result.stdout[:2000]
            print(f"  [完成] 获取到搜索结果 ({len(search_info)} 字符)")
            return search_info
        else:
            print(f"  [警告] 搜索未返回结果，将使用AI知识库")
            return None

    except Exception as e:
        print(f"  [警告] 搜索失败 ({e})，将使用AI知识库")
        return None


def validate_article_accuracy(topic, content, search_info):
    """验证文章内容的准确性"""
    print("  [验证] 正在验证内容准确性...")

    client = get_zhipu_anthropic_client()

    if search_info:
        validate_prompt = f"""请验证以下文章内容是否准确。

【主题】{topic}

【参考信息（来自网络搜索）】
{search_info}

【待验证的文章内容】
{content[:1000]}

【验证要求】
请检查文章中是否存在以下问题：
1. 编造的功能、特性或技术术语
2. 与参考信息不一致的关键信息
3. 虚构的案例、数据或统计信息

如果发现问题，请列出具体的问题点。如果没有问题，请回答"内容准确"。
"""
    else:
        validate_prompt = f"""请验证以下文章内容是否准确。

【主题】{topic}

【待验证的文章内容】
{content[:1000]}

【验证要求】
请检查文章中是否存在编造或不确定的信息。如果发现可能不准确的内容，请指出。
"""

    try:
        response = client.messages.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": validate_prompt}],
            max_tokens=1000
        )

        validation_result = response.content[0].text
        print(f"  [验证结果] {validation_result}")

        # 如果验证发现严重问题，返回False
        if "不准确" in validation_result or "编造" in validation_result or "虚构" in validation_result:
            print("  [警告] 验证发现内容可能不准确，建议人工审核")
            return False

        return True

    except Exception as e:
        print(f"  [警告] 验证失败: {e}")
        return True  # 验证失败时不阻止生成


def generate_article_content(topic, style="专业"):
    """使用AI生成文章内容（基于搜索结果确保准确性）"""

    client = get_zhipu_anthropic_client()

    # 先搜索获取准确信息
    search_info = search_topic_info(topic)

    # 构建增强的 prompt
    if search_info:
        context_prompt = f"""你是一位专业的技术文章作者。请基于以下搜索结果，为一篇今日头条文章撰写关于"{topic}"的内容。

【搜索结果参考（必须基于此信息）】
{search_info}

【严格写作要求】
1. 字数：1500-2000字
2. 风格：{style}、通俗易懂、有吸引力
3. 结构：
   - 引人入胜的标题
   - 简短的导语（100字内）
   - 3-5个主要章节（使用H2标题）
   - 每个章节包含具体内容、例子或数据
   - 总结性结尾

4. **绝对禁止的内容（违反将导致内容不可用）**：
   - ❌ 编造搜索结果中不存在的产品功能、模块或组件名称
   - ❌ 虚构具体的数据、统计数字、版本号
   - ❌ 想象不存在的特性或使用场景
   - ❌ 使用"例如"后面跟随编造的案例

5. **必须遵守的原则**：
   - ✅ 所有功能名称、术语必须来自搜索结果
   - ✅ 如果搜索结果信息不足，明确说明"根据现有资料..."
   - ✅ 不确定的信息使用"据公开资料显示"、"通常"等限定词
   - ✅ 语言生动但基于事实
   - ✅ 适当使用列表、引用等格式
   - ✅ 符合今日头条用户阅读习惯

6. 输出格式：Markdown

请直接输出文章内容，不要添加其他说明文字。"""
    else:
        context_prompt = f"""你是一位专业的技术文章作者。请为一篇今日头条文章撰写关于"{topic}"的内容。

【严格写作要求】
1. 字数：1500-2000字
2. 风格：{style}、通俗易懂、有吸引力
3. 结构：
   - 引人入胜的标题
   - 简短的导语（100字内）
   - 3-5个主要章节（使用H2标题）
   - 每个章节包含具体内容、例子或数据
   - 总结性结尾

4. **绝对禁止的内容**：
   - ❌ 编造不确定的产品功能、模块或组件名称
   - ❌ 虚构具体的数据、统计数字、版本号
   - ❌ 想象不存在的特性或使用场景
   - ❌ 使用"例如"后面跟随不确定的案例

5. **必须遵守的原则**：
   - ✅ 仅基于你训练数据中确定的信息
   - ✅ 不确定的信息使用"据我所知"、"通常"等限定词
   - ✅ 避免过于具体的细节描述
   - ✅ 语言生动但保守
   - ✅ 适当使用列表、引用等格式
   - ✅ 符合今日头条用户阅读习惯

6. 输出格式：Markdown

请直接输出文章内容，不要添加其他说明文字。"""

    try:
        response = client.messages.create(
            model="glm-4-flash",
            messages=[
                {"role": "user", "content": context_prompt}
            ],
            max_tokens=4096
        )

        content = response.content[0].text

        # 验证内容准确性
        validate_article_accuracy(topic, content, search_info)

        return content

    except Exception as e:
        print(f"[错误] AI生成失败: {e}")
        return None


def markdown_to_toutiao_html(markdown_content, title):
    """将Markdown转换为今日头条HTML格式"""

    html_lines = []
    lines = markdown_content.split('\n')

    # HTML模板
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Microsoft YaHei', sans-serif;
            line-height: 1.8;
            color: #333;
            background: #f8f9fa;
            margin: 0;
            padding: 20px;
        }}
        .article-container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px 50px;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }}
        h1 {{
            font-size: 28px;
            font-weight: bold;
            color: #0e639c;
            text-align: center;
            margin: 0 0 30px 0;
            padding-bottom: 20px;
            border-bottom: 3px solid #0e639c;
            line-height: 1.4;
        }}
        h2 {{
            font-size: 22px;
            color: #0e639c;
            margin: 40px 0 20px 0;
            padding-left: 15px;
            border-left: 5px solid #0e639c;
            font-weight: 600;
        }}
        h3 {{
            font-size: 18px;
            color: #0e639c;
            margin: 25px 0 12px 0;
            font-weight: 600;
        }}
        p {{
            margin-bottom: 15px;
            line-height: 1.8;
            color: #333;
        }}
        strong {{
            color: #0e639c;
            font-weight: 600;
        }}
        ul, ol {{
            margin-left: 25px;
            margin-bottom: 15px;
        }}
        li {{
            margin-bottom: 8px;
            line-height: 1.7;
        }}
        blockquote {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            font-size: 14px;
        }}
        th {{
            border: 1px solid #ddd;
            padding: 12px;
            background-color: #0e639c;
            color: white;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            border: 1px solid #ddd;
            padding: 12px;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .diagram {{
            background: #f0f7ff;
            border: 1px dashed #90caf9;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            font-family: 'Courier New', 'Consolas', monospace;
            font-size: 14px;
            line-height: 1.2;
            text-align: center;
            white-space: pre;
            overflow-x: auto;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #999;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="article-container">
        {{CONTENT}}
    </div>
</body>
</html>"""

    in_code_block = False
    in_list = False
    content_started = False

    for line in lines:
        # 跳过空行，直到内容开始
        if not line.strip() and not content_started:
            continue

        content_started = True

        # 代码块
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        # 标题
        if line.startswith('# '):
            if not html_lines:  # 第一个标题作为文章标题
                continue  # 跳过，已经在HTML模板的title中
            html_lines.append(f'<h1>{line[2:].strip()}</h1>')
        elif line.startswith('## '):
            html_lines.append(f'<h2>{line[3:].strip()}</h2>')
        elif line.startswith('### '):
            html_lines.append(f'<h3>{line[4:].strip()}</h3>')

        # 引用
        elif line.strip().startswith('>'):
            html_lines.append(f'<blockquote>{line.strip()[1:].strip()}</blockquote>')

        # 列表
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{line.strip()[2:]}</li>')

        # 有序列表
        elif re.match(r'^\d+\.\s', line.strip()):
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if not html_lines[-1].startswith('<ol>'):
                html_lines.append('<ol>')
            text = line.strip().split('.', 1)[1].strip()
            html_lines.append(f'<li>{text}</li>')

        # 普通段落
        elif line.strip():
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append(f'<p>{line.strip()}</p>')

    # 闭合标签
    if in_list:
        html_lines.append('</ul>')

    # 组装HTML
    content_html = '\n'.join(html_lines)
    full_html = html_template.replace('{CONTENT}', content_html)

    return full_html


def create_article(topic, output_dir=None, style="专业"):
    """创建文章"""

    print(f"\n{'='*60}")
    print(f"[创建文章] 主题: {topic}")
    print(f"{'='*60}\n")

    # 生成内容
    print("[1/3] 正在生成文章内容...")
    markdown_content = generate_article_content(topic, style)

    if not markdown_content:
        print("[错误] 内容生成失败")
        return None

    print(f"[完成] 生成了 {len(markdown_content)} 字符的内容")

    # 提取标题
    title = topic
    for line in markdown_content.split('\n'):
        if line.startswith('# '):
            title = line[2:].strip()
            break

    print(f"[2/3] 正在转换为HTML格式...")
    html_content = markdown_to_toutiao_html(markdown_content, title)
    print("[完成] HTML转换完成")

    # 保存文件
    print(f"[3/3] 正在保存文件...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path.cwd()

    filename = f"Article_{title}_{timestamp}.html"
    file_path = output_path / filename

    # 清理文件名中的非法字符
    filename = filename.replace(':', '').replace('/', '').replace('\\', '').replace('?', '').replace('*', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')
    file_path = output_path / filename

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"[完成] 文件已保存: {file_path}")

    print(f"\n{'='*60}")
    print(f"[发布步骤]")
    print(f"{'='*60}")
    print(f"1. 在浏览器打开: {file_path}")
    print(f"2. 全选复制 (Ctrl+A, Ctrl+C)")
    print(f"3. 粘贴到今日头条编辑器")
    print(f"4. 调整格式并发布\n")

    return file_path


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='创建今日头条文章',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('topic', help='文章主题')
    parser.add_argument('--output-dir', help='输出目录')
    parser.add_argument('--style', default='专业', help='写作风格')

    args = parser.parse_args()

    create_article(args.topic, args.output_dir, args.style)


if __name__ == '__main__':
    main()
