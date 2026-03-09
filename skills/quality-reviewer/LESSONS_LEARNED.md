# Quality-Reviewer 经验教训

本文档记录在审查过程中发现的常见问题和解决方案，帮助避免重复错误。

---

## 关键教训

### 1. 不要添加自定义CSS (P0) 🔴

**问题**: "下半截页面空白"
- **现象**: 侧边栏下半部分内容无法访问
- **用户体验**: 需要修复CSS后才能查看完整内容

**根本原因**:
```css
/* 这些CSS模式会破坏飞书文档的原始布局 */
body {
    height: 100vh;  /* ❌ 限制body高度 */
    overflow-y: auto !important;  /* ❌ 强制覆盖原始滚动行为 */
}

.wiki-ssr-container {
    max-height: 100vh;  /* ❌ 限制容器高度 */
}
```

**解决方案**:
1. ✅ **移除所有自定义CSS** - 保留原始样式
2. ✅ **让浏览器自然渲染** - 不要干预布局
3. ✅ **只修复资源路径** - 专注于资源下载，不修改样式

**检测方法**:
```python
# 检测危险CSS模式
forbidden_patterns = [
    r"height:\s*100vh",  # 会破坏飞书布局
    r"overflow-y:\s*auto\s*!important",  # 强制覆盖可能破坏原始滚动
    r"body\s*\{[^}]*max-height",  # 限制body高度
]
```

**相关文件**:
- `gethtml/handlers/feishu_downloader_v2.py` - 2026-03-05修复此问题
- `test_data/broken_feishu.html` - 问题示例

---

### 2. 必须测试滚动功能 (P0) 🔴

**问题**: 静态HTML分析无法检测滚动是否可用

**案例**: 飞书侧边栏滚动问题
- 静态分析: HTML结构完整 ✅
- 实际使用: 滚动条无法操作 ❌
- 用户影响: 目录下半部分无法访问

**解决方案**: 使用Playwright模拟真实用户滚动
```python
async def test_scrolling(self, page, selector):
    """测试元素是否可滚动"""
    element = await page.query_selector(selector)
    if not element:
        return {"scrollable": False, "reason": "Element not found"}

    # 获取滚动信息
    scroll_height = await element.evaluate("el => el.scrollHeight")
    client_height = await element.evaluate("el => el.clientHeight")

    # 尝试滚动到底部
    await element.evaluate("el => el.scrollTop = el.scrollHeight")
    await page.wait_for_timeout(500)  # 等待滚动动画

    # 验证是否可以滚动
    final_scroll_top = await element.evaluate("el => el.scrollTop")

    return {
        "scrollable": scroll_height > client_height,
        "can_reach_bottom": final_scroll_top > 0,
        "scroll_height": scroll_height,
        "client_height": client_height
    }
```

**测试用例**:
```json
{
  "test_sidebar_scrolling": {
    "description": "侧边栏可滚动到底部",
    "selector": ".wiki-ssr-sidebar__wrapper",
    "expected": {
      "scrollable": true,
      "content_at_bottom_accessible": true
    },
    "severity": "P0"
  }
}
```

---

### 3. 必须对比原始网页 (P1) 🟡

**问题**: 无对比基准无法发现质量下降

**案例**: 飞书文档下载
- 版本A (FeishuDownloaderV2): 30-40% 完整度
- 版本B (GenericDownloader): 90-95% 完整度
- **无对比时**: 两者都通过了静态HTML检查 ✅
- **有对比时**: 版本A明显质量不足 ❌

**解决方案**: 同时打开原网页和下载版本，对比关键指标
```python
async def compare_pages(self, original_url, downloaded_html):
    """对比原始网页和下载版本"""

    # 打开原网页
    page1 = await self.browser.new_page()
    await page1.goto(original_url)
    original_text = await page1.evaluate("() => document.body.innerText")

    # 打开下载版本
    page2 = await self.browser.new_page()
    await page2.goto(f"file:///{downloaded_html}")
    downloaded_text = await page2.evaluate("() => document.body.innerText")

    # 计算相似度
    similarity = self._calculate_text_similarity(original_text, downloaded_text)

    return {
        "text_similarity": similarity,
        "original_length": len(original_text),
        "downloaded_length": len(downloaded_text),
        "acceptable": similarity >= 0.90
    }
```

