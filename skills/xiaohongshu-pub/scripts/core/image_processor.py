"""
图片处理模块 - 处理Base64图片的解码和保存

Image processor module - Decode and save base64 images.
"""

import base64
import io
from pathlib import Path
from typing import List, Dict
from PIL import Image

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import IMAGES_OUTPUT_DIR


class ImageProcessor:
    """图片处理器"""

    def __init__(self, output_dir: Path = None):
        """
        初始化图片处理器

        Args:
            output_dir: 图片输出目录，默认为项目根目录下的images/
        """
        self.output_dir = output_dir or IMAGES_OUTPUT_DIR

    def save_base64_images(self, images: List[Dict], document_name: str) -> List[str]:
        """
        解码并保存Base64图片

        Args:
            images: 图片列表，来自HTMLExtractor
            document_name: 文档名称（用于创建子目录）

        Returns:
            保存的图片路径列表
        """
        if not images:
            return []

        # 创建输出目录
        doc_dir = self.output_dir / document_name
        doc_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []

        for img in images:
            index = img['index']
            img_format = img['format']
            base64_data = img['data']

            # 生成文件名
            filename = doc_dir / f"image_{index}.jpeg"

            try:
                # 解码base64数据
                image_data = base64.b64decode(base64_data)

                # 使用PIL验证并转换为JPEG
                image = Image.open(io.BytesIO(image_data))

                # 转换为RGB模式（如果需要）
                if image.mode != 'RGB':
                    image = image.convert('RGB')

                # 保存为JPEG格式
                image.save(filename, 'JPEG', quality=95)

                saved_paths.append(str(filename))

            except Exception as e:
                print(f"  [!] 图片 {index} 解码/保存失败: {e}")
                continue

        return saved_paths

    def validate_images(self, image_paths: List[str]) -> bool:
        """
        验证图片文件是否有效

        Args:
            image_paths: 图片路径列表

        Returns:
            是否所有图片都有效
        """
        for path in image_paths:
            p = Path(path)
            if not p.exists():
                print(f"  [!] 图片不存在: {path}")
                return False

            try:
                img = Image.open(path)
                img.verify()
            except Exception as e:
                print(f"  [!] 图片无效: {path} - {e}")
                return False

        return True

    def get_image_count(self, document_name: str) -> int:
        """
        获取已保存的图片数量

        Args:
            document_name: 文档名称

        Returns:
            图片数量
        """
        doc_dir = self.output_dir / document_name
        if not doc_dir.exists():
            return 0

        # 统计image_*.jpeg文件
        image_files = list(doc_dir.glob("image_*.jpeg"))
        return len(image_files)

    def get_existing_images(self, document_name: str) -> List[str]:
        """
        获取已保存的图片路径列表

        Args:
            document_name: 文档名称

        Returns:
            图片路径列表（按index排序）
        """
        doc_dir = self.output_dir / document_name
        if not doc_dir.exists():
            return []

        # 查找所有image_*.jpeg文件
        image_files = list(doc_dir.glob("image_*.jpeg"))

        # 按index排序
        image_files.sort(key=lambda p: int(p.stem.split('_')[1]))

        return [str(p) for p in image_files]
