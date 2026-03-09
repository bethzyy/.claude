# image-gen Skill API Key 获取说明

## 8层 Fallback 链的 API Key 来源

### API Key 加载机制（两层设计）

#### 第一层：从 post/config.py 导入（首选）
```python
# skills/image-gen/image_generator.py (第106-113行)
config_path = Path(__file__).parent.parent.parent / 'post' / 'config.py'
if config_path.exists():
    from config import Config, get_volcano_client, get_antigravity_client, get_zhipuai_client
```

**post/config.py 的配置加载**：
```python
# post/config.py (第14-32行)
def load_env():
    """加载.env文件"""
    env_file = BASE_DIR / ".env"  # post/.env

    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# 自动加载
load_env()
```

#### 第二层：直接从环境变量获取（备选）
```python
# skills/image-gen/image_generator.py (第115-146行)
self.Config = type('Config', (), {
    'VOLCANO_API_KEY': os.environ.get('VOLCANO_API_KEY', ''),
    'ZHIPU_API_KEY': os.environ.get('ZHIPU_API_KEY', ''),
})
```

---

## 各层级使用的 API Key

### 8层 Fallback 链

| 层级 | 模型 | API Key 环境变量 | 用途 |
|------|------|-----------------|------|
| **1** | Gemini 3 Flash Image | `GOOGLE_API_KEY` | Google最新图像模型 |
| **2** | Antigravity (Flux 1.1 Pro) | `ANTIGRAVITY_API_KEY` | 高质量图像生成 |
| **2** | Antigravity (Flux Schnell) | `ANTIGRAVITY_API_KEY` | 快速批处理 |
| **2** | Antigravity (DALL-E 3) | `ANTIGRAVITY_API_KEY` | OpenAI最新模型 |
| **3** | Seedream 5.0 | `VOLCANO_API_KEY` | 豆包最高级模型 |
| **4** | Seedream 4.5 | `VOLCANO_API_KEY` | 豆包高级模型 |
| **5** | Seedream 4.0 | `VOLCANO_API_KEY` | 豆包中级模型 |
| **6** | Seedream 3.0 t2i | `VOLCANO_API_KEY` | 豆包免费模型 |
| **7** | CogView-3-flash | `ZHIPU_API_KEY` | 智谱AI图像模型 |
| **8** | Pollinations | **无需API Key** | 免费公开服务 |

---

## API Key 配置方式

### 方式1：配置 post/.env 文件（推荐）

**文件位置**：`C:\D\CAIE_tool\MyAIProduct\post\.env`

**内容格式**：
```bash
# ZhipuAI (智谱AI)
ZHIPU_API_KEY=你的智谱API密钥

# Antigravity (本地图像服务)
ANTIGRAVITY_BASE_URL=http://127.0.0.1:8045/v1
ANTIGRAVITY_API_KEY=你的Antigravity密钥

# Volcano/豆包/Seedream
VOLCANO_API_KEY=你的豆包API密钥
VOLCANO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# Google Gemini
GOOGLE_API_KEY=你的Gemini API密钥
```

### 方式2：设置系统环境变量

**Windows CMD**：
```cmd
set ZHIPU_API_KEY=你的密钥
set VOLCANO_API_KEY=你的密钥
set ANTIGRAVITY_API_KEY=你的密钥
set GOOGLE_API_KEY=你的密钥
```

**Windows PowerShell**：
```powershell
$env:ZHIPU_API_KEY="你的密钥"
$env:VOLCANO_API_KEY="你的密钥"
$env:ANTIGRAVITY_API_KEY="你的密钥"
$env:GOOGLE_API_KEY="你的密钥"
```

**Linux/Mac**：
```bash
export ZHIPU_API_KEY="你的密钥"
export VOLCANO_API_KEY="你的密钥"
export ANTIGRAVITY_API_KEY="你的密钥"
export GOOGLE_API_KEY="你的密钥"
```

---

## 重要说明

### 1. 配置优先级
```
post/.env 文件 → 系统环境变量 → 代码默认值
```

### 2. 最小配置（推荐入门）
如果你只需要基础功能，**最少只需要**：
```bash
ZHIPU_API_KEY=你的智谱API密钥
```
这样就能使用：
- ✅ 第7层：CogView-3-flash
- ✅ 第8层：Pollinations（免费）

### 3. 推荐配置（高成功率）
为了获得98-99%的成功率，建议配置：
```bash
ZHIPU_API_KEY=你的智谱API密钥
VOLCANO_API_KEY=你的豆包API密钥
ANTIGRAVITY_API_KEY=你的Antigravity密钥
GOOGLE_API_KEY=你的Gemini API密钥
```

### 4. Antigravity 配置（可选）
Antigravity 是一个本地服务，需要单独部署：
- 下载：https://github.com/anti-gravity/openai-proxy
- 默认地址：`http://127.0.0.1:8045/v1`
- 如果没有部署，相关层级会自动跳过

---

## 验证配置

### 检查配置是否加载成功

```bash
cd C:\D\CAIE_tool\MyAIProduct\post
python config.py
```

**预期输出**：
```
================================================================================
当前配置 (Config)
================================================================================
anti-gravity Base URL: http://127.0.0.1:8045/v1
anti-gravity API Key: 已设置
ZhipuAI API Key: 已设置
OpenAI API Key: 未设置
Volcano API Key: 已设置
默认图像尺寸: 1024x1024
默认图像质量: standard
================================================================================
```

---

## 常见问题

### Q1: 为什么有些层级没有API Key也能工作？
**A**:
- 第8层（Pollinations）是完全免费的公开服务，不需要API Key
- 如果没有某层的API Key，会自动跳到下一层

### Q2: 如何查看使用了哪一层？
**A**: image-gen skill 会在返回结果中显示 `model_used` 字段：
```json
{
  "success": true,
  "model_used": "Seedream 5.0",
  "path": "generated_images/image_xxx.jpg"
}
```

### Q3: VOLCANO_API_KEY 是什么？
**A**: VOLCANO_API_KEY 是字节跳动（豆包）的API密钥，用于调用 Seedream 系列模型：
- Seedream 5.0（最高级）
- Seedream 4.5
- Seedream 4.0
- Seedream 3.0 t2i（免费）

### Q4: 如何获取这些API Key？
**A**:
1. **ZHIPU_API_KEY**: https://open.bigmodel.cn/
2. **VOLCANO_API_KEY**: https://www.volcengine.com/
3. **GOOGLE_API_KEY**: https://ai.google.dev/
4. **ANTIGRAVITY_API_KEY**: 本地服务，需要自己部署

---

## 总结

**image-gen skill 的 API key 获取路径**：
```
post/.env 文件
    ↓ (通过 load_env() 函数)
os.environ 环境变量
    ↓ (通过 Config 类)
image-generator.py 的 _load_config() 方法
    ↓
各层级模型使用对应的 API Key
```

**核心要点**：
- ✅ 所有 API Key 都通过环境变量管理
- ✅ 无硬编码密钥
- ✅ 支持多层级的自动降级
- ✅ 最少只需 ZHIPU_API_KEY 即可运行
- ✅ 配置越多，成功率越高（98-99%）
