---
name: image-gen
description: Generate AI images from text prompts with 8-level fallback chain. ALWAYS use this skill when user wants to "generate images", "create pictures", "make AI art", "生成图片", "创建配图", "AI绘图", or discusses generating AI images from text descriptions.
version: 3.0.0
---

# AI Image Generator with 8-Level Fallback Chain

Generate high-quality AI images from text prompts using multiple image generation models with automatic fallback.

## ⚠️ CRITICAL DESIGN PRINCIPLE ⚠️

**THE 8-LEVEL FALLBACK MECHANISM IS A CORE DESIGN AND CANNOT BE CHANGED**

This skill uses an 8-level fallback chain to ensure high reliability and success rates. Any modification to remove or bypass the fallback mechanism is strictly prohibited.

### Why Fallback is Essential

1. **Reliability**: If primary API fails or quota is exhausted, automatically switch to alternatives
2. **Cost Optimization**: Try fastest options first (Gemini → CogView) before external services
3. **High Success Rate**: 8 different services ensure near-100% generation success
4. **User Experience**: No manual intervention needed - automatic failover

**Removing fallback = Breaking the skill** ❌

---

## What's New in v3.0.0

- **🏗️ Architecture Migration to Anthropic Official Standard**: Complete migration to single-location architecture
  - **NEW LOCATION**: All code now in `.claude/skills/image-gen/scripts/` (official standard)
  - **OLD LOCATION**: `skills/image-gen/` (deprecated, dual-location architecture)
  - **Backward Compatible**: Existing commands still work through wrapper script
  - **Command Change**: Use `python .claude/skills/image-gen/main.py` or just `/skill image-gen`
  - **Benefits**: Unified structure, easier maintenance, consistent with other skills
  - **Migration**: Part of global skills architecture standardization (2026-03-08)

## Command Format

```bash
python C:/D/CAIE_tool/MyAIProduct/.claude/skills/image-gen/main.py <prompts> [options]
```

## Parameters

- `prompts` (required): Comma-separated or JSON array of text prompts
- `--output-dir`: Output directory (default: current dir)
- `--style`: Style: realistic/artistic/cartoon/technical (default: realistic)
- `--count`: Images per prompt (default: 1)
- `--format`: Output format: json/text (default: text)
- `--size`: Image size: 1024x1024/2048x2048 (default: 1024x1024)

## Examples

```bash
# Single image
python .claude/skills/image-gen/main.py "A mountain landscape"

# Multiple images with JSON output
python .claude/skills/image-gen/main.py '["p1", "p2", "p3"]' --format json --style realistic

# Custom style and output directory
python .claude/skills/image-gen/main.py "futuristic city" --style artistic --output-dir ./my-images
```

---

## 8-Level Fallback Chain

### Fallback Priority (v2.1.1)

```
1. Gemini 3 Flash Image (gemini-3-flash-image) ⭐ PRIORITY
   ├─ Resolution: 1024x1024
   ├─ Provider: Google (via Antigravity)
   ├─ Speed: Fastest generation
   └─ Status: Highest quality, latest model

2. Antigravity Multi-Model (excluding Gemini)
   ├─ Flux 1.1 Pro (flux-1.1-pro)
   ├─ Flux Schnell (flux-schnell)
   ├─ Gemini 2 Flash Image (gemini-2-flash-image)
   ├─ DALL-E 3 (dall-e-3)
   ├─ Provider: Antigravity API
   └─ Status: High-quality alternatives to Gemini

3. Seedream 5.0 (doubao-seedream-5-0-260128)
   ├─ Resolution: 2048x2048
   ├─ Provider: Volcano (字节跳动)
   └─ Status: Latest version, highest resolution

4. Seedream 4.5 (doubao-seedream-4-5-251128)
   ├─ Resolution: 2048x2048
   ├─ Provider: Volcano
   └─ Status: High quality alternative

5. Seedream 4.0 (doubao-seedream-4-0-250828)
   ├─ Resolution: 2048x2048
   ├─ Provider: Volcano
   └─ Status: Stable version

6. Seedream 3.0 t2i (doubao-seedream-3-0-t2i-250415)
   ├─ Resolution: 1024x1024
   ├─ Provider: Volcano
   └─ Status: Free tier

7. CogView-3-flash (cogview-3-flash)
   ├─ Resolution: 1024x1024
   ├─ Provider: ZhipuAI (智谱AI)
   └─ Status: Reliable fallback

8. Pollinations (free public API)
   ├─ Provider: Pollinations.ai
   └─ Status: Last resort (no quota limits)
```

