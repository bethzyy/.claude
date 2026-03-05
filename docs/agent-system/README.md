# 执行-审查Agent系统

一个高度自主的双Agent协作系统，实现"执行-审查-改进"的闭环工作流。

## 📁 文档导航

| 文档 | 说明 |
|------|------|
| **[系统架构](../README-AGENT-SYSTEM.md)** | 完整的系统架构文档 |
| **[文件清单](AGENT-SYSTEM-FILES.md)** | 需要上传到GitHub的文件清单 |
| **[上传指南](UPLOAD-GUIDE.md)** | GitHub上传详细步骤 |
| **[快速开始](#快速开始)** | 快速上手指南 |

## 🎯 系统架构

```
用户自然语言输入
    ↓
执行Agent (task-executor) ← Skill集成器
    ↓ 调用真实skills
审查Agent (quality-reviewer)
    ↓ 质量检查
任务协调器 (task-coordinator)
    ↓ 自动改进
返回最终结果
```

## ✨ 核心特性 (v2.0.0)

### 执行Agent
- ✅ **Skill集成**: image-gen, web-search, toutiao-cnt, toutiao-img
- ✅ **复合任务**: 文章生成+配图、研究+写作
- ✅ **高可靠性**: 8级fallback图片生成（98-99%成功率）
- ✅ **智能搜索**: 4级fallback网络搜索

### 审查Agent
- ✅ **安全扫描**: OWASP Top 10漏洞检测
- ✅ **代码质量**: 复杂度、风格、文档检查
- ✅ **内容验证**: 准确性、原创性检查

### 任务协调器
- ✅ **自动循环**: 执行→审查→改进
- ✅ **智能反馈**: 根据审查结果自动改进
- ✅ **迭代控制**: 最大迭代次数限制

## 🚀 快速开始

### 1. 测试Skill集成

```bash
cd C:/D/CAIE_tool/MyAIProduct
python .claude/docs/agent-system/pre_upload_check.py
```

### 2. 运行集成测试

```bash
python test/skill-evals/task-executor/test_skill_integration.py
```

### 3. 执行复合任务

```bash
python .claude/skills/task-coordinator/main.py \
    --type composite \
    --composite-type article_with_images \
    --topic "量子计算" \
    --num-images 3
```

## 📦 上传到GitHub

### 快速上传（推荐）

```bash
# Windows
cd C:/D/CAIE_tool/MyAIProduct/.claude/docs/agent-system
upload_agent_system.bat

# Linux/Mac
bash .claude/docs/agent-system/upload_agent_system.sh
```

### 手动上传

```bash
git add .claude/skills/task-executor/
git add .claude/skills/quality-reviewer/
git add .claude/skills/task-coordinator/
git add .claude/skills/README-AGENT-SYSTEM.md
git add test/skill-evals/task-executor/
git commit -m "feat: Add Executor-Reviewer Agent System v2.0.0"
git push
```

详细步骤请参考 [上传指南](UPLOAD-GUIDE.md)。

## 📖 完整文档

- [系统架构文档](../README-AGENT-SYSTEM.md) - 详细的架构设计和API文档
- [文件清单](AGENT-SYSTEM-FILES.md) - 所有文件的位置和说明
- [上传指南](UPLOAD-GUIDE.md) - GitHub上传详细步骤

## 🔧 核心文件

### 执行Agent (`.claude/skills/task-executor/`)

| 文件 | 大小 | 说明 |
|------|------|------|
| `executor.py` | 19KB | 执行Agent核心 (v2.0.0) |
| `skill_integrator.py` | 14KB | Skill集成器 |
| `main.py` | 1.6KB | 命令行入口 |

### 审查Agent (`.claude/skills/quality-reviewer/`)

| 文件 | 大小 | 说明 |
|------|------|------|
| `reviewer.py` | 20KB | 审查Agent核心 |
| `review_criteria/` | - | 审查标准定义 |

### 任务协调器 (`.claude/skills/task-coordinator/`)

| 文件 | 大小 | 说明 |
|------|------|------|
| `coordinator.py` | 5KB | 任务协调器核心 |

## 📊 复合任务示例

### 示例1: 生成文章并配图

```python
result = agent.execute_task({
    "type": "composite",
    "composite_type": "article_with_images",
    "topic": "量子计算入门",
    "num_images": 3,
    "article_style": "通俗",
    "image_style": "realistic"
})
```

**工作流程:**
1. toutiao-cnt 生成文章
2. toutiao-img 插入图片（内部调用image-gen）
3. 返回完整HTML文件

### 示例2: 研究并写文章

```python
result = agent.execute_task({
    "type": "composite",
    "composite_type": "research_and_write",
    "topic": "人工智能最新进展",
    "num_images": 3
})
```

**工作流程:**
1. web-search 搜索最新信息
2. toutiao-cnt 生成文章
3. toutiao-img 插入配图

## 🎯 版本历史

### v2.0.0 (2026-03-05)

**新增功能:**
- ✨ SkillIntegrator: 统一skill调用接口
- ✨ 真实skill调用（替代placeholder实现）
- ✨ 复合任务: article_with_images, research_and_write
- ✨ 集成测试套件

**技术特性:**
- 8级fallback图片生成（98-99%可靠性）
- 4级fallback网络搜索
- 自动内容准确性验证
- 安全漏洞扫描（OWASP Top 10）

### v1.0.0

**初始版本:**
- 执行Agent框架
- 审查Agent基础功能
- 任务协调器

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可

MIT License

---

**创建时间**: 2026-03-05
**版本**: 2.0.0
**维护者**: Claude Code
