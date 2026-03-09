#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Toutiao Article Content Integrator
===============================
智能整合内容到现有今日头条文章

功能：
1. 分析现有HTML文章结构
2. 接收新内容（Markdown/文本/HTML）
3. 智能整合（避免重复章节）
4. 在合适位置插入新内容
5. 生成更新后的HTML文件

Usage:
    python integrate_content.py <html_file> <new_content> [options]
    python integrate_content.py article.html "新内容" --position after "工具对比"
    python integrate_content.py article.html content.md --merge
"""

import argparse
import re
import os
import sys
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup, NavigableString, Tag
import html

# ASCII符号避免Windows GBK编码问题
OK = "[OK]"
ERROR = "[ERROR]"
WARNING = "[WARNING]"
INFO = "[INFO]"


class HTMLAnalyzer:
    """HTML文章结构分析器"""

    def __init__(self, html_content):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.sections = self._extract_sections()

    def _extract_sections(self):
        """提取文章的章节结构"""
        sections = []

        # 查找所有标题（h1, h2, h3, h4）
        for heading in self.soup.find_all(['h1', 'h2', 'h3', 'h4']):
            level = int(heading.name[1])  # h1->1, h2->2, etc.
            title = heading.get_text().strip()

            # 收集该标题下的内容
            content_elements = []
            next_elem = heading.find_next_sibling()

            while next_elem:
                if next_elem.name in ['h1', 'h2', 'h3', 'h4']:
                    # 遇到同级或更高级标题，停止
                    if int(next_elem.name[1]) <= level:
                        break
                content_elements.append(next_elem)
                next_elem = next_elem.find_next_sibling()

            sections.append({
                'level': level,
                'title': title,
                'element': heading,
                'content': content_elements
            })

        return sections

    def find_section_by_title(self, title_pattern):
        """根据标题模式查找章节"""
        for section in self.sections:
            if re.search(title_pattern, section['title'], re.IGNORECASE):
                return section
        return None

    def find_insert_position(self, after_title=None, before_title=None):
        """查找插入位置"""
        if after_title:
            section = self.find_section_by_title(after_title)
            if section:
                # 在该章节的最后一个内容元素之后插入
                if section['content']:
                    return section['content'][-1].find_next_sibling()
                else:
                    return section['element'].find_next_sibling()

        if before_title:
            section = self.find_section_by_title(before_title)
            if section:
                return section['element']

        # 默认：在文章结尾插入
        return None

    def section_exists(self, title_pattern):
        """检查章节是否已存在"""
        return self.find_section_by_title(title_pattern) is not None

    def get_section_titles(self):
        """获取所有章节标题"""
        return [s['title'] for s in self.sections]


class ContentIntegrator:
    """内容整合器"""

    def __init__(self, html_file_path):
        self.html_file = Path(html_file_path)
        self.analyzer = None

    def load_html(self):
        """加载HTML文件"""
        with open(self.html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.analyzer = HTMLAnalyzer(content)
        return content

    def ensure_diagram_style(self, html_content):
        """
        确保HTML中包含优化的.diagram样式

        如果<style>标签中不存在.diagram样式，则添加优化的样式
        这样可以自动修复ASCII架构图的格式问题
        """
        diagram_css = """
        .diagram {
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
        }"""

        # 使用BeautifulSoup解析HTML
        soup = self.analyzer.soup if self.analyzer else BeautifulSoup(html_content, 'html.parser')

        # 查找<style>标签
        style_tag = soup.find('style')

        if style_tag and '.diagram' not in style_tag.get_text():
            # 添加.diagram样式到现有的<style>标签
            style_tag.string = style_tag.get_text() + diagram_css
            return str(soup)
        elif not style_tag:
            # 如果没有<style>标签，在<head>中创建一个
            head = soup.find('head')
            if head:
                new_style = soup.new_tag('style')
                new_style.string = diagram_css
                head.append(new_style)
            return str(soup)

        # 已经有.diagram样式，直接返回
        return html_content

    def markdown_to_html(self, markdown_text):
        """将Markdown转换为HTML（简化版）"""
        html_lines = []
        lines = markdown_text.split('\n')

        in_code_block = False
        in_list = False

        for line in lines:
            # 代码块
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                if in_code_block:
                    html_lines.append('<div class="code-block">')
                else:
                    html_lines.append('</div>')
                continue

            if in_code_block:
                html_lines.append(html.escape(line))
                continue

            # 标题
            if line.startswith('### '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h3>{line[4:].strip()}</h3>')
            elif line.startswith('## '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h2>{line[3:].strip()}</h2>')
            elif line.startswith('# '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h1>{line[2:].strip()}</h1>')

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
                list_text = re.sub(r'^\d+\.\s', '', line.strip())
                html_lines.append(f'<li>{list_text}</li>')

            # 表格
            elif '|' in line and line.strip():
                cells = [cell.strip() for cell in line.split('|')]
                cells = [c for c in cells if c]  # 移除空单元格

                if cells:
                    if not html_lines or not html_lines[-1].startswith('<table'):
                        html_lines.append('<table>')

                    if html_lines[-1] == '<table>':
                        html_lines.append('<thead><tr>')
                        for cell in cells:
                            html_lines.append(f'<th>{cell}</th>')
                        html_lines.append('</tr></thead><tbody>')
                    elif not set(line.strip()) == {'-', '|'}:  # 跳过分隔行
                        html_lines.append('<tr>')
                        for cell in cells:
                            html_lines.append(f'<td>{cell}</td>')
                        html_lines.append('</tr>')

            # 普通段落
            elif line.strip():
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                if html_lines and html_lines[-1] == '</tbody>':
                    html_lines.append('</table>')
                html_lines.append(f'<p>{line.strip()}</p>')

        # 闭合标签
        if in_list:
            html_lines.append('</ul>')
        if html_lines and html_lines[-1] == '</tbody>':
            html_lines.append('</table>')

        return '\n'.join(html_lines)

    def parse_new_content(self, content):
        """解析新内容"""
        # 如果是文件路径
        if os.path.exists(content):
            with open(content, 'r', encoding='utf-8') as f:
                content = f.read()

        # 检测内容类型
        if content.strip().startswith('<!DOCTYPE') or content.strip().startswith('<html'):
            # HTML格式
            return content
        else:
            # Markdown格式
            return self.markdown_to_html(content)

    def integrate(self, new_content, position='end', after_title=None,
                  before_title=None, merge_sections=False):
        """整合新内容到文章中"""
        # 加载现有文章
        original_html = self.load_html()
        soup = self.analyzer.soup

        # 解析新内容
        new_html = self.parse_new_content(new_content)
        new_soup = BeautifulSoup(new_html, 'html.parser')

        # 检查重复章节
        if merge_sections:
            new_headings = new_soup.find_all(['h2', 'h3', 'h4'])
            for heading in new_headings:
                title = heading.get_text().strip()
                if self.analyzer.section_exists(title):
                    print(f"{WARNING} 章节已存在: {title}，跳过")
                    heading.decompose()

        # 查找插入位置
        insert_point = None

        if position == 'after' and after_title:
            insert_point = self.analyzer.find_insert_position(after_title=after_title)
        elif position == 'before' and before_title:
            insert_point = self.analyzer.find_insert_position(before_title=before_title)
        elif position == 'end':
            insert_point = None  # 插入到末尾

        # 插入新内容
        if insert_point:
            insert_point.insert_before(new_soup)
            print(f"{INFO} 内容已插入到指定位置")
        else:
            # 插入到结尾
            container = soup.find('div', class_='article-container')
            if container:
                container.append(new_soup)
                print(f"{INFO} 内容已添加到文章末尾")
            else:
                soup.body.append(new_soup)
                print(f"{INFO} 内容已添加到body末尾")

        # 确保包含优化的.diagram样式
        result_html = str(soup)
        result_html = self.ensure_diagram_style(result_html)

        return result_html

    def save(self, html_content, suffix='-updated'):
        """保存更新后的HTML"""
        output_file = self.html_file.stem + suffix + self.html_file.suffix
        output_path = self.html_file.parent / output_file

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path


def print_usage_examples():
    """打印使用示例"""
    examples = """
