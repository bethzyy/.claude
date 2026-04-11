---
name: video-lines
description: Extract clean dialogue and transcript text from MP4 videos using AI speech recognition. ALWAYS use this skill when the user wants to "提取视频台词", "视频转文字", "MP4转txt", "提取视频字幕", "视频语音转文本", "把视频台词写成文字", "把视频转成文字", "extract video dialogue", "transcribe video", "convert video to text", "video speech to text", "extract video subtitles", "get video transcript", "video to text", "运行准确度测试", "run accuracy test", "test accuracy", "验证转录准确度", or discusses extracting spoken content, dialogue, conversation, or speech from video files (MP4, AVI, MOV, etc.). Even if the user doesn't explicitly ask for a "skill" or "tool", if they need to get spoken words from a video file, use this skill. This skill handles long videos (1-5 hours) through automatic segmentation and uses ZhipuAI GLM-ASR-2512 for high-accuracy Chinese speech recognition. Supports ultra-long videos (4-5 hours) with smart chunking for LLM post-processing.
version: 2.8.0
entry_point: main.py
author: Claude Code
tags: [video, transcription, asr, llm-enhancement, chinese]
---

## Version History

- **v2.8.0** (2026-03-13): 准确度测试集成到 evals.json
  - 添加 `--accuracy-test` 参数支持
  - evals.json 添加 ID 11 准确度测试用例
  - skill-creator 可通过 evals.json 触发准确度测试
  - description 添加准确度测试触发词
- **v2.7.0** (2026-03-13): 音频级别幻觉防护（双层防护架构）
  - **音频层**：使用 ffmpeg `silenceremove` 滤镜裁剪末尾静音，参数 `stop_periods=-1`
  - **文本层**：检测末尾的 XML 标签模式（如 `</persisted-output>`），仅移除连续出现的幻觉
  - 移除不可靠的结束语模式匹配
  - 保留改进的分段提示词（段落长度：3-5句，最长10句）
  - 详细开发经验：`references/LESSONS_LEARNED_V2.7.0.md`
- **v2.6.0** (2026-03-13): 忠实原文设为默认
- **v2.6.0** (2026-03-13): 忠实原文设为默认
  - `faithful` 模式现在为默认行为
  - 新增 `--optimize` 参数：启用优化模式（同音字校正、标点修复等）
  - 默认输出完全忠实于原话，只做智能分段
- **v2.5.0** (2026-03-12): 忠实原文模式
  - 新增 `--faithful` 参数：只进行智能分段，不修改原文内容
  - 适用于需要完全忠实于原话的场景
- **v2.4.0** (2026-03-09): 智能分段处理超长视频
  - 新增自动检测：内容超过 40,000 字符时自动启用分段模式
  - 智能分段：按段落边界分割，不在句子中间切断
  - 独立处理：每段独立调用 LLM 增强
  - 无缝合并：合并所有段落的处理结果
  - 支持 4-5 小时超长视频（80K+ 字符）
- **v2.3.3** (2026-03-09): 修复长文本输出截断问题
  - 将 `max_tokens` 从 8192 增加到 32768
  - 支持约 30K-60K 中文字符的长视频转录
- **v2.3.2** (2026-03-09): 使用 Anthropic SDK 支持 GLM Coding Plan
  - 改用 `anthropic` SDK 而非 `requests` 直接调用
  - Base URL: `https://open.bigmodel.cn/api/anthropic`
  - 支持 Coding Plan 套餐的配额
- **v2.3.1** (2026-03-09): 默认模型改为 glm-4.7
- **v2.3.0** (2026-03-09): LLM 后处理改用 Anthropic 兼容接口
  - `TranscriptEnhancer` 改用 `https://open.bigmodel.cn/api/anthropic/v1/messages` 端点
  - 移除对 `zhipuai` SDK 的 LLM 调用依赖（ASR 仍需 SDK）
  - API Key 从环境变量读取，不硬编码
- **v2.2.0** (2026-03-09): LLM 后处理增强
  - 新增 `TranscriptEnhancer` 类，实现智能分段、同音字校正、标点修复、专有名词修正
  - 新增 `--no-llm` 和 `--llm-model` 参数
  - 默认启用 LLM 后处理（使用 `--no-llm` 跳过）
