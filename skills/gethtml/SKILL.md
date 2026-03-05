---
name: gethtml
description: Download complete webpages with all resources for offline browsing. Automatically detects and handles Feishu (Lark) documents with pure Playwright implementation (100% FREE, no API required). ALWAYS use this skill when user wants to "download webpage", "save page", "download article", "save website", "下载网页", "保存网页", "下载文章", "保存网站", "下载飞书文档", or discusses downloading webpages including Feishu documents.
version: 1.1.0
---

# gethtml Skill - Webpage Downloader with Feishu Support

下载完整网页及所有资源（CSS、JS、图片、字体）以供离线浏览。自动检测并处理飞书文档（纯 Playwright 实现，100% 免费，无需 API）。

## ⭐ 新功能 v1.1.0

- ✨ **飞书文档智能检测**：自动识别飞书 URL
- ✨ **纯 Playwright 实现**：100% 免费，无需任何 API
- ✨ **双格式输出**：同时生成 Markdown 和 HTML
- ✨ **图片自动下载**：自动下载并替换为本地路径
- ✨ **可扩展架构**：轻松添加更多网站支持

---

## 版本

**v1.1.0** (2026-03-05) - 飞书文档支持

---

## 命令格式

```bash
python C:/D/CAIE_tool/MyAIProduct/gethtml/gethtml_skill.py <url> [output_name] [options]
```

---

## 参数

### 位置参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `url` | string | ✅ | 要下载的 URL（支持普通网页和飞书文档） |
| `output_name` | string | ❌ | 自定义输出目录名（默认：域名） |

### 选项参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `--wait` | string | - | 等待的 CSS 选择器（用于动态内容） |
| `--wait-time` | int | 3000 | 额外等待时间（毫秒） |
| `--timeout` | int | 30000 | 导航超时时间（毫秒） |
| `--headless` | flag | True | 无头模式运行浏览器 |
| `--no-headless` | flag | - | 有头模式运行浏览器（调试用） |
| `--login` | flag | False | 启用登录模式 |
| `--cdp-port` | int | 9222 | Chrome DevTools Protocol 端口 |
| `--interactive` | flag | False | 交互式登录模式 |
| `--output-dir` | string | downloads | 基础输出目录 |
| `--feishu-format` | choice | both | 飞书输出格式：both\|markdown\|html |
| `--force-generic` | flag | False | 强制使用通用下载器（忽略飞书检测） |
| `--verbose, -v` | flag | False | 详细输出 |

---

## 使用示例

### 基础下载（普通网页）

```bash
# 下载普通网页
python gethtml/gethtml_skill.py https://example.com

# 自定义输出目录名
python gethtml/gethtml_skill.py https://example.com my_saved_page
```

### 飞书文档下载（自动检测）

```bash
# 下载飞书 Wiki（自动检测并使用专用下载器）
python gethtml/gethtml_skill.py https://xxx.feishu.cn/wiki/abc123

# 下载飞书 Docx
python gethtml/gethtml_skill.py https://xxx.feishu.cn/docx/def456

# 下载飞书表格
python gethtml/gethtml_skill.py https://xxx.feishu.cn/sheets/sheet789
```

### 飞书文档 - 格式控制

```bash
# 默认：同时输出 Markdown 和 HTML
python gethtml/gethtml_skill.py https://xxx.feishu.cn/wiki/abc123

# 仅输出 Markdown
python gethtml/gethtml_skill.py https://xxx.feishu.cn/wiki/abc123 --feishu-format markdown

# 仅输出 HTML
python gethtml/gethtml_skill.py https://xxx.feishu.cn/wiki/abc123 --feishu-format html
```

### 动态内容页面

```bash
# 等待特定元素加载
python gethtml/gethtml_skill.py https://spa.example.com --wait .main-content

# 等待更长时间
python gethtml/gethtml_skill.py https://slow-loading.com --wait-time 10000
```

### 需要登录的页面

```bash
# 步骤 1：启动 Chrome CDP
chrome.exe --remote-debugging-port=9222

# 步骤 2：在 Chrome 中登录网站

# 步骤 3：下载页面
python gethtml/gethtml_skill.py https://members.example.com/dashboard --login --cdp-port 9222

# 或使用交互式登录模式
python gethtml/gethtml_skill.py https://example.com/members --login --interactive
```

### 调试模式

```bash
# 显示浏览器窗口（调试用）
python gethtml/gethtml_skill.py https://example.com --no-headless

# 详细输出
python gethtml/gethtml_skill.py https://example.com --verbose
```

---

## 支持的 URL 类型

### 普通网页

所有公开可访问的网页。

### 飞书文档（自动检测）

| 类型 | URL 模式 | 说明 |
|------|----------|------|
| **Wiki** | `https://xxx.feishu.cn/wiki/...` | 飞书知识库 |
| **Docx** | `https://xxx.feishu.cn/docx/...` | 飞书文档 |
| **Sheets** | `https://xxx.feishu.cn/sheets/...` | 飞书表格 |
| **Mindnote** | `https://xxx.feishu.cn/mindnote/...` | 飞书思维导图 |

---

## 输出结构

### 普通网页

