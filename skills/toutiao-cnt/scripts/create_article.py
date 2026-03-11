#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Toutiao Article Creator - v5.1.0 明确扩展边界
==============================================
根据主题生成今日头条文章，杜绝编造

Key Features:
- 基于事实生成：搜索结果和用户内容作为唯一事实来源
- 明确扩展边界：清晰定义"适当扩展"的允许/禁止范围
- 增强验证机制：检查扩展内容是否有事实依据
- 自适应字数：根据事实材料量自动调整
- 严格模式：无事实材料时拒绝生成（阈值提高到 300 字符）

v5.1.0 Changes:
- 明确定义"适当扩展"的允许/禁止边界
- 严格模式触发阈值从 100 提高到 300 字符
- 增强验证机制：检查扩展内容是否有事实依据
- 新增高严重度问题：技术细节编造、过度推断

Usage:
    python create_article.py "元宵节风俗" --output-dir "./output"
    python create_article.py "Claude Code Agent" --content article.html --strict
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
import re
import subprocess

# 添加路径以导入config
# __file__ = .claude/skills/toutiao-cnt/scripts/create_article.py
# 需要: MyAIProduct/post/config.py
# 路径: scripts(1) -> toutiao-cnt(2) -> skills(3) -> .claude(4) -> MyAIProduct(5) -> post
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'post'))

try:
    from config import get_zhipu_anthropic_client
except ImportError:
    print("[错误] 无法导入配置，请确保 config.py 存在")
    sys.exit(1)


