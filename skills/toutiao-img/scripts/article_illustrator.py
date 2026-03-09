# -*- coding: utf-8 -*-
"""
Article Illustrator Module v2.1.5
HTML article processing and image insertion logic

This module handles HTML article parsing, image insertion, and output generation.
Extracted from add_images_to_toutiao_article.py for better modularity.

Changes in v2.1.5:
- Updated: Version synchronization with add_images_to_toutiao_article.py v2.1.5
- Note: No code changes in this module for v2.1.5 (changes were in calling module)
- Note: Image naming scheme changed to position-based (insertion_point_N.jpg)

Changes in v2.1.4:
- Added: Image reuse functionality to avoid regenerating existing AI images
  - Checks for img_*.jpg files in output_dir before generating
  - Reuses existing images, only generates missing ones
  - Saves time and API quota when re-running skill
- Note: Table images (table_*.jpg) still regenerated each run

Changes in v2.1.3:
- Optimized: Table styling now uses fixed 600px width (reduced from 100%)
- Optimized: Table font size increased to 24px (from 14px) for better readability
- Optimized: Table padding reduced to 8px (from 14px) to minimize whitespace
- Result: Tables are more compact and mobile-friendly

Changes in v2.1.2:
- Fixed: Directory name now uses readable document name (no more hash)
- Fixed: Insertion point 2 now works correctly after table conversion
- Improved: AI images inserted BEFORE table conversion to preserve insertion points

Changes in v2.1.0:
- Added table-to-image conversion functionality
- Integrated convert_tables_to_images() method
- Modified insert_images_to_content() workflow
"""

import re
import os
from pathlib import Path
from datetime import datetime
from typing import List, Tuple


class ArticleIllustrator:
    """Handler for HTML article illustration"""

    def __init__(self, html_path: Path):
        """
        Initialize the article illustrator

        Args:
            html_path: Path to the HTML article file
        """
        self.html_path = Path(html_path)

    def get_image_output_dir(self) -> Path:
        """
        Get the image output directory

        Creates a structured directory:
        - images/ folder in HTML file's parent directory
        - Subdirectory named after the document (HTML filename without extension)
        - Uses original document name (supports Chinese characters)

        Returns:
            Path: Image output directory path
        """
        images_dir = self.html_path.parent / "images"

        # Use original document name (supports Chinese and other UTF-8 characters)
        # Windows 10+ has full UTF-8 path support
        stem = self.html_path.stem
        doc_subdir = images_dir / stem

        # Create directory if it doesn't exist
        doc_subdir.mkdir(parents=True, exist_ok=True)

        return doc_subdir

    def extract_content(self) -> tuple[str, str]:
        """
        Extract title and body content from HTML

        Returns:
            Tuple of (title, body_content)

        Raises:
            FileNotFoundError: If HTML file doesn't exist
            ValueError: If required HTML tags are missing
        """
        if not self.html_path.exists():
            raise FileNotFoundError(f"找不到文件: {self.html_path}")

        # Read HTML content
        with open(self.html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Extract title
        title_match = re.search(r'<title>(.*?)</title>', html_content, re.DOTALL)
        if not title_match:
            title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.DOTALL)
        title = title_match.group(1).strip() if title_match else self.html_path.stem

        # Extract body content
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL)
        if not body_match:
            raise ValueError("无法提取文章内容：缺少 <body> 标签")

        body_content = body_match.group(1)
        # Remove existing h1 tag (will be re-added in output)
        body_content = re.sub(r'<h1[^>]*>.*?</h1>', '', body_content, flags=re.DOTALL)

        return title, body_content

    def insert_images_to_content(
        self,
        content: str,
        image_paths: List[str],
        num_images: int,
        convert_tables: bool = True
    ) -> str:
        """
        Insert images into article content at strategic positions

        Fixed workflow (v2.1.2):
        1. Insert AI-generated images FIRST (while </table> tags still exist)
        2. Convert tables to images AFTER AI images are inserted

        This ensures insertion point 2 (after </table>) works correctly.

        Insertion points for AI images:
        - Image 1: After introduction (before first <h2>)
        - Image 2: After tables (</table> followed by <h2> or <h3>)
        - Image 3: At 3rd major section (after 3rd <h2>)

        Args:
            content: HTML body content
            image_paths: List of generated image paths
            num_images: Number of images to insert
            convert_tables: Whether to convert HTML tables to images (default: True)

        Returns:
            HTML content with inserted images
        """
        # Step 1: Clean HTML content
        content = self._clean_html_content(content)

        # Step 2: Insert AI-generated images (before table conversion)
        # Insertion point 1: After introduction (before first <h2>)
        if len(image_paths) > 0:
            img_tag = self._create_image_tag(image_paths[0], "文章主题配图")
            content = re.sub(
                r'(\n\s*<h2[^>]*>)',
                lambda m: f'\n\n{img_tag}\n{m.group(1)}',
                content,
                count=1
            )

        # Insertion point 2: After tables (</table> followed by <h2> or <h3>)
        if len(image_paths) > 1:
            img_tag = self._create_image_tag(image_paths[1], "内容详解配图")
            content = re.sub(
                r'(</table>\s*)(\s*<h[23][^>]*>)',
                lambda m: f'{m.group(1)}\n\n{img_tag}\n{m.group(2)}',
                content,
                count=1
            )

        # Insertion point 3: At 3rd major section (after 3rd <h2>)
        if len(image_paths) > 2:
            img_tag = self._create_image_tag(image_paths[2], "实际应用配图")
            h2_count = 0

            def replace_third_h2(match):
                nonlocal h2_count
                h2_count += 1
                if h2_count == 3:
                    return match.group(0) + '\n\n' + img_tag
                return match.group(0)

            content = re.sub(r'(<h2[^>]*>.*?</h2>)', replace_third_h2, content)

        # Step 3: Convert tables to images (AFTER AI images are inserted)
        if convert_tables:
            from table_converter import convert_tables_to_images
            content, table_images = convert_tables_to_images(
                content,
                self.get_image_output_dir(),
                self.html_path  # Pass HTML file path for relative path calculation
            )
            print(f"[INFO] Converted {len(table_images)} table(s) to images")

        return content

    def create_output_html(self, title: str, content: str, output_path: Path = None) -> Path:
        """
        Create the output HTML file with images

        Args:
            title: Article title
            content: HTML content with images
            output_path: Output file path (default: {original}-images.html)

        Returns:
            Path: Output HTML file path
        """
        if output_path is None:
            output_path = self.html_path.parent / f"{self.html_path.stem}-images.html"

        html_content = self._generate_html_template(title, content)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path

    def _create_image_tag(self, img_path: str, caption: str) -> str:
        """
        Create HTML img tag with proper styling and caption

        Args:
            img_path: Image file path
            caption: Image caption/description

        Returns:
            HTML string with img and caption
        """
        img_path = Path(img_path).resolve()
        # Output HTML will be in the same directory as original HTML
        html_parent = self.html_path.parent.resolve()

        # Calculate relative path: HTML所在目录 -> images/文档子目录/
        try:
            relative_path = img_path.relative_to(html_parent)
            # Use as_posix() to ensure forward slashes, then encode/decode to preserve UTF-8
            img_name = relative_path.as_posix()
        except ValueError:
            # Fallback: try to extract just the filename and images/ part
            # This handles cases where img_path is not under html_parent
            if 'images' in str(img_path):
                # Extract path from 'images/' onwards
                parts = str(img_path).split('images')
                if len(parts) > 1:
                    img_name = 'images' + parts[-1].replace('\\', '/')
                else:
                    img_name = str(img_path).replace('\\', '/')
            else:
                img_name = str(img_path).replace('\\', '/')

        # Build HTML tag ensuring UTF-8 encoding is preserved
        html_tag = f'<p style="text-align: center;">\n'
        html_tag += f'<img src="{img_name}" alt="{caption}" style="max-width: 650px; width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">\n'
        html_tag += f'</p>\n'
        html_tag += f'<p style="text-align: center; color: #888; font-size: 13px; margin-top: 8px; margin-bottom: 20px;">图：{caption}</p>'

        return html_tag

    def _clean_html_content(self, content: str) -> str:
        """
        Clean HTML content by fixing common issues

        Args:
            content: Raw HTML content

        Returns:
            Cleaned HTML content
        """
        # Fix double-nested <p> tags
        content = re.sub(r'<p style="[^"]*"><p>(.*?)</p></p>', r'<p>\1</p>', content, flags=re.DOTALL)
        # Clean up duplicate style attributes
        content = re.sub(r' style="([^"]*)"; style="([^"]*)"', r' style="\1; \2"', content)
        return content

    def _generate_html_template(self, title: str, content: str) -> str:
        """
        Generate complete HTML document with styling

        Args:
            title: Article title
            content: Article body content with images

        Returns:
            Complete HTML document string
        """
        return f"""<!DOCTYPE html>
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
        .code-block {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
            overflow-x: auto;
            font-family: Consolas, Monaco, 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
        }}
        ul, ol {{
            margin-left: 25px;
            margin-bottom: 15px;
        }}
        li {{
            margin-bottom: 8px;
            line-height: 1.7;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: Consolas, Monaco, 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #999;
            font-size: 14px;
        }}
        @media (max-width: 768px) {{
            .article-container {{ padding: 20px; }}
            h1 {{ font-size: 24px; }}
            h2 {{ font-size: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="article-container">
        <h1>{title}</h1>

{content}

        <div class="footer">
            生成时间：{datetime.now().strftime('%Y-%m-%d')}<br>
            适用工具：Claude Code (claude.ai/code)
        </div>
    </div>
</body>
</html>
"""


