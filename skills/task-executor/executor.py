#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行Agent - 负责任务执行和自我进化

Version: 2.0.0
Updated: 2026-03-05
Changes:
- 集成SkillIntegrator，支持调用现有skills
- 替换placeholder实现为真实skill调用
- 新增复合任务支持（article_with_images, research_and_write）
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from importlib import util


class CapabilityManager:
    """能力管理系统 - 支持自我进化"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.capabilities_file = base_dir / "capabilities.json"
        self.learning_modules_dir = base_dir / "learning_modules"
        self.knowledge_base_dir = base_dir / "knowledge_base"

        # 确保目录存在
        self.learning_modules_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)

        # 加载已有能力和学习模块
        self.capabilities = self._load_capabilities()
        self.learning_modules = self._load_learning_modules()

    def _load_capabilities(self) -> Dict:
        """加载内置能力"""
        if self.capabilities_file.exists():
            return json.loads(self.capabilities_file.read_text(encoding='utf-8'))
        return {
            "code_generation": {
                "description": "代码生成能力",
                "implemented": True
            },
            "content_generation": {
                "description": "内容生成能力",
                "implemented": True
            },
            "data_analysis": {
                "description": "数据分析能力",
                "implemented": True
            },
            "image_generation": {
                "description": "图片生成能力（通过image-gen skill）",
                "implemented": True
            },
            "web_search": {
                "description": "网络搜索能力（通过web-search skill）",
                "implemented": True
            },
            "article_creation": {
                "description": "文章生成能力（通过toutiao-cnt skill）",
                "implemented": True
            },
            "article_illustration": {
                "description": "文章配图能力（通过toutiao-img skill）",
                "implemented": True
            }
        }

    def _load_learning_modules(self) -> Dict:
        """加载学习的模块"""
        modules = {}
        for module_file in self.learning_modules_dir.glob("*.py"):
            if module_file.name.startswith("_"):
                continue
            capability_name = module_file.stem
            modules[capability_name] = str(module_file)
        return modules

    def can_handle(self, task_type: str) -> bool:
        """检查是否能处理该任务类型"""
        # 1. 检查内置能力
        if task_type in self.capabilities:
            return True

        # 2. 检查学习的模块
        if task_type in self.learning_modules:
            return True

        # 3. 尝试学习新能力
        return self._try_learn_capability(task_type)

    def _try_learn_capability(self, task_type: str) -> bool:
        """尝试学习新能力"""
        print(f"[自我进化] 发现新任务类型: {task_type}")

        # 方式1: 从知识库搜索
        if self._search_knowledge_base(task_type):
            return True

        return False

    def _search_knowledge_base(self, task_type: str) -> bool:
        """从知识库搜索相关实现"""
        # 搜索相关文档
        for pattern_file in self.knowledge_base_dir.glob("**/*.md"):
            content = pattern_file.read_text(encoding='utf-8')
            if task_type.lower() in content.lower():
                print(f"[知识库] 找到相关知识: {pattern_file}")
                self._add_capability_from_file(task_type, pattern_file)
                return True

        return False

    def _add_capability_from_file(self, task_type: str, file_path: Path):
        """从文件添加能力"""
        capability = {
            "type": task_type,
            "source": str(file_path),
            "learned_at": datetime.now().isoformat()
        }
        self.capabilities[task_type] = capability
        self._save_capabilities()

    def _save_capabilities(self):
        """保存能力配置"""
        self.capabilities_file.write_text(
            json.dumps(self.capabilities, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )


class ExecutorAgent:
    """执行Agent - 负责任务执行"""

    def __init__(self, task_id: str, task_dir: Path, project_root: Optional[Path] = None):
        """
        初始化执行Agent

        Args:
            task_id: 任务ID
            task_dir: 任务目录
            project_root: 项目根目录（默认为task_dir的父目录）
        """
        self.task_id = task_id
        self.task_dir = task_dir
        self.task_dir.mkdir(parents=True, exist_ok=True)

        # 确定项目根目录
        if project_root is None:
            # 向上查找项目根目录（包含skills目录的位置）
            self.project_root = self._find_project_root()
        else:
            self.project_root = Path(project_root)

        # 初始化Skill集成器
        from skill_integrator import SkillIntegrator
        self.skill_integrator = SkillIntegrator(self.project_root)

        # 初始化能力管理器
        self.capability_manager = CapabilityManager(
            self.task_dir / "capabilities"
        )

        # 内置执行器
        self.builtin_executors = {
            "code_generation": self._execute_code_task,
            "content_generation": self._execute_content_task,
            "data_analysis": self._execute_analysis_task,
            "image_generation": self._execute_image_task,
            "web_search": self._execute_search_task,
            "composite": self._execute_composite_task
        }

        print(f"[执行Agent] 初始化完成")
        print(f"  任务ID: {self.task_id}")
        print(f"  任务目录: {self.task_dir}")
        print(f"  项目根目录: {self.project_root}")

    def _find_project_root(self) -> Path:
        """查找项目根目录（包含skills目录）"""
        current = Path.cwd()

        # 向上查找，最多5层
        for _ in range(5):
            if (current / "skills").exists():
                return current
            current = current.parent

        # 如果找不到，使用当前目录
        return Path.cwd()

    def execute_task(self, task_config: Dict) -> Dict:
        """执行任务"""
        task_type = task_config.get("type", "generic")

        print(f"\n[执行Agent] 开始执行任务: {task_type}")
        print(f"{'='*60}")

        # 1. 检查能力
        if not self.capability_manager.can_handle(task_type):
            return {
                "status": "failed",
                "error": f"无法处理任务类型: {task_type}",
                "suggestion": f"任务类型 {task_type} 尚未学习"
            }

        # 2. 获取执行器
        executor = self._get_executor(task_type)

        # 3. 执行任务
        try:
            start_time = time.time()
            result = executor(task_config)
            elapsed_time = time.time() - start_time

            result["status"] = "completed"
            result["task_type"] = task_type
            result["timestamp"] = datetime.now().isoformat()
            result["elapsed_time"] = round(elapsed_time, 2)

            # 4. 保存结果
            self._save_result(result)

            print(f"\n[完成] 任务执行成功，耗时 {elapsed_time:.2f} 秒")
            print(f"{'='*60}\n")

            return result

        except Exception as e:
            error_result = {
                "status": "failed",
                "error": str(e),
                "task_type": task_type
            }
            print(f"\n[失败] 任务执行失败: {e}")
            print(f"{'='*60}\n")
            return error_result

    def _get_executor(self, task_type: str):
        """获取任务执行器"""
        # 1. 检查内置执行器
        if task_type in self.builtin_executors:
            return self.builtin_executors[task_type]

        # 2. 检查学习的模块
        if task_type in self.capability_manager.learning_modules:
            return self._load_learning_module(task_type)

        # 3. 返回默认执行器
        return self._execute_generic_task

    def _load_learning_module(self, task_type: str):
        """动态加载学习的模块"""
        module_path = self.capability_manager.learning_modules[task_type]

        # 动态导入
        spec = util.spec_from_file_location(task_type, module_path)
        if spec and spec.loader:
            module = util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return getattr(module, 'execute', None)

        return None

    def _execute_code_task(self, config: Dict) -> Dict:
        """执行代码生成任务"""
        prompt = config.get("prompt", "")
        language = config.get("language", "python")

        print(f"[代码生成] 语言: {language}, 提示: {prompt[:50]}...")

        # 这里可以调用AI生成代码
        # 为了演示，返回模拟结果
        code = f"# Auto-generated {language} code\n# Prompt: {prompt}\n\ndef main():\n    pass\n"

        return {
            "type": "code",
            "code": code,
            "language": language,
            "prompt": prompt
        }

    def _execute_content_task(self, config: Dict) -> Dict:
        """执行内容生成任务 - 调用toutiao-cnt skill"""
        topic = config.get("topic", "")
        content_type = config.get("content_type", "article")
        style = config.get("style", "专业")

        print(f"[内容生成] 主题: {topic}, 类型: {content_type}")

        try:
            # 根据content_type选择不同的生成方法
            if content_type == "article":
                result = self.skill_integrator.create_article(
                    topic=topic,
                    style=style,
                    output_dir=self.task_dir / "output"
                )

                if result["success"]:
                    print(f"  [成功] 文章已生成: {result['article_path']}")
                    print(f"  [信息] 标题: {result['title']}, 字数: {result['word_count']}")

                return {
                    "type": "content",
                    "content_type": content_type,
                    "article_path": result.get("article_path"),
                    "title": result.get("title"),
                    "word_count": result.get("word_count", 0),
                    "success": result.get("success", False),
                    "error": result.get("error")
                }

            else:
                return {
                    "type": "content",
                    "content_type": content_type,
                    "success": False,
                    "error": f"不支持的内容类型: {content_type}"
                }

        except Exception as e:
            return {
                "type": "content",
                "content_type": content_type,
                "success": False,
                "error": str(e)
            }

    def _execute_analysis_task(self, config: Dict) -> Dict:
        """执行数据分析任务"""
        data_source = config.get("data_source", "")

        print(f"[数据分析] 数据源: {data_source}")

        return {
            "type": "analysis",
            "data_source": data_source,
            "summary": "Analysis summary placeholder"
        }

    def _execute_image_task(self, config: Dict) -> Dict:
        """执行图片生成任务 - 调用image-gen skill"""
        prompts = config.get("prompts", [])
        style = config.get("style", "realistic")
        output_dir = config.get("output_dir")

        print(f"[图片生成] 数量: {len(prompts)}, 风格: {style}")

        results = []
        for prompt in prompts:
            try:
                result = self.skill_integrator.generate_image(
                    prompt=prompt,
                    style=style,
                    output_dir=output_dir or self.task_dir / "output" / "images"
                )
                results.append(result)

                if result["success"]:
                    print(f"  [成功] {prompt[:30]}... -> {Path(result['path']).name}")
                else:
                    print(f"  [失败] {prompt[:30]}... - {result.get('error', 'Unknown error')}")

            except Exception as e:
                results.append({
                    "success": False,
                    "prompt": prompt,
                    "error": str(e)
                })
                print(f"  [异常] {prompt[:30]}... - {e}")

        success_count = sum(1 for r in results if r.get("success"))

        return {
            "type": "image",
            "images": results,
            "total": len(results),
            "success_count": success_count
        }

    def _execute_search_task(self, config: Dict) -> Dict:
        """执行网络搜索任务 - 调用web-search skill"""
        query = config.get("query", "")
        source = config.get("source", "auto")
        max_results = config.get("max_results", 10)

        print(f"[网络搜索] 查询: {query}, 源: {source}")

        try:
            result = self.skill_integrator.search_web(
                query=query,
                source=source,
                max_results=max_results
            )

            if result["success"]:
                print(f"  [成功] 找到 {len(result['results'])} 个结果 (来源: {result['source_used']})")
                if result.get("cached"):
                    print(f"  [缓存] 使用缓存结果")
            else:
                print(f"  [失败] {result.get('error', 'Unknown error')}")

            return {
                "type": "search",
                "query": query,
                "results": result.get("results", []),
                "source_used": result.get("source_used", "unknown"),
                "cached": result.get("cached", False),
                "total_results": len(result.get("results", [])),
                "success": result.get("success", False),
                "error": result.get("error")
            }

        except Exception as e:
            return {
                "type": "search",
                "query": query,
                "error": str(e),
                "results": [],
                "success": False
            }

    def _execute_composite_task(self, config: Dict) -> Dict:
        """执行复合任务 - 组合多个skills"""
        task_type = config.get("composite_type")

        print(f"[复合任务] 类型: {task_type}")

        if task_type == "article_with_images":
            return self._execute_article_with_images(config)
        elif task_type == "research_and_write":
            return self._execute_research_and_write(config)
        else:
            return {
                "type": "composite",
                "success": False,
                "error": f"不支持的复合任务类型: {task_type}"
            }

    def _execute_article_with_images(self, config: Dict) -> Dict:
        """生成文章并配图 - 典型的skill组合场景"""
        topic = config.get("topic", "")
        num_images = config.get("num_images", 3)
        article_style = config.get("article_style", "专业")
        image_style = config.get("image_style", "realistic")

        print(f"[文章+配图] 主题: {topic}, 图片数: {num_images}")

        try:
            result = self.skill_integrator.create_article_with_images(
                topic=topic,
                num_images=num_images,
                article_style=article_style,
                image_style=image_style,
                output_dir=self.task_dir / "output"
            )

            if result.get("success"):
                print(f"  [成功] 文章已生成并配图")
                print(f"  [文章] {result['article_path']}")
                print(f"  [图片] {len(result.get('images', []))} 张")
                if result.get("warning"):
                    print(f"  [警告] {result['warning']}")

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "topic": topic,
                "type": "composite"
            }

    def _execute_research_and_write(self, config: Dict) -> Dict:
        """研究并写文章 - 搜索+生成+配图"""
        topic = config.get("topic", "")
        num_images = config.get("num_images", 3)

        print(f"[研究+写作] 主题: {topic}")

        try:
            result = self.skill_integrator.research_and_write(
                topic=topic,
                num_images=num_images,
                output_dir=self.task_dir / "output"
            )

            if result.get("success"):
                print(f"  [成功] 研究并写作完成")
                print(f"  [文章] {result.get('article_path')}")
                print(f"  [研究] 找到 {result.get('research_results', 0)} 条资料")
                print(f"  [图片] {len(result.get('images', []))} 张")

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "topic": topic,
                "type": "composite"
            }

    def _execute_generic_task(self, config: Dict) -> Dict:
        """执行通用任务"""
        print(f"[通用任务] {config}")

        return {
            "type": "generic",
            "config": config
        }

    def improve(self, task: Dict, feedback: Dict) -> Dict:
        """根据反馈改进结果"""
        print(f"[改进] 根据反馈改进任务")

        # 提取反馈意见
        suggestions = feedback.get("suggestions", [])
        issues = feedback.get("issues", [])

        print(f"  建议: {len(suggestions)} 条")
        print(f"  问题: {len(issues)} 条")

        # 结合原始任务和反馈生成新任务
        improved_config = task.copy()
        improved_config["feedback"] = feedback
        improved_config["iteration"] = task.get("iteration", 0) + 1

        # 重新执行
        return self.execute_task(improved_config)

    def _save_result(self, result: Dict):
        """保存执行结果"""
        result_file = self.task_dir / "execution_result.json"
        result_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        print(f"[保存] 执行结果已保存: {result_file}")
