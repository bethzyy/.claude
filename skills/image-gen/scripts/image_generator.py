# -*- coding: utf-8 -*-
"""
AI Image Generator v2.1.1 - 8-Level Fallback Chain
Core image generation module for image-gen skill

This module provides the ImageGenerator class for generating AI images
from text prompts using an 8-level fallback mechanism to ensure high success rates.

CRITICAL DESIGN PRINCIPLE:
⚠️ FALLBACK MECHANISM IS A CORE DESIGN AND CANNOT BE CHANGED ⚠️
The 8-level fallback chain ensures reliability when primary APIs fail or run out of quota.

Changes in v2.1.1:
- **Priority Change**: Antigravity promoted to level 2 (after Gemini, before Seedream)
- New order: Gemini → Antigravity → Seedream 5.0/4.5/4.0/3.0 → CogView → Pollinations
- **Reason**: Antigravity provides multiple high-quality models (Flux, DALL-E) as excellent alternatives

Changes in v2.1.0:
- **Priority Change**: Gemini 3 Flash Image promoted to level 1 (fastest, highest quality)
- Reordered fallback chain: Gemini → Seedream 5.0/4.5/4.0/3.0 → Antigravity (no Gemini) → CogView → Pollinations
- Updated to 8-level fallback mechanism

Changes in v2.0.0:
- Implemented 7-level fallback chain from standalone_image_generator_v9.py
- Added support for Seedream 5.0, 4.5, 4.0, 3.0 t2i
- Added Antigravity multi-model support
- Added CogView-3-flash and Pollinations fallbacks
- Removed single-model dependency
"""

import os
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from io import BytesIO

try:
    from PIL import Image
    import requests
    from zhipuai import ZhipuAI
    from openai import OpenAI