- **v2.1.0** (2026-03-09): 输出路径改进
  - 默认将台词文件输出到源视频所在目录
- **v2.0.0** (2026-03-08): skill-creator 完全重新生成 + Anthropic 官方标准架构
- **v1.0.0** (2026-03-08): 初始版本

---

# Video Lines Skill - Extract Dialogue from Videos

Extract spoken dialogue and transcript text from MP4 videos using ZhipuAI GLM-ASR-2512 speech recognition with automatic segmentation for long videos.

## When to Use

Use this skill whenever the user needs to:
- Extract dialogue, conversation, or speech from a video file
- Transcribe video content to text
- Create subtitles or captions from video
- Convert courseware, lectures, or meeting recordings to text
- Get searchable text from video content

**Common triggers**:
- "提取这个视频的台词"
- "把视频转成文字"
- "transcribe the video"
- "get the dialogue from this recording"

## What This Skill Does

This skill performs a complete video-to-text workflow:

1. **Extract audio** from the video file using ffmpeg (16kHz mono WAV)
2. **Segment audio** into 25-second chunks (API limit is 30 seconds)
3. **Transcribe each segment** using ZhipuAI GLM-ASR-2512
4. **Clean the output** by removing separators and markers
5. **LLM post-processing** for intelligent enhancement (default: enabled):
   - Smart paragraph segmentation by semantic meaning
   - Homophone correction based on context
   - Punctuation restoration
   - Proper noun capitalization (GitHub, Markdown, VS Code, AI, etc.)
   - **Auto-chunking for ultra-long videos** (4-5 hours, 80K+ chars):
     - Automatically detects when content exceeds 40,000 characters
     - Splits at paragraph boundaries (no mid-sentence cuts)
     - Processes each chunk independently
     - Merges results seamlessly

## LLM Enhancement Modes

### Faithful Mode (default)
Only performs intelligent segmentation, keeping original text completely unchanged.
This is now the default behavior since v2.6.0.
Use when you need the transcript to be **100% faithful to the original speech**.

```bash
# Default: faithful mode (verbatim transcripts)
python .claude/skills/video-lines/main.py video.mp4
```

### Optimization Mode (`--optimize`)
Applies intelligent optimizations:
- Smart paragraph segmentation
- Homophone correction (e.g., "人需" → "仍需")
- Punctuation restoration
- Proper noun capitalization

```bash
# Enable optimization mode
python .claude/skills/video-lines/main.py video.mp4 --optimize
```

## Quick Start

```bash
# Basic usage - faithful mode (default since v2.6.0)
python .claude/skills/video-lines/main.py video.mp4

# Optimization mode: enable homophone correction, punctuation fixes, etc.
python .claude/skills/video-lines/main.py video.mp4 --optimize

# Skip LLM post-processing (use basic cleaning only)
python .claude/skills/video-lines/main.py video.mp4 --no-llm

# Specify LLM model
python .claude/skills/video-lines/main.py video.mp4 --llm-model glm-4-flash

# Specify custom output file
python .claude/skills/video-lines/main.py video.mp4 -o /custom/path/transcript.txt

# Raw format (with segment markers)
python .claude/skills/video-lines/main.py video.mp4 --format raw

# JSON output
python .claude/skills/video-lines/main.py video.mp4 --json

# Run accuracy test
python .claude/skills/video-lines/main.py --accuracy-test mcpmark_v1
```

## Architecture

This skill follows **Anthropic's official standard architecture**:

```
.claude/skills/video-lines/      # Official standard location
├── SKILL.md                     # This file (skill metadata)
├── main.py                      # Wrapper script (delegates to scripts/)
├── requirements.txt             # Dependencies
├── scripts/                     # Implementation code (Anthropic standard)
│   ├── main.py                 # CLI entry point
│   ├── video_transcriber.py    # Transcription module
│   └── transcript_cleaner.py   # Text cleaning + LLM enhancement
├── references/                  # Technical documentation
│   ├── CHANGELOG.md            # Version history
│   ├── IMPLEMENTATION_V2.2.0.md # Technical implementation report
│   ├── LESSONS_LEARNED.md      # Best practices and patterns
│   └── BENCHMARKS.md           # Performance metrics
└── evals/
    └── evals.json              # Test cases (10 scenarios)
```

