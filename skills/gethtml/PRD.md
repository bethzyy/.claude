# GetHTML Skill - PRD 文档

## 文档信息

| 属性 | 值 |
|------|-----|
| **名称** | gethtml |
| **版本** | v1.1.0 |
| **状态** | ✅ 已实现 |
| **入口文件** | gethtml_skill.py |
| **技术栈** | Python + Playwright + BeautifulSoup + aiohttp |
| **最后更新** | 2026-03-24 |

---

## 1. 产品概述

### 1.1 产品定位

GetHTML 是一个网页下载工具，支持完整下载网页及所有资源（CSS、JS、图片、字体）以供离线浏览。特别支持飞书文档的自动检测和处理。

### 1.2 核心价值

- **100% 免费**: 纯 Playwright 实现，无需 API
- **飞书支持**: 自动检测飞书 URL，专用下载器
- **双格式输出**: Markdown + HTML 同时生成
- **资源完整**: 自动下载所有相关资源

### 1.3 触发模式

```
"download webpage", "save page", "download article", "save website",
"下载网页", "保存网页", "下载文章", "保存网站", "下载飞书文档"
```

---

## 2. 功能需求

### F1: 网页下载

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `url` | string | 必需 | 要下载的 URL |
| `output_name` | string | 域名 | 自定义输出目录名 |
| `--wait` | string | - | 等待的 CSS 选择器 |
| `--wait-time` | int | 3000 | 额外等待时间（毫秒） |
| `--timeout` | int | 30000 | 导航超时（毫秒） |
| `--login` | flag | False | 启用登录模式 |
| `--cdp-port` | int | 9222 | Chrome CDP 端口 |

### F2: 飞书文档下载

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `--feishu-format` | choice | both | 输出格式: both/markdown/html |
| `--force-generic` | flag | False | 强制使用通用下载器 |

**支持的飞书 URL**:
- Wiki: `https://xxx.feishu.cn/wiki/...`
- Docx: `https://xxx.feishu.cn/docx/...`
- Sheets: `https://xxx.feishu.cn/sheets/...`
- Mindnote: `https://xxx.feishu.cn/mindnote/...`

### F3: 登录支持

- **CDP 模式**: 连接已登录的 Chrome 实例
- **交互式登录**: 自动打开浏览器等待登录

---

## 3. 技术架构

### 3.1 模块结构

```
gethtml/
├── gethtml_skill.py           # CLI 入口
├── base_downloader.py         # 抽象基类
├── site_router.py             # URL 路由
└── handlers/
    ├── feishu_downloader_v2.py # 飞书下载器
    └── generic_downloader.py   # 通用下载器
```

### 3.2 策略模式 + 工厂模式

```
gethtml_skill.py
    ↓
SiteRouter (URL 识别与路由)
    ↓
    ├→ FeishuDownloaderV2 (飞书专用)
    ├→ GenericDownloader (通用网页)
    └→ [Future] 其他平台...
```

---

## 4. 使用示例

### 4.1 基础下载

```bash
python gethtml/gethtml_skill.py https://example.com
```

### 4.2 飞书文档

```bash
# 自动检测
python gethtml/gethtml_skill.py https://xxx.feishu.cn/wiki/abc123

# 仅 Markdown
python gethtml/gethtml_skill.py https://xxx.feishu.cn/wiki/abc123 --feishu-format markdown
```

### 4.3 需要登录的页面

```bash
# 步骤 1：启动 Chrome CDP
chrome.exe --remote-debugging-port=9222

# 步骤 2：在 Chrome 中登录

# 步骤 3：下载
python gethtml/gethtml_skill.py https://members.example.com --login --cdp-port 9222
```

### 4.4 动态内容

```bash
python gethtml/gethtml_skill.py https://spa.example.com --wait .main-content
```

---

## 5. 输出结构

### 5.1 普通网页

```
downloads/
└── example.com/
    ├── index.html          # 主 HTML（URL 已重写）
    └── assets/
        ├── css/
        ├── js/
        ├── images/
        └── fonts/
```

### 5.2 飞书文档

```
downloads/
└── xxx.feishu.cn/
    ├── index.md           # Markdown 格式
    ├── index.html         # HTML 格式
    └── assets/            # 下载的图片
```

---

## 6. 费用说明

```
总费用：$0
├── 许可证：MIT（免费）
├── API 费用：$0（不需要）
├── 工具费用：$0（纯 Playwright）
└── 使用限制：无
```

---

## 7. 依赖项

```bash
pip install playwright beautifulsoup4 aiohttp lxml requests
playwright install chromium
```

---

## 8. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.1.0 | 2026-03-05 | 飞书文档支持 |
| v1.0.0 | 2025-03-05 | 初始版本 |

---

## 9. 相关文件

- **SKILL.md**: `.claude/skills/gethtml/SKILL.md`
- **主入口**: `gethtml/gethtml_skill.py`
- **路由器**: `gethtml/site_router.py`
- **飞书下载器**: `gethtml/handlers/feishu_downloader_v2.py`