except ImportError as e:
    raise ImportError(
        f"Missing required dependency: {e}\n"
        "Install with: pip install pillow requests zhipuai openai"
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Style descriptions appended to prompts
STYLE_DESCRIPTIONS = {
    "realistic": "realistic photography, high quality, professional lighting",
    "artistic": "artistic style, creative, elegant composition",
    "cartoon": "cartoon illustration, colorful, friendly style",
    "technical": "technical diagram, flowchart, architecture diagram, clean infographic style",
    "auto": "professional quality visualization"
}

# Supported image sizes
SUPPORTED_SIZES = ["1024x1024", "2048x2048"]

# Antigravity image models (priority by quality/speed)
ANTIGRAVITY_IMAGE_MODELS = [
    ("gemini-3-flash-image", "Gemini 3 Flash Image", "Google latest image model"),
    ("flux-1.1-pro", "Flux 1.1 Pro", "Black Forest Labs professional"),
    ("flux-schnell", "Flux Schnell", "Fast version, good for batch"),
    ("gemini-2-flash-image", "Gemini 2 Flash Image", "Second generation Gemini"),
    ("dall-e-3", "DALL-E 3", "OpenAI latest image model"),
]


class ImageGenerator:
    """AI Image Generator with 8-Level Fallback Chain"""

    def __init__(self, output_dir: Path, style: str = "realistic", size: str = "1024x1024"):
        """
        Initialize the image generator with fallback support

        Args:
            output_dir: Directory to save generated images
            style: Image style (realistic/artistic/cartoon/technical/auto)
            size: Image size (1024x1024 or 2048x2048)
        """
        self.output_dir = Path(output_dir)
        self.style = style if style in STYLE_DESCRIPTIONS else "realistic"
        self.size = size if size in SUPPORTED_SIZES else "1024x1024"

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load config
        self._load_config()

    def _load_config(self):
        """Load API configuration from environment"""
        # Import config from parent project
        import sys
        config_path = Path(__file__).parent.parent.parent / 'post' / 'config.py'
        if config_path.exists():
            sys.path.insert(0, str(config_path.parent))
            from config import Config, get_volcano_client, get_antigravity_client, get_zhipuai_client
            self.Config = Config
            self.get_volcano_client = get_volcano_client
            self.get_antigravity_client = get_antigravity_client
            self.get_zhipuai_client = get_zhipuai_client
        else:
            # Fallback to environment variables
            self.Config = type('Config', (), {
                'VOLCANO_API_KEY': os.environ.get('VOLCANO_API_KEY', ''),
                'VOLCANO_BASE_URL': os.environ.get('VOLCANO_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3'),
                'ZHIPU_API_KEY': os.environ.get('ZHIPU_API_KEY', ''),
            })
            self.get_volcano_client = self._get_volcano_client_fallback
            self.get_antigravity_client = self._get_antigravity_client_fallback
            self.get_zhipuai_client = self._get_zhipuai_client_fallback

    def _get_volcano_client_fallback(self):
        """Fallback Volcano client loader"""
        if not self.Config.VOLCANO_API_KEY:
            return None
        return OpenAI(
            base_url=self.Config.VOLCANO_BASE_URL,
            api_key=self.Config.VOLCANO_API_KEY
        )

    def _get_antigravity_client_fallback(self):
        """Fallback Antigravity client loader"""
        antigravity_key = os.environ.get('ANTIGRAVITY_API_KEY', '')
        antigravity_url = os.environ.get('ANTIGRAVITY_BASE_URL', 'http://127.0.0.1:8045/v1')
        if not antigravity_key:
            return None
        return OpenAI(base_url=antigravity_url, api_key=antigravity_key)

    def _get_zhipuai_client_fallback(self):
        """Fallback ZhipuAI client loader"""
        if not self.Config.ZHIPU_API_KEY:
            return None
        return ZhipuAI(api_key=self.Config.ZHIPU_API_KEY)

    def _sanitize_prompt(self, prompt: str) -> str:
        """Sanitize prompt for use in filename"""
        safe = re.sub(r'[^\w\s-]', '', prompt, flags=re.ASCII)
        safe = re.sub(r'\s+', '_', safe)
        return safe[:50]

    def _enhance_prompt(self, prompt: str) -> str:
        """Enhance prompt with style description"""
        style_desc = STYLE_DESCRIPTIONS[self.style]
        if style_desc.lower() not in prompt.lower():
            return f"{prompt}, {style_desc}"
        return prompt

    def generate_single(self, prompt: str, index: int = 0) -> Dict:
        """
        Generate a single image using 8-level fallback mechanism

        Fallback Chain (v2.1.1):
        1. Gemini 3 Flash Image (Google, fastest & highest quality)
        2. Antigravity (Flux/DALL-E, excluding Gemini)
        3. Seedream 5.0 (latest, 2048x2048)
        4. Seedream 4.5 (high quality)
        5. Seedream 4.0 (stable)
        6. Seedream 3.0 t2i (free)
        7. CogView-3-flash (ZhipuAI)
        8. Pollinations (free public service)

        Args:
            prompt: Text prompt for image generation
            index: Image index for filename

        Returns:
            Dictionary with success status, path, prompt, and error
        """
        enhanced_prompt = self._enhance_prompt(prompt)

        # Try all fallback levels (8 levels)
        for level in range(1, 9):
            result = self._try_fallback_level(enhanced_prompt, index, level)
            if result["success"]:
                return result

        # All levels failed
        return {
            "success": False,
            "path": None,
            "prompt": prompt,
            "index": index,
            "error": "All 8 fallback levels failed"
        }

    def _try_fallback_level(self, prompt: str, index: int, level: int) -> Dict:
        """Try a specific fallback level"""
        result = {
            "success": False,
            "path": None,
            "prompt": prompt,
            "index": index,
            "error": None
        }

        try:
            if level == 1:
                return self._try_gemini(prompt, index)
            elif level == 2:
                return self._try_antigravity(prompt, index)
            elif level == 3:
                return self._try_seedream_5_0(prompt, index)
            elif level == 4:
                return self._try_seedream_4_5(prompt, index)
            elif level == 5:
                return self._try_seedream_4_0(prompt, index)
            elif level == 6:
                return self._try_seedream_3_0(prompt, index)
            elif level == 7:
                return self._try_cogview(prompt, index)
            elif level == 8:
                return self._try_pollinations(prompt, index)
        except Exception as e:
            result["error"] = f"Level {level}: {str(e)[:200]}"
            logger.warning(f"[Fallback {level}/8] Error: {result['error']}")

        return result

    def _try_gemini(self, prompt: str, index: int) -> Dict:
        """Try Gemini 3 Flash Image (Level 1 - Priority)"""
        logger.info("[Fallback 1/8] Trying Gemini 3 Flash Image...")

        result = {"success": False, "path": None, "prompt": prompt, "index": index, "error": None}

        try:
            client = self.get_antigravity_client()
            if not client:
                result["error"] = "Gemini: Antigravity client not configured"
                return result

            logger.info("[Gemini] Using gemini-3-flash-image...")

            response = client.images.generate(
                model="gemini-3-flash-image",
                prompt=prompt,
                size="1024x1024"
            )

            if response.data and len(response.data) > 0:
                img_url = response.data[0].url
                logger.info("[Gemini] Success with Gemini 3 Flash Image")
                return self._download_and_save(img_url, result, "gemini-3-flash-image")
            else:
                result["error"] = "Gemini: Empty response"
                return result

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                result["error"] = "Gemini: Quota exhausted"
            else:
                result["error"] = f"Gemini: {error_str[:100]}"
            return result

    def _try_seedream_5_0(self, prompt: str, index: int) -> Dict:
        """Try Seedream 5.0 (Latest)"""
        logger.info("[Fallback 3/8] Trying Seedream 5.0...")
        return self._try_seedream_model(prompt, index, "doubao-seedream-5-0-260128", "Seedream 5.0", "2048x2048")

    def _try_seedream_4_5(self, prompt: str, index: int) -> Dict:
        """Try Seedream 4.5"""
        logger.info("[Fallback 4/8] Trying Seedream 4.5...")
        return self._try_seedream_model(prompt, index, "doubao-seedream-4-5-251128", "Seedream 4.5", "2048x2048")

    def _try_seedream_4_0(self, prompt: str, index: int) -> Dict:
        """Try Seedream 4.0"""
        logger.info("[Fallback 5/8] Trying Seedream 4.0...")
        return self._try_seedream_model(prompt, index, "doubao-seedream-4-0-250828", "Seedream 4.0", "2048x2048")

    def _try_seedream_3_0(self, prompt: str, index: int) -> Dict:
        """Try Seedream 3.0 t2i (Free)"""
        logger.info("[Fallback 6/8] Trying Seedream 3.0 t2i...")
        return self._try_seedream_model(prompt, index, "doubao-seedream-3-0-t2i-250415", "Seedream 3.0 t2i", "1024x1024")

    def _try_seedream_model(self, prompt: str, index: int, model_version: str, model_name: str, size: str) -> Dict:
        """Try a specific Seedream model"""
        result = {"success": False, "path": None, "prompt": prompt, "index": index, "error": None}

        try:
            client = self.get_volcano_client()
            if not client:
                result["error"] = f"{model_name}: Volcano client not configured"
                return result

            response = client.images.generate(
                model=model_version,
                prompt=prompt,
                size=size,
                response_format="url",
                extra_body={"watermark": False}
            )

            if response.data and len(response.data) > 0:
                img_url = response.data[0].url
                return self._download_and_save(img_url, result, model_name)
            else:
                result["error"] = f"{model_name}: Empty response"
                return result

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                result["error"] = f"{model_name}: Quota exhausted"
            else:
                result["error"] = f"{model_name}: {error_str[:100]}"
            return result

    def _try_antigravity(self, prompt: str, index: int) -> Dict:
        """Try Antigravity multi-model fallback (excluding Gemini - already at level 1)"""
        logger.info("[Fallback 2/8] Trying Antigravity models (excluding Gemini)...")

        result = {"success": False, "path": None, "prompt": prompt, "index": index, "error": None}

        try:
            client = self.get_antigravity_client()
            if not client:
                result["error"] = "Antigravity: Client not configured"
                return result

            # Skip first model (Gemini) as it's already tried at level 1
            for model_id, model_name, model_desc in ANTIGRAVITY_IMAGE_MODELS[1:]:
                try:
                    logger.info(f"[Antigravity] Trying {model_name}...")

                    response = client.images.generate(
                        model=model_id,
                        prompt=prompt,
                        size="1024x1024"
                    )

                    if response.data and len(response.data) > 0:
                        img_url = response.data[0].url
                        logger.info(f"[Antigravity] Success with {model_name}")
                        return self._download_and_save(img_url, result, f"antigravity-{model_id}")
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "quota" in error_str.lower():
                        logger.warning(f"[Antigravity] {model_name} quota exhausted, trying next...")
                        continue
                    else:
                        logger.warning(f"[Antigravity] {model_name} failed: {error_str[:80]}")
                        continue

            result["error"] = "Antigravity: All models failed"
            return result

        except Exception as e:
            result["error"] = f"Antigravity: {str(e)[:100]}"
            return result

    def _try_cogview(self, prompt: str, index: int) -> Dict:
        """Try CogView-3-flash"""
        logger.info("[Fallback 7/8] Trying CogView-3-flash...")

        result = {"success": False, "path": None, "prompt": prompt, "index": index, "error": None}

        try:
            client = self.get_zhipuai_client()
            if not client:
                result["error"] = "CogView: ZhipuAI client not configured"
                return result

            response = client.images.generations(
                model="cogview-3-flash",
                prompt=prompt,
                size=self.size
            )

            if response.data and len(response.data) > 0:
                img_url = response.data[0].url
                return self._download_and_save(img_url, result, "cogview-3-flash")
            else:
                result["error"] = "CogView: Empty response"
                return result

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                result["error"] = "CogView: Quota exhausted"
            else:
                result["error"] = f"CogView: {error_str[:100]}"
            return result

    def _try_pollinations(self, prompt: str, index: int) -> Dict:
        """Try Pollinations (free public service)"""
        logger.info("[Fallback 8/8] Trying Pollinations...")

        result = {"success": False, "path": None, "prompt": prompt, "index": index, "error": None}

        try:
            import urllib.parse
            encoded_prompt = urllib.parse.quote(prompt)
            img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"

            return self._download_and_save(img_url, result, "pollinations", timeout=120)

        except Exception as e:
            result["error"] = f"Pollinations: {str(e)[:100]}"
            return result

    def _download_and_save(self, img_url: str, result: Dict, model_name: str,
                          filename_prefix: str = None, timeout: int = 60) -> Dict:
        """
        Download and save image with customizable filename

        Args:
            img_url: Image URL
            result: Result dict with 'index'
            model_name: Name of model used
            filename_prefix: Optional prefix (e.g., 'insertion_point_1')
                            If None, uses default 'img_{index}_{timestamp}' format
            timeout: Request timeout

        Returns:
            Updated result dict with path
        """
        try:
            img_response = requests.get(img_url, timeout=timeout)
            if img_response.status_code == 200:
                # Generate filename based on prefix or default format
                if filename_prefix:
                    filename = f"{filename_prefix}.jpg"
                else:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                    filename = f"img_{result['index']}_{timestamp}.jpg"

                img_path = self.output_dir / filename

                img = Image.open(BytesIO(img_response.content))
                img.save(str(img_path), 'JPEG', quality=95)

                result["success"] = True
                result["path"] = str(img_path.absolute())
                result["model_used"] = model_name
                logger.info(f"[OK] Generated using {model_name}: {filename}")
                return result
            else:
                result["error"] = f"HTTP {img_response.status_code}"
                return result
        except Exception as e:
            result["error"] = str(e)[:200]
            return result

    def generate_batch(self, prompts: List[str], count_per_prompt: int = 1) -> List[Dict]:
        """
        Generate multiple images from a list of prompts

        Args:
            prompts: List of text prompts
            count_per_prompt: Number of images per prompt

        Returns:
            List of result dictionaries
        """
        all_prompts = []
        for prompt in prompts:
            all_prompts.extend([prompt] * count_per_prompt)

        results = []
        for i, prompt in enumerate(all_prompts):
            logger.info(f"[{i+1}/{len(all_prompts)}] Generating image for: {prompt[:50]}...")
            result = self.generate_single(prompt, i)
            results.append(result)

        return results
