# Quality Reviewer Skill - PRD 文档

## 文档信息

| 属性 | 值 |
|------|-----|
| **名称** | quality-reviewer |
| **版本** | v2.1.0 |
| **状态** | ✅ 已实现 |
| **入口文件** | main.py |
| **技术栈** | Python + Playwright + BeautifulSoup |
| **最后更新** | 2026-03-24 |

---

## 1. 产品概述

### 1.1 产品定位

Quality Reviewer 是审查 Agent，负责质量检查、安全扫描（OWASP Top 10）、风险评估、代码风格审查、网页下载质量审查。

### 1.2 核心价值

- **安全扫描**: OWASP Top 10 漏洞检测
- **代码审查**: 代码风格、性能、最佳实践
- **网页测试**: Playwright 动态测试
- **风险评估**: 综合风险报告

### 1.3 触发模式

```
"review code", "check quality", "validate content", "audit code",
"审查代码", "检查质量", "验证内容", "安全扫描", "检测漏洞",
"把代码写成审查报告", "把检测结果变成报告"
```

---

## 2. 功能需求

### F1: 支持的审查类型

| 类型 | 输入格式 | 主要检查 |
|------|---------|---------|
| `code` | `{type: "code", code: "..."}` | OWASP Top 10, 漏洞扫描, 代码风格 |
| `content` | `{type: "content", content: "..."}` | 语法, 原创性, 合规性, 长度 |
| `image` | `{type: "image", images: [...]}` | 图片数量, 质量 |
| `web-download` | `{type: "web-download", html_path: "..."}` | 静态+动态测试, 对比验证 |
| `generic` | 任意格式 | 基础质量检查 |

### F2: 网页下载质量审查

**静态检查**:
- HTML 结构完整性
- CSS 资源下载率
- 图片/字体完整性

**动态测试（Playwright）**:
- 滚动功能测试（侧边栏、主页面）
- 交互元素测试（链接、按钮）
- 对比测试（原网页 vs 下载版本）
- 自动检测"下半截空白"问题

### F3: 关键检查项

| 优先级 | 检查项 | 描述 |
|--------|--------|------|
| P0 | 危险 CSS 检测 | `height: 100vh`, `overflow-y: auto !important` |
| P0 | 侧边栏滚动 | 验证可滚动到底部 |
| P1 | 内容完整度 | 与原网页相似度 ≥ 90% |
| P1 | 资源完整性 | CSS/图片/JS 下载率 ≥ 70% |

---

## 3. 技术架构

### 3.1 模块结构

```
.claude/skills/quality-reviewer/
├── main.py                    # CLI 入口
├── scripts/
│   ├── reviewer.py           # 审查逻辑
│   └── web_interaction_tester.py # Playwright 动态测试
├── test_cases/
│   └── feishu_test_cases.json # 测试用例
└── requirements.txt
```

### 3.2 审查输出

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

---

## 4. 使用示例

### 4.1 代码审查

```json
{
  "task_id": "review_001",
  "result": {
    "type": "code",
    "code": "def login(username, password): ...",
    "language": "python"
  }
}
```

### 4.2 网页下载审查

```json
{
  "task_id": "web_review_001",
  "result": {
    "type": "web-download",
    "html_path": "/path/to/downloaded.html",
    "original_url": "https://example.com",
    "assets_dir": "/path/to/assets"
  }
}
```

---

## 5. 依赖项

```bash
pip install playwright>=1.40.0 beautifulsoup4>=4.12.0 lxml>=5.0.0
playwright install chromium
```

---

## 6. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.1.0 | - | 描述格式标准化 |
| v2.0.0 | 2026-03-06 | 新增网页下载质量审查 + Playwright 动态测试 |
| v1.0.0 | - | 初始版本 - 代码/内容/图片审查 |

---

## 7. 相关文件

- **SKILL.md**: `.claude/skills/quality-reviewer/SKILL.md`
- **主入口**: `.claude/skills/quality-reviewer/main.py`
- **动态测试**: `.claude/skills/quality-reviewer/scripts/web_interaction_tester.py`
