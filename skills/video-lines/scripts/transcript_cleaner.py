#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Transcript Cleaner - Clean transcription output by removing markers and separators

Part of video-lines skill v2.7.0 - Audio-level hallucination prevention
"""

import os
import re
import time
from typing import Dict, Tuple, Optional, List


class TranscriptCleaner:
    """Clean video transcription output by removing artifacts."""

    # Regex patterns for cleaning
    SEPARATOR_PATTERN = r'^=+\s*$'
    SEGMENT_MARKER_PATTERN = r'^\[分段 \d+\]\s*$'
    SEGMENT_MARKER_ALT_PATTERN = r'^\[Segment \d+\]\s*$'
    TITLE_PATTERN = r'^视频语音转文字结果\s*$'
    TITLE_ALT_PATTERN = r'^Video Speech-to-Text Transcription\s*$'
    MULTIPLE_NEWLINES_PATTERN = r'\n\s*\n\s*\n+'

    def clean(self, content: str) -> Tuple[str, Dict]:
        """Clean transcription content by removing artifacts.

        Args:
            content: Raw transcription content

        Returns:
            Tuple of (cleaned_content, statistics_dict)
        """
        original_length = len(content)

        # Apply cleaning steps
        cleaned = self._remove_separators(content)
        cleaned = self._remove_markers(cleaned)
        cleaned = self._remove_titles(cleaned)
        cleaned = self._normalize_spacing(cleaned)
        cleaned = cleaned.strip()

        stats = {
            "original_length": original_length,
            "cleaned_length": len(cleaned),
            "removed_chars": original_length - len(cleaned),
        }
        return cleaned, stats

    def clean_file(self, input_path: str, output_path: str = None) -> Dict:
        """Clean transcription file.

        Args:
            input_path: Path to input file
            output_path: Path to output file (default: overwrite input)

        Returns:
            Statistics dictionary
        """
        if output_path is None:
            output_path = input_path

        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        cleaned_content, stats = self.clean(content)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)

        return stats

    def _remove_separators(self, content: str) -> str:
        """Remove === separator lines."""
        return re.sub(self.SEPARATOR_PATTERN, '', content, flags=re.MULTILINE)

    def _remove_markers(self, content: str) -> str:
        """Remove [分段 N] and [Segment N] markers."""
        content = re.sub(self.SEGMENT_MARKER_PATTERN, '', content, flags=re.MULTILINE)
        content = re.sub(self.SEGMENT_MARKER_ALT_PATTERN, '', content, flags=re.MULTILINE)
        return content

    def _remove_titles(self, content: str) -> str:
        """Remove title lines."""
        content = re.sub(self.TITLE_PATTERN, '', content, flags=re.MULTILINE)
        content = re.sub(self.TITLE_ALT_PATTERN, '', content, flags=re.MULTILINE)
        return content

    def _normalize_spacing(self, content: str) -> str:
        """Normalize multiple consecutive newlines to double newlines."""
        return re.sub(self.MULTIPLE_NEWLINES_PATTERN, '\n\n', content)


class TranscriptEnhancer:
    """Use LLM to enhance transcription quality.

    Performs intelligent post-processing:
    1. Smart paragraph segmentation by semantic meaning
    2. Sentence boundary optimization
    3. Homophone correction based on context
    4. Punctuation restoration and correction
    5. Proper noun capitalization fix

    Uses Anthropic SDK for GLM Coding Plan compatibility.

    Smart Chunking (v2.4.0):
    - Auto-detects when content exceeds threshold
    - Splits at paragraph boundaries (no mid-sentence cuts)
    - Processes each chunk independently
    - Merges results seamlessly
    """

    # Chunking configuration for ultra-long videos
    CHUNK_SIZE = 40000  # Max chars per chunk (safe threshold for LLM)
    OVERLAP_SIZE = 200  # Overlap chars for context continuity

    # Prompt template for LLM enhancement (standard mode with optimizations)
    ENHANCEMENT_PROMPT = """你是一个专业的音频转录文本编辑专家。请对以下从视频中提取的台词文本进行优化。

