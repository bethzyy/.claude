# 小红书HTML发布工具 (Xiaohongshu HTML Publisher)

自动将HTML文章发布到小红书平台的工具。

## 功能特性

- ✅ **自动提取内容**：从HTML提取标题、正文、base64图片
- ✅ **Chrome自动化**：连接已登录的Chrome，无需重复登录
- ✅ **智能发布**：自动点击"上传图文"、上传图片、填写内容
- ✅ **状态验证**：验证发布成功并返回笔记链接
- ✅ **图片重用**：自动检测并重用已保存的图片

## 快速开始

### 1. 前置要求

**启动Chrome远程调试模式：**

```batch
chrome.exe --remote-debugging-port=9222
```

**或者在Chrome快捷方式添加参数：**

```
chrome.exe --remote-debugging-port=9222
```

**确保已在Chrome中登录小红书账号。**

### 2. 安装依赖

```bash
cd skills/xiaohongshu-pub
pip install -r requirements.txt
```

### 3. 使用方法

#### 基本用法

```bash
# 交互式发布（会询问是否自动发布）
python main_publisher.py article.html

# 自动发布（无需手动确认）✨ 推荐
python main_publisher.py article.html --auto-publish

# 跳过内容检查（快速发布）
python main_publisher.py article.html --auto-publish --no-verify
```

#### 其他选项

```bash
# 指定Chrome端口
python main_publisher.py article.html --port 9222

# 仅检查Chrome连接
python main_publisher.py --check-only

# 仅提取内容（不发布）
python main_publisher.py article.html --extract-only
```

### 4. 在Claude Code对话中使用

```
你: 把这篇文章发布到小红书
你: 将 article.html 发布到小红书
你: 发布到小红书 article.html
```

## 输出目录

图片保存在 `images/{document_name}/` 目录下：

```
images/
└── 文章标题/
    ├── image_0.jpeg
    ├── image_1.jpeg
    └── image_2.jpeg
```

## HTML格式要求

### 标准格式

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>文章标题</title>
    <meta name="keywords"="话题1,话题2,话题3">
</head>
<body>
    <div class="content">
        <p>正文内容...</p>

        <p>更多内容...</p>

        <!-- Base64图片 -->
        <img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAA...">
        <img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAA...">
    </div>
</body>
</html>
```

### 提取规则

| 元素 | 提取规则 |
|------|---------|
| 标题 | `<title>`标签内容 |
| 正文 | `<div class="content">` 或 `<body>` 的文本 |
| 图片 | `data:image/*;base64,...` 格式的 `<img>` 标签 |
| 话题 | `<meta name="keywords">` 或从内容推断 |

## 项目结构

```
skills/xiaohongshu-pub/
├── SKILL.md                    # 技能文档
├── README.md                   # 本文件
├── requirements.txt            # 依赖清单
├── main_publisher.py           # 主入口
├── config.py                   # 配置管理
│
├── core/                       # 核心模块
│   ├── __init__.py
│   ├── html_extractor.py      # HTML提取
│   ├── image_processor.py     # 图片处理
│   ├── browser_publisher.py   # 浏览器自动化
│   └── validator.py           # 状态验证
│
└── utils/                      # 工具函数
    ├── __init__.py
    ├── chrome_launcher.py     # Chrome启动
    └── logger.py              # 日志管理
```

## 常见问题

### Q: Chrome连接失败

**A:** 确保Chrome已启动远程调试模式：

```batch
# 检查是否有Chrome进程
tasklist | findstr chrome.exe

# 启动远程调试
chrome.exe --remote-debugging-port=9222
```

### Q: 未找到"上传图文"选项卡

**A:** 页面可能已更新，工具会尝试继续执行。如果失败，请手动点击"上传图文"。

### Q: 图片上传失败

**A:**
1. 检查图片文件是否存在
2. 检查Chrome是否允许文件访问权限
3. 查看控制台错误信息

### Q: 发布后找不到笔记链接

**A:** 笔记链接通常在发布成功后显示。如果未自动获取，请在小红书APP中查看。

## 依赖说明

| 依赖 | 版本 | 用途 |
|------|------|------|
| beautifulsoup4 | >=4.12.0 | HTML解析 |
| lxml | >=4.9.0 | BeautifulSoup解析器 |
| selenium | >=4.15.0 | 浏览器自动化 |
| Pillow | >=10.0.0 | 图片处理 |

## 技术细节

### Chrome远程调试

Selenium连接到已有的Chrome实例，而不是启动新的浏览器：

```python
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)
```

### Base64图片提取

使用正则表达式提取Base64编码的图片：

```python
pattern = r'data:image/(jpeg|png);base64,([^"]+)'
matches = re.findall(pattern, html_content)
```

### JavaScript点击"上传图文"

由于小红书页面使用动态加载，使用JavaScript点击更可靠：

```javascript
var all = document.querySelectorAll('div, span');
for (var i = 0; i < all.length; i++) {
    if (all[i].textContent.trim() === '上传图文') {
        all[i].click();
        return true;
    }
}
```

### 循环重找文件输入框

图片上传后DOM结构变化，每次上传前重新查找元素：

```python
for path in image_paths:
    # 每次重新查找（避免stale element）
    file_inputs = driver.find_elements(By.XPATH, '//input[@type="file"]')
    file_inputs[0].send_keys(str(Path(path).absolute()))
```

## 版本历史

- **v1.0.0** (2026-03-04): 初始版本
  - HTML内容提取
  - Base64图片处理
  - Selenium自动化发布
  - 发布状态验证

## 许可

MIT License

## 作者

Created by Claude Code for MyAIProduct project.
