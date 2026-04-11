# Video Lines Skill - PRD 文档

## 文档信息

| 属性 | 值 |
|------|-----|
| **名称** | video-lines |
| **版本** | v2.8.0 |
| **状态** | ✅ 已实现 |
| **入口文件** | main.py |
| **技术栈** | Python + ffmpeg + ZhipuAI GLM-ASR-2512 + Anthropic SDK |
| **最后更新** | 2026-03-24 |

---

## 1. 产品概述

### 1.1 产品定位

Video Lines 是一个视频台词提取工具，使用 ZhipuAI GLM-ASR-2512 进行高精度中文语音识别，支持超长视频（4-5 小时）自动分段处理。

### 1.2 核心价值

- **高精度 ASR**: GLM-ASR-2512 模型，专为中文优化
- **超长视频支持**: 自动分段，支持 4-5 小时视频
- **LLM 后处理**: 智能分段、同音字校正、标点修复
- **忠实原文模式**: 默认完全忠实于原话，不做修改

### 1.3 触发模式

```
"提取视频台词", "视频转文字", "MP4转txt", "提取视频字幕",
"视频语音转文本", "把视频台词写成文字", "把视频转成文字",
"extract video dialogue", "transcribe video"
```

---

## 2. 功能需求

### F1: 视频转录

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `video_path` | string | 必需 | 视频文件路径 |
| `-o` | string | 源目录 | 输出文件路径 |
| `--format` | choice | clean | 输出格式: clean/raw/json |
| `--no-llm` | flag | False | 跳过 LLM 后处理 |
| `--optimize` | flag | False | 启用优化模式 |

### F2: LLM 增强模式

| 模式 | 描述 |
|------|------|
| **忠实模式**（默认） | 只进行智能分段，不修改原文 |
| **优化模式**（--optimize） | 同音字校正、标点修复、专有名词修正 |

### F3: 超长视频处理

- **自动检测**: 内容超过 40,000 字符时启用分段
- **智能分段**: 按段落边界分割，不在句子中间切断
- **独立处理**: 每段独立调用 LLM
- **无缝合并**: 合并所有段落的处理结果

### F4: 幻觉防护（双层）

| 层级 | 机制 | 说明 |
|------|------|------|
| 音频层 | ffmpeg silenceremove | 裁剪末尾静音（stop_periods=-1） |
| 文本层 | XML 标签检测 | 检测 `</persisted-output>` 等模式 |

---

## 3. 技术架构

### 3.1 模块结构

```
.claude/skills/video-lines/
├── main.py                    # CLI 入口
├── scripts/
│   ├── main.py               # 主程序
│   ├── video_transcriber.py  # 转录模块
│   └── transcript_cleaner.py # 清理 + LLM 增强
├── references/                # 技术文档
└── evals/                     # 测试用例
```

### 3.2 工作流程

```
1. 提取音频（ffmpeg 16kHz mono WAV）
2. 分段音频（25 秒/段，API 限制 30 秒）
3. 转录每段（GLM-ASR-2512）
4. 清理输出（移除分隔符）
5. LLM 后处理（可选）
6. 输出转录文件
```

### 3.3 音频提取命令

```bash
ffmpeg -i video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 -y audio.wav
```

---

## 4. 使用示例

### 4.1 基础使用

```bash
# 忠实模式（默认）
python .claude/skills/video-lines/main.py video.mp4
```

### 4.2 优化模式

```bash
# 启用同音字校正、标点修复
python .claude/skills/video-lines/main.py video.mp4 --optimize
```

### 4.3 跳过 LLM 后处理

```bash
python .claude/skills/video-lines/main.py video.mp4 --no-llm
```

### 4.4 自定义输出

```bash
python .claude/skills/video-lines/main.py video.mp4 -o /custom/path/transcript.txt --format json
```

### 4.5 准确度测试

```bash
python .claude/skills/video-lines/main.py --accuracy-test mcpmark_v1
```

---

## 5. 性能指标

| 视频时长 | ASR 时间 | 含 LLM | 说明 |
|----------|----------|--------|------|
| 1 小时 | ~5-10 分钟 | ~6-12 分钟 | 单次 LLM 调用 |
| 2 小时 | ~10-20 分钟 | ~12-22 分钟 | 单次 LLM 调用 |
| 4-5 小时 | ~20-35 分钟 | ~25-45 分钟 | 自动分段（2-3 次 LLM） |

**验证数据**:
- 测试视频: 2 小时 18 分钟
- 分段数: 333 段（25 秒/段）
- 成功率: 100%
- 字符数: 39,588

---

## 6. 准确度测试

| 测试 ID | 名称 | 时长 | 最低相似度 | 最新结果 |
|---------|------|------|------------|----------|
| mcpmark_v1 | MCP Mark 培训视频 | ~70 分钟 | 85% | 87.69% |

---

## 7. 依赖项

```
zhipuai>=0.1.0
anthropic
```

**系统工具**: `ffmpeg`

---

## 8. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.8.0 | 2026-03-13 | 准确度测试集成到 evals.json |
| v2.7.0 | 2026-03-13 | 双层幻觉防护（音频层 + 文本层） |
| v2.6.0 | 2026-03-13 | 忠实原文设为默认 |
| v2.4.0 | 2026-03-09 | 智能分段处理超长视频 |
| v2.3.3 | 2026-03-09 | max_tokens 增加到 32768 |
| v2.2.0 | 2026-03-09 | LLM 后处理增强 |

---

## 9. 相关文件

- **SKILL.md**: `.claude/skills/video-lines/SKILL.md`
- **主入口**: `.claude/skills/video-lines/main.py`
- **转录模块**: `.claude/skills/video-lines/scripts/video_transcriber.py`
- **清理模块**: `.claude/skills/video-lines/scripts/transcript_cleaner.py`
- **经验教训**: `.claude/skills/video-lines/references/LESSONS_LEARNED.md`
