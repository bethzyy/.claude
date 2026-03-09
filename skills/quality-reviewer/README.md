# Quality-Reviewer Agent - 网页交互测试能力

## 增强概述

**Version**: 2.0.0
**Release Date**: 2026-03-06
**Status**: ✅ Complete

Quality-Reviewer Agent现已支持**网页下载质量审查**，包含Playwright动态测试能力。

---

## 新增功能

### 1. 网页下载质量审查 (web-download)

**审查能力**:
- ✅ **静态分析**: HTML结构、CSS检查、资源完整性
- ✅ **动态测试**: 滚动功能、侧边栏交互、点击测试
- ✅ **对比验证**: 原网页 vs 下载版本相似度
- ✅ **经验检测**: 自动识别已知问题（下半截空白等）

**关键检查**:
1. **P0 - 危险CSS检测**: `height: 100vh`, `overflow-y: auto !important`
2. **P0 - 侧边栏滚动**: 验证可滚动到底部
3. **P1 - 内容完整度**: 与原网页相似度≥90%
4. **P1 - 资源完整性**: CSS/图片/JS下载率≥70%

---

## 核心组件

### 新增文件

| 文件 | 说明 |
|------|------|
| `web_interaction_tester.py` | Playwright动态测试模块（核心） |
| `LESSONS_LEARNED.md` | 网页下载经验教训文档 |
| `test_cases/feishu_test_cases.json` | 飞书文档测试用例 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `reviewer.py` | 添加`_review_web_download()`及相关方法 |
| `SKILL.md` | 更新至v2.0.0，添加web-download类型说明 |

---

## 使用方法

### 输入格式

```json
{
  "task_id": "web_review_001",
  "result": {
    "type": "web-download",
    "html_path": "/path/to/downloaded.html",
    "original_url": "https://example.com",
    "html_content": "<html>...</html>",
    "assets_dir": "/path/to/assets"
  }
}
```

### 审查输出

```json
{
  "type": "web_download_review",
  "overall_score": 85,
  "approved": true,
  "static_checks": {
    "html_structure": {"passed": true},
    "custom_css": {"passed": true, "p0_count": 0},
    "resources": {"passed": true}
  },
  "dynamic_checks": {
    "scrolling": {"passed": true, "scrollable": true},
    "sidebar": {"passed": true, "can_scroll_to_bottom": true},
    "click_interactions": {"passed": true}
  },
  "comparison": {
    "text_similarity": 0.92,
    "acceptable": true
  },
  "lessons": {
    "critical_issues": [],
    "warnings": []
  }
}
```

---

## 依赖项

### 必需

```bash
pip install playwright>=1.40.0 beautifulsoup4>=4.12.0 lxml>=5.0.0
playwright install chromium
```

### 可选

```bash
pip install pytest>=7.0.0  # 用于单元测试
```

---

## 测试用例

### 飞书文档测试

位于 `test_cases/feishu_test_cases.json`

**测试场景**:
1. **基础下载测试** (TC001, TC002, TC007)
2. **质量检查测试** (TC002, TC003, TC004)
3. **完整功能测试** (所有测试用例)

**运行测试**:
```bash
cd .claude/skills/quality-reviewer
python web_interaction_tester.py /path/to/downloaded.html
```

---

## 关键问题检测

### 1. "下半截空白"问题 (P0)

**检测方法**: 正则表达式搜索 `height: 100vh`

**修复建议**: 移除所有自定义CSS

**相关经验**: LESSONS_LEARNED.md #1

### 2. 侧边栏滚动失效 (P0)

**检测方法**: Playwright滚动测试

**修复建议**: 不修改overflow样式

**相关经验**: LESSONS_LEARNED.md #2

### 3. 内容不完整 (P1)

**检测方法**: 与原网页文本相似度对比

**修复建议**: 增加等待时间或使用CDP模式

**相关经验**: LESSONS_LEARNED.md #3

---

## 得分计算

| 类别 | 权重 | 说明 |
|------|------|------|
| **静态检查** | 40% | HTML结构、CSS、资源完整性 |
| **动态测试** | 30% | 滚动、侧边栏、交互测试 |
| **对比测试** | 20% | 与原网页相似度 |
| **经验检查** | 10% | 已知问题检测 |

**通过标准**:
- 总分 ≥ 70
- 无P0问题
- `custom_css`检查必须通过