def search_topic_info(topic: str, timeout: int = 60) -> dict:
    """使用网络搜索获取主题相关信息

    Returns:
        dict: {
            'success': bool,
            'content': str,  # 搜索结果内容
            'sources': list,  # 来源列表
            'error': str  # 错误信息（如果失败）
        }
    """
    print(f"  [搜索] 正在搜索关于'{topic}'的最新信息...")

    # 使用新的 web-search 路径
    search_script = 'C:/D/CAIE_tool/MyAIProduct/.claude/skills/web-search/main.py'

    try:
        result = subprocess.run(
            ['python', search_script, topic, '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8'
        )

        if result.returncode == 0 and result.stdout:
            try:
                data = json.loads(result.stdout)
                content = data.get('content', '')

                if content:
                    # 提取来源信息（如果有）
                    sources = data.get('sources', [])
                    if not sources:
                        sources = ['网络搜索']

                    print(f"  [完成] 获取到搜索结果 ({len(content)} 字符)")
                    return {
                        'success': True,
                        'content': content[:5000],  # 限制最大长度
                        'sources': sources
                    }
            except json.JSONDecodeError:
                # 如果不是 JSON，尝试解析纯文本
                if result.stdout:
                    print(f"  [完成] 获取到搜索结果 ({len(result.stdout)} 字符)")
                    return {
                        'success': True,
                        'content': result.stdout[:5000],
                        'sources': ['网络搜索']
                    }

        error_msg = result.stderr if result.stderr else "未知错误"
        print(f"  [警告] 搜索未返回结果: {error_msg}")
        return {
            'success': False,
            'content': '',
            'sources': [],
            'error': error_msg
        }

    except subprocess.TimeoutExpired:
        print(f"  [警告] 搜索超时（{timeout}秒），将使用其他信息源")
        return {
            'success': False,
            'content': '',
            'sources': [],
            'error': '搜索超时'
        }
    except Exception as e:
        print(f"  [警告] 搜索失败 ({e})")
        return {
            'success': False,
            'content': '',
            'sources': [],
            'error': str(e)
        }


def read_user_content(content_input: str) -> dict:
    """读取用户提供的内容

    Args:
        content_input: 文件路径或直接文本

    Returns:
        dict: {
            'success': bool,
            'content': str,
            'source_type': str,  # 'file' or 'text'
            'error': str  # 错误信息（如果失败）
        }
    """
    if not content_input:
        return {'success': False, 'content': '', 'source_type': None}

    # 检查是否是文件路径
    content_path = Path(content_input)

    # 如果是相对路径，尝试多种常见位置
    possible_paths = [
        content_path,  # 原始路径
        Path.cwd() / content_input,  # 当前工作目录
    ]

    for path in possible_paths:
        if path.exists() and path.is_file():
            try:
                # 根据文件扩展名处理
                suffix = path.suffix.lower()

                if suffix in ['.html', '.htm']:
                    # HTML 文件 - 提取文本内容
                    with open(path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    # 简单提取 body 内容
                    import re
                    body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
                    if body_match:
                        # 移除 HTML 标签
                        text = re.sub(r'<[^>]+>', ' ', body_match.group(1))
                        text = re.sub(r'\s+', ' ', text).strip()
                    else:
                        text = html_content
                    print(f"  [内容] 读取 HTML 文件: {path} ({len(text)} 字符)")
                    return {
                        'success': True,
                        'content': text,
                        'source_type': 'file',
                        'file_path': str(path)
                    }
                elif suffix in ['.md', '.markdown']:
                    # Markdown 文件
                    with open(path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    print(f"  [内容] 读取 Markdown 文件: {path} ({len(text)} 字符)")
                    return {
                        'success': True,
                        'content': text,
                        'source_type': 'file',
                        'file_path': str(path)
                    }
                else:
                    # 其他文本文件
                    with open(path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    print(f"  [内容] 读取文本文件: {path} ({len(text)} 字符)")
                    return {
                        'success': True,
                        'content': text,
                        'source_type': 'file',
                        'file_path': str(path)
                    }
            except Exception as e:
                print(f"  [警告] 读取文件失败: {e}")
                return {
                    'success': False,
                    'content': '',
                    'source_type': 'file',
                    'error': str(e)
                }

    # 不是文件，当作直接文本处理
    print(f"  [内容] 使用直接输入的文本 ({len(content_input)} 字符)")
    return {
        'success': True,
        'content': content_input,
        'source_type': 'text'
    }


def calculate_suggested_words(fact_content: str, min_words: int = 500, max_words: int = 2000) -> int:
    """根据事实材料量计算建议字数

    规则：
    - 事实材料 < 500 字：建议 500-800 字（精简）
    - 事实材料 500-2000 字：建议 1000-1500 字（适中）
    - 事实材料 > 2000 字：建议 1500-2000 字（详尽）
    """
    fact_len = len(fact_content)

    if fact_len < 500:
        return min(800, max(min_words, fact_len + 300))
    elif fact_len < 2000:
        return min(1500, max(min_words, fact_len // 2 + 500))
    else:
        return min(max_words, fact_len // 3 + 1000)


def build_fact_based_prompt(topic: str, style: str, fact_content: str, sources: list, suggested_words: int) -> str:
    """构建基于事实的 Prompt

    核心原则：
    1. 事实材料是唯一依据
    2. 字数根据事实材料量自适应
    3. 强制标注信息来源
    4. 禁止编造
    """
    sources_str = '、'.join(sources) if sources else '用户提供'

    return f"""你是一位严谨的技术文章作者。请基于以下事实材料，撰写关于"{topic}"的今日头条文章。

【事实材料（必须作为唯一依据）】
{fact_content}

【信息来源】
{sources_str}

【严格写作要求】
1. **字数要求**：{suggested_words} 字左右（根据事实材料量自适应，不可硬凑）

2. **核心原则 - 基于事实（最重要）**：
   - ✅ 所有信息必须来自上述事实材料
   - ❌ 绝对禁止编造事实材料中不存在的信息
   - ❌ 禁止添加事实材料中没有的具体数据、版本号、功能名称

3. **适当扩展的严格规则**：
   **允许的扩展（必须保持事实不变）**：
   - ✅ 重组事实顺序（保持事实不变）
   - ✅ 添加过渡句（必须基于已有事实，如"此外"、"另外"）
   - ✅ 简化术语（不改变原意，如"API接口"简化为"接口"）
   - ✅ 添加段落标题（基于内容归纳，不编造新概念）

   **禁止的扩展（视为编造）**：
   - ❌ 添加未提及的案例、示例、应用场景
   - ❌ 添加未提及的数据、版本号、配置参数
   - ❌ 做出未提及的预测、推测、假设
   - ❌ 描述未提及的功能、特性、模块名称
   - ❌ 添加"例如"引出的事实材料中不存在的案例
   - ❌ 基于有限信息进行过度推断或"补充背景"

3. **信息来源标注**：
   - 文章末尾必须添加"参考来源"部分
   - 列出上述信息来源

4. **风格要求**：
   - {style}、严谨准确（准确性 > 可读性 > 篇幅）
   - 通俗易懂，适合今日头条用户阅读
   - 结构清晰，使用 H2/H3 标题分段

5. **结构建议**：
   - 引言（简明扼要说明主题）
   - 2-4 个核心章节（每个章节聚焦一个要点）
   - 总结（概括核心观点）
   - 参考来源（必须包含）

6. **当事实材料不足时**：
   - 宁可简短也不要编造
   - 明确说明"根据现有资料..."
   - 不要用"例如"引出编造的案例

7. 输出格式：Markdown

请直接输出文章内容，不要添加其他说明文字。"""


def build_knowledge_only_prompt(topic: str, style: str, min_words: int, max_words: int) -> str:
    """构建纯知识库 Prompt（保守策略）

    当没有事实材料时使用，要求 AI：
    1. 使用限定词
    2. 承认知识边界
    3. 添加免责声明
    4. 宁可简短也不编造
    """
    return f"""你是一位谨慎的文章作者。请为"{topic}"撰写今日头条文章。

【重要提示】由于未获取到外部事实材料，你只能基于训练数据中的确定知识撰写。

【严格写作要求】
1. **字数要求**：{min_words}-{max_words} 字（根据你确定知道的内容量调整，宁可简短）

2. **核心原则 - 保守谨慎（最重要）**：
   - ✅ 只写你确定知道的内容
   - ✅ 使用"据我所知"、"通常"、"一般来说"等限定词
   - ✅ 对于不确定的信息，明确说"建议查阅最新官方资料"
   - ❌ 禁止编造具体数据、版本号、功能列表
   - ❌ 禁止使用"例如"引出你不确定的案例

3. **免责声明**（必须包含）：
   - 在文章开头或结尾添加类似声明：
   - "本文基于作者已有知识撰写，部分信息可能已更新，建议读者查阅最新官方资料获取准确信息。"

4. **风格要求**：
   - {style}、保守准确
   - 通俗易懂，适合今日头条用户阅读

5. **结构建议**：
   - 简短引言（包含免责声明）
   - 2-3 个核心章节（只写确定的内容）
   - 总结（重申信息可能有更新）

6. **绝对禁止**：
   - 编造具体的产品功能名称（除非你100%确定）
   - 虚构公司、团队、人物信息
   - 编造不存在的技术特性

7. 输出格式：Markdown

请直接输出文章内容，不要添加其他说明文字。"""


def validate_article_accuracy(topic: str, content: str, fact_content: str, strict: bool = False) -> dict:
    """验证文章内容的准确性

    Args:
        topic: 文章主题
        content: 文章内容
        fact_content: 事实材料
        strict: 严格模式

    Returns:
        dict: {
            'passed': bool,
            'issues': list,  # 问题列表
            'severity': str  # 'high', 'medium', 'low'
        }
    """
    print("  [验证] 正在验证内容准确性...")

    client = get_zhipu_anthropic_client()

    # 验证全文（不只是前 1000 字）
    content_to_validate = content
    if len(content) > 4000:
        # 如果文章太长，分段验证
        content_to_validate = content[:2000] + "\n...\n" + content[-2000:]

    if fact_content:
        validate_prompt = f"""请严格验证以下文章内容是否准确。

【主题】{topic}

【事实材料（作为验证基准）】
{fact_content[:3000]}

【待验证的文章内容】
{content_to_validate}

【验证要求】
请检查文章中是否存在以下问题，并按严重程度分类：

**高严重度问题**（必须修正，严格模式下阻止生成）：
1. 编造事实材料中不存在的产品功能、模块或组件名称
2. 虚构具体的数据、统计数字、版本号
3. 编造不存在的公司、团队、人物信息
4. 与事实材料明显矛盾的信息
5. **添加"例如"引出的事实材料中不存在的案例**
6. **添加未提及的技术细节（API参数、配置项、代码示例）**
7. **基于有限信息进行过度推断或"补充背景"**

**中严重度问题**（建议修正）：
1. 过度概括或简化导致不准确
2. 缺少必要的限定词（"通常"、"一般"等）
3. **添加的过渡句超出了事实材料支持的范围**

**低严重度问题**（可选修正）：
1. 表达不够精确
2. 可以更加严谨的表述

**扩展内容验证**（关键）：
对于文章中每个"扩展"部分（过渡句、解释、背景补充），请检查：
- 该内容是否能在事实材料中找到直接依据？
- 如果不能，是否属于"允许的扩展"（重组顺序、简化术语）？
- 如果属于"禁止的扩展"，应标记为高严重度问题

【输出格式】
请按以下 JSON 格式输出：
{{
    "passed": true/false,
    "issues": [
        {{"severity": "high/medium/low", "description": "问题描述", "location": "相关文本片段"}}
    ],
    "overall_severity": "high/medium/low"
}}

如果没有发现问题，输出：
{{"passed": true, "issues": [], "overall_severity": "low"}}
"""
    else:
        validate_prompt = f"""请验证以下文章内容是否保守准确。

【主题】{topic}

【待验证的文章内容】
{content_to_validate}

【验证要求】
由于没有事实材料作为基准，请检查文章是否：
1. 使用了适当的限定词（"据我所知"、"通常"等）
2. 包含免责声明
3. 没有编造不确定的具体信息
4. 保守谨慎，宁可简短

【输出格式】
{{"passed": true/false, "issues": [{{"severity": "high/medium/low", "description": "问题"}}], "overall_severity": "high/medium/low"}}
"""

    try:
        response = client.messages.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": validate_prompt}],
            max_tokens=1000
        )

        validation_result = response.content[0].text

        # 尝试解析 JSON
        try:
            # 提取 JSON 部分
            json_match = re.search(r'\{[\s\S]*\}', validation_result)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # 无法解析，使用默认值
                result = {
                    'passed': True,
                    'issues': [],
                    'overall_severity': 'low'
                }
        except json.JSONDecodeError:
            # 解析失败，检查关键词
            has_issues = any(kw in validation_result for kw in ['不准确', '编造', '虚构', '问题'])
            result = {
                'passed': not has_issues,
                'issues': [{'severity': 'medium', 'description': validation_result[:200]}] if has_issues else [],
                'overall_severity': 'medium' if has_issues else 'low'
            }

        # 打印验证结果
        if result['issues']:
            print(f"  [验证结果] 发现 {len(result['issues'])} 个问题:")
            for issue in result['issues'][:5]:  # 最多显示5个
                print(f"    - [{issue.get('severity', 'unknown')}] {issue.get('description', '')[:80]}")
        else:
            print(f"  [验证结果] 内容验证通过")

        # 严格模式下，高严重度问题阻止生成
        if strict and result.get('overall_severity') == 'high':
            result['passed'] = False
            print("  [警告] 严格模式：高严重度问题，拒绝生成")

        return result

    except Exception as e:
        print(f"  [警告] 验证失败: {e}")
        # 验证失败时，非严格模式允许通过
        return {
            'passed': not strict,
            'issues': [{'severity': 'low', 'description': f'验证异常: {e}'}],
            'overall_severity': 'low'
        }


def generate_article_content(topic: str, style: str = "专业", user_content: str = None,
                             strict: bool = False, min_words: int = 500, max_words: int = 2000) -> str:
    """使用AI生成文章内容

    Args:
        topic: 文章主题
        style: 写作风格
        user_content: 用户提供的内容（文件路径或直接文本）
        strict: 严格模式，无事实材料则拒绝生成
        min_words: 最小字数
        max_words: 最大字数

    Returns:
        str: 生成的文章内容，或 None（严格模式下无事实材料）
    """
    client = get_zhipu_anthropic_client()

    # 1. 收集事实材料
    fact_content = ""
    sources = []

    # 1.1 首先检查用户内容
    if user_content:
        user_result = read_user_content(user_content)
        if user_result['success']:
            fact_content = user_result['content']
            sources.append('用户提供内容')
            print(f"  [信息源] 使用用户内容作为事实材料")

    # 1.2 如果没有用户内容，尝试网络搜索
    if not fact_content:
        search_result = search_topic_info(topic)
        if search_result['success']:
            fact_content = search_result['content']
            sources = search_result['sources']
            print(f"  [信息源] 使用网络搜索作为事实材料")

    # 2. 检查是否有事实材料（阈值从 100 提高到 300，避免技术内容触发过于宽松）
    has_facts = bool(fact_content and len(fact_content.strip()) > 300)

    # 3. 严格模式检查
    if strict and not has_facts:
        print("\n[错误] 严格模式：未获取到足够的事实材料，拒绝生成文章")
        print("[建议] 请提供以下任一信息源：")
        print("  1. 使用 --content 参数提供相关内容文件")
        print("  2. 使用 --content 参数直接提供相关文本")
        print("  3. 去掉 --strict 参数，允许基于知识库生成（保守模式）")
        return None

    # 4. 根据是否有事实材料选择 Prompt 策略
    if has_facts:
        # 基于事实的 Prompt
        suggested_words = calculate_suggested_words(fact_content, min_words, max_words)
        prompt = build_fact_based_prompt(topic, style, fact_content, sources, suggested_words)
        print(f"  [策略] 基于事实生成，建议字数: {suggested_words}")
    else:
        # 保守的知识库 Prompt
        prompt = build_knowledge_only_prompt(topic, style, min_words, max_words)
        print(f"  [策略] 保守模式生成（无外部事实材料），字数范围: {min_words}-{max_words}")

    # 5. 调用 AI 生成
    try:
        response = client.messages.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096
        )

        content = response.content[0].text

        # 6. 验证内容准确性
        validation = validate_article_accuracy(topic, content, fact_content, strict)

        # 7. 严格模式下验证失败则拒绝
        if strict and not validation['passed']:
            print(f"\n[错误] 严格模式：内容验证未通过")
            print(f"[问题列表] {validation['issues']}")
            return None

        return content

    except Exception as e:
        print(f"[错误] AI生成失败: {e}")
        return None


def markdown_to_toutiao_html(markdown_content: str, title: str) -> str:
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
        .source-reference {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-radius: 5px;
            margin-top: 30px;
            font-size: 14px;
            color: #666;
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


def create_article(topic: str, output_dir: str = None, style: str = "专业",
                   user_content: str = None, strict: bool = False,
                   min_words: int = 500, max_words: int = 2000) -> Path:
    """创建文章

    Args:
        topic: 文章主题
        output_dir: 输出目录
        style: 写作风格
        user_content: 用户提供的内容（文件路径或直接文本）
        strict: 严格模式，无事实材料则拒绝生成
        min_words: 最小字数
        max_words: 最大字数

    Returns:
        Path: 生成的文件路径，或 None（生成失败）
    """
    print(f"\n{'='*60}")
    print(f"[创建文章] 主题: {topic}")
    print(f"{'='*60}")
    if strict:
        print(f"[模式] 严格模式 - 无事实材料将拒绝生成")
    if user_content:
        print(f"[内容源] {user_content}")
    print()

    # 生成内容
    print("[1/3] 正在生成文章内容...")
    markdown_content = generate_article_content(
        topic, style, user_content, strict, min_words, max_words
    )

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
        description='创建今日头条文章（基于事实生成，杜绝编造）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 基本创建（使用网络搜索）
  python create_article.py "Python 3.12 新特性"

  # 使用用户内容（关键场景）
  python create_article.py "Claude Code Agent" --content article.html

  # 严格模式（无事实则拒绝生成）
  python create_article.py "主题" --content source.md --strict

  # 非严格模式 + 无搜索结果（预期：保守生成）
  python create_article.py "不存在的主题xyz123"
"""
    )

    parser.add_argument('topic', help='文章主题')
    parser.add_argument('--output-dir', help='输出目录')
    parser.add_argument('--style', default='专业', help='写作风格')
    parser.add_argument('--content', help='用户提供的内容（文件路径或直接文本）')
    parser.add_argument('--strict', action='store_true',
                        help='严格模式：无事实材料则拒绝生成')
    parser.add_argument('--min-words', type=int, default=500,
                        help='最小字数（默认 500）')
    parser.add_argument('--max-words', type=int, default=2000,
                        help='最大字数（默认 2000）')

    args = parser.parse_args()

    result = create_article(
        args.topic,
        args.output_dir,
        args.style,
        args.content,
        args.strict,
        args.min_words,
        args.max_words
    )

    if result is None:
        sys.exit(1)


if __name__ == '__main__':
    main()