**对比指标**:
1. **文本相似度** (≥90%为合格)
2. **图片数量** (不应减少)
3. **布局结构** (侧边栏、主内容区)
4. **交互功能** (滚动、点击)

---

### 4. 资源完整性验证 (P1) 🟡

**问题**: 下载的HTML缺少关键资源

**常见问题**:
- ❌ CSS文件未下载 (样式丢失)
- ❌ 图片未下载 (显示alt文本)
- ❌ 字体未下载 (使用系统字体)
- ❌ JS文件未下载 (交互功能失效)

**检测方法**:
```python
def check_resource_completeness(self, result):
    """检查资源完整性"""
    html = result.get("html_content", "")
    soup = BeautifulSoup(html, 'lxml')

    # 统计资源引用
    css_links = len(soup.find_all('link', rel='stylesheet'))
    img_tags = len(soup.find_all('img'))
    script_tags = len(soup.find_all('script'))

    # 检查资源是否存在
    assets_dir = result.get("assets_dir")
    if assets_dir and Path(assets_dir).exists():
        downloaded_css = len(list(Path(assets_dir).glob("**/*.css")))
        downloaded_img = len(list(Path(assets_dir).glob("**/*.{jpg,png,gif,svg}")))
        downloaded_js = len(list(Path(assets_dir).glob("**/*.js")))
    else:
        downloaded_css = downloaded_img = downloaded_js = 0

    return {
        "css": {"expected": css_links, "downloaded": downloaded_css},
        "images": {"expected": img_tags, "downloaded": downloaded_img},
        "js": {"expected": script_tags, "downloaded": downloaded_js},
        "passed": (
            downloaded_css >= css_links * 0.9 and
            downloaded_img >= img_tags * 0.8 and
            downloaded_js >= script_tags * 0.8
        )
    }
```

---

### 5. 骨架屏（Skeleton Screen）检测 (P0) 🔴

**问题**: SPA应用（如飞书）使用占位符元素，JavaScript异步填充真实内容

**现象** (capture_and_analyze.py 测试结果):
```json
{
  "sidebar_analysis": {
    "found": true,
    "visible": false,
    "dimensions": {
      "width": 0,
      "height": 0,
      "scrollHeight": 0
    },
    "items_count": 0,
    "text_length": 0
  },
  "content_analysis": {
    "found": false
  },
  "scroll_results": [
    {"height": 650, "content_length": 0}
  ]
}
```

**根本原因**:
- 飞书使用骨架屏占位符：`<div class="wiki-ssr-sidebar__placeholder"></div>`
- HTML已下载但JavaScript未执行完成
- 页面高度650px（极小）说明内容未加载
- 滚动15次无效果（content_length=0）

**检测方法**:
```python
def detect_skeleton_screens(self, result):
    """检测骨架屏占位符"""
    html = result.get("html_content", "")

    # 检测飞书骨架屏类名
    skeleton_classes = [
        'wiki-ssr-sidebar__placeholder',
        'wiki-ssr-sidebar__placeholder',
        'skeleton',
        'placeholder',
        'loading-shelter'
    ]

    soup = BeautifulSoup(html, 'lxml')
    placeholder_count = 0

    for class_name in skeleton_classes:
        placeholders = soup.find_all(class_=class_name)
        placeholder_count += len(placeholders)

    # 检查文本内容是否为空
    text_length = len(soup.get_text(strip=True))

    # 检查页面高度是否异常小
    page_height = result.get('page_height', 0)

    return {
        "has_skeleton_screens": placeholder_count > 0,
        "placeholder_count": placeholder_count,
        "text_too_short": text_length < 500,
        "page_height_suspicious": page_height < 1000,
        "is_skeleton_content": (
            placeholder_count > 5 and
            text_length < 500 and
            page_height < 1000
        )
    }
```

