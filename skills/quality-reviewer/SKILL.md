---
name: quality-reviewer
description: 审查Agent - 负责质量检查、安全扫描（OWASP Top 10）、风险评估、代码风格审查、网页下载质量审查（含Playwright动态测试）。ALWAYS use this skill when user wants to "review code", "check quality", "validate content", "audit code", "scan for security issues", "check for vulnerabilities", "test webpage interactions", "validate download quality", "审查代码", "检查质量", "验证内容", "安全扫描", "检测漏洞", "审查网页下载", "测试网页交互", "验证下载质量", "代码审查", "质量检查", "安全审计", "漏洞检测", "把代码写成审查报告", "把检测结果变成报告", "把分析转成质量报告", "将审查结果转换为报告", "把...写成", "把...转成", "把...变成", "将...转换为", or discusses reviewing, auditing, checking quality, scanning for security issues, validating content, or transforming code/reviews into quality reports. Supports code review (OWASP Top 10 security scanning), content validation, image quality checks, web download quality assessment (with Playwright dynamic testing), AND comprehensive risk assessment. MUST trigger for ANY quality review or validation request including conversion patterns like "把 [code/review] 写成/转成/变成 [report]".
version: 2.1.0
entry_point: main.py
author: Claude Code
tags: [reviewer, agent, quality-check, security-scan, web-test, playwright]
---

## 新增功能 (v2.0.0)

### 网页下载质量审查 (web-download)

**支持动态测试** - 使用Playwright进行真实浏览器测试：
- ✅ 滚动功能测试（侧边栏、主页面）
- ✅ 交互元素测试（链接、按钮）
- ✅ 对比测试（原网页 vs 下载版本）
- ✅ 自动检测"下半截空白"问题
- ✅ P0级别危险CSS检测

**输入格式**:
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

**审查输出**:
```json
{
  "type": "web_download_review",
  "overall_score": 85,
  "approved": true,
  "static_checks": {
    "html_structure": {...},
    "custom_css": {...},
    "resources": {...}
  },
  "dynamic_checks": {
    "scrolling": {...},
    "sidebar": {...},
    "click_interactions": {...}
  },
  "comparison": {
    "text_similarity": 0.92
  },
  "lessons": {
    "critical_issues": [],
    "warnings": []
  }
}
```

**关键检查**:
1. **P0 - 危险CSS检测**: `height: 100vh`, `overflow-y: auto !important`
2. **P0 - 侧边栏滚动**: 验证可滚动到底部
3. **P1 - 内容完整度**: 与原网页相似度≥90%
4. **P1 - 资源完整性**: CSS/图片/JS下载率≥70%

---

## 支持的审查类型

| 类型 | 输入格式 | 主要检查 |
|------|---------|---------|
| `code` | `{type: "code", code: "..."}` | OWASP Top 10, 漏洞扫描, 代码风格 |
| `content` | `{type: "content", content: "..."}` | 语法, 原创性, 合规性, 长度 |
| `image` | `{type: "image", images: [...]}` | 图片数量, 质量 |
| `web-download` | `{type: "web-download", html_path: "..."}` | **NEW**: 静态+动态测试, 对比验证 |
| `generic` | 任意格式 | 基础质量检查 |

---

## 依赖项

**网页审查需要**:
```bash
pip install playwright>=1.40.0 beautifulsoup4>=4.12.0 lxml>=5.0.0
playwright install chromium
```

---

## 相关文档

- **LESSONS_LEARNED.md** - 网页下载经验教训（下半截空白等问题）
- **web_interaction_tester.py** - Playwright动态测试模块
- **test_cases/feishu_test_cases.json** - 飞书文档测试用例

---

**版本历史**:
- **v2.0.0** (2026-03-06): 新增网页下载质量审查 + Playwright动态测试
- **v1.0.0**: 初始版本 - 代码/内容/图片审查
