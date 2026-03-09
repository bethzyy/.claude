---
name: video-lines
description: Extract clean dialogue and transcript text from MP4 videos using AI speech recognition. ALWAYS use this skill when the user wants to "提取视频台词", "视频转文字", "MP4转txt", "提取视频字幕", "视频语音转文本", "把视频台词写成文字", "把视频转成文字", "extract video dialogue", "transcribe video", "convert video to text", "video speech to text", "extract video subtitles", "get video transcript", "video to text", or discusses extracting spoken content, dialogue, conversation, or speech from video files (MP4, AVI, MOV, etc.). Even if the user doesn't explicitly ask for a "skill" or "tool", if they need to get spoken words from a video file, use this skill. This skill handles long videos (2-3 hours) through automatic segmentation and uses ZhipuAI GLM-ASR-2512 for high-accuracy Chinese speech recognition.
version: 2.3.3
entry_point: main.py
author: Claude Code
tags: [video, transcription, asr, llm-enhancement, chinese]
---

## Version History

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

## Quick Start

```bash
# Basic usage (output saved to same directory as video)
python .claude/skills/video-lines/main.py video.mp4

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

| Video Duration | Estimated Time | Including LLM |
|----------------|----------------|---------------|
| 1 hour | ~5-10 min | ~6-12 min |
| 2 hours | ~10-20 min | ~12-22 min |
| 3 hours | ~15-25 min | ~17-27 min |

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