# Convenience functions for backward compatibility
def get_image_output_dir(html_path: Path) -> Path:
    """Get image output directory for an HTML file"""
    return ArticleIllustrator(html_path).get_image_output_dir()


def extract_content_from_html(html_path: Path) -> tuple[str, str]:
    """Extract title and body content from HTML file"""
    return ArticleIllustrator(html_path).extract_content()


def insert_images_to_content(
    content: str,
    image_paths: List[str],
    num_images: int,
    html_path: Path,
    convert_tables: bool = True
) -> str:
    """Insert images into HTML content with optional table conversion"""
    illustrator = ArticleIllustrator(html_path)
    return illustrator.insert_images_to_content(content, image_paths, num_images, convert_tables)


def create_output_html(
    title: str,
    content: str,
    output_path: Path,
    html_path: Path = None
) -> Path:
    """Create output HTML file"""
    if html_path:
        illustrator = ArticleIllustrator(html_path)
        return illustrator.create_output_html(title, content, output_path)
    else:
        # Fallback for backward compatibility
        from pathlib import Path
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.8; color: #333; background: #f8f9fa; margin: 0; padding: 20px; }}
        .article-container {{ max-width: 800px; margin: 0 auto; background: white; padding: 40px 50px; border-radius: 8px; }}
        h1 {{ font-size: 28px; color: #0e639c; text-align: center; border-bottom: 3px solid #0e639c; }}
        h2 {{ font-size: 22px; color: #0e639c; margin: 40px 0 20px 0; padding-left: 15px; border-left: 5px solid #0e639c; }}
        p {{ margin-bottom: 15px; line-height: 1.8; }}
    </style>
</head>
<body>
    <div class="article-container">
        <h1>{title}</h1>
{content}
    </div>
</body>
</html>"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_path
