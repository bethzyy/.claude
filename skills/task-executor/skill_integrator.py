# -*- coding: utf-8 -*-
"""
Skill集成器 - 统一管理所有外部skill调用

该模块提供一个统一的接口来调用现有的skills：
- image-gen: AI图片生成（8级fallback）
- web-search: 网络搜索（4级fallback）
- toutiao-cnt: 今日头条文章生成
- toutiao-img: 文章配图

Version: 1.0.0
Created: 2026-03-05
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class SkillIntegrator:
    """Skill集成器 - 提供统一的skill调用接口"""

    def __init__(self, project_root: Path):
        """
        初始化Skill集成器

        Args:
            project_root: 项目根目录路径
        """
        self.project_root = Path(project_root)
        self.skills_dir = self.project_root / "skills"

        # 添加skills目录到Python路径
        skills_str = str(self.skills_dir)
        if skills_str not in sys.path:
            sys.path.insert(0, skills_str)

        # 缓存已导入的skill模块
        self._cache = {}

        print(f"[SkillIntegrator] 初始化完成")
        print(f"  项目根目录: {self.project_root}")
        print(f"  Skills目录: {self.skills_dir}")

    def generate_image(
        self,
        prompt: str,
        style: str = "realistic",
        output_dir: Optional[Path] = None
    ) -> Dict:
        """
        调用image-gen skill生成图片

        使用8级fallback机制确保高成功率：
        Gemini → Antigravity → Seedream 5.0/4.5/4.0/3.0 → CogView → Pollinations

        Args:
            prompt: 图片提示词
            style: 图片风格 (realistic/artistic/cartoon/technical)
            output_dir: 输出目录

        Returns:
            {
                "success": True,
                "path": "path/to/image.jpg",
                "model_used": "Seedream 5.0",
                "prompt": "original prompt"
            }
        """
        from image_gen.image_generator import ImageGenerator

        # 使用默认输出目录
        if output_dir is None:
            output_dir = self.project_root / "output" / "images"
        else:
            output_dir = Path(output_dir)

        # 创建图片生成器
        generator = ImageGenerator(output_dir=output_dir, style=style)

        print(f"[image-gen] 生成图片: {prompt[:50]}...")

        # 调用生成方法
        result = generator.generate_single(prompt=prompt)

        return {
            "success": result.get("success", False),
            "path": result.get("path"),
            "model_used": result.get("model_used"),
            "prompt": prompt,
            "error": result.get("error")
        }

    def search_web(
        self,
        query: str,
        source: str = "auto",
        max_results: int = 10
    ) -> Dict:
        """
        调用web-search skill搜索信息

        使用4级fallback机制：
        MCP WebSearch → Tavily → DuckDuckGo → AI Knowledge

        Args:
            query: 搜索查询
            source: 搜索源 (auto/mcp_websearch/tavily/duckduckgo/ai_knowledge)
            max_results: 最大结果数

        Returns:
            {
                "success": True,
                "results": [...],
                "source_used": "tavily",
                "query": "original query"
            }
        """
        from web_search.search_engine import WebSearchEngine

        engine = WebSearchEngine()

        print(f"[web-search] 搜索: {query[:50]}...")

        # 执行搜索
        result = engine.search(
            query=query,
            source=source,
            max_results=max_results
        )

        return {
            "success": result.get("success", False),
            "results": result.get("results", []),
            "source_used": result.get("provider_used", "unknown"),
            "query": query,
            "cached": result.get("cached", False),
            "error": result.get("error")
        }

    def create_article(
        self,
        topic: str,
        style: str = "专业",
        output_dir: Optional[Path] = None
    ) -> Dict:
        """
        调用toutiao-cnt skill生成文章

        Args:
            topic: 文章主题
            style: 文章风格 (专业/通俗/学术)
            output_dir: 输出目录

        Returns:
            {
                "success": True,
                "article_path": "path/to/article.html",
                "title": "article title",
                "word_count": 5000
            }
        """
        from toutiao_cnt.create_article import create_article

        # 使用默认输出目录
        if output_dir is None:
            output_dir = self.project_root / "output" / "articles"
        else:
            output_dir = Path(output_dir)

        print(f"[toutiao-cnt] 生成文章: {topic}")

        # 调用文章生成函数
        try:
            article_path = create_article(
                topic=topic,
                output_dir=str(output_dir),
                style=style
            )

            if article_path:
                # 读取文件获取字数
                article_content = Path(article_path).read_text(encoding='utf-8')
                word_count = len(article_content)

                # 提取标题
                title = topic
                for line in article_content.split('\n'):
                    if line.startswith('# '):
                        title = line[2:].strip()
                        break

                return {
                    "success": True,
                    "article_path": str(article_path),
                    "title": title,
                    "word_count": word_count,
                    "topic": topic
                }
            else:
                return {
                    "success": False,
                    "error": "文章生成失败",
                    "topic": topic
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "topic": topic
            }

    def add_images_to_article(
        self,
        article_path: Path,
        image_style: str = "realistic",
        num_images: int = 3
    ) -> Dict:
        """
        调用toutiao-img skill为文章配图

        Args:
            article_path: 文章HTML文件路径
            image_style: 图片风格
            num_images: 图片数量

        Returns:
            {
                "success": True,
                "images_inserted": 3,
                "image_paths": ["path1", "path2", "path3"],
                "article_path": "path/to/article.html"
            }
        """
        from toutiao_img.add_images_to_toutiao_article import add_images_to_toutiao_article

        article_path = Path(article_path)

        if not article_path.exists():
            return {
                "success": False,
                "error": f"文章文件不存在: {article_path}",
                "article_path": str(article_path)
            }

        print(f"[toutiao-img] 为文章配图: {article_path.name}")

        try:
            output_path, image_paths = add_images_to_toutiao_article(
                html_file_path=str(article_path),
                image_style=image_style,
                num_images=num_images
            )

            return {
                "success": True,
                "images_inserted": len(image_paths),
                "image_paths": image_paths,
                "article_path": str(output_path)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "article_path": str(article_path)
            }

    def create_article_with_images(
        self,
        topic: str,
        num_images: int = 3,
        article_style: str = "专业",
        image_style: str = "realistic",
        output_dir: Optional[Path] = None
    ) -> Dict:
        """
        复合任务：生成文章并配图

        这是skill集成的典型场景，展示了如何组合多个skills。

        Workflow:
        Step 1: 调用 toutiao-cnt 生成文章
        Step 2: 调用 toutiao-img 插入图片（内部调用 image-gen）

        Args:
            topic: 文章主题
            num_images: 图片数量
            article_style: 文章风格
            image_style: 图片风格
            output_dir: 输出目录

        Returns:
            {
                "success": True,
                "article_path": "path/to/article.html",
                "images": [...],
                "title": "article title"
            }
        """
        print(f"\n{'='*60}")
        print(f"[复合任务] 生成文章并配图")
        print(f"  主题: {topic}")
        print(f"  图片数: {num_images}")
        print(f"{'='*60}\n")

        # Step 1: 生成文章
        print("[Step 1/2] 生成文章...")
        article_result = self.create_article(
            topic=topic,
            style=article_style,
            output_dir=output_dir
        )

        if not article_result["success"]:
            return article_result

        print(f"  ✓ 文章已生成: {article_result['article_path']}")
        print(f"  ✓ 标题: {article_result['title']}")
        print(f"  ✓ 字数: {article_result['word_count']}")

        # Step 2: 为文章配图
        print(f"\n[Step 2/2] 添加配图...")
        images_result = self.add_images_to_article(
            article_path=Path(article_result["article_path"]),
            image_style=image_style,
            num_images=num_images
        )

        if not images_result["success"]:
            # 图片添加失败，但文章已生成
            return {
                "success": True,  # 部分成功
                "article_path": article_result["article_path"],
                "images": [],
                "title": article_result["title"],
                "topic": topic,
                "warning": "文章已生成，但配图失败: " + images_result.get("error", "")
            }

        print(f"  ✓ 成功插入 {len(images_result['image_paths'])} 张配图")

        return {
            "success": True,
            "article_path": images_result["article_path"],
            "images": images_result["image_paths"],
            "title": article_result["title"],
            "topic": topic,
            "word_count": article_result.get("word_count", 0)
        }

    def research_and_write(
        self,
        topic: str,
        num_images: int = 3,
        output_dir: Optional[Path] = None
    ) -> Dict:
        """
        复合任务：研究并写文章

        Workflow:
        Step 1: 搜索相关信息
        Step 2: 基于搜索结果生成文章
        Step 3: 为文章配图

        Args:
            topic: 研究主题
            num_images: 图片数量
            output_dir: 输出目录

        Returns:
            {
                "success": True,
                "topic": "research topic",
                "article_path": "...",
                "images": [...],
                "research_results": 10
            }
        """
        print(f"\n{'='*60}")
        print(f"[复合任务] 研究并写文章")
        print(f"  主题: {topic}")
        print(f"{'='*60}\n")

        # Step 1: 搜索相关信息
        print("[Step 1/3] 搜索资料...")
        search_result = self.search_web(query=topic)

        research_count = len(search_result.get("results", []))
        source_used = search_result.get("source_used", "unknown")

        print(f"  ✓ 找到 {research_count} 条结果 (来源: {source_used})")

        # Step 2: 生成文章
        print(f"\n[Step 2/3] 生成文章...")
        article_result = self.create_article(
            topic=topic,
            output_dir=output_dir
        )

        if not article_result["success"]:
            return {
                "success": False,
                "error": "文章生成失败: " + article_result.get("error", ""),
                "topic": topic
            }

        print(f"  ✓ 文章已生成")

        # Step 3: 为文章配图
        print(f"\n[Step 3/3] 添加配图...")
        images_result = self.add_images_to_article(
            article_path=Path(article_result["article_path"]),
            num_images=num_images
        )

        return {
            "success": images_result["success"],
            "topic": topic,
            "article_path": article_result.get("article_path"),
            "title": article_result.get("title"),
            "images": images_result.get("image_paths", []),
            "research_results": research_count,
            "research_source": source_used
        }


if __name__ == "__main__":
    """测试SkillIntegrator"""
    import tempfile

    # 使用临时目录进行测试
    with tempfile.TemporaryDirectory() as temp_dir:
        integrator = SkillIntegrator(Path(temp_dir))

        print("\n" + "="*60)
        print("测试Skill集成器")
        print("="*60)

        # 测试1: 网络搜索
        print("\n[测试1] 网络搜索")
        search_result = integrator.search_web("Python async await", max_results=3)
        print(f"结果: {search_result['success']}")
        print(f"来源: {search_result.get('source_used')}")
        print(f"结果数: {len(search_result.get('results', []))}")

        # 测试2: 图片生成
        print("\n[测试2] 图片生成")
        image_result = integrator.generate_image("A beautiful mountain landscape")
        print(f"结果: {image_result['success']}")
        print(f"路径: {image_result.get('path')}")
        print(f"模型: {image_result.get('model_used')}")

    print("\n[完成] 测试结束")
