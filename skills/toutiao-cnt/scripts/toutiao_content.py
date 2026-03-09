#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Toutiao Content Manager - 统一入口
===============================
支持两种模式：
1. 创建新文章：根据主题生成今日头条文章
2. 整合内容：向现有文章添加新内容

Usage:
    # 创建新文章
    python toutiao_content.py create "元宵节风俗"

    # 整合内容
    python toutiao_content.py integrate article.html "新内容"

    # 从文件整合
    python toutiao_content.py integrate article.html content.md
"""

import argparse
import sys
import os
from pathlib import Path

# 添加路径以导入模块
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
sys.path.insert(0, str(script_dir.parent.parent / 'post'))

def create_article(theme, output_dir=None, style=None):
    """创建新文章"""
    print(f"\n{'='*60}")
    print(f"[创建模式] 主题: {theme}")
    print(f"{'='*60}\n")

    try:
        # 导入文章创建模块
        sys.path.insert(0, str(script_dir))
        from create_article import create_article as create_article_module

        # 设置默认风格
        if not style:
            style = "专业"

        # 调用创建函数
        return create_article_module(theme, output_dir, style)

    except Exception as e:
        print(f"[错误] 创建文章失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def integrate_content(html_file, content, **kwargs):
    """整合内容到现有文章"""
    print(f"\n{'='*60}")
    print(f"[整合模式] 源文件: {html_file}")
    print(f"{'='*60}\n")

    # 导入整合模块
    try:
        from integrate_content import ContentIntegrator

        integrator = ContentIntegrator(html_file)

        # 解析参数
        position = kwargs.get('position', 'end')
        after_title = kwargs.get('after')
        before_title = kwargs.get('before')
        merge = kwargs.get('merge', False)
        list_sections = kwargs.get('list_sections', False)
        output_suffix = kwargs.get('output_suffix', '-updated')

        # 加载HTML
        integrator.load_html()

        # 仅列出章节
        if list_sections:
            print(f"\n文章章节结构：")
            print("=" * 60)
            for i, section in enumerate(integrator.analyzer.sections, 1):
                level = section['level']
                title = section['title']
                indent = "  " * (level - 1)
                print(f"{i}. {indent}{title}")
            print("=" * 60)
            return

        # 执行整合
        updated_html = integrator.integrate(
            content,
            position=position,
            after_title=after_title,
            before_title=before_title,
            merge_sections=merge
        )

        # 保存文件
        output_path = integrator.save(updated_html, output_suffix)

        print(f"\n[完成] 输出文件: {output_path}")
        print(f"\n发布步骤：")
        print(f"  1. 在浏览器打开输出文件")
        print(f"  2. 全选复制 (Ctrl+A, Ctrl+C)")
        print(f"  3. 粘贴到今日头条编辑器")

    except Exception as e:
        print(f"[错误] 整合失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description='Toutiao Content Manager - 创建新文章或整合内容',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：

1. 创建新文章：
   python toutiao_content.py create "元宵节风俗"
   python toutiao_content.py create "RPA自动化" --style professional

2. 整合内容：
   python toutiao_content.py integrate article.html "新内容"
   python toutiao_content.py integrate article.html content.md --merge
   python toutiao_content.py integrate article.html --list-sections

3. 指定输出目录：
   python toutiao_content.py create "主题" --output-dir "/path/to/dir"
        """
    )

    subparsers = parser.add_subparsers(dest='mode', help='操作模式')

    # 创建模式
    create_parser = subparsers.add_parser('create', help='创建新文章')
    create_parser.add_argument('theme', help='文章主题')
    create_parser.add_argument('--output-dir', help='输出目录')
    create_parser.add_argument('--style', help='文风风格 (professional/casual/academic等)')

    # 整合模式
    integrate_parser = subparsers.add_parser('integrate', help='整合内容到现有文章')
    integrate_parser.add_argument('html_file', help='现有HTML文章路径')
    integrate_parser.add_argument('content', nargs='?', help='新内容（文本/文件路径/HTML）')
    integrate_parser.add_argument('--position', choices=['after', 'before', 'end'],
                                  default='end', help='插入位置')
    integrate_parser.add_argument('--after', help='在此章节之后插入')
    integrate_parser.add_argument('--before', help='在此章节之前插入')
    integrate_parser.add_argument('--merge', action='store_true',
                                  help='智能合并，跳过重复章节')
    integrate_parser.add_argument('--list-sections', action='store_true',
                                  help='列出文章现有章节')
    integrate_parser.add_argument('--output-suffix', default='-updated',
                                  help='输出文件后缀')

    args = parser.parse_args()

    if not args.mode:
        parser.print_help()
        sys.exit(1)

    if args.mode == 'create':
        create_article(args.theme, args.output_dir, args.style)
    elif args.mode == 'integrate':
        if not args.content and not args.list_sections:
            print("[错误] 整合模式需要提供内容或使用 --list-sections")
            sys.exit(1)
        integrate_content(
            args.html_file,
            args.content,
            position=args.position,
            after=args.after,
            before=args.before,
            merge=args.merge,
            list_sections=args.list_sections,
            output_suffix=args.output_suffix
        )


if __name__ == '__main__':
    main()
