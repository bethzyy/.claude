# -*- coding: utf-8 -*-
"""
头条文章配图 Skill v2.1.5
为今日头条纯文本文章自动生成配图

更新日志：
v2.1.5 (2026-03-04)
- 图片命名改进：使用语义化文件名 `insertion_point_N.jpg`
  - 文件名清晰表达插入位置（第1个、第2个、第3个插入点）
  - 复用逻辑更加严谨可靠（按位置精确匹配）
  - 调试友好，打开文件夹即一目了然
  - 修复了v2.1.4无法验证图片是否对应正确位置的问题
- 改进：部分图片复用时只生成缺失位置的图片
- 新增：find_existing_images_by_position() 函数按位置查找现有图片
- 新增：call_image_gen_skill_with_prefixes() 函数支持自定义文件名前缀

v2.1.4 (2026-03-04)
- 图片复用：检查并重用已存在的AI配图，避免重复生成
  - 如果output_dir中已有足够的img_*.jpg文件，直接复用
  - 只生成缺失的图片，节省时间和API配额
  - 表格图片仍然每次重新生成（因为样式可能调整）
- 改进：智能检测现有图片，提升执行效率

v2.1.0 (2026-03-04)
- 表格转图片：自动将 HTML 表格转换为图片，保留格式
- 上下文感知提示词：使用 GLM-4-flash 分析文章内容，生成相关提示词
- 移除通用提示词：不再使用默认的 generic prompts
- 编码修复：修复 AI 提示词生成的编码问题

v2.0.0 (2026-03-04)
- 架构重构：图片生成功能迁移到 image-gen skill
- 新增模块：article_illustrator.py 处理 HTML 文章逻辑
- 向后兼容：现有命令行用法不变
- 提升可维护性：职责分离，代码更清晰

v1.2.0 (2026-03-04)
- 图片统一存储在 images/ 目录
- 每个文档拥有独立的图片子目录
- 支持多次配图共用同一目录
- 自动计算相对路径确保图片正确显示

v1.1.0 (2026-03-03)
- 修复只插入1张图片的bug
- 第2张图片：支持匹配表格后的 <h2> 或 <h3>
- 第3张图片：改为在第3个 <h2> 后插入，不再依赖"案例"关键词

v1.0.0
- 初始版本
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Import HTML processing module
from article_illustrator import (
    ArticleIllustrator,
    get_image_output_dir,
    extract_content_from_html,
    insert_images_to_content,
    create_output_html
)


def get_image_output_dir(html_path):
    """
    获取图片输出目录

    规则：
    - 在HTML文件同级目录创建 images/ 文件夹
    - 在 images/ 下以文档名创建子目录
    - 多次配图共用同一子目录

    Args:
        html_path: HTML文件路径

    Returns:
        Path: 图片输出目录路径
    """
    html_path = Path(html_path)
    images_dir = html_path.parent / "images"
    doc_subdir = images_dir / html_path.stem

    # 创建目录（如果不存在）
    doc_subdir.mkdir(parents=True, exist_ok=True)

    return doc_subdir


def add_images_to_toutiao_article(html_file_path, image_style="realistic", num_images=3):
    """
    为头条文章添加配图

    Args:
        html_file_path: HTML文件路径
        image_style: 图片风格 (realistic, artistic, cartoon, technical)
        num_images: 配图数量 (默认3张)

    Returns:
        output_html_path: 输出HTML文件路径
        image_paths: 生成的图片路径列表
    """
    # 验证文件存在
    html_path = Path(html_file_path)
    if not html_path.exists():
        raise FileNotFoundError(f"找不到文件: {html_file_path}")

    print(f"正在处理: {html_path.name}")

    # 使用 ArticleIllustrator 提取内容
    illustrator = ArticleIllustrator(html_path)
    title, body_content = illustrator.extract_content()

    print(f"文章标题: {title}")
    print(f"正文长度: {len(body_content)} 字符")

    # 使用AI生成配图提示词
    print(f"\n正在分析文章内容，生成 {num_images} 张配图提示词...")
    prompts = generate_image_prompts_with_ai(
        theme=title,
        content=body_content,
        image_style=image_style,
        num_images=num_images
    )

    # 调用 image-gen skill 生成图片
    print(f"\n开始生成 {num_images} 张配图...")

    # 清理提示词（移除可能导致JSON解析问题的字符）
    clean_prompts = []
    for p in prompts:
        prompt_text = p[0]
        # 移除开头和结尾的引号（如果AI生成的提示词带有引号）
        prompt_text = prompt_text.strip()
        if prompt_text.startswith('"') and prompt_text.endswith('"'):
            prompt_text = prompt_text[1:-1]
        # 移除单引号
        prompt_text = prompt_text.replace("'", "")
        clean_prompts.append(prompt_text)

    # Skip debug print to avoid encoding issues
    # print(f"生成的提示词: {[p[:80] for p in clean_prompts]}")

    # Check for existing AI images by position (reuse if available)
    output_dir = illustrator.get_image_output_dir()
    existing_by_position = find_existing_images_by_position(output_dir, num_images)

    if len(existing_by_position) == num_images:
        # All insertion point images exist, reuse all
        print(f"[INFO] Found all {num_images} insertion point images, reusing all...")
        image_paths = [str(existing_by_position[pos]) for pos in range(1, num_images + 1)]
        print(f"[INFO] Skipped AI image generation (saved ~{num_images * 30} seconds)")
    elif len(existing_by_position) > 0:
        # Partial images exist, generate only missing ones
        missing_positions = [p for p in range(1, num_images + 1) if p not in existing_by_position]
        print(f"[INFO] Found {len(existing_by_position)} existing images, generating {len(missing_positions)} missing...")

        try:
            # Generate only missing images with proper prefixes
            if len(missing_positions) > 0:
                # Prepare prompts and prefixes for missing positions
                missing_prompts = []
                filename_prefixes = []
                for pos in missing_positions:
                    # Use the corresponding prompt for this position
                    prompt_index = pos - 1  # Convert to 0-based index
                    if prompt_index < len(clean_prompts):
                        missing_prompts.append(clean_prompts[prompt_index])
                        filename_prefixes.append(f"insertion_point_{pos}")

                # Generate missing images with position-specific prefixes
                image_gen_results = call_image_gen_skill_with_prefixes(
                    prompts=missing_prompts,
                    output_dir=output_dir,
                    style=image_style,
                    filename_prefixes=filename_prefixes
                )
            else:
                image_gen_results = []
        except Exception as e:
            # Use ASCII-safe error messages
            error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
            print(f"[ERROR] Image generation failed: {error_msg}")
            image_gen_results = []

        # Combine existing and newly generated images in correct order
        image_paths = []
        for pos in range(1, num_images + 1):
            if pos in existing_by_position:
                image_paths.append(str(existing_by_position[pos]))
            elif image_gen_results:
                # Find the corresponding generated image
                # The results are in the same order as missing_positions
                result_idx = missing_positions.index(pos) if pos in missing_positions else -1
                if result_idx >= 0 and result_idx < len(image_gen_results):
                    image_paths.append(image_gen_results[result_idx]['path'])

        if len(image_paths) < num_images:
            print(f"警告: 总共只有 {len(image_paths)}/{num_images} 张配图")
    else:
        # No existing images, generate all
        print(f"[INFO] No existing images found, generating {num_images} images...")

        try:
            # Generate all images with position-based prefixes
            filename_prefixes = [f"insertion_point_{i}" for i in range(1, num_images + 1)]
            image_gen_results = call_image_gen_skill_with_prefixes(
                prompts=clean_prompts,
                output_dir=output_dir,
                style=image_style,
                filename_prefixes=filename_prefixes
            )
        except Exception as e:
            # Use ASCII-safe error messages
            error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
            print(f"[ERROR] Image generation failed: {error_msg}")
            image_gen_results = []

        # All images are newly generated
        image_paths = [img['path'] for img in image_gen_results] if image_gen_results else []

        if len(image_paths) < num_images:
            print(f"警告: 总共只有 {len(image_paths)}/{num_images} 张配图")

    # 在文章中插入配图（自动转换表格为图片）
    content_with_images = illustrator.insert_images_to_content(
        content=body_content,
        image_paths=image_paths,
        num_images=num_images,
        convert_tables=True  # Enable table-to-image conversion
    )

    # 生成输出HTML
    output_html_path = illustrator.create_output_html(title, content_with_images)

    print(f"\n[OK] 完成!")
    print(f"  输出文件: {output_html_path}")
    print(f"  生成图片: {len(image_paths)} 张")

    return str(output_html_path), image_paths


def find_existing_images_by_position(output_dir: Path, num_images: int) -> dict:
    """
    按插入点查找现有图片

    Args:
        output_dir: 图片输出目录
        num_images: 需要的图片数量

    Returns:
        字典: {position: image_path}，position从1开始
    """
    existing = {}
    for pos in range(1, num_images + 1):
        matches = list(output_dir.glob(f"insertion_point_{pos}.jpg"))
        if matches:
            # Should only be one matching file
            existing[pos] = matches[0]
    return existing


def call_image_gen_skill_with_prefixes(prompts, output_dir, style, filename_prefixes):
    """
    调用 image-gen skill 生成图片，使用自定义文件名前缀

    Args:
        prompts: 提示词列表
        output_dir: 图片输出目录
        style: 图片风格
        filename_prefixes: 文件名前缀列表（如 ['insertion_point_1', 'insertion_point_2']）

    Returns:
        生成的图片路径列表
    """
    # 查找 image-gen 脚本
    image_gen_script = Path(__file__).parent.parent.parent / 'image-gen' / 'main.py'

    if not image_gen_script.exists():
        raise FileNotFoundError(
            f"[ERROR] image-gen skill not found.\n"
            f"Expected location: {image_gen_script}\n"
            "Please install image-gen skill first."
        )

    results = []

    # 为每个提示词生成对应的图片（使用对应的prefix）
    for prompt, prefix in zip(prompts, filename_prefixes):
        # 使用环境变量传递单个 prompt
        env = os.environ.copy()
        import base64
        prompts_json = json.dumps([prompt], ensure_ascii=False)
        prompts_b64 = base64.b64encode(prompts_json.encode('utf-8')).decode('ascii')
        env['IMAGE_GEN_PROMPTS'] = prompts_b64

        cmd = [
            sys.executable,
            str(image_gen_script),
            '--use-env-prompts',
            '--output-dir', str(output_dir),
            '--style', style,
            '--format', 'json',
            '--size', '1024x1024',
            '--filename-prefix', prefix  # 新增：使用位置前缀
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=600,
                env=env
            )

            if result.returncode == 0:
                try:
                    output_data = json.loads(result.stdout)
                    images = output_data.get('images', [])
                    if images:
                        results.append(images[0])  # 只取第一张（因为我们只传了一个prompt）
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Failed to parse image-gen JSON output: {e}")
            else:
                print(f"[ERROR] image-gen failed with return code {result.returncode}")
                if result.stderr:
                    print(f"[ERROR] stderr: {result.stderr[:500]}")

        except subprocess.TimeoutExpired:
            print("[ERROR] image-gen timed out after 10 minutes")
        except Exception as e:
            print(f"[ERROR] Failed to call image-gen: {e}")

    return results


def call_image_gen_skill(prompts, output_dir, style):
    """
    调用 image-gen skill 生成图片

    通过 subprocess 执行 image-gen/generate_images.py
    使用环境变量传递 JSON 数据（避免命令行特殊字符问题）

    Args:
        prompts: 提示词列表
        output_dir: 图片输出目录
        style: 图片风格

    Returns:
        生成的图片路径列表
    """
    # 查找 image-gen 脚本
    image_gen_script = Path(__file__).parent.parent.parent / 'image-gen' / 'main.py'

    if not image_gen_script.exists():
        raise FileNotFoundError(
            f"[ERROR] image-gen skill not found.\n"
            f"Expected location: {image_gen_script}\n"
            "Please install image-gen skill first."
        )

    # 使用环境变量传递 JSON 数据
    env = os.environ.copy()
    # 将 prompts 列表编码为 base64 以避免特殊字符问题
    import base64
    prompts_json = json.dumps(prompts, ensure_ascii=False)
    prompts_b64 = base64.b64encode(prompts_json.encode('utf-8')).decode('ascii')
    env['IMAGE_GEN_PROMPTS'] = prompts_b64

    cmd = [
        sys.executable,
        str(image_gen_script),
        '--use-env-prompts',  # 新增标志：使用环境变量
        '--output-dir', str(output_dir),
        '--style', style,
        '--format', 'json',
        '--size', '1024x1024'
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=600,
            env=env
        )

        if result.returncode == 0:
            try:
                output_data = json.loads(result.stdout)
                return output_data.get('images', [])
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to parse image-gen JSON output: {e}")
                print(f"[ERROR] Output preview: {result.stdout[:200] if result.stdout else 'empty'}")
                return []
        else:
            print(f"[ERROR] image-gen failed with return code {result.returncode}")
            if result.stderr:
                print(f"[ERROR] stderr: {result.stderr[:500]}")
            if result.stdout:
                print(f"[ERROR] stdout: {result.stdout[:500]}")
            return []

    except subprocess.TimeoutExpired:
        print("[ERROR] image-gen timed out after 10 minutes")
        return []
    except Exception as e:
        print(f"[ERROR] Failed to call image-gen: {e}")
        return []


def extract_content_key_points(html_content: str, title: str) -> dict:
    """
    Extract key content points for image generation planning using AI

    Args:
        html_content: HTML body content
        title: Article title

    Returns:
        Dictionary with main_topic, key_concepts, and visual_opportunities
    """
    from zhipuai import ZhipuAI

    api_key = os.environ.get('ZHIPU_API_KEY')
    if not api_key:
        print("[WARNING] 未设置 ZHIPU_API_KEY，使用默认内容分析")
        return _get_default_content_analysis(title)

    client = ZhipuAI(api_key=api_key)

    # Limit content to first 3000 chars for token efficiency
    content_preview = html_content[:3000] if len(html_content) > 3000 else html_content

    prompt = f"""分析以下文章内容，提取适合生成配图的关键信息。

