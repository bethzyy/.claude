"""
小红书HTML发布工具 - 配置管理

Configuration management for Xiaohongshu HTML publishing tool.
"""

from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Chrome远程调试端口
CHROME_DEBUG_PORT = 9222

# 小红书发布页面URL
XIAOHONGSHU_PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish"

# 图片输出目录（相对于项目根目录）
IMAGES_OUTPUT_DIR = PROJECT_ROOT / "images"

# 默认话题标签
DEFAULT_TOPICS = ["AI", "技术分享", "干货"]

# Selenium等待时间（秒）
DEFAULT_WAIT_TIME = 3
IMAGE_UPLOAD_WAIT_TIME = 1.5

# 发布成功关键词
PUBLISH_SUCCESS_KEYWORDS = [
    "发布成功",
    "已发布",
    "success",
    "published=true"
]

# 内容最大长度
MAX_CONTENT_LENGTH = 10000

# 合集配置
COLLECTIONS = {
    "美就是意义": "非遗、景色、色彩、美学相关内容",
    "饮食养生": "吃喝、养生、食材相关内容",
    "地方风物志": "包含地域信息的内容"
}

# 设置选项
SETTINGS = {
    "allow_copy": False  # 关闭"允许正文复制"
}