```
downloads/
└── example.com/
    ├── index.html          # 主 HTML（URL 已重写）
    └── assets/
        ├── css/            # 样式表
        ├── js/             # JavaScript 文件
        ├── images/         # 图片
        └── fonts/          # 字体
```

### 飞书文档

```
downloads/
└── xxx.feishu.cn/
    ├── index.md           # Markdown 格式
    ├── index.html         # HTML 格式（带样式）
    └── assets/            # 下载的图片
        ├── img_001.jpg
        ├── img_002.png
        └── ...
```

---

## 💰 费用说明

### 完全免费 ⭐

```
总费用：$0
├── 许可证：MIT（免费）
├── API 费用：$0（不需要）
├── 工具费用：$0（纯 Playwright）
├── 申请费用：$0（无需申请）
└── 使用限制：无
```

### 飞书文档下载

- ✅ 完全免费
- ✅ 无需 API key
- ✅ 无需第三方工具
- ✅ 纯 Playwright 实现
- ✅ 零安装成本

---

## 架构设计

### 策略模式 + 工厂模式

```
gethtml_skill.py (CLI 入口)
    ↓
SiteRouter (URL 识别与路由)
    ↓
    ├→ FeishuDownloaderV2 (飞书专用 - 纯 Playwright)
    ├→ GenericDownloader (通用网页 - Playwright)
    └→ [Future] 其他平台...
```

### 组件

| 组件 | 文件 | 职责 |
|------|------|------|
| **BaseDownloader** | `base_downloader.py` | 抽象基类 |
| **SiteRouter** | `site_router.py` | URL 路由 |
| **FeishuDownloaderV2** | `handlers/feishu_downloader_v2.py` | 飞书下载器 |
| **GenericDownloader** | `handlers/generic_downloader.py` | 通用下载器 |

---

## 技术栈

- **Python 3.8+**
- **Playwright** - 浏览器自动化
- **BeautifulSoup4** - HTML 解析
- **aiohttp** - 异步图片下载
- **lxml** - XML/HTML 解析

---

## 依赖安装

```bash
pip install playwright beautifulsoup4 aiohttp lxml requests
playwright install chromium
```

---

## 测试

### 运行测试

```bash
cd gethtml

# 简单测试
python test_feishu_simple.py

# 单元测试
python test/test_feishu_downloader.py

# URL 检测演示
python demo_url_detection.py
```

### 测试结果

```
[OK] URL 检测测试完成
[OK] 初始化测试完成
[OK] 模拟下载测试完成
[OK] Markdown 生成测试完成
[OK] 所有测试完成
```

---

## 注意事项

### 通用事项

1. **CORS 限制**：部分第三方资源可能因 CORS 限制无法下载
2. **动态内容**：捕获完整 HTML 快照，包括懒加载内容
3. **网络连接**：需要稳定的网络连接
4. **文件编码**：Windows 控制台可能显示乱码，但文件保存正确

### 飞书文档

1. **访问权限**：需要有权限访问该文档（就像在浏览器中打开一样）
2. **登录状态**：私密文档需要在浏览器中先登录
3. **图片下载**：图片会自动下载到 `assets/` 目录
4. **URL 检测**：自动检测飞书 URL，无需手动指定

---

## 相关文件

### 核心实现

- **主入口**: `gethtml/gethtml_skill.py`
- **基类**: `gethtml/base_downloader.py`
- **路由器**: `gethtml/site_router.py`
- **飞书下载器**: `gethtml/handlers/feishu_downloader_v2.py`
- **通用下载器**: `gethtml/handlers/generic_downloader.py`

### 文档

- **快速开始**: `gethtml/QUICK_START.md`
- **免费说明**: `gethtml/README_FREE.md`
- **完整指南**: `gethtml/FEISHU_GUIDE.md`
- **实施完成**: `gethtml/IMPLEMENTATION_COMPLETE.md`

### 测试

- **单元测试**: `gethtml/test/test_feishu_downloader.py`
- **简单测试**: `gethtml/test_feishu_simple.py`
- **URL 演示**: `gethtml/demo_url_detection.py`

---

## 版本历史

### v1.1.0 (2026-03-05) - 飞书文档支持 ⭐

**新功能**：
- ✨ 飞书文档自动检测和路由
- ✨ 纯 Playwright 实现（100% 免费）
- ✨ Markdown + HTML 双格式输出
- ✨ 图片自动下载
- ✨ 可扩展架构（BaseDownloader + SiteRouter）
- ✨ 完整的测试和文档

**改进**：
- 📝 完善的使用文档
- 🧪 完整的单元测试
- 🔧 向后兼容所有 v1.0.0 功能

### v1.0.0 (2025-03-05) - 初始版本

- 通用网页下载
- CDP 登录支持
- 资源下载和 URL 重写

---

## ⚠️ 重要说明

1. **100% 免费**：无任何费用、API、申请或第三方工具
2. **自动检测**：飞书 URL 自动识别，无需手动指定
3. **向后兼容**：所有 v1.0.0 功能完全保留
4. **开箱即用**：零安装，零配置
5. **可扩展**：轻松添加更多网站支持

---

**最后更新**: 2026-03-05
**状态**: 生产就绪 ✅
**飞书支持**: 纯 Playwright（免费）
**总费用**: $0（100% 免费）
