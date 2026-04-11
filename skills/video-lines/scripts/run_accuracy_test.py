#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
准确度测试脚本 - 运行视频转录并对比基准文件

Usage:
    python run_accuracy_test.py [test_id]
    python run_accuracy_test.py mcpmark_v1

如果未指定 test_id，将运行所有准确度测试。
"""

import os
import sys
import json
import re
import difflib
from pathlib import Path
from datetime import datetime

# 添加 scripts 目录到路径
SCRIPTS_DIR = Path(__file__).parent
EVALS_DIR = SCRIPTS_DIR.parent / "evals"


def calculate_similarity(transcript_path: str, benchmark_path: str) -> dict:
    """
    计算转录文本与基准文本的相似度

    Returns:
        dict: 包含 similarity, transcript_chars, benchmark_chars, diff_details
    """
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    with open(benchmark_path, 'r', encoding='utf-8') as f:
        benchmark = f.read()

    # 去除空白后比较（更公平的比较）
    trans_norm = re.sub(r'\s+', '', transcript)
    bench_norm = re.sub(r'\s+', '', benchmark)

    similarity = difflib.SequenceMatcher(None, trans_norm, bench_norm).ratio()

    return {
        'similarity': similarity,
        'transcript_chars': len(trans_norm),
        'benchmark_chars': len(bench_norm),
        'transcript_raw_chars': len(transcript),
        'benchmark_raw_chars': len(benchmark)
    }


def load_test_config(test_id: str = None) -> list:
    """加载测试配置"""
    config_path = EVALS_DIR / "accuracy_tests.json"

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        return []

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    tests = config.get('accuracy_tests', [])

    if test_id:
        tests = [t for t in tests if t['id'] == test_id]

    return tests


def run_transcription(video_path: str) -> str:
    """
    运行视频转录

    Returns:
        str: 转录输出文件路径
    """
    from video_transcriber import VideoTranscriber
    from transcript_cleaner import TranscriptCleaner, TranscriptEnhancer

    # 生成输出路径
    video_dir = os.path.dirname(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join(video_dir, f"{video_name}_transcript.txt")

    # 正确的 VideoTranscriber 初始化方式
    transcriber = VideoTranscriber(
        segment_duration=25,
        ffmpeg_path=None
    )

    # 使用 transcribe_video 方法进行转录
    stats = transcriber.transcribe_video(
        video_path,
        output_path,
        include_markers=False,
        progress_callback=None
    )

    if stats.get('total_segments', 0) == 0:
        raise RuntimeError("Transcription failed: no segments processed")

    # 清理输出
    cleaner = TranscriptCleaner()
    cleaner.clean_file(output_path)

    # LLM 后处理（faithful 模式）
    enhancer = TranscriptEnhancer(model="glm-4.6", faithful=True)
    enhanced_content, enhance_stats = enhancer.enhance(
        open(output_path, 'r', encoding='utf-8').read()
    )

    if enhance_stats.get("success", False):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_content)

    return output_path


def run_accuracy_test(test: dict) -> dict:
    """
    运行单个准确度测试

    Returns:
        dict: 测试结果
    """
    test_id = test['id']
    video_path = test['video_reference']
    benchmark_file = EVALS_DIR / test['benchmark_file']
    min_similarity = test['metrics']['min_similarity']
    target_similarity = test['metrics'].get('target_similarity', min_similarity)

    print(f"\n{'='*60}")
    print(f"Running accuracy test: {test['name']}")
    print(f"Test ID: {test_id}")
    print(f"Video: {video_path}")
    print(f"Benchmark: {benchmark_file}")
    print(f"{'='*60}")

    result = {
        'test_id': test_id,
        'test_name': test['name'],
        'timestamp': datetime.now().isoformat(),
        'video_path': video_path,
        'benchmark_path': str(benchmark_file),
        'passed': False,
        'similarity': 0,
        'min_similarity': min_similarity,
        'target_similarity': target_similarity
    }

    # 检查文件是否存在
    if not os.path.exists(video_path):
        result['error'] = f"Video file not found: {video_path}"
        print(f"ERROR: {result['error']}")
        return result

    if not benchmark_file.exists():
        result['error'] = f"Benchmark file not found: {benchmark_file}"
        print(f"ERROR: {result['error']}")
        return result

    try:
        # 运行转录
        print("\n[1/2] Running transcription...")
        transcript_path = run_transcription(video_path)
        print(f"Transcript saved to: {transcript_path}")

        # 计算相似度
        print("\n[2/2] Calculating similarity...")
        metrics = calculate_similarity(transcript_path, str(benchmark_file))

        result['similarity'] = metrics['similarity']
        result['transcript_chars'] = metrics['transcript_chars']
        result['benchmark_chars'] = metrics['benchmark_chars']

        # 判断是否通过
        if metrics['similarity'] >= min_similarity:
            result['passed'] = True
            status = "PASS"
            if metrics['similarity'] >= target_similarity:
                status += " (target met!)"
        else:
            status = "FAIL"

        print(f"\n{'='*60}")
        print(f"RESULT: {status}")
        print(f"Similarity: {metrics['similarity']:.2%}")
        print(f"Threshold: {min_similarity:.2%} (min) / {target_similarity:.2%} (target)")
        print(f"Transcript chars: {metrics['transcript_chars']:,}")
        print(f"Benchmark chars: {metrics['benchmark_chars']:,}")
        print(f"{'='*60}")

    except Exception as e:
        result['error'] = str(e)
        print(f"\nERROR: {e}")

    return result


def update_test_config(test_id: str, similarity: float):
    """更新测试配置中的 last_test_similarity"""
    config_path = EVALS_DIR / "accuracy_tests.json"

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    for test in config.get('accuracy_tests', []):
        if test['id'] == test_id:
            test['metadata']['last_test_similarity'] = round(similarity, 4)
            test['metadata']['last_test_date'] = datetime.now().strftime('%Y-%m-%d')
            break

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Run accuracy tests for video-lines skill')
    parser.add_argument('test_id', nargs='?', help='Specific test ID to run (optional)')
    parser.add_argument('--all', action='store_true', help='Run all accuracy tests')
    parser.add_argument('--list', action='store_true', help='List available tests')
    args = parser.parse_args()

    # 列出测试
    if args.list:
        tests = load_test_config()
        print("\nAvailable accuracy tests:")
        print("-" * 60)
        for test in tests:
            print(f"  ID: {test['id']}")
            print(f"  Name: {test['name']}")
            print(f"  Min Similarity: {test['metrics']['min_similarity']:.0%}")
            print(f"  Last Result: {test['metadata'].get('last_test_similarity', 'N/A')}")
            print("-" * 60)
        return

    # 加载测试
    test_id = args.test_id if not args.all else None
    tests = load_test_config(test_id)

    if not tests:
        print("No tests found.")
        if test_id:
            print(f"  Requested test ID: {test_id}")
        sys.exit(1)

    # 运行测试
    results = []
    for test in tests:
        result = run_accuracy_test(test)
        results.append(result)

        # 更新配置文件中的相似度记录
        if 'similarity' in result:
            update_test_config(test['id'], result['similarity'])

    # 打印汇总
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r.get('passed', False))
    total = len(results)

    for r in results:
        status = "PASS" if r.get('passed') else "FAIL"
        sim = f"{r.get('similarity', 0):.2%}" if 'similarity' in r else "ERROR"
        print(f"  [{status}] {r['test_id']}: {sim}")

    print(f"\nTotal: {passed}/{total} passed")

    # 返回退出码
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
