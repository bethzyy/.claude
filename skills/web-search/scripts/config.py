#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理 - API密钥加载
"""
import os
from pathlib import Path


def get_tavily_api_key() -> str:
    """
    安全获取Tavily API Key
    优先级：
    1. 环境变量 TAVILY_API_KEY
    2. 项目目录下的 .env 文件
    3. C:\D\CAIE_tool\LLM_Configs\tavily\apikey.txt（自动检测）
    4. 用户配置目录下的 apikey.txt
    """
    # 方式1: 环境变量（推荐）
    api_key = os.environ.get('TAVILY_API_KEY', '').strip()
    if api_key:
        return api_key

    # 方式2: 项目目录下的 .env 文件
    project_dir = Path(__file__).parent.parent.parent
    env_file = project_dir / '.env'
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('TAVILY_API_KEY='):
                        return line.split('=', 1)[1].strip()
        except Exception:
            pass

    # 方式3: LLM_Configs目录（项目默认配置位置）
    llm_config_path = Path('C:/D/CAIE_tool/LLM_Configs/tavily/apikey.txt')
    if llm_config_path.exists():
        try:
            with open(llm_config_path, 'r', encoding='utf-8') as f:
                key = f.read().strip()
                if key:
                    return key
        except Exception:
            pass

    # 方式4: 用户配置目录（标准位置）
    user_config_path = Path.home() / '.config' / 'tavily' / 'apikey.txt'
    if user_config_path.exists():
        try:
            with open(user_config_path, 'r', encoding='utf-8') as f:
                key = f.read().strip()
                if key:
                    return key
        except Exception:
            pass

    return ""


def get_zhipu_api_key() -> str:
    """
    安全获取ZhipuAI API Key
    优先级：环境变量 > .env文件 > apikeyValue.txt
    """
    api_key = os.environ.get('ZHIPU_API_KEY', '').strip()
    if api_key:
        return api_key

    # 检查项目根目录的.env
    project_dir = Path(__file__).parent.parent.parent
    env_file = project_dir / '.env'
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('ZHIPU_API_KEY='):
                        return line.split('=', 1)[1].strip()
        except Exception:
            pass

    # 方式3: LLM_Configs目录（第一个API key）
    llm_config_path = Path('C:/D/CAIE_tool/LLM_Configs/GLM/apikeyValue.txt')
    if llm_config_path.exists():
        try:
            with open(llm_config_path, 'r', encoding='utf-8') as f:
                key = f.read().strip()
                if key:
                    return key
        except Exception:
            pass

    return ""


