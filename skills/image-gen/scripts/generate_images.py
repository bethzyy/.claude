# -*- coding: utf-8 -*-
"""
AI Image Generator v2.1.1 - CLI Entry Point
Generate AI images from text prompts

Usage:
    python generate_images.py <prompts> [options]

Examples:
    python generate_images.py "A mountain landscape"
    python generate_images.py '["cat", "dog"]' --style cartoon --format json

Fallback Order (v2.1.1):
1. Gemini 3 Flash Image (fastest)
2. CogView-3-flash (ZhipuAI) ⭐ Promoted
3. Seedream 5.0/4.5/4.0/3.0
4. Antigravity (Flux/DALL-E)
5. Pollinations (free)
"""

import sys
import os
import json
import base64
import argparse
from pathlib import Path
from typing import List

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from image_generator import ImageGenerator, STYLE_DESCRIPTIONS, SUPPORTED_SIZES


def parse_prompts(prompts_arg: str = None, use_env: bool = False) -> List[str]:
    """
    Parse prompts from command line argument or environment variable

    Supports both comma-separated and JSON array formats:
    - "cat, dog, bird" -> ["cat", "dog", "bird"]
    - '["cat", "dog", "bird"]' -> ["cat", "dog", "bird"]
    - Environment variable IMAGE_GEN_PROMPTS (base64-encoded JSON)

    Args:
        prompts_arg: Command line prompts argument
        use_env: If True, read from IMAGE_GEN_PROMPTS environment variable

    Returns:
        List of prompt strings
    """
    # Priority 1: Environment variable (base64-encoded JSON)
    if use_env and 'IMAGE_GEN_PROMPTS' in os.environ:
        try:
            prompts_b64 = os.environ['IMAGE_GEN_PROMPTS']
            prompts_json = base64.b64decode(prompts_b64).decode('utf-8')
            return json.loads(prompts_json)
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON decode error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Failed to parse IMAGE_GEN_PROMPTS: {e}", file=sys.stderr)
            sys.exit(1)

    # Priority 2: Command line argument
    if prompts_arg:
        prompts_arg = prompts_arg.strip()

        # Try JSON format first
        if prompts_arg.startswith('['):
            try:
                return json.loads(prompts_arg)
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON decode error: {e}", file=sys.stderr)
                sys.exit(1)

        # Fall back to comma-separated
        return [p.strip() for p in prompts_arg.split(',') if p.strip()]

    # No prompts provided
    return []


def output_text(results: List[dict], output_dir: Path):
    """
    Output results in human-readable text format

    Args:
        results: List of result dictionaries
        output_dir: Output directory path
    """
    total = len(results)
    success_count = sum(1 for r in results if r['success'])

    for i, result in enumerate(results, 1):
        prompt = result['prompt'][:50]
        if result['success']:
            filename = Path(result['path']).name
            print(f"[{i}/{total}] Generating image for: {prompt}")
            print(f"  [OK] Saved: {filename}")
        else:
            print(f"[{i}/{total}] Generating image for: {prompt}")
            print(f"  [ERROR] {result['error']}")

    print(f"\nGenerated {success_count}/{total} images in {output_dir}/")


def output_json(results: List[dict], output_dir: Path) -> str:
    """
    Output results in JSON format

    Args:
        results: List of result dictionaries
        output_dir: Output directory path

    Returns:
        JSON string
    """
    success_results = [r for r in results if r['success']]

    output_data = {
        "success": len(success_results) > 0,
        "images": [
            {
                "path": r['path'],
                "prompt": r['prompt'],
                "index": r['index']
            }
            for r in success_results
        ],
        "count": len(success_results),
        "output_dir": str(output_dir.absolute())
    }

    return json.dumps(output_data, ensure_ascii=False, indent=2)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Generate AI images from text prompts using ZhipuAI CogView-3-flash',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "A mountain landscape"
  %(prog)s "cat, dog, bird" --style cartoon
  %(prog)s '["sunset", "ocean"]' --format json --style realistic
  %(prog)s "futuristic city" --output-dir ./my-images

Styles:
  realistic - Professional photography (default)
  artistic  - Creative and elegant
  cartoon   - Colorful illustration
  technical - Clean infographics
  auto      - Automatic style selection
        """
    )

    parser.add_argument(
        'prompts',
        nargs='?',  # Optional when --use-env-prompts is set
        help='Comma-separated or JSON array of text prompts'
    )

    parser.add_argument(
        '--use-env-prompts',
        action='store_true',
        help='Read prompts from IMAGE_GEN_PROMPTS environment variable (base64-encoded JSON)'
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path.cwd(),
        help='Output directory (default: current directory)'
    )

    parser.add_argument(
        '--style',
        choices=list(STYLE_DESCRIPTIONS.keys()),
        default='realistic',
        help='Image style (default: realistic)'
    )

    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Number of images per prompt (default: 1)'
    )

    parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )

    parser.add_argument(
        '--size',
        choices=SUPPORTED_SIZES,
        default='1024x1024',
        help='Image size (default: 1024x1024)'
    )

    parser.add_argument(
        '--filename-prefix',
        type=str,
        default=None,
        help='Custom filename prefix (e.g., "insertion_point_1"). If specified, uses this prefix instead of default "img_INDEX_TIMESTAMP.jpg" format'
    )

    args = parser.parse_args()

    # Parse prompts
    try:
        prompts = parse_prompts(args.prompts, use_env=args.use_env_prompts)
    except Exception as e:
        print(f"[ERROR] Failed to parse prompts: {e}", file=sys.stderr)
        sys.exit(1)

    if not prompts:
        print("[ERROR] No valid prompts provided", file=sys.stderr)
        sys.exit(1)

    # Check API key
    if not os.environ.get('ZHIPU_API_KEY'):
        print("[ERROR] Environment variable ZHIPU_API_KEY is required", file=sys.stderr)
        sys.exit(1)

    # Generate images
    try:
        generator = ImageGenerator(
            output_dir=args.output_dir,
            style=args.style,
            size=args.size
        )

        # Generate multiple images per prompt if count > 1
        all_prompts = []
        for prompt in prompts:
            all_prompts.extend([prompt] * args.count)

        results = generator.generate_batch(all_prompts, count_per_prompt=1)

        # Rename files if filename prefix is specified
        if args.filename_prefix:
            for result in results:
                if result["success"]:
                    old_path = Path(result["path"])
                    new_path = old_path.parent / f"{args.filename_prefix}.jpg"
                    try:
                        old_path.rename(new_path)
                        result["path"] = str(new_path.absolute())
                    except Exception as e:
                        print(f"[WARNING] Failed to rename {old_path.name} to {new_path.name}: {e}", file=sys.stderr)

        # Output results
        if args.format == 'json':
            print(output_json(results, args.output_dir))
        else:
            output_text(results, args.output_dir)

        # Exit with error if any generation failed
        if not any(r['success'] for r in results):
            sys.exit(1)

    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