文章标题：{title}

文章内容片段：
{content_preview}

请以JSON格式返回：
{{
    "main_topic": "文章核心主题（一句话）",
    "key_concepts": ["核心概念1", "核心概念2", "核心概念3"],
    "visual_opportunities": [
        {{
            "section": "章节名称",
            "description": "该部分内容描述",
            "suggested_image_type": "flowchart/diagram/comparison/architecture/infographic",
            "prompt_hint": "建议的生图提示词方向"
        }}
    ]
}}

要求：
1. 识别3-5个最适合可视化展示的内容点
2. 优先选择可以用流程图、对比图、架构图展示的内容
3. 提示词应具体、描述性强，便于AI生图理解
"""

    try:
        response = client.chat.completions.create(
            model='glm-4-flash',
            messages=[
                {'role': 'system', 'content': '你是一名资深编辑，擅长为技术文章策划配图。'},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )

        content = response.choices[0].message.content

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)

        return json.loads(content)

    except Exception as e:
        print(f"[WARNING] AI content analysis failed: {e}")
        return _get_default_content_analysis(title)


def _get_default_content_analysis(title: str) -> dict:
    """Fallback content analysis when AI is unavailable"""
    safe_title = title.encode('ascii', errors='ignore').decode('ascii').strip()
    if not safe_title:
        safe_title = "Article Content"

    return {
        "main_topic": safe_title,
        "key_concepts": [safe_title, "Key Concept 2", "Key Concept 3"],
        "visual_opportunities": [
            {
                "section": "Introduction",
                "description": f"Overview of {safe_title}",
                "suggested_image_type": "infographic",
                "prompt_hint": f"Main concept visualization of {safe_title}"
            },
            {
                "section": "Details",
                "description": "Key details and explanations",
                "suggested_image_type": "diagram",
                "prompt_hint": "Detailed process flow and explanation"
            },
            {
                "section": "Application",
                "description": "Practical applications",
                "suggested_image_type": "comparison",
                "prompt_hint": "Application scenario demonstration"
            }
        ]
    }


def generate_context_aware_prompts(key_points: dict, num_images: int, style: str) -> List[str]:
    """
    Generate context-aware image prompts based on content analysis

    Args:
        key_points: Output from extract_content_key_points()
        num_images: Number of images to generate
        style: Image style (realistic/artistic/cartoon/technical)

    Returns:
        List of specific, content-relevant prompts
    """
    from zhipuai import ZhipuAI

    api_key = os.environ.get('ZHIPU_API_KEY')
    if not api_key:
        print("[WARNING] 未设置 ZHIPU_API_KEY，使用基础提示词")
        return _generate_fallback_prompts(key_points, num_images, style)

    client = ZhipuAI(api_key=api_key)

    visual_opps = key_points.get('visual_opportunities', [])[:num_images]

    prompt = f"""基于以下文章内容分析，生成{num_images}个具体的AI生图提示词。