【优化要求】
1. 智能分段：按语义主题划分段落，每个段落表达一个完整的意思
2. 断句优化：修复不完整的句子，确保句子通顺完整
3. 同音字校正：根据上下文修正明显的同音字错误（如"人需说明"→"仍需说明"）
4. 标点修复：添加或修正标点符号，使阅读更流畅
5. 专有名词修正：修正技术术语的大小写（如 GitHub, Markdown, VS Code, AI, PPT, Word 等）

【注意事项】
- 保持原文内容不变，只做格式和纠错处理
- 不要添加原文没有的内容
- 保持口语化的表达风格
- 不要添加任何说明或解释，直接输出优化后的文本

【原文】
{content}

【优化后的文本】"""

    # Prompt template for faithful mode (no modifications, only segmentation)
    FAITHFUL_ENHANCEMENT_PROMPT = """你是专业的音频转录文本编辑专家。请对以下从视频中提取的台词文本进行智能分段。

【智能分段规则】
1. 按对话轮次分段：识别不同说话人或对话转换
2. 按语义主题分段：话题转换时分段
3. 控制段落长度：
   - 理想长度：3-5句话（约100-200字）
   - 最长不超过10句话（约400字）
4. 自然边界识别：在以下情况分段
   - 明显的停顿词后（"嗯"、"好"、"OK"等单独成句时）
   - 话题转换词（"另外"、"说到"、"接下来"、"然后"等）
   - 问句和答句之间
   - 总结性语句后

【严格禁止】
- 不要修改任何文字
- 不要删除任何内容
- 不要添加任何内容
- 不要做同音字校正
- 不要修改标点符号

【原文】
{content}

