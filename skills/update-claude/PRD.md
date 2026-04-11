# Update Claude Skill - PRD 文档

## 文档信息

| 属性 | 值 |
|------|-----|
| **名称** | update-claude |
| **版本** | v2.0.0 |
| **状态** | ✅ 已实现 |
| **入口文件** | - |
| **技术栈** | Python |
| **最后更新** | 2026-03-24 |

---

## 1. 产品概述

### 1.1 产品定位

Update Claude 是一个 CLAUDE.md 自动更新工具，扫描项目变化并更新文档。支持选择更新主项目或任意子项目的文档。

### 1.2 核心价值

- **自动扫描**: 检测新增目录/项目、主要文件
- **多文档支持**: 可选择更新主项目或子项目
- **交互式选择**: 显示所有 CLAUDE.md 文件供选择
- **批量更新**: 支持一键更新所有文档

### 1.3 触发模式

```
"更新cc", "update cc", "cc update", "更新 CLAUDE.md",
"sync documentation", "刷新项目文档", "更新进度"
```

---

## 2. 功能需求

### F1: 文档发现

扫描项目，找到所有 CLAUDE.md 文件：
- 主项目：`MyAIProduct/CLAUDE.md`
- 子项目：`food/CLAUDE.md`, `jobMatchTool/CLAUDE.md` 等

### F2: 交互式选择

```
检测到以下 CLAUDE.md 文件：
  [1] 主项目 - MyAIProduct/CLAUDE.md
  [2] food - food/CLAUDE.md
  [3] jobMatchTool - jobMatchTool/CLAUDE.md
  ...
  [0] all - 更新所有文档

请选择要更新的文档（输入编号，默认:1）:
```

### F3: 自动检测内容

- **新项目检测**: 扫描目录下的 README.md/CLAUDE.md/package.json/requirements.txt
- **新技能检测**: 扫描 `.claude/skills/` 目录下的 SKILL.md
- **配置文件检测**: 扫描 .env.example, config.* 等

### F4: 更新规则

1. **主项目列表**: 添加检测到的新项目
2. **常用命令**: 添加新项目的启动命令
3. **全局技能**: 添加新发现的 skills
4. **版本历史**: 添加今天日期的更新记录
5. **新增章节**: 为重要的新功能添加专门章节

---

## 3. 技术架构

### 3.1 工作流程

```
1. 发现所有 CLAUDE.md 文件
2. 交互式选择要更新的文档
3. 扫描对应目录的项目结构
4. 对比选定的 CLAUDE.md
5. 生成更新建议
6. 应用更新
```

### 3.2 扫描规则

| 标记文件 | 说明 |
|----------|------|
| `README.md` | 独立项目 |
| `CLAUDE.md` | 子项目 |
| `package.json` | Node.js 项目 |
| `requirements.txt` | Python 项目 |

---

## 4. 使用示例

### 4.1 更新主项目

```
用户: 更新cc

AI: 检测到以下 CLAUDE.md 文件：
    [1] 主项目 - MyAIProduct/CLAUDE.md
    ...
    请选择要更新的文档（输入编号，默认:1）: 1

    正在更新：MyAIProduct/CLAUDE.md
    ✓ 更新版本历史
    ✓ 添加新功能说明
```

### 4.2 批量更新

```
用户: cc update

AI: 请选择要更新的文档（输入编号，默认:1）: 0

    批量更新模式
    - [1/4] MyAIProduct/CLAUDE.md... ✓
    - [2/4] food/CLAUDE.md... ✓
    - [3/4] post/CLAUDE.md... ✓
    - [4/4] jobMatchTool/CLAUDE.md... ✓

    所有文档已更新完成！
```

---

## 5. 更新内容示例

```markdown
## 检测到的变化

### 新增功能
- ✅ 图片重用优化
- ✅ 自动内容检查

### 需要更新
- 版本历史：添加 2026-03-04 条目
- 功能特性：更新说明

## 已应用更新
✓ 更新版本历史
✓ 添加新功能说明
```

---

## 6. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0.0 | 2026-03-04 | 多文档支持：选择更新主项目或子项目、交互式选择、批量更新 |
| v1.2.0 | 2026-03-04 | 快捷触发词：添加"更新cc"、"update cc" |
| v1.1.0 | - | 初始版本：自动扫描主项目变化、更新主 CLAUDE.md |

---

## 7. 注意事项

- 保留原有的格式和结构
- 不删除手动添加的内容
- 保持 Markdown 格式整洁
- 询问用户后再应用重大更改
- 更新前会显示预览

---

## 8. 相关文件

- **SKILL.md**: `.claude/skills/update-claude/SKILL.md`
