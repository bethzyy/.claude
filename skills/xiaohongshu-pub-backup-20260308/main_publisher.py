#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书HTML发布工具 - 主入口

Xiaohongshu HTML Publisher - Main entry point.

自动将HTML文章发布到小红书平台。
支持：
- 自动提取HTML标题、内容、base64图片
- Chrome浏览器自动化发布
- 发布状态验证
"""

import sys
import time
import argparse
from pathlib import Path

# Windows UTF-8控制台输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加父目录到路径以支持相对导入
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import HTMLExtractor, ImageProcessor, BrowserPublisher, PublishValidator, CollectionClassifier
from utils import ProgressLogger, ChromeLauncher
from config import CHROME_DEBUG_PORT


def truncate_by_paragraphs(content: str, max_length: int) -> str:
    """
    按段落截断内容（从后往前删除段落，保持段落完整性）

    Args:
        content: 原始内容
        max_length: 最大长度

    Returns:
        截断后的内容
    """
    import re

    # 按段落分割（多个连续换行符视为段落分隔）
    paragraphs = re.split(r'\n\s*\n', content)

    # 如果只有一个段落，直接按字符截断
    if len(paragraphs) <= 1:
        return content[:max_length]

    # 从前往后累加段落，直到接近max_length
    result_paragraphs = []
    current_length = 0

    for para in paragraphs:
        para_length = len(para) + 2  # +2 是段落之间的换行符

        if current_length + para_length <= max_length:
            result_paragraphs.append(para)
            current_length += para_length
        else:
            # 这个段落加上会超限，停止添加
            break

    # 如果连第一个段落都超限，直接截断
    if not result_paragraphs:
        return paragraphs[0][:max_length]

    # 用双换行符连接段落
    truncated_content = '\n\n'.join(result_paragraphs)

    return truncated_content


def verify_content(data: dict) -> bool:
    """
    验证内容是否符合发布要求

    Args:
        data: 提取的内容数据

    Returns:
        是否通过验证
    """
    print("\n[内容检查]")

    issues = []

    # 小红书字数限制
    MAX_TITLE_LENGTH = 20  # 标题最多20字
    MIN_TITLE_LENGTH = 5   # 标题最少5字
    MAX_CONTENT_LENGTH = 1000  # 正文最多1000字
    MIN_CONTENT_LENGTH = 50    # 正文最少50字

    # 检查标题
    if not data['title'] or data['title'] == "未命名标题":
        issues.append("❌ 标题为空或未命名")
    elif len(data['title']) < MIN_TITLE_LENGTH:
        issues.append(f"❌ 标题过短: {len(data['title'])}字（最少{MIN_TITLE_LENGTH}字）")
    elif len(data['title']) > MAX_TITLE_LENGTH:
        issues.append(f"❌ 标题过长: {len(data['title'])}字（最多{MAX_TITLE_LENGTH}字）")
    else:
        print(f"  ✅ 标题长度: {len(data['title'])}字")

    # 检查内容
    content_length = len(data['content'])
    if content_length < MIN_CONTENT_LENGTH:
        issues.append(f"❌ 内容过短: {content_length}字（最少{MIN_CONTENT_LENGTH}字）")
    elif content_length > MAX_CONTENT_LENGTH:
        issues.append(f"❌ 内容过长: {content_length}字（最多{MAX_CONTENT_LENGTH}字）")
        # 按段落截断内容（从后往前删除段落）
        original_length = content_length
        data['content'] = truncate_by_paragraphs(data['content'], MAX_CONTENT_LENGTH)
        new_length = len(data['content'])
        removed_paragraphs = (original_length - new_length) > 0
        print(f"  ⚠️  内容已从{original_length}字截断到{new_length}字")
        if removed_paragraphs:
            print(f"     (保留了前面的完整段落)")
    else:
        print(f"  ✅ 内容长度: {content_length}字")

    # 检查图片
    if len(data['images']) == 0:
        issues.append("⚠️  没有图片（建议添加至少1张图片）")
    else:
        print(f"  ✅ 图片数量: {len(data['images'])}张")

    # 检查话题
    if not data['topics']:
        print(f"  ⚠️  没有话题标签（将使用默认）")
        data['topics'] = ["AI", "技术分享"]
    else:
        print(f"  ✅ 话题标签: {', '.join(data['topics'])}")

    # 打印问题汇总
    if issues:
        print("\n[发现问题]:")
        for issue in issues:
            print(f"  {issue}")

        # 检查是否有严重错误（❌标记的）
        has_critical = any('❌' in issue for issue in issues)
        if has_critical:
            return False

    print("\n✅ 内容检查通过")
    return True


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='小红书HTML发布工具 - 自动将HTML文章发布到小红书'
    )
    parser.add_argument(
        'html_file',
        nargs='?',
        help='HTML文件路径'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='仅检查Chrome连接，不执行发布'
    )
    parser.add_argument(
        '--extract-only',
        action='store_true',
        help='仅提取内容，不发布'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=CHROME_DEBUG_PORT,
        help=f'Chrome远程调试端口（默认: {CHROME_DEBUG_PORT}）'
    )
    parser.add_argument(
        '--manual',
        action='store_true',
        help='手动模式：填写内容后手动点击发布按钮（默认自动发布）'
    )
    parser.add_argument(
        '--auto-publish',
        action='store_true',
        help='[已弃用] 现在默认自动发布，使用--manual可切换为手动模式'
    )
    parser.add_argument(
        '--no-verify',
        action='store_true',
        help='跳过内容检查步骤'
    )
    return parser.parse_args()


def print_banner():
    """打印欢迎横幅"""
    print("\n" + "=" * 60)
    print("小红书HTML发布工具 v1.0.0")
    print("=" * 60)
    print("\n功能特性:")
    print("  ✅ 自动提取HTML标题、内容、base64图片")
    print("  ✅ Chrome浏览器自动化发布")
    print("  ✅ 发布状态验证")
    print("\n前置要求:")
    print("  1. Chrome已启动远程调试模式:")
    print(f"     chrome.exe --remote-debugging-port={CHROME_DEBUG_PORT}")
    print("  2. 已在Chrome中登录小红书")
    print("=" * 60 + "\n")


def main():
    """主函数"""
    args = parse_args()

    print_banner()

    # 检查模式
    if args.check_only:
        print("[检查模式] 验证Chrome连接...")
        publisher = BrowserPublisher(debug_port=args.port)
        if publisher.connect():
            print("\n✅ Chrome连接成功!")
            print(f"当前页面: {publisher.get_current_url()}")
            return 0
        else:
            print("\n❌ Chrome连接失败!")
            return 1

    # 没有HTML文件
    if not args.html_file:
        print("\n[错误] 请指定HTML文件路径")
        print("\n使用方法:")
        print("  python main_publisher.py article.html")
        print("  python main_publisher.py article.html --port 9222")
        print("\n其他选项:")
        print("  --check-only    仅检查Chrome连接")
        print("  --extract-only  仅提取内容，不发布")
        print("  --port PORT     指定Chrome调试端口")
        return 1

    html_file = Path(args.html_file)

    # 验证文件存在
    if not html_file.exists():
        print(f"\n[错误] 文件不存在: {html_file}")
        return 1

    # 初始化进度日志
    progress = ProgressLogger(total_steps=4)

    # ========== 步骤1: 提取内容 ==========
    progress.step("提取文章内容")

    try:
        extractor = HTMLExtractor()
        data = extractor.extract(args.html_file)

        print(f"  标题: {data['title']}")
        print(f"  字数: {len(data['content'])} 字")
        print(f"  图片: {len(data['images'])} 张 (base64)")
        if data['topics']:
            print(f"  话题: {', '.join(data['topics'])}")

    except Exception as e:
        print(f"\n[错误] 提取失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # ========== 步骤1.5: 验证内容 ==========
    if not args.no_verify:
        print("\n[步骤1.5] 验证内容...")

        if not verify_content(data):
            print("\n⚠️  内容检查发现问题，是否继续发布？")
            try:
                confirm = input("继续发布？(y/N): ").strip().lower()
                if confirm != 'y':
                    print("已取消发布")
                    return 0
            except (EOFError, KeyboardInterrupt):
                print("\n已取消发布")
                return 0
    else:
        print("\n[跳过] 内容检查已禁用")

    # ========== 步骤1.6: 保存文案到txt并检查 ==========
    print("\n[步骤1.6] 保存文案到txt文档...")

    import re

    # 创建test/temp目录（如果不存在）
    temp_dir = Path(__file__).parent.parent.parent / "test" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名（基于文档名和时间戳）
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    doc_name = data.get('document_name', 'article')
    txt_file = temp_dir / f"{doc_name}_content_{timestamp}.txt"

    # 保存文案到txt
    try:
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"标题: {data['title']}\n")
            f.write(f"字数: {len(data['content'])}字\n")
            f.write(f"图片: {len(data['images'])}张\n")
            f.write(f"话题: {', '.join(data.get('topics', []))}\n")
            f.write("\n" + "=" * 50 + "\n")
            f.write("【标题】\n")
            f.write(data['title'] + "\n\n")
            f.write("=" * 50 + "\n")
            f.write("【正文内容】\n")
            f.write(data['content'])
            if data.get('topics'):
                f.write("\n\n" + "=" * 50 + "\n")
                f.write("【话题标签】\n")
                f.write(" ".join([f"#{topic}" for topic in data['topics']]))

        print(f"  ✅ 文案已保存到: {txt_file}")

        # 显示文案内容供检查
        print("\n" + "=" * 60)
        print("【文案检查】")
        print("=" * 60)

        # 显示标题
        print(f"\n📌 标题 ({len(data['title'])}字):")
        print(f"   {data['title']}")

        # 显示正文（分段显示）
        paragraphs = re.split(r'\n\s*\n', data['content'])
        print(f"\n📝 正文 ({len(data['content'])}字, {len(paragraphs)}段):")
        print("   " + "-" * 56)

        # 显示前5段预览
        preview_paragraphs = paragraphs[:5]
        for i, para in enumerate(preview_paragraphs, 1):
            # 截断过长的段落
            display_para = para if len(para) <= 100 else para[:97] + "..."
            print(f"   [{i}] {display_para}")

        if len(paragraphs) > 5:
            print(f"   ... (还有{len(paragraphs) - 5}段，详见txt文件)")

        print("   " + "-" * 56)

        # 显示话题
        if data.get('topics'):
            print(f"\n🏷️  话题标签: {' '.join([f'#{t}' for t in data['topics']])}")

        # 显示图片信息
        if data.get('images'):
            print(f"\n🖼️  图片数量: {len(data['images'])}张")

        print("\n" + "=" * 60)
        print(f"💡 提示: 完整内容已保存到txt文件，可打开检查分段和格式")
        print("=" * 60)

    except Exception as e:
        print(f"  [!] 保存txt文件失败: {e}")

    # 仅提取模式
    if args.extract_only:
        print("\n[仅提取模式] 内容已提取，不执行发布")
        print(f"\n标题: {data['title']}")
        print(f"\n内容预览（前200字）:")
        print(data['content'][:200] + "...")
        return 0

    # ========== 步骤2.5: 判断合集 ==========
    print("\n[步骤2.5] 判断合集...")

    classifier = CollectionClassifier()
    collection_suggestion = classifier.get_collection_suggestion(
        data['title'],
        data['content']
    )

    if collection_suggestion['collection']:
        print(f"  ✅ 推荐合集: {collection_suggestion['collection']}")
        print(f"     理由: {collection_suggestion['reason']}")
        collection = collection_suggestion['collection']
    else:
        print(f"  ⚠️  未找到合适的合集")
        collection = None

    # ========== 步骤2: 处理图片 ==========
    progress.step("处理图片")

    processor = ImageProcessor()

    # 检查是否已有图片
    existing_images = processor.get_existing_images(data['document_name'])
    if existing_images:
        print(f"  发现已有图片: {len(existing_images)} 张")
        print(f"  使用现有图片: {existing_images[0]}")
        image_paths = existing_images
    else:
        if data['images']:
            image_paths = processor.save_base64_images(
                data['images'],
                data['document_name']
            )
            print(f"  已保存到: images/{data['document_name']}/")
        else:
            print(f"  [提示] HTML中没有base64图片")
            image_paths = []

    # ========== 步骤3: 发布 ==========
    progress.step("自动发布")

    publisher = BrowserPublisher(debug_port=args.port)

    # 添加默认话题（如果没有）
    topics = data['topics'] if data['topics'] else ["AI", "技术分享"]

    publish_result = publisher.publish(
        data['title'],
        data['content'],
        image_paths,
        topics,
        collection=collection  # 传入合集名称
    )

    if not publish_result:
        print("\n[错误] 发布失败")
        return 1

    # ========== 步骤4: 验证状态 ==========
    progress.step("验证发布状态")

    validator = PublishValidator(publisher.driver)
    status = validator.validate()

    # 打印结果
    validator.print_result(status)

    # 自动发布或提示用户手动发布
    print("\n" + "=" * 60)

    # 判断是否自动发布（默认自动发布）
    auto_publish = True

    # 如果指定了--manual，询问用户
    if hasattr(args, 'manual') and args.manual:
        print("🎯 下一步操作:")
        print("=" * 60)
        print("\n选项:")
        print("  1. 自动点击'发布'按钮")
        print("  2. 手动在浏览器中检查并发布")

        try:
            choice = input("\n请选择 (1/2, 默认:1): ").strip()
            auto_publish = (choice != '2')
        except (EOFError, KeyboardInterrupt):
            # 非交互模式，使用默认值（自动发布）
            auto_publish = True

    # 执行发布
    if auto_publish:
        print("\n" + "=" * 60)
        print("[自动发布] 正在点击'发布'按钮...")
        print("=" * 60)

        if publisher.click_publish_button():
            print("  ✅ 发布按钮已点击")

            # 等待页面响应
            print("  等待发布结果...")
            time.sleep(5)

            # 再次验证
            final_status = validator.validate()
            validator.print_result(final_status)

            if final_status['success']:
                print("\n🎉 发布成功!")
                if final_status['note_url']:
                    print(f"笔记链接: {final_status['note_url']}")
                print("\n" + "=" * 60)
                progress.complete("发布完成")
                return 0
            else:
                print("\n⚠️  请在浏览器中确认发布状态")
                print("提示: 可能需要处理弹窗或验证码")
        else:
            print("\n❌ 无法自动点击发布按钮")
            print("\n请在浏览器中手动点击'发布'按钮")
    else:
        print("\n" + "=" * 60)
        print("🎯 手动发布")
        print("=" * 60)
        print("\n请在浏览器中:")
        print("  1. 检查标题和正文是否正确")
        print("  2. 调整图片顺序（如需要）")
        print("  3. 点击'发布'按钮")
        print("\n提示: 发布完成后可关闭浏览器")

    print("\n" + "=" * 60)
    progress.complete("发布流程完成")

    return 0


if __name__ == '__main__':
    sys.exit(main())