使用示例：

1. 添加内容到文章末尾：
   python integrate_content.py article.html "新章节内容"

2. 在指定章节后插入：
   python integrate_content.py article.html content.md --position after --after "工具对比"

3. 在指定章节前插入：
   python integrate_content.py article.html content.html --position before --before "总结"

4. 智能合并（自动跳过重复章节）：
   python integrate_content.py article.html content.md --merge

5. 从Markdown文件添加：
   python integrate_content.py article.html new_content.md

6. 查看文章现有章节：
   python integrate_content.py article.html --list-sections
"""
    print(examples)


def main():
    parser = argparse.ArgumentParser(
        description='智能整合内容到今日头条文章',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=print_usage_examples()
    )

    parser.add_argument('html_file', help='现有HTML文章路径')
    parser.add_argument('content', nargs='?', help='新内容（文本/Markdown文件路径/HTML字符串）')

    parser.add_argument('--position', choices=['after', 'before', 'end'],
                        default='end', help='插入位置（默认：end）')
    parser.add_argument('--after', help='在此章节之后插入')
    parser.add_argument('--before', help='在此章节之前插入')
    parser.add_argument('--merge', action='store_true',
                        help='智能合并，跳过重复章节')
    parser.add_argument('--list-sections', action='store_true',
                        help='列出文章现有章节')
    parser.add_argument('--output-suffix', default='-updated',
                        help='输出文件后缀（默认：-updated）')

    args = parser.parse_args()

    # 检查文件存在
    if not os.path.exists(args.html_file):
        print(f"{ERROR} 文件不存在: {args.html_file}")
        sys.exit(1)

    # 创建整合器
    integrator = ContentIntegrator(args.html_file)
    integrator.load_html()

    # 仅列出章节
    if args.list_sections:
        print(f"\n文章章节结构：")
        print("=" * 60)
        for i, section in enumerate(integrator.analyzer.sections, 1):
            indent = "  " * (section['level'] - 1)
            print(f"{i}. {indent}{section['title']}")
        print("=" * 60)
        return

    # 需要提供新内容
    if not args.content:
        print(f"{ERROR} 请提供要添加的内容")
        print("使用 --help 查看帮助")
        sys.exit(1)

    # 执行整合
    print(f"\n{INFO} 开始整合内容...")
    print(f"{INFO} 源文件: {args.html_file}")

    try:
        updated_html = integrator.integrate(
            args.content,
            position=args.position,
            after_title=args.after,
            before_title=args.before,
            merge_sections=args.merge
        )

        # 保存文件
        output_path = integrator.save(updated_html, args.output_suffix)

        print(f"{OK} 完成！")
        print(f"  输出文件: {output_path}")
        print(f"\n发布步骤：")
        print(f"  1. 在浏览器打开输出文件")
        print(f"  2. 全选复制 (Ctrl+A, Ctrl+C)")
        print(f"  3. 粘贴到今日头条编辑器")

    except Exception as e:
        print(f"{ERROR} 处理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
