#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web搜索CLI工具 - 多级fallback网络搜索
"""
import sys
import os
import argparse
import json
import time

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from search_engine import WebSearchEngine


def format_text_output(result: dict) -> str:
    """格式化文本输出"""
    output = []

    if result.get('success'):
        output.append(f"=== 搜索结果 ===")
        output.append(f"查询: {result.get('query', '')}")
        output.append(f"来源: {result.get('provider_used', '').upper()}")
        output.append(f"结果数: {len(result.get('results', []))}")
        output.append(f"缓存: {'是' if result.get('cached') else '否'}")

        # 显示内容
        content = result.get('content', '')
        if content:
            output.append(f"\n{content}")

        # 显示尝试记录
        attempts = result.get('attempts', [])
        if len(attempts) > 1:
            output.append(f"\n[尝试记录]")
            for attempt in attempts:
                status = "✓" if attempt['success'] else "✗"
                output.append(f"  {status} {attempt['provider']}: {attempt.get('error', 'OK')}")

    else:
        output.append(f"=== 搜索失败 ===")
        output.append(f"查询: {result.get('query', '')}")
        output.append(f"错误: {result.get('error', '未知错误')}")

        # 显示尝试记录
        attempts = result.get('attempts', [])
        if attempts:
            output.append(f"\n[尝试记录]")
            for attempt in attempts:
                status = "✓" if attempt['success'] else "✗"
                output.append(f"  {status} {attempt['provider']}: {attempt.get('error', 'OK')}")

    return '\n'.join(output)


def format_json_output(result: dict) -> str:
    """格式化JSON输出"""
    return json.dumps(result, ensure_ascii=False, indent=2)


def format_markdown_output(result: dict) -> str:
    """格式化Markdown输出"""
    output = []

    if result.get('success'):
        output.append(f"# 搜索结果: {result.get('query', '')}")
        output.append(f"\n**来源**: {result.get('provider_used', '').upper()}")
        output.append(f"**结果数**: {len(result.get('results', []))}")
        output.append(f"**缓存**: {'是' if result.get('cached') else '否'}")

        # 显示搜索结果
        results = result.get('results', [])
        if results:
            output.append(f"\n## 搜索结果\n")
            for i, r in enumerate(results, 1):
                output.append(f"### {i}. {r['title']}")
                output.append(f"{r['snippet']}")
                if r.get('url'):
                    output.append(f"\n**链接**: {r['url']}")
                output.append("")

        # 显示尝试记录
        attempts = result.get('attempts', [])
        if len(attempts) > 1:
            output.append(f"\n## 尝试记录\n")
            for attempt in attempts:
                status = "✓" if attempt['success'] else "✗"
                error = attempt.get('error', 'OK')
                output.append(f"- {status} **{attempt['provider']}**: {error}")

    else:
        output.append(f"# 搜索失败")
        output.append(f"\n**查询**: {result.get('query', '')}")
        output.append(f"**错误**: {result.get('error', '未知错误')}")

    return '\n'.join(output)


def main():
    """主函数"""
    # 修复Windows编码问题
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(
        description='多级fallback网络搜索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "Python编程教程"              # 基本搜索
  %(prog)s "Rust语言" --source duckduckgo # 指定搜索源
  %(prog)s "WebAssembly" --format json    # JSON输出
  %(prog)s "" --clear-cache               # 清空缓存
  %(prog)s "" --cache-stats               # 缓存统计

搜索源:
  auto        自动选择（默认，依次尝试智谱MCP → Tavily → DuckDuckGo → AI知识库）
  zhipu_mcp   使用智谱MCP（单配额，apikeyValue.txt）
  tavily      使用Tavily API（需要配置TAVILY_API_KEY）
  duckduckgo  使用DuckDuckGo（完全免费，无需API Key）
  ai_knowledge 使用AI知识库（需要配置ZHIPU_API_KEY，仅预训练知识）
        """
    )

    parser.add_argument('query', nargs='*', help='搜索查询（空查询时可用于--clear-cache或--cache-stats）')
    parser.add_argument('--max-results', type=int, default=5, help='最大结果数（默认: 5）')
    parser.add_argument('--timeout', type=int, default=30, help='超时时间（秒，默认: 30）')
    parser.add_argument('--format', choices=['text', 'json', 'markdown'], default='text',
                        help='输出格式（默认: text）')
    parser.add_argument('--source', choices=['auto', 'zhipu_mcp', 'tavily', 'duckduckgo', 'ai_knowledge'],
                        default='auto', help='指定搜索源（默认: auto，可选: auto, zhipu_mcp, tavily, duckduckgo, ai_knowledge）')
    parser.add_argument('--no-cache', action='store_true', help='禁用缓存')
    parser.add_argument('--clear-cache', action='store_true', help='清空缓存并退出')
    parser.add_argument('--cache-stats', action='store_true', help='显示缓存统计并退出')

    args = parser.parse_args()

    # 初始化搜索引擎
    engine = WebSearchEngine()

    # 处理清空缓存
    if args.clear_cache:
        engine.clear_cache()
        print("[SUCCESS] 缓存已清空")
        return 0

    # 处理缓存统计
    if args.cache_stats:
        stats = engine.get_cache_stats()
        print("=== 缓存统计 ===")
        print(f"目录: {stats.get('cache_dir', 'N/A')}")
        print(f"文件数: {stats.get('total_files', 0)}")
        print(f"总大小: {stats.get('total_size_mb', 0):.2f} MB")
        print(f"过期文件: {stats.get('expired_files', 0)}")
        return 0

    # 检查查询
    query = ' '.join(args.query) if args.query else ''
    if not query:
        parser.print_help()
        return 1

    # 执行搜索
    print(f"[INFO] 开始搜索: \"{query}\"")
    start_time = time.time()

    result = engine.search(
        query=query,
        max_results=args.max_results,
        source=args.source,
        timeout=args.timeout,
        use_cache=not args.no_cache
    )

    elapsed = time.time() - start_time

    # 格式化输出
    if args.format == 'json':
        output = format_json_output(result)
    elif args.format == 'markdown':
        output = format_markdown_output(result)
    else:
        output = format_text_output(result)

    print(f"\n{output}")
    print(f"\n[耗时: {elapsed:.2f}秒]")

    return 0 if result.get('success') else 1


if __name__ == "__main__":
    sys.exit(main())