**解决方案**:
1. ✅ **增加等待时间**: 20秒 → 40秒
2. ✅ **检测真实内容**: 检查非占位符文本长度
3. ✅ **验证关键元素**: 等待真实内容加载（非placeholder类）
4. ✅ **CDP模式验证**: 确认浏览器已登录并完全加载

**测试案例**:
```python
# 等待真实内容（非骨架屏）
await page.wait_for_selector(
    '.wiki-content:not(:empty)',
    timeout=30000
)

# 或者等待特定文本内容出现
await page.wait_for_function(
    """() => {
        const content = document.querySelector('.wiki-content');
        return content && content.innerText.length > 500;
    }""",
    timeout=30000
)
```

---

### 6. CDP连接状态验证 (P1) 🟡

**问题**: 连接到CDP端口成功 ≠ 页面内容已加载

**测试发现**:
```python
# CDP连接成功
browser = await p.chromium.connect_over_cdp("http://localhost:9222")
# [OK] CDP连接成功

# 但内容未加载
await page.goto(url, wait_until='domcontentloaded')
# 结果：sidebar.visible=false, content_length=0
```

**验证方法**:
```python
async def verify_cdp_content_loaded(self, page):
    """验证CDP连接后内容是否真正加载"""
    checks = {
        "cdp_connected": True,
        "page_loaded": False,
        "javascript_executed": False,
        "content_rendered": False
    }

    # 1. 检查页面URL
    url = page.url
    if url and "feishu.cn" in url:
        checks["page_loaded"] = True

    # 2. 检查JavaScript是否执行
    js_executed = await page.evaluate("""() => {
        return typeof window !== 'undefined' &&
               typeof document !== 'undefined' &&
               document.readyState === 'complete'
    }""")
    checks["javascript_executed"] = js_executed

    # 3. 检查内容是否渲染
    content_check = await page.evaluate("""() => {
        const content = document.querySelector('.wiki-content, article, main');
        return {
            found: !!content,
            has_text: content ? content.innerText.length > 100 : false,
            no_placeholders: !document.querySelector('.placeholder, .skeleton')
        }
    }""")

    checks["content_rendered"] = (
        content_check["found"] and
        content_check["has_text"] and
        content_check["no_placeholders"]
    )

    return checks
```

**解决方案**:
1. ✅ **多阶段验证**: URL → JS执行 → 内容渲染
2. ✅ **重试机制**: 检测到骨架屏时重新加载
3. ✅ **用户确认**: 提示用户手动检查浏览器

---

### 7. 等待策略优化 (P1) 🟡

**问题**: `networkidle`太严格，`domcontentloaded`太早

**测试对比**:

| 策略 | 超时时间 | 骨架屏检测 | 内容加载度 |
|------|---------|-----------|-----------|
| `networkidle` | 30s | ❌ 超时 | 0% |
| `domcontentloaded` | 60s | ⚠️ 通过 | 0% (骨架屏) |
| `commit` + 等待40s | 40s | ⚠️ 通过 | 0% (骨架屏) |
| `commit` + 等待 + 滚动15次 | 90s | ⚠️ 通过 | 0% (仍需登录) |

**优化策略**:
```python
async def smart_wait_for_content(self, page, url):
    """智能等待策略"""

    # 1. 基础加载（使用commit，最快）
    await page.goto(url, wait_until='commit', timeout=60000)

    # 2. 等待DOM结构
    await page.wait_for_load_state('domcontentloaded')

    # 3. 等待关键元素（非骨架屏）
    try:
        await page.wait_for_selector(
            '.wiki-content, article, main',
            timeout=20000
        )
    except:
        pass  # 继续尝试

    # 4. 等待真实内容（文本长度>500）
    await page.wait_for_function(
        """() => {
            const content = document.querySelector('.wiki-content, article, main');
            return content && content.innerText.length > 500;
        }""",
        timeout=30000
    )

    # 5. 激进滚动（触发懒加载）
    for i in range(10):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)

    # 6. 回到顶部
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(1000)
```