### What Changed in v2.1.1

- **Priority Change**: Antigravity promoted to level 2 (after Gemini), before Seedream series
- **Reason**: Antigravity provides multiple high-quality models (Flux, DALL-E) as excellent alternatives
- **Impact**: After Gemini, Antigravity models will be tried before Seedream
- **Fallback Order**: Gemini → Antigravity → Seedream 5.0/4.5/4.0/3.0 → CogView → Pollinations

### What Changed in v2.1.0

- **Priority Change**: Gemini 3 Flash Image promoted from level 5 to level 1
- **Reason**: Gemini is fastest and generates highest quality images
- **Impact**: Most images will now use Gemini instead of Seedream
- **Fallback Levels**: Increased from 7 to 8 (Gemini extracted from Antigravity)
```

### Fallback Logic

```python
def generate_image(prompt):
    for level in range(1, 9):  # 8 levels
        result = try_level(prompt, level)
        if result.success:
            return result  # Stop at first success

    # If all 8 levels fail
    return Error("All 8 fallback levels exhausted")
```

### Error Detection

Each level automatically detects and handles:
- **429 HTTP Status**: Quota exhausted → Try next level
- **Network Timeout**: Retry once → Try next level
- **API Errors**: Log error → Try next level
- **Authentication Fail**: Skip to next level

---

## Configuration

### Required Environment Variables

```bash
# Volcano / Seedream (Primary)
VOLCANO_API_KEY=your_volcano_api_key
VOLCANO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# ZhipuAI (CogView)
ZHIPU_API_KEY=your_zhipuai_api_key

# Antigravity (Optional)
ANTIGRAVITY_API_KEY=your_antigravity_api_key
ANTIGRAVITY_BASE_URL=http://127.0.0.1:8045/v1
```

### Config Loading Priority

1. Load from `post/config.py` (if available)
2. Fallback to environment variables
3. Fallback to defaults

---

## Image Specifications

| Model | Resolution | Format | Quality |
|-------|-----------|--------|---------|
| Seedream 5.0/4.5/4.0 | 2048x2048 | JPEG | 95% |
| Seedream 3.0 t2i | 1024x1024 | JPEG | 95% |
| Antigravity | 1024x1024 | JPEG | 95% |
| CogView-3-flash | 1024x1024 | JPEG | 95% |
| Pollinations | Variable | JPEG | 95% |

---

## Style Descriptions

| Style | Description | Prompt Enhancement |
|-------|-------------|-------------------|
| `realistic` | Professional photography | "realistic photography, high quality, professional lighting" |
| `artistic` | Creative and elegant | "artistic style, creative, elegant composition" |
| `cartoon` | Colorful illustration | "cartoon illustration, colorful, friendly style" |
| `technical` | Clean infographics | "technical diagram, flowchart, architecture diagram, clean infographic style" |
| `auto` | Automatic selection | "professional quality visualization" |

---

## Output Formats

### Text Format (Default)

```
[1/3] Generating image for: A mountain landscape
  [OK] Saved: img_0_20260304_120000.jpg

[2/3] Generating image for: A sunset over ocean
  [OK] Saved: img_1_20260304_120007.jpg

[3/3] Generating image for: A forest path
  [OK] Saved: img_2_20260304_120015.jpg

Generated 3/3 images in ./images/
```

### JSON Format

```json
{
  "success": true,
  "images": [
    {
      "path": "/full/path/to/img_0_20260304_120000.jpg",
      "prompt": "A mountain landscape",
      "index": 0,
      "model_used": "seedream-5-0"
    },
    {
      "path": "/full/path/to/img_1_20260304_120007.jpg",
      "prompt": "A sunset over ocean",
      "index": 1,
      "model_used": "seedream-5-0"
    },
    {
      "path": "/full/path/to/img_2_20260304_120015.jpg",
      "prompt": "A forest path",
      "index": 2,
      "model_used": "antigravity-gemini-3-flash-image"
    }
  ],
  "count": 3,
  "output_dir": "/full/path/to/images"
}
```

---

## Usage from Other Skills

### Calling via Subprocess

```python
import subprocess
import json
import sys

