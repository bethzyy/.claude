# Agent Smith - Project Knowledge Base

## Job Search Suite

### jobMatchTool (v2.4.4)
- **技术栈**: Python 3.11+, ZhipuAI GLM-4.6, PyPDF2
- **核心功能**: AI 驱动的简历-JD 匹配（6 层评分体系）
- **技术亮点**:
  - 50-70x 缓存提速（MD5-based）
  - 支持 8 大招聘平台
  - EXE 打包（112MB）
- **API Key 问题**: ✅ 已解决（用户可提供）
- **技术可行性**: 10/10
- **市场定位**: 蓝海市场（142 个产品中 0 竞品）

### JobSearchTool (v1.5.5)
- **技术栈**: Python 3.8+, Selenium 4.15+, Tkinter
- **核心功能**: 多平台职位爬虫（6 大中国招聘平台）
- **技术亮点**:
  - Magic Mode 反检测
  - EXE 打包（35MB）
  - 无 AI API 依赖
- **法律风险**: 🔴 高（爬虫可能违反 ToS）
- **推荐度**: 🚫 不推荐单独上架

## MultiCC

- **技术栈**: Electron, React, TypeScript
- **核心功能**: 多窗口 Claude Code 管理器
- **技术亮点**:
  - EXE 就绪
  - 开发者工具定位
  - 无外部服务依赖
- **法律风险**: 🟢 无风险
- **推荐度**: ⭐⭐⭐⭐⭐ 第一优先级

## Image Generation Tools

### image-gen (v2.0.0)
- **技术栈**: Python, 多模型 API（8 级 fallback）
- **核心功能**: AI 图片生成，98-99% 可靠性
- **技术亮点**:
  - 8 级 fallback 链（Seedream 5.0 → ... → Pollinations）
  - 模块化设计
  - 多风格支持（realistic, artistic, cartoon）
- **市场定位**: 红海市场（71 个竞品，50%）
- **差异化**: "The Most Stable AI Image Generator"
- **待确认**: MuleRun 模型支持范围

### toutiao-img (v2.1.5)
- **技术栈**: Python, 委托 image-gen
- **核心功能**: 头条文章插图生成
- **技术亮点**:
  - 表格转图片（Selenium）
  - 上下文感知 prompts
  - 智能图片复用
- **依赖**: 完全依赖 image-gen

## Web Search

### web-search (v2.1.0)
- **技术栈**: Python, 多搜索源
- **核心功能**: 4 级 fallback 搜索
- **Fallback 链**: MCP WebSearch → Tavily → DuckDuckGo → AI Knowledge
- **技术亮点**:
  - 智能环境检测（CLI vs Skill）
  - 50-70x 缓存提速
  - 透明日志

## Food Recommendation

### food (v93.5)
- **技术栈**: HTML/CSS/JS, ZhipuAI GLM-4.7
- **核心功能**: 基于节气的中式食疗推荐
- **技术亮点**:
  - 玻璃拟态设计
  - 完整 i18n 系统（zh/en）
  - 无服务器依赖
- **市场定位**: 中文垂直市场
- **文化壁垒**: 高（难以国际化）

## Utility Tools

### gethtml
- **技术栈**: Python, Playwright
- **核心功能**: 网页完整下载（含 CSS, 图片, 字体）
- **特色**: 支持 Feishu 文档下载
- **法律风险**: 🔴 高（版权问题）
- **建议**: 开源免费，明确免责声明

### GitTool
- **技术栈**: Python
- **核心功能**: Git 工作流自动化
- **市场定位**: 小众市场

## Platform Research

### MuleRun Analysis (142 Agents)

**类别分布**:
- Image Generation: 71 (50%) - 红海
- Chat & Writing: 29 (20%) - 竞争激烈
- Developer Tools: 18 (13%) - 中等竞争
- **Job Search: 0 (0%) - 蓝海** 🌊

**定价策略**:
- 一次性: $5-99（最常见）
- 订阅制: $5-49/月
- 按量计费: $0.01-0.50/次

**技术要求**:
- EXE 支持（桌面工具）
- API 包装（AI 服务）
- Skill 格式（Claude Code 集成）

---

**最后更新**: 2026-03-06
**维护者**: Agent Smith (CTO)
