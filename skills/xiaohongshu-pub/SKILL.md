---
name: xiaohongshu-pub
description: Publish HTML articles to Xiaohongshu (Little Red Book). ALWAYS use this skill when user wants to "publish to xiaohongshu", "发布到小红书", "把...发布到小红书", "小红书发布", "将...发布到小红书", "把...发到小红书", "小红书发布工具", or discusses publishing content to 小红书 (Little Red Book) platform. Automatically extracts title, content, and base64 images from HTML files using BeautifulSoup, then publishes via Chrome remote debugging with Selenium automation. Handles the complete workflow: HTML parsing → base64 image extraction → Chrome connection → tab clicking → image uploading → content filling → publishing → validation. MUST trigger for ANY Xiaohongshu publishing task including "把 [html_file] 发布到小红书", "将 [article] 发布到小红书" patterns. Supports automatic content extraction from HTML, image reuse detection, and publish status validation.
version: 2.0.0
---

# 小红书HTML发布工具 (Xiaohongshu Publisher)

自动将HTML文章发布到小红书平台。

## 使用方法

在Claude Code对话中：

```
你: 把这篇文章发布到小红书
你: 将 article.html 发布到小红书
你: 发布到小红书 article.html
```

## 前置要求

1. **Chrome远程调试模式启动**：
   ```bash
   chrome.exe --remote-debugging-port=9222
   ```

2. **已在Chrome中登录小红书**

## 功能特性

- ✅ **自动提取内容**：从HTML提取标题、正文、base64图片
- ✅ **文案检查**：自动保存文案到txt文档，显示预览供检查
- ✅ **Chrome自动化**：连接已登录的Chrome，无需重复登录
- ✅ **智能发布**：自动点击"上传图文"、上传图片、填写内容
- ✅ **状态验证**：验证发布成功并返回笔记链接
- ✅ **图片重用**：自动检测并重用已保存的图片

## 版本历史

- **v2.0.0** (2026-03-08): 架构迁移到Anthropic官方标准 🏗️
  - **新位置**: 所有代码现在在 `.claude/skills/xiaohongshu-pub/scripts/` (官方标准)
  - **旧位置**: `skills/xiaohongshu-pub/` (已弃用，双位置架构)
  - **向后兼容**: 现有命令通过包装脚本继续工作
  - **命令变更**: 使用 `python .claude/skills/xiaohongshu-pub/main.py` 或直接 `/skill xiaohongshu-pub`
  - **优势**: 统一结构、更易维护、与其他技能一致
  - **迁移**: 全局技能架构标准化的一部分 (2026-03-08)

- **v1.1.0** (2026-03-04): 文案检查 + 开关定位改进
  - ✨ 新增：提取文案后自动保存到txt文档
  - ✨ 新增：在发布前显示文案预览（标题、正文分段、话题、图片信息）
  - 🐛 修复："允许正文复制"开关定位改为优先查找左侧（之前是右侧）
  - 📝 改进：txt文件保存到 `test/temp/` 目录，文件名包含时间戳
  - 📝 改进：正文预览显示前5段，超过5段提示查看txt文件

- **v1.0.0**: 初始版本
  - HTML内容提取
  - Base64图片处理
  - Selenium自动化发布
  - 发布状态验证
