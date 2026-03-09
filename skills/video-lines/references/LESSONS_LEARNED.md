# Video-Lines Skill - Lessons Learned

**Version**: 2.2.0
**Last Updated**: 2026-03-09
**Purpose**: Capture best practices and avoid pitfalls for future development

---

## Priority Encoding

- **P0** (Critical): Must follow, or risk breaking core functionality
- **P1** (Important): Should follow for quality and maintainability
- **P2** (Nice to have): Consider for future improvements

---

## LLM Post-Processing Best Practices

### P0: Graceful Degradation is Non-Negotiable

**Rule**: LLM calls can and will fail. Always have a fallback path.

```python
# ✅ CORRECT: Always return a result
try:
    enhanced = self._call_llm(prompt)
    return enhanced, {"success": True}
except Exception as e:
    # Return original content on failure
    return content, {"success": False, "error": str(e)}

# ❌ WRONG: Letting exceptions propagate
try:
    enhanced = self._call_llm(prompt)
    return enhanced
except Exception as e:
    raise  # This breaks the entire workflow!
```

**Why**: API failures, network issues, rate limiting - all can happen. Users expect a result, not an error.

**Applied in**: `TranscriptEnhancer.enhance()` lines 155-165

---

### P0: Temperature Setting Matters

**Rule**: Use lower temperature for text enhancement tasks.

```python
# ✅ CORRECT: Low temperature for consistency
response = client.chat.completions.create(
    model=self.model,
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3,  # Consistent corrections
    max_tokens=8192
)

# ❌ WRONG: High temperature introduces randomness
response = client.chat.completions.create(
    model=self.model,
    messages=[{"role": "user", "content": prompt}],
    temperature=0.9,  # Unpredictable corrections
    max_tokens=8192
)
```

**Temperature Guide**:
- **0.0 - 0.3**: Text enhancement, correction, formatting (deterministic)
- **0.4 - 0.7**: General conversation, explanation (balanced)
- **0.8 - 1.0**: Creative writing, brainstorming (random)

**Applied in**: `TranscriptEnhancer._call_llm()` line 199

---

### P1: Prompt Structure is Key

**Rule**: Use structured prompts with clear sections.

```python
# ✅ CORRECT: Structured prompt with clear sections
ENHANCEMENT_PROMPT = """你是一个专业的音频转录文本编辑专家。

【优化要求】
1. 明确要求1
2. 明确要求2
3. 明确要求3

【注意事项】
- 约束1
- 约束2

【原文】
{content}

【优化后的文本】"""

# ❌ WRONG: Unstructured prompt
ENHANCEMENT_PROMPT = """请帮我优化这段文本：{content}。注意要修复错误，改善格式，保持原意，不要添加内容。"""
```

**Why**: Structured prompts are:
- Easier to maintain
- Less ambiguous for the LLM
- More consistent results
- Debuggable (can isolate sections)

**Applied in**: `TranscriptEnhancer.ENHANCEMENT_PROMPT` lines 107-125

---

### P1: Explicit Constraints Prevent Hallucination

**Rule**: Always specify what NOT to do.

```python
# ✅ CORRECT: Explicit "do not" instructions
【注意事项】
- 保持原文内容不变，只做格式和纠错处理
- 不要添加原文没有的内容
- 不要添加任何说明或解释，直接输出优化后的文本

# ❌ WRONG: No negative constraints
请优化这段文本。
```

**Why**: LLMs tend to be helpful. Without constraints, they may:
- Add content they think is missing
- Include explanatory notes
- Summarize or compress

**Applied in**: `TranscriptEnhancer.ENHANCEMENT_PROMPT` lines 117-120

---

### P1: Processing Time Transparency

**Rule**: Always show users what's happening, especially for slow operations.

```python
# ✅ CORRECT: Progress feedback
print("[INFO] Running LLM post-processing...")
# ... do work ...
print(f"  LLM enhancement complete ({processing_time_ms:.0f}ms)")

# ❌ WRONG: Silent operation
# ... do work without feedback ...
```

**Why**: Users perceive 10 seconds of silence as "hung", but "Processing (10s remaining)" as progress.

**Applied in**: `main.py` lines 197-208

---

### P2: Model Selection Should Be Configurable

**Rule**: Let users choose the LLM model.

```python
# ✅ CORRECT: Configurable model
parser.add_argument(
    "--llm-model",
    default="glm-4-flash",
    help="LLM model for post-processing (default: glm-4-flash)"
)

# ❌ WRONG: Hardcoded model
MODEL = "glm-4-flash"  # Users can't change this
```

**Why**: Different use cases need different trade-offs:
- Speed vs. Quality (glm-4-flash vs. glm-4.7)
- Cost sensitivity (smaller models for batch processing)