---

## 架构设计

```
quality-reviewer (v2.0.0)
├── reviewer.py                    # 主审查逻辑
│   ├── _review_web_download()     # NEW: 网页下载审查
│   ├── _check_for_custom_css()    # NEW: P0 CSS检测
│   └── _calculate_web_score()     # NEW: 网页质量得分
│
├── web_interaction_tester.py      # NEW: Playwright测试模块
│   ├── test_scrolling()           # 滚动测试
│   ├── test_sidebar()             # 侧边栏测试
│   ├── test_click_interactions()  # 交互测试
│   └── compare_pages()            # 对比测试
│
├── LESSONS_LEARNED.md             # NEW: 经验教训文档
└── test_cases/
    └── feishu_test_cases.json     # NEW: 测试用例
```

---

## 复用gethtml经验

**复用的模式**:
- ✅ Playwright async/await模式
- ✅ 滚动策略（参考`_scroll_feishu_aggressively()`）
- ✅ 截图功能（视觉对比）
- ✅ CDP模式支持（未来扩展）

**代码模式**:
```python
# gethtml项目
async def download_page(self, url: str):
    self.browser = await self.playwright.chromium.launch()
    page = await self.context.new_page()
    await page.goto(url)
    # 滚动逻辑
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

# web_interaction_tester.py (复用相同模式)
async def test_scrolling(self, page: Page):
    await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
```

---

## 验证步骤

### 1. 单元测试
```bash
cd .claude/skills/quality-reviewer
python -m pytest tests/test_web_interaction.py -v
```

### 2. 集成测试 - "下半截空白"检测
```bash
# 准备测试HTML（包含问题的版本）
echo '<html><body style="height: 100vh">...</body></html>' > test_broken.html

python main.py '{"type": "web-download", "html_path": "test_broken.html"}'

# 预期: 检测到custom CSS问题，P0严重性
```

### 3. 对比测试
```bash
python main.py '{
  "type": "web-download",
  "original_url": "https://ocnzldtvkztt.feishu.cn/wiki/...",
  "html_path": "downloads/feishu_doc/index.html"
}'
```

### 4. 端到端测试
- 用已知的飞书下载测试
- 验证能自动检测常见问题
- 验证对比功能正常工作

---

## 预期效果

### 增强后的能力

1. **自动检测"下半截空白"问题** ✅
   - 检测`height: 100vh`等危险CSS模式
   - P0级别，阻止通过

2. **测试滚动功能** ✅
   - 自动滚动到底部
   - 验证内容可访问性
   - 检测滚动条是否工作

3. **对比原始网页** ✅
   - 同时打开两个页面
   - 计算相似度指标
   - 生成视觉diff截图

4. **经验学习** ✅
   - 记录已知问题模式
   - 自动检测这些问题
   - 提供具体修复建议

### 质量提升对比

| 指标 | v1.0.0 (之前) | v2.0.0 (之后) |
|------|--------------|--------------|
| **静态分析** | ✅ | ✅ |
| **动态测试** | ❌ | ✅ |
| **交互功能测试** | ❌ | ✅ |
| **常见问题检测** | ❌ | ✅ |
| **对比验证** | ❌ | ✅ |

---

## 工作量总结

| Phase | 任务 | 实际工作量 |
|-------|------|----------|
| **Phase 1** | 创建LESSONS_LEARNED.md | 5分钟 |
| **Phase 2** | 实现web_interaction_tester.py | 30分钟 |
| **Phase 3** | 集成到reviewer.py | 20分钟 |
| **Phase 4** | 设计测试用例 | 10分钟 |
| **Phase 5** | 更新文档和SKILL.md | 5分钟 |
| **总计** | | **70分钟** |

---

## 成功标准

- [x] 能自动检测"下半截空白"类型的问题
- [x] 能测试侧边栏滚动功能
- [x] 能对比原始网页和下载版本
- [x] 生成详细的审查报告
- [x] 与现有reviewer.py无缝集成
- [x] 测试执行时间 <30秒/页面

---

## 相关文档

- **gethtml/CLAUDE.md** - 下载工具完整文档
- **gethtml/LESSONS_LEARNED.md** - 下载工具开发经验
- **PLAN_COMPLETED.md** - 飞书下载测试报告

---

**最后更新**: 2026-03-06
**版本**: 2.0.0
**状态**: ✅ 完成并可用