**关键指标**:
- **最小文本长度**: 500字符
- **最小页面高度**: 1000px
- **无骨架屏类**: `placeholder`, `skeleton`
- **真实内容元素**: 非空文本节点

---

### 8. 飞书文档特殊处理 (P2) 🟢

**问题**: 飞书文档的JavaScript渲染依赖

**特点**:
- 内容存储为JSON格式 (`<span data-leaf="true" data-string="true">`)
- 需要JavaScript渲染才能显示
- 离线HTML可能无法完整显示

**解决方案**:
1. **推荐方案**: 使用GenericDownloader (90-95%完整度)
   ```bash
   python gethtml_skill.py <feishu-url> --force-generic --login --cdp-port 9222
   ```

2. **文本提取方案**: 使用FeishuDownloaderV2 (30-40%完整度)
   ```bash
   python gethtml_skill.py <feishu-url> --feishu-format markdown
   ```

**质量对比**:

| Metric | Generic Downloader | FeishuDownloaderV2 |
|--------|-------------------|-------------------|
| **Layout** | ✅ Original dual-column | ❌ Single-column |
| **Left Sidebar** | ✅ Complete | ❌ Removed |
| **Resources** | ✅ 106+ files (18MB) | ⚠️ Limited |
| **Completeness** | 90-95% | 30-40% |
| **Use Case** | Offline browsing | Text extraction |

---

## 检查清单

### 下载质量审查 (Web Download Review)

**静态检查** (Static Checks):
- [ ] HTML结构完整
- [ ] 无危险CSS模式 (height: 100vh, overflow-y: auto !important)
- [ ] 资源完整性 (CSS/图片/JS)
- [ ] 文本长度合理（>500字符）
- [ ] **无骨架屏占位符** (placeholder类)
- [ ] **页面高度合理** (>1000px)

**动态测试** (Dynamic Tests):
- [ ] 侧边栏可滚动
- [ ] 内容区域可滚动
- [ ] 底部内容可访问
- [ ] 交互元素可点击
- [ ] **CDP内容已加载**（非骨架屏）
- [ ] **JavaScript已执行**（真实内容渲染）

**对比测试** (Comparison Tests):
- [ ] 文本相似度 ≥90%
- [ ] 图片数量相当
- [ ] 布局结构一致
- [ ] **无占位符残留**

---

## 常见问题快速参考

| 问题 | 检测方法 | 解决方案 |
|------|---------|---------|
| **下半截空白** | 检查`height: 100vh` | 移除自定义CSS |
| **侧边栏无法滚动** | Playwright滚动测试 | 不修改overflow样式 |
| **图片缺失** | 统计`<img>`标签 | 完善资源下载逻辑 |
| **内容不完整** | 对比原网页相似度 | 增加等待时间或CDP模式 |
| **布局破坏** | 截图对比 | 保留原始样式 |
| **骨架屏内容** | 检测placeholder类 | 等待真实内容，验证文本长度 |
| **CDP内容未加载** | 多阶段验证 | URL→JS→内容，检查非占位符 |
| **等待策略不当** | 测试不同wait参数 | commit+等待+滚动组合策略 |

---

## 相关文档

- **gethtml/CLAUDE.md** - 下载工具完整文档
- **gethtml/LESSONS_LEARNED.md** - 下载工具开发经验
- **PLAN_COMPLETED.md** - 飞书下载测试报告

---

**最后更新**: 2026-03-06
**版本**: 1.1.0
**基于**: 飞书文档下载审查经验 + 骨架屏检测经验

**更新记录**:
- **2026-03-06 v1.1.0**: 新增骨架屏检测、CDP验证、等待策略优化
- **2026-03-06 v1.0.0**: 初始版本，基于飞书下载问题总结