# Prepare prompts
prompts = ["cat", "dog", "bird"]
prompts_json = json.dumps(prompts, ensure_ascii=False)

# Run command
cmd = [
    sys.executable,
    '.claude/skills/image-gen/main.py',
    prompts_json,
    '--format', 'json',
    '--style', 'cartoon'
]

result = subprocess.run(cmd, capture_output=True, text=True)

# Parse output
if result.returncode == 0:
    output_data = json.loads(result.stdout)
    for img in output_data['images']:
        print(f"Generated: {img['path']} using {img['model_used']}")
```

### Environment Variable Transmission

```python
import os
import base64
import subprocess

# Encode prompts to avoid command-line length limits
prompts = ["prompt 1", "prompt 2", "prompt 3"]
prompts_b64 = base64.b64encode(
    json.dumps(prompts).encode('utf-8')
).decode('ascii')

env = os.environ.copy()
env['IMAGE_GEN_PROMPTS'] = prompts_b64

cmd = [
    sys.executable,
    '.claude/skills/image-gen/main.py',
    '--use-env-prompts',
    '--format', 'json'
]

result = subprocess.run(cmd, env=env, capture_output=True, text=True)
```

---

## Error Handling

### Graceful Degradation

The skill handles errors gracefully:

1. **Single Image Failure**: Continues with remaining images
2. **API Quota Exhausted**: Automatically switches to next level
3. **Network Timeout**: Retries once, then fallback
4. **Invalid Prompt**: Returns error message, continues batch

### Error Messages

```
[ERROR] [Fallback 1/7] Seedream 5.0: Quota exhausted
[INFO] [Fallback 2/7] Trying Seedream 4.5...
[OK] Generated using Seedream 4.5: img_0_20260304_120000.jpg
```

---

## Dependencies

```bash
pip install pillow requests zhipuai openai
```

---

## Version History

- **v2.0.0** (2026-03-04): **CRITICAL UPDATE - 7-LEVEL FALLBACK**
  - ⚠️ Implemented 7-level fallback chain from standalone_image_generator_v9.py
  - ⚠️ Fallback mechanism is now a CORE DESIGN PRINCIPLE
  - Added Seedream 5.0, 4.5, 4.0, 3.0 t2i support
  - Added Antigravity multi-model support
  - Added CogView-3-flash and Pollinations fallbacks
  - Removed single-model dependency
  - **BREAKING CHANGE**: Single-model approach removed

- **v1.0.0** (2026-03-04): Initial release
  - CogView-3-flash only (no fallback)
  - Basic image generation

---

## Technical Details

### Architecture

```
ImageGenerator Class
├── generate_single() - Entry point
├── _try_fallback_level() - Level dispatcher
├── Fallback Implementations:
│   ├── _try_seedream_5_0() - Level 1
│   ├── _try_seedream_4_5() - Level 2
│   ├── _try_seedream_4_0() - Level 3
│   ├── _try_seedream_3_0() - Level 4
│   ├── _try_antigravity() - Level 5
│   ├── _try_cogview() - Level 6
│   └── _try_pollinations() - Level 7
└── _download_and_save() - Common downloader
```

### API Differences

| Provider | Endpoint | Size Parameter | Notes |
|----------|----------|----------------|-------|
| Seedream | `client.images.generate()` | `"2048x2048"` | Uses `extra_body` for watermark |
| CogView | `client.images.generations()` | `"1024x1024"` | **Note**: Plural `generations` |
| Antigravity | `client.images.generate()` | `"1024x1024"` | Multi-model internal fallback |
| Pollinations | `requests.get(url)` | N/A | No client needed |

---

## ⚠️ CRITICAL REMINDERS ⚠️

1. **NEVER remove fallback mechanism** - This breaks reliability
2. **ALWAYS try all 7 levels** - Before giving up
3. **LOG every fallback attempt** - For debugging
4. **Return model_used** - For transparency
5. **Handle quota errors gracefully** - Auto-switch to next level

---

## Related Files

- **Core Logic**: `.claude/skills/image-gen/scripts/image_generator.py`
- **CLI Entry**: `.claude/skills/image-gen/main.py`
- **Reference Implementation**: `post/picture/standalone_image_generator_v9.py`
- **Configuration**: `post/config.py`

---

**Last Updated**: 2026-03-04
**Status**: Production Ready ✅
**Fallback Levels**: 7 (non-negotiable)
