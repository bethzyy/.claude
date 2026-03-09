# -*- coding: utf-8 -*-
"""
Table to Image Converter v2.1.3
Convert HTML tables to images for Toutiao publishing

This module handles conversion of HTML <table> elements to <img> elements
to preserve formatting when publishing to Toutiao platform.

Optimizations in v2.1.3:
- Fixed table width to 600px (previously 100%) to reduce whitespace
- Increased font size to 24px (from 14px) for better readability
- Reduced padding to 8px (from 14px) to minimize empty space
- Tables are now more compact and easier to read on mobile devices

Changes in v2.1.0:
- Initial table-to-image conversion using Selenium
- Enhanced table styling with professional appearance
"""

import re
import os
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional


def capture_table_as_image(table_html: str, output_path: Path) -> bool:
    """
    Capture HTML table as screenshot image using Selenium

    Args:
        table_html: HTML string containing <table> element
        output_path: Path to save screenshot image

    Returns:
        bool: Success status
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        print("[WARNING] Selenium not installed. Falling back to html2image or skipping table conversion.")
        return False

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--window-size=1200,800')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')

    driver = None
    temp_file = None
    try:
        driver = webdriver.Chrome(options=chrome_options)

        # Create minimal HTML page with enhanced table styling
        html_page = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            margin: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Microsoft YaHei', sans-serif;
            background: white;
            padding: 20px;
        }}
        table {{
            border-collapse: collapse;
            width: 600px;
            margin: 10px auto;
            font-size: 24px;
            background: white;
        }}
        th {{
            border: 2px solid #0e639c;
            padding: 8px;
            background-color: #0e639c;
            color: white;
            text-align: left;
            font-weight: 600;
            font-size: 24px;
        }}
        td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
            vertical-align: top;
            font-size: 24px;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
    </style>
</head>
<body>{table_html}</body>
</html>"""

        # Create temporary HTML file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_page)
            temp_file = f.name

        # Load page from file
        driver.get(f"file:///{temp_file.replace(os.sep, '/')}")

        # Wait for table to load
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(('tag name', 'table'))
        )

        # Find table element and capture screenshot
        table = driver.find_element('tag name', 'table')
        table.screenshot(str(output_path))

        return True

    except Exception as e:
        print(f"[ERROR] Failed to capture table: {e}")
        return False
    finally:
        if driver:
            driver.quit()
        # Clean up temp file
        if temp_file and Path(temp_file).exists():
            try:
                Path(temp_file).unlink()
            except:
                pass


def convert_tables_to_images(content: str, output_dir: Path, html_file_path: Path = None) -> Tuple[str, List[str]]:
    """
    Convert all <table> elements to <img> elements

    Args:
        content: HTML content with tables
        output_dir: Directory to save table images
        html_file_path: Path to the HTML file (for calculating relative paths)

    Returns:
        Tuple of (modified_content, list of table_image_paths)
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("[WARNING] beautifulsoup4 not installed. Skipping table conversion.")
        return content, []

    soup = BeautifulSoup(content, 'html.parser')
    tables = soup.find_all('table')
    table_images = []

    if not tables:
        print("[INFO] No tables found in content")
        return str(soup), []

    print(f"[INFO] Found {len(tables)} table(s) to convert")

    # Calculate relative path from HTML file to images directory
    if html_file_path:
        html_parent = html_file_path.parent.resolve()
        try:
            relative_images_dir = output_dir.resolve().relative_to(html_parent)
            images_prefix = relative_images_dir.as_posix() + "/"
        except ValueError:
            # If output_dir is not under html_parent, use just filename
            images_prefix = ""
    else:
        images_prefix = ""

    for idx, table in enumerate(tables):
        # Generate table image filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"table_{idx}_{timestamp}.jpg"
        table_img_path = output_dir / filename

        # Capture table as image
        table_html = str(table)
        if capture_table_as_image(table_html, table_img_path):
            # Create img tag to replace table with correct relative path
            img_src = f"{images_prefix}{filename}"
            img_tag = f'<p style="text-align: center;"><img src="{img_src}" alt="表格 {idx + 1}" style="max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"></p><p style="text-align: center; color: #888; font-size: 13px; margin-top: 8px; margin-bottom: 20px;">表 {idx + 1}</p>'

            # Replace table with img
            table.replace_with(BeautifulSoup(img_tag, 'html.parser'))

            table_images.append(str(table_img_path))
            print(f"[INFO] Converted table {idx + 1} to image: {filename}")
        else:
            print(f"[WARNING] Failed to convert table {idx + 1}, keeping original HTML")

    return str(soup), table_images


# Convenience function for backward compatibility
def capture_table_with_html2image(table_html: str, output_path: Path) -> bool:
    """
    Alternative: Capture table using html2image library (lighter than Selenium)

    Use this if Selenium/Chrome is not available.

    Args:
        table_html: HTML string containing <table> element
        output_path: Path to save screenshot image

    Returns:
        bool: Success status
    """
    try:
        from html2image import Html2Image
    except ImportError:
        print("[WARNING] html2image not installed. Install with: pip install html2image")
        return False

    hti = Html2Image(size=(1200, 800))

    html_page = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; }}
        th {{ background-color: #0e639c; color: white; }}
    </style>
</head>
<body>{table_html}</body>
</html>"""

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        hti.screenshot(html_str=html_page, save_as=str(output_path.name), path=str(output_path.parent))
        return True
    except Exception as e:
        print(f"[ERROR] html2image failed: {e}")
        return False


def check_chrome_available() -> bool:
    """
    Check if Chrome/ChromeDriver is available for Selenium

    Returns:
        bool: True if Chrome is available
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        driver.quit()
        return True
    except Exception as e:
        print(f"[INFO] Chrome not available for table conversion: {e}")
        return False