**Applied in**: `main.py` lines 131-135

---

## Prompt Design Patterns

### P0: Use Examples in Prompts

**Rule**: Show, don't just tell.

```python
# ✅ CORRECT: Examples included
同音字校正：根据上下文修正明显的同音字错误（如"人需说明"→"仍需说明"）

# ❌ WRONG: No examples
同音字校正：修正同音字错误。
```

**Why**: Examples reduce ambiguity by 10x.

---

### P1: Define the Role Clearly

**Rule**: Tell the LLM who it's supposed to be.

```python
# ✅ CORRECT: Role defined
你是一个专业的音频转录文本编辑专家。

# ❌ WRONG: No role definition
请优化以下文本。
```

**Why**: Role-setting primes the LLM's behavior and expectations.

**Applied in**: `TranscriptEnhancer.ENHANCEMENT_PROMPT` line 107

---

### P2: Use Delimiters for Content Sections

**Rule**: Use clear markers for where content starts/ends.

```python
# ✅ CORRECT: Clear delimiters
【原文】
{content}

【优化后的文本】

# ❌ WRONG: No delimiters
内容：{content}
优化后：
```

**Why**: Delimiters prevent the LLM from confusing instructions with content.

---

## Error Handling Patterns

### P0: Never Let One Failure Stop the Entire Pipeline

**Rule**: Partial success is better than total failure.

```python
# ✅ CORRECT: Continue on non-critical errors
try:
    enhanced_content = enhancer.enhance(content)
except Exception as e:
    print(f"[WARN] LLM enhancement failed: {e}")
    print("Using original cleaned output")
    # Continue with original content

# ❌ WRONG: Fail entire pipeline
try:
    enhanced_content = enhancer.enhance(content)
except Exception as e:
    raise  # Stops everything!
```

**Applied in**: `main.py` lines 197-214

---

### P1: Log Errors, Don't Just Show Them

**Rule**: Keep a record for debugging.

```python
# ✅ CORRECT: Detailed error info
return {
    "success": False,
    "error": str(e),
    "original_length": original_length,
    "processing_time_ms": 0
}

# ❌ WRONG: Minimal error info
return {"error": str(e)}
```

**Why**: Debugging requires context. Include:
- What failed
- What inputs were used
- How long it took
- Any other relevant state

---

## Backward Compatibility

### P0: New Features Should Be Opt-Out, Not Opt-In

**Rule**: Improve by default, allow users to revert.

```python
# ✅ CORRECT: New feature on by default
parser.add_argument(
    "--no-llm",  # Note: "no-llm" flag, not "enable-llm"
    action="store_true",
    help="Skip LLM post-processing (use basic cleaning only)"
)

# ❌ WRONG: New feature off by default
parser.add_argument(
    "--enable-llm",  # Users won't discover this
    action="store_true",
    help="Enable LLM post-processing"
)
```

**Why**: Most users won't read documentation. Default should be the best experience.

**Applied in**: `main.py` lines 125-129

---

### P1: Version Numbers Matter

**Rule**: Use semantic versioning consistently.

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes (2.0.0 → 3.0.0)
MINOR: New features, backward compatible (2.2.0 → 2.3.0)
PATCH: Bug fixes (2.2.0 → 2.2.1)
```

**Applied in**: All version numbers in SKILL.md, CHANGELOG.md

---

## Performance Considerations

### P0: Measure Before Optimizing

**Rule**: Never optimize without baseline metrics.

```python
# ✅ CORRECT: Track processing time
start_time = time.time()
# ... do work ...
processing_time = (time.time() - start_time) * 1000
stats["processing_time_ms"] = round(processing_time, 2)

# ❌ WRONG: No measurement
# ... do work ...
# No idea how long it took!
```

**Applied in**: `TranscriptEnhancer.enhance()` lines 148-167

---

### P1: Cache When Possible

**Rule**: Don't repeat expensive operations.

```python
# ✅ CORRECT: Check cache first
cache_key = hashlib.md5(content.encode()).hexdigest()
if cache_key in cache:
    return cache[cache_key]

# ❌ WRONG: Always recompute
result = expensive_operation(content)
```

**Future consideration**: Add enhancement result caching for identical content.

---

## Code Organization

### P1: Single Responsibility Classes

**Rule**: One class, one purpose.

```python
# ✅ CORRECT: Separate classes for separate concerns
class TranscriptCleaner:
    """Remove artifacts from raw ASR output."""

class TranscriptEnhancer:
    """Use LLM to enhance transcription quality."""

# ❌ WRONG: One class does everything
class TranscriptProcessor:
    """Extract, clean, AND enhance. (Too much!)"""
