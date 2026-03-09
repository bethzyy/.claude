#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Transcript Cleaner - Clean transcription output by removing markers and separators

Part of video-lines skill v2.3.3 - Fixed long text truncation (max_tokens 8192→32768)
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
    """

    # Prompt template for LLM enhancement
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

    def __init__(self, model: str = "glm-4.6"):
        """Initialize the enhancer.

        Args:
            model: LLM model to use (default: glm-4.7)
        """
        self.model = model
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

    def enhance(self, content: str) -> Tuple[str, Dict]:
        """Enhance transcription content using LLM.

        Args:
            content: Raw transcription content (after basic cleaning)

        Returns:
            Tuple of (enhanced_content, statistics_dict)
        """
        start_time = time.time()
        original_length = len(content)

        # Build prompt
        prompt = self.ENHANCEMENT_PROMPT.format(content=content)

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