文章主题：{key_points.get('main_topic', 'Article')}

核心概念：{', '.join(key_points.get('key_concepts', []))}

可视化机会：
{json.dumps(visual_opps, ensure_ascii=False, indent=2)}

图像风格：{style}

请生成{num_images}个提示词，每个提示词：
1. 紧密对应上述"可视化机会"中的一个
2. 使用英文（AI生图模型理解更好）
3. 包含具体的视觉元素描述（流程图、对比图、架构图等）
4. 添加技术细节（如箭头、框图、颜色标注等）
5. 字数控制在50-100词

请以JSON数组格式返回：
["prompt1", "prompt2", "prompt3"]

示例：
对于"Agent Teams架构"的内容，提示词应为：
"Technical diagram showing Agent Teams architecture with 5 specialized agents working together. Central hub coordinating workflow, arrows showing communication paths between agents. Clean infographic style with color-coded agent roles, icons representing tools and permissions. Professional blueprint aesthetic."
"""

    try:
        response = client.chat.completions.create(
            model='glm-4-flash',
            messages=[
                {'role': 'system', 'content': '你是专业的AI生图提示词工程师。'},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.5,
            max_tokens=1000
        )

        content = response.choices[0].message.content

        # Extract JSON array
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            prompts = json.loads(json_match.group(0))
            if len(prompts) == num_images:
                return prompts

        # Fallback if parsing failed
        return _generate_fallback_prompts(key_points, num_images, style)

    except Exception as e:
        print(f"[WARNING] AI prompt generation failed: {e}")
        return _generate_fallback_prompts(key_points, num_images, style)


def _generate_fallback_prompts(key_points: dict, num_images: int, style: str) -> List[str]:
    """Generate fallback prompts based on content analysis"""
    style_desc = {
        "realistic": "realistic photography, high quality, professional lighting",
        "artistic": "artistic style, creative, elegant composition",
        "cartoon": "cartoon illustration, colorful, friendly style",
        "technical": "technical diagram, flowchart, architecture diagram, clean infographic style",
        "auto": "professional quality visualization"
    }.get(style, "realistic photography, high quality")

    main_topic = key_points.get('main_topic', 'Article Content')
    safe_topic = main_topic.encode('ascii', errors='ignore').decode('ascii').strip()
    if not safe_topic:
        safe_topic = "Article Content"

    prompts = []
    for i in range(num_images):
        if i == 0:
            prompt = f"Professional visualization of {safe_topic} main concept, {style_desc}"
        elif i == 1:
            prompt = f"Detailed diagram showing {safe_topic} key components and structure, {style_desc}"
        else:
            prompt = f"Practical application scenario of {safe_topic} with examples, {style_desc}"
        prompts.append(prompt)

    return prompts


def generate_image_prompts_with_ai(theme, content, image_style, num_images):
    """
    使用AI生成上下文感知的配图提示词

    New implementation (v2.1.0):
    1. Extract title and content from HTML
    2. Use GLM-4-flash to analyze content and extract key points
    3. Generate specific prompts based on visual opportunities
    4. Return prompts for image generation

    Args:
        theme: 文章主题/标题
        content: 文章正文内容
        image_style: 图片风格
        num_images: 需要生成的提示词数量

    Returns:
        List of tuples: [(prompt_text, description), ...]
    """
    print(f"[INFO] Analyzing content for: {theme}")

    # Stage 1: Extract key content points
    print("[INFO] Extracting key content points...")
    key_points = extract_content_key_points(content, theme)

    print(f"[INFO] Main topic: {key_points.get('main_topic', 'Unknown')}")
    print(f"[INFO] Found {len(key_points.get('visual_opportunities', []))} visual opportunities")

    # Stage 2: Generate specific prompts
    print("[INFO] Generating context-aware prompts...")
    prompts = generate_context_aware_prompts(key_points, num_images, image_style)

    print(f"[INFO] Generated {len(prompts)} prompts:")
    for i, prompt in enumerate(prompts, 1):
        print(f"  {i}. {prompt[:80]}...")

    # Convert to tuple format for compatibility
    return [(prompt, f"context_img{i+1}") for i, prompt in enumerate(prompts)]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python add_images_to_toutiao_article.py <html文件路径> [风格] [图片数量]")
        print("\n风格选项:")
        print("  realistic - 真实摄影风格（默认）")
        print("  artistic - 艺术创作风格")
        print("  cartoon - 卡通插画风格")
        print("  technical - 技术图表风格")
        sys.exit(1)

    html_file = sys.argv[1]
    style = sys.argv[2] if len(sys.argv) > 2 else "realistic"
    num = int(sys.argv[3]) if len(sys.argv) > 3 else 3

    try:
        output_path, images = add_images_to_toutiao_article(html_file, style, num)
        print("\n发布步骤:")
        print("1. 用浏览器打开输出的HTML文件")
        print("2. 全选并复制内容 (Ctrl+A, Ctrl+C)")
        print("3. 粘贴到今日头条编辑器")
        print("4. 上传对应的图片文件")
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)