```

**Why**: Easier to test, maintain, and extend.

**Applied in**: `transcript_cleaner.py` lines 15-95, 95-231

---

### P2: Type Hints Are Documentation

**Rule**: Use type hints for better IDE support and self-documenting code.

```python
# ✅ CORRECT: Type hints
def enhance(self, content: str) -> Tuple[str, Dict]:
    """Enhance transcription content using LLM."""

# ❌ WRONG: No type hints
def enhance(self, content):
    """Enhance transcription content using LLM."""
```

**Applied in**: All methods in `transcript_cleaner.py`

---

## Anti-Patterns to Avoid

### ❌ Anti-Pattern: Mixing Languages in Prompts

```python
# ❌ WRONG: Mixed Chinese and English instructions
请优化文本。Do not add content.保持原意。

# ✅ CORRECT: Consistent language
请优化文本。不要添加内容。保持原意。
```

**Why**: LLMs perform better with consistent language.

---

### ❌ Anti-Pattern: Over-Constraining the LLM

```python
# ❌ WRONG: Too many constraints
【优化要求】
1. 智能分段：按语义主题划分段落，每个段落表达一个完整的意思
2. 断句优化：修复不完整的句子，确保句子通顺完整
3. 同音字校正：根据上下文修正明显的同音字错误（如"人需说明"→"仍需说明"）
4. 标点修复：添加或修正标点符号，使阅读更流畅
5. 专有名词修正：修正技术术语的大小写（如 GitHub, Markdown, VS Code, AI, PPT, Word 等）
6. 格式统一：统一数字、日期、时间的格式
7. 口语化处理：保持口语化的表达风格
8. 内容验证：验证内容的完整性和一致性
9. 风格一致性：保持全文风格一致
10. 特殊符号处理：正确处理特殊符号和表情符号

# ✅ CORRECT: Focused requirements
【优化要求】
1. 智能分段：按语义主题划分段落
2. 断句优化：修复不完整的句子
3. 同音字校正：修正明显的同音字错误
4. 标点修复：添加或修正标点符号
5. 专有名词修正：修正技术术语的大小写
```

**Why**: Too many constraints confuse the LLM and reduce performance. Focus on the top 5 improvements.

---

### ❌ Anti-Pattern: Silent Failures

```python
# ❌ WRONG: Silent failure
try:
    enhanced = self._call_llm(prompt)
except:
    pass  # Swallows all errors!

# ✅ CORRECT: Logged failure
try:
    enhanced = self._call_llm(prompt)
except Exception as e:
    logger.error(f"LLM enhancement failed: {e}")
    return content, {"success": False, "error": str(e)}
```

**Why**: Silent failures make debugging impossible.

---

## Future Improvements

### P2: Streaming Enhancement (Future)

**Challenge**: LLM needs full context for intelligent segmentation.

**Potential Solution**: Sliding window approach with overlap.

```python
# Pseudocode for future implementation
window_size = 5000  # characters
overlap = 500       # characters

for i in range(0, len(content), window_size - overlap):
    window = content[i:i + window_size]
    enhanced_window = enhancer.enhance(window)
    # Merge with overlap resolution
```

---

### P2: Confidence Score Visualization (Future)

**Benefit**: Show users which regions need manual review.

```python
# Potential output format
{
    "text": "这是仍需说明的问题",
    "confidence": 0.95,  # ASR confidence
    "enhanced": true,    # LLM modified
    "changes": ["人需 → 仍需"]
}
```

---

## Checklist for Future LLM Integrations

Before adding LLM-based features, ask:

- [ ] Does it have graceful degradation?
- [ ] Is the temperature setting appropriate?
- [ ] Is the prompt structured and unambiguous?
- [ ] Are there explicit "do not" constraints?
- [ ] Is processing time shown to users?
- [ ] Is the model configurable?
- [ ] Are there examples in the prompt?
- [ ] Is the role clearly defined?
- [ ] Are delimiters used for content sections?
- [ ] Does one failure stop the entire pipeline?
- [ ] Are errors logged with context?
- [ ] Is it backward compatible?
- [ ] Is processing time measured?
- [ ] Can it be cached?
- [ ] Does each class have a single responsibility?

---

## Conclusion

The most important lessons from v2.2.0:

1. **Graceful degradation** is non-negotiable for LLM features
2. **Prompt structure** matters more than prompt length
3. **Default behavior** should be the best experience
4. **Transparency** builds user trust (show progress, errors, timing)
5. **Measurement** enables optimization

**Remember**: The goal is to improve user experience, not to add complexity.

---

## Related Documents

- `CHANGELOG.md` - Version history
- `IMPLEMENTATION_V2.2.0.md` - Technical details
- `BENCHMARKS.md` - Performance metrics
- `SKILL.md` - User documentation