## Implementation Details

### Audio Extraction

```bash
ffmpeg -i video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 -y audio.wav
```

### Transcription

```python
from zhipuai import ZhipuAI

client = ZhipuAI(api_key=os.environ.get("ZHIPU_API_KEY"))
response = client.audio.transcriptions.create(
    model="GLM-ASR-2512",
    file=audio_file
)
```

### LLM Enhancement (v2.2.0)

```python
enhancer = TranscriptEnhancer(model="glm-4-flash")
enhanced_content, stats = enhancer.enhance(cleaned_content)
```

**Enhancement features**:
- Smart paragraph segmentation
- Homophone correction (e.g., "人需" → "仍需")
- Punctuation restoration
- Proper noun capitalization

## Output Formats

### Clean Format (Default)

Pure dialogue text without any markers.

### Raw Format

Includes segment markers for debugging.

### JSON Format

```json
{
  "success": true,
  "output_file": "path/to/transcript.txt",
  "stats": {
    "total_segments": 333,
    "total_chars": 39588
  }
}
```

## Processing Time

| Video Duration | Estimated Time | Including LLM | Notes |
|----------------|----------------|---------------|-------|
| 1 hour | ~5-10 min | ~6-12 min | Single LLM call |
| 2 hours | ~10-20 min | ~12-22 min | Single LLM call |
| 3 hours | ~15-25 min | ~17-27 min | Single LLM call |
| 4-5 hours | ~20-35 min | ~25-45 min | Auto chunking (2-3 LLM calls) |

## Error Handling

- **Missing API key**: Prompt user to set `ZHIPU_API_KEY`
- **ffmpeg not found**: Auto-detect from multiple paths
- **Segment failures**: Automatic retry (up to 3 attempts)
- **LLM failures**: Graceful fallback to basic cleaning

## Dependencies

- Python packages: `zhipuai>=0.1.0`
- System tools: `ffmpeg`

## References

For detailed technical information, see the `references/` directory:

| Document | Description |
|----------|-------------|
| **[CHANGELOG.md](references/CHANGELOG.md)** | Complete version history |
| **[IMPLEMENTATION_V2.2.0.md](references/IMPLEMENTATION_V2.2.0.md)** | Technical implementation report for v2.2.0 |
| **[LESSONS_LEARNED.md](references/LESSONS_LEARNED.md)** | Best practices and patterns |
| **[BENCHMARKS.md](references/BENCHMARKS.md)** | Performance metrics and comparisons |

## Verified Performance

**Test Data**:
- Video: 2 hours 18 minutes
- Segments: 333 (25 seconds each)
- Success rate: 100%
- Characters: 39,588
- Processing: ~20 min total (ASR + LLM enhancement)

## Accuracy Tests

### Overview

准确度测试用于验证转录输出与已知基准的相似度，确保修改后准确度不会下降。

### Test Structure

```
evals/
├── evals.json              # 触发测试 (10 scenarios)
├── accuracy_tests.json     # 准确度测试配置
└── benchmarks/             # 基准文件目录
    └── mcpmark/
        └── benchmark.txt   # 真实台词基准
```

### Available Tests

| Test ID | Name | Duration | Min Similarity | Last Result |
|---------|------|----------|----------------|-------------|
| mcpmark_v1 | MCP Mark 培训视频 | ~70 min | 85% | 87.69% |

### Running Accuracy Tests

```bash
# 列出所有可用测试
python .claude/skills/video-lines/scripts/run_accuracy_test.py --list

# 运行特定测试
python .claude/skills/video-lines/scripts/run_accuracy_test.py mcpmark_v1

# 运行所有测试
python .claude/skills/video-lines/scripts/run_accuracy_test.py --all
```

### Test Metrics

- **min_similarity**: 最低通过阈值 (85%)
- **target_similarity**: 目标相似度 (88%)
- **计算方法**: 去除空白字符后的字符级相似度 (difflib.SequenceMatcher)
