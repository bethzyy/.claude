# Changelog

All notable changes to the video-lines skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-03-09

### Added
- **LLM Post-Processing**: Added `TranscriptEnhancer` class for intelligent transcription enhancement
  - Smart paragraph segmentation by semantic meaning
  - Homophone correction based on context (e.g., "人需" → "仍需", "信" → "星号")
  - Sentence boundary optimization
  - Punctuation restoration and correction
  - Proper noun capitalization fix (GitHub, Markdown, VS Code, AI, PPT, Word, etc.)
- **CLI Parameters**: Added `--no-llm` flag to skip LLM post-processing
- **CLI Parameters**: Added `--llm-model` parameter to specify LLM model (default: `glm-4-flash`)

### Changed
- **Default Behavior**: LLM post-processing is now enabled by default for `clean` format output
- **Processing Time**: Added LLM enhancement time display in progress output (~80-90 seconds for 40K chars)

### Technical
- **Enhancement Prompt**: Designed 5-axis optimization prompt for consistent output
- **Error Handling**: Graceful degradation if LLM fails - falls back to basic cleaning
- **Temperature Setting**: Uses `temperature=0.3` for more consistent text enhancement

### Industry Research
- Validated approach against OpenAI Cookbook "Enhancing Whisper transcriptions"
- Confirmed ASR + LLM post-processing is industry standard (Otter.ai, Descript, Rev)

## [2.1.0] - 2026-03-09

### Added
- **Smart Output Path**: Output file now defaults to source video directory
  - Example: `/path/to/video.mp4` → `/path/to/video_transcript.txt`
  - Previous behavior: output to current working directory

### Changed
- **Path Resolution**: Output file naming logic updated for better user experience
- **Documentation**: Updated SKILL.md with new default behavior

## [2.0.0] - 2026-03-08

### Added
- **Skill-Creator Integration**: Complete code generation using skill-creator framework
- **Anthropic Official Standard**: Migrated to single-location architecture
  - Implementation: `.claude/skills/video-lines/scripts/`
  - Entry point: `.claude/skills/video-lines/main.py`
- **Test Suite**: Added 10 test cases in `evals/evals.json`

### Changed
- **Architecture Migration**: From dual-location to Anthropic official standard
  - Old: `skills/video-lines/` + `.claude/skills/video-lines/` (non-standard)
  - New: `.claude/skills/video-lines/scripts/` (official standard)
- **Version Bump**: v1.x → v2.0.0 to represent complete regeneration

### Removed
- **Old Directories**: Removed `skills/video-lines/` and old `.claude/skills/video-lines/`
- **Reference Documentation**: Removed v1.0.0 reference docs after migration

### Technical
- **Code Style**: Unified code formatting and structure
- **Documentation**: Complete rewrite of SKILL.md with new architecture details
- **Backup**: All old versions backed up to `*-backup-20260308/` directories

## [1.1.0] - 2026-03-08

### Added
- **Skill-Creator SKILL.md**: Using skill-creator optimized description
- **Test Cases**: Added trigger pattern evaluation framework

### Changed
- **Hybrid Approach**: skill-creator metadata + manual implementation code
- **Version Management**: Unified to single version for easier maintenance

## [1.0.0] - 2026-03-08

### Added
- **Initial Release**: Manual implementation of video dialogue extraction
- **Core Features**:
  - Audio extraction from MP4 videos using ffmpeg
  - Automatic segmentation (25-second chunks)
  - ZhipuAI GLM-ASR-2512 transcription
  - Basic text cleaning (removing separators, markers)
  - Dual output formats (clean/raw)
  - JSON output support
  - Automatic retry logic with exponential backoff
- **Tested**: 2 hours 18 minutes video, 333 segments, 39,588 characters

### Technical
- **Segment Duration**: 25 seconds (safe margin under 30-second API limit)
- **Retry Logic**: 3 attempts with 5s, 10s, 15s intervals
- **Processing Time**: ~10-20 minutes for 2-3 hour videos

---

## Version Summary

| Version | Date | Key Changes | Breaking Changes |
|---------|------|-------------|------------------|
| v2.2.0 | 2026-03-09 | LLM post-processing | No (use --no-llm to skip) |
| v2.1.0 | 2026-03-09 | Smart output paths | No |
| v2.0.0 | 2026-03-08 | Architecture migration | Yes (directory structure) |
| v1.1.0 | 2026-03-08 | Test framework | No |
| v1.0.0 | 2026-03-08 | Initial release | N/A |