【分段后的文本】"""

    def __init__(self, model: str = "glm-4.6", faithful: bool = True):
        """Initialize the enhancer.

        Args:
            model: LLM model to use (default: glm-4.6)
            faithful: If True, use faithful mode (no text modifications, only segmentation)
                      Default is True since v2.6.0
        """
        self.model = model
        self.faithful = faithful
        self.api_key = self._load_api_key()

        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY not found in environment or config files")

        # Initialize Anthropic client for GLM Coding Plan
        try:
            from anthropic import Anthropic
            self.client = Anthropic(
                api_key=self.api_key,
                base_url="https://open.bigmodel.cn/api/anthropic"
            )
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def _load_api_key(self) -> Optional[str]:
        """Load API key from multiple sources.

        Priority:
        1. C:/D/CAIE_tool/LLM_Configs/GLM/apikeyValue2.txt (Coding Plan key - preferred)
        2. C:/D/CAIE_tool/LLM_Configs/GLM/apikeyValue.txt (Primary key)
        3. ZHIPU_API_KEY environment variable (fallback)

        Returns:
            API key string or None if not found
        """
        # 1. Try Coding Plan key first (apikeyValue2.txt) - this has separate quota
        coding_plan_key_path = "C:/D/CAIE_tool/LLM_Configs/GLM/apikeyValue2.txt"
        if os.path.exists(coding_plan_key_path):
            try:
                with open(coding_plan_key_path, 'r') as f:
                    api_key = f.read().strip()
                    if api_key:
                        return api_key
            except Exception:
                pass

        # 2. Try primary key (apikeyValue.txt)
        primary_key_path = "C:/D/CAIE_tool/LLM_Configs/GLM/apikeyValue.txt"
        if os.path.exists(primary_key_path):
            try:
                with open(primary_key_path, 'r') as f:
                    api_key = f.read().strip()
                    if api_key:
                        return api_key
            except Exception:
                pass

        # 3. Try environment variable as fallback
        api_key = os.environ.get("ZHIPU_API_KEY")
        if api_key:
            return api_key

        return None

    def _remove_trailing_asr_hallucination(self, content: str) -> Tuple[str, Dict]:
        """Remove obvious ASR hallucination patterns from the end of content.

        Detects and removes common ASR hallucination artifacts that appear at the end:
        - XML-like tags (</tag>, <tag>)
        - System markers (</persisted-output>, etc.)
        - Technical artifacts that don't belong in speech

        This is a conservative check - only removes obvious non-speech patterns
        that appear consecutively at the END of the transcript.

        Args:
            content: Transcription content

        Returns:
            Tuple of (cleaned_content, stats)
        """
        lines = content.strip().split('\n')
        if not lines:
            return content, {"removed": False}

        # Patterns that indicate ASR hallucination (not real speech)
        hallucination_patterns = [
            r'^</[a-zA-Z0-9_-]+>$',  # Closing XML-like tags
            r'^<[a-zA-Z0-9_-]+>$',   # Opening XML-like tags
        ]

        # Find the last non-empty line as reference point
        last_content_idx = len(lines) - 1
        while last_content_idx >= 0 and not lines[last_content_idx].strip():
            last_content_idx -= 1

        if last_content_idx < 0:
            return content, {"removed": False}

        # Check if the last content line is a hallucination pattern
        last_line = lines[last_content_idx].strip()
        is_hallucination = False
        for pattern in hallucination_patterns:
            if re.match(pattern, last_line):
                is_hallucination = True
                break

        if not is_hallucination:
            return content, {"removed": False}

        # Found hallucination at the end - find where it starts
        # Look backwards for consecutive hallucination lines
        first_hallucination_idx = last_content_idx
        for i in range(last_content_idx - 1, max(-1, last_content_idx - 10), -1):
            line = lines[i].strip()
            # Skip empty lines
            if not line:
                continue
            # Check if this line is also a hallucination
            line_is_hallucination = False
            for pattern in hallucination_patterns:
                if re.match(pattern, line):
                    line_is_hallucination = True
                    break
            if line_is_hallucination:
                first_hallucination_idx = i
            else:
                # Found a non-hallucination line, stop looking
                break

        # Remove the hallucination lines
        removed_lines = lines[first_hallucination_idx:]
        cleaned_lines = lines[:first_hallucination_idx]
        removed_content = '\n'.join(removed_lines)

        return '\n'.join(cleaned_lines), {
            "removed": True,
            "removed_chars": len(removed_content),
            "removed_lines": len(removed_lines),
            "trigger": f"ASR hallucination pattern: {last_line}"
        }

    def enhance(self, content: str) -> Tuple[str, Dict]:
        """Enhance transcription content using LLM with auto-chunking.

        Automatically detects when content exceeds threshold and enables
        smart chunking for ultra-long videos (4-5 hours, 80K+ chars).

        Note: ASR hallucination is prevented at two levels:
        1. Audio level: trimming end silence before transcription
        2. Text level: detecting obvious hallucination patterns

        Args:
            content: Raw transcription content (after basic cleaning)

        Returns:
            Tuple of (enhanced_content, statistics_dict)
        """
        # Step 1: Remove obvious ASR hallucination patterns from the end
        content, hallucination_stats = self._remove_trailing_asr_hallucination(content)

        # Step 2: Auto-detect if chunking is needed
        if len(content) > self.CHUNK_SIZE:
            result, stats = self._enhance_with_chunking(content)
        else:
            result, stats = self._enhance_single(content)

        # Merge hallucination stats into result stats
        stats["hallucination_detection"] = hallucination_stats
        return result, stats

    def _enhance_single(self, content: str) -> Tuple[str, Dict]:
        """Enhance a single chunk of content.

        Args:
            content: Single chunk of transcription content

        Returns:
            Tuple of (enhanced_content, statistics_dict)
        """
        start_time = time.time()
        original_length = len(content)

        # Select prompt based on faithful mode
        prompt_template = self.FAITHFUL_ENHANCEMENT_PROMPT if self.faithful else self.ENHANCEMENT_PROMPT
        prompt = prompt_template.format(content=content)

        # Call LLM
        try:
            enhanced = self._call_llm(prompt)
        except Exception as e:
            # If LLM fails, return original content
            return content, {
                "success": False,
                "error": str(e),
                "original_length": original_length,
                "enhanced_length": original_length,
                "processing_time_ms": 0
            }

        processing_time = (time.time() - start_time) * 1000

        stats = {
            "success": True,
            "original_length": original_length,
            "enhanced_length": len(enhanced),
            "length_diff": len(enhanced) - original_length,
            "processing_time_ms": round(processing_time, 2),
            "model_used": self.model
        }

        return enhanced, stats

    def _enhance_with_chunking(self, content: str) -> Tuple[str, Dict]:
        """Process ultra-long content by splitting into chunks.

        Args:
            content: Ultra-long transcription content

        Returns:
            Tuple of (enhanced_content, statistics_dict)
        """
        start_time = time.time()
        original_length = len(content)

        # Split content into chunks
        chunks = self._split_into_chunks(content)
        total_chunks = len(chunks)

        print(f"  Content too long ({original_length} chars), splitting into {total_chunks} chunks")

        # Process each chunk
        enhanced_chunks = []
        total_chunk_time = 0
        failed_chunks = 0

        for i, chunk in enumerate(chunks):
            chunk_start = time.time()
            print(f"  LLM enhancement: chunk {i+1}/{total_chunks} ({len(chunk)} chars)...")

            enhanced, chunk_stats = self._enhance_single(chunk)

            if chunk_stats["success"]:
                enhanced_chunks.append(enhanced)
                total_chunk_time += chunk_stats["processing_time_ms"]
            else:
                # If a chunk fails, use original content for that chunk
                print(f"    Warning: Chunk {i+1} failed, using original content")
                enhanced_chunks.append(chunk)
                failed_chunks += 1

        # Merge all chunks
        merged_content = self._merge_chunks(enhanced_chunks)

        processing_time = (time.time() - start_time) * 1000

        stats = {
            "success": True,
            "original_length": original_length,
            "enhanced_length": len(merged_content),
            "length_diff": len(merged_content) - original_length,
            "processing_time_ms": round(processing_time, 2),
            "model_used": self.model,
            "chunking": {
                "enabled": True,
                "total_chunks": total_chunks,
                "failed_chunks": failed_chunks,
                "chunk_size": self.CHUNK_SIZE
            }
        }

        return merged_content, stats

    def _split_into_chunks(self, content: str) -> List[str]:
        """Split content into chunks at paragraph boundaries.

        Ensures chunks are split at paragraph boundaries (\\n\\n) to
        maintain semantic integrity.

        Args:
            content: Content to split

        Returns:
            List of content chunks
        """
        # Split by paragraph boundaries
        paragraphs = content.split('\n\n')

        chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para_length = len(para) + 2  # +2 for '\n\n' that will be added back

            # If adding this paragraph would exceed chunk size, start a new chunk
            if current_length + para_length > self.CHUNK_SIZE and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length

        # Add the last chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def _merge_chunks(self, chunks: List[str]) -> str:
        """Merge processed chunks back into single content.

        Args:
            chunks: List of enhanced content chunks

        Returns:
            Merged content string
        """
        return '\n\n'.join(chunks)

    def _call_llm(self, prompt: str) -> str:
        """Call LLM via Anthropic SDK.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            The LLM's response text
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=32768,  # Support long transcripts (30K-60K Chinese characters)
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract content from Anthropic response format
        if response.content and len(response.content) > 0:
            return response.content[0].text.strip()

        raise Exception(f"Unexpected API response format: empty content")

    def enhance_file(self, input_path: str, output_path: str = None) -> Dict:
        """Enhance transcription file.

        Args:
            input_path: Path to input file
            output_path: Path to output file (default: overwrite input)

        Returns:
            Statistics dictionary
        """
        if output_path is None:
            output_path = input_path

        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        enhanced_content, stats = self.enhance(content)

        if stats["success"]:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_content)

        stats["input_path"] = input_path
        stats["output_path"] = output_path

        return stats
