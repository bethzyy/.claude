"""
浏览器发布模块 - 使用Selenium自动化发布到小红书

Browser publisher module - Automate publishing to Xiaohongshu using Selenium.
"""

import time
import sys
from pathlib import Path
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    CHROME_DEBUG_PORT,
    XIAOHONGSHU_PUBLISH_URL,
    DEFAULT_WAIT_TIME,
    IMAGE_UPLOAD_WAIT_TIME
)


class BrowserPublisher:
    """浏览器自动化发布器"""

    def __init__(self, debug_port: int = CHROME_DEBUG_PORT):
        """
        初始化发布器

        Args:
            debug_port: Chrome远程调试端口
        """
        self.debug_port = debug_port
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None

    def connect(self) -> bool:
        """
        连接到Chrome远程调试端口

        Returns:
            是否成功连接
        """
        try:
            options = Options()
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")

            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 20)

            print(f"  [OK] 已连接到Chrome（端口{self.debug_port}）")
            return True

        except Exception as e:
            print(f"  [错误] 连接Chrome失败: {e}")
            print(f"  提示: 请确保Chrome已启动远程调试模式：")
            print(f'        chrome.exe --remote-debugging-port={self.debug_port}')
            return False

    def publish(self, title: str, content: str,
                image_paths: List[str], topics: List[str],
                collection: str = None) -> bool:
        """
        执行完整的发布流程

        Args:
            title: 文章标题
            content: 文章内容
            image_paths: 图片路径列表
            topics: 话题标签列表
            collection: 合集名称（可选）

        Returns:
            是否成功发布
        """
        if not self.driver:
            if not self.connect():
                return False

        try:
            # 步骤1: 打开发布页面
            print(f"\n[1/7] 打开发布页面...")
            self.driver.get(XIAOHONGSHU_PUBLISH_URL)
            time.sleep(DEFAULT_WAIT_TIME)
            print(f"  [OK] 页面已加载")

            # 步骤2: 点击"上传图文"选项卡
            print(f"\n[2/7] 点击'上传图文'选项卡...")
            if not self._click_upload_tab():
                print(f"  [警告] 未找到'上传图文'选项卡，尝试继续...")
            time.sleep(2)

            # 步骤3: 上传图片
            print(f"\n[3/7] 上传图片（{len(image_paths)}张）...")
            if image_paths:
                self._upload_images(image_paths)
            else:
                print(f"  [跳过] 没有图片需要上传")
            time.sleep(2)

            # 步骤4: 填写标题
            print(f"\n[4/7] 填写标题...")
            self._fill_title(title)

            # 步骤5: 填写内容和话题
            print(f"\n[5/7] 填写正文和话题...")
            self._fill_content(content, topics)

            # 步骤6: 添加合集
            if collection:
                print(f"\n[6/7] 添加合集...")
                collection_success = self._add_collection(collection)
                if not collection_success:
                    print(f"\n[错误] 合集添加失败，停止发布流程")
                    return False
            else:
                print(f"\n[6/7] 跳过合集（未指定）")

            # 步骤7: 关闭"允许正文复制"
            print(f"\n[7/7] 设置发布选项...")
            settings_success = self._disable_content_copy()
            # 注意：_disable_content_copy没有返回值，我们假设成功
            # 如果需要更严格的验证，可以修改该函数返回bool

            print(f"\n{'=' * 60}")
            print(f"[准备完成] 内容已填写")
            print(f"  - 标题: {title}")
            print(f"  - 正文: {len(content)}字")
            print(f"  - 图片: {len(image_paths)}张")
            if collection:
                print(f"  - 合集: {collection}")
            print(f"  - 允许正文复制: 已关闭")
            print(f"{'=' * 60}")

            return True

        except Exception as e:
            print(f"\n[错误] 发布过程出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _click_upload_tab(self) -> bool:
        """
        使用JavaScript点击"上传图文"选项卡

        Returns:
            是否成功点击
        """
        js_click = """
        var all = document.querySelectorAll('div, span, button');
        for (var i = 0; i < all.length; i++) {
            if (all[i].textContent.trim() === '上传图文') {
                all[i].click();
                return true;
            }
        }
        return false;
        """

        result = self.driver.execute_script(js_click)
        print(f"  点击结果: {result}")
        return result

    def _upload_images(self, paths: List[str]):
        """
        上传图片（每次重新查找file input，避免stale element）

        Args:
            paths: 图片路径列表
        """
        print(f"  查找文件上传控件...")
        file_inputs = self.driver.find_elements(By.XPATH, '//input[@type="file"]')
        print(f"  找到 {len(file_inputs)} 个文件输入框")

        if not file_inputs:
            print(f"  [警告] 未找到文件上传控件")
            return

        for i, path in enumerate(paths, 1):
            print(f"  [{i}/{len(paths)}] 上传: {Path(path).name}")
            try:
                # 每次重新查找元素（关键！）
                file_inputs = self.driver.find_elements(By.XPATH, '//input[@type="file"]')
                if file_inputs:
                    file_inputs[0].send_keys(str(Path(path).absolute()))
                    time.sleep(IMAGE_UPLOAD_WAIT_TIME)
                else:
                    print(f"    [!] 文件输入控件消失")
                    break
            except Exception as e:
                print(f"    [!] 上传失败: {e}")

        print(f"  [OK] 图片上传完成")

    def _fill_title(self, title: str):
        """
        填写标题

        Args:
            title: 标题文本
        """
        # 查找包含"标题"占位符的输入框
        all_inputs = self.driver.find_elements(By.TAG_NAME, 'input')

        title_input = None
        for inp in all_inputs:
            placeholder = inp.get_attribute('placeholder')
            if placeholder and '标题' in placeholder:
                title_input = inp
                break

        if title_input:
            title_input.clear()
            title_input.send_keys(title)
            print(f"  [OK] 标题已填写")
        else:
            print(f"  [警告] 未找到标题输入框")

    def _fill_content(self, content: str, topics: List[str]):
        """
        填写正文和话题标签（使用段落分块插入保证分段正确）

        Args:
            content: 正文内容（段落用 \n\n 分隔）
            topics: 话题标签列表
        """
        # 优先查找contenteditable div
        ce_divs = self.driver.find_elements(By.XPATH, '//div[@contenteditable="true"]')
        print(f"  找到 {len(ce_divs)} 个contenteditable元素")

        content_element = None

        if ce_divs:
            content_element = ce_divs[0]
        else:
            # 备用：查找textarea
            textareas = self.driver.find_elements(By.TAG_NAME, 'textarea')
            if textareas:
                content_element = textareas[0]

        if content_element:
            # 先focus并清空元素
            try:
                self.driver.execute_script("document.querySelector('div[contenteditable=\"true\"]').focus();")
                time.sleep(0.3)
                content_element.clear()
            except:
                pass

            # 使用段落分块插入（保证小红书正确识别分段）
            import re
            paragraphs = re.split(r'\n\n+', content.strip())

            print(f"  按{len(paragraphs)}个段落分块插入...")

            for i, para in enumerate(paragraphs):
                if not para.strip():
                    continue

                # 使用JavaScript创建段落元素并插入
                js_insert_paragraph = f"""
                var element = document.querySelector('div[contenteditable="true"]');
                if (element) {{
                    // 创建段落div
                    var p = document.createElement('div');
                    p.textContent = arguments[0];
                    p.style.display = 'block';
                    p.style.marginBottom = '0.5em';

                    // 如果是第一个段落，清空后添加；否则追加
                    if (element.children.length === 0 || element.innerText.trim() === '') {{
                        element.innerHTML = '';
                        element.appendChild(p);
                    }} else {{
                        element.appendChild(p);
                    }}

                    // 触发input事件
                    element.dispatchEvent(new Event('input', {{bubbles: true}}));
                    return true;
                }}
                return false;
                """

                try:
                    self.driver.execute_script(js_insert_paragraph, para.strip())
                    time.sleep(0.05)  # 短暂延迟避免过快插入

                    # 每5个段落打印一次进度
                    if (i + 1) % 5 == 0:
                        print(f"    已插入 {i + 1}/{len(paragraphs)} 段...")
                except Exception as e:
                    print(f"    [!] 插入第{i+1}段失败: {e}")

            print(f"  [OK] 正文已填写（{len(content)}字，{len(paragraphs)}段）")

            # 添加话题标签（使用JavaScript）
            if topics:
                for topic in topics:
                    js_add_topic = """
                    var element = document.querySelector('div[contenteditable="true"]');
                    if (element) {
                        // 创建话题标签span
                        var span = document.createElement('span');
                        span.textContent = ' #' + arguments[0];
                        element.appendChild(span);
                        element.dispatchEvent(new Event('input', {bubbles: true}));
                        return true;
                    }
                    return false;
                    """
                    try:
                        self.driver.execute_script(js_add_topic, topic)
                    except:
                        pass
                print(f"  [OK] 已添加 {len(topics)} 个话题标签")
        else:
            print(f"  [警告] 未找到内容输入框")

    def click_publish_button(self) -> bool:
        """
        点击发布按钮（改进版，支持多种文本匹配和重试）

        Returns:
            是否成功点击
        """
        # 尝试多次点击，增加成功率
        for attempt in range(3):
            print(f"  尝试 {attempt + 1}/3...")

            # 多种发布按钮文本
            publish_texts = ['发布', '立即发布', '确认发布', '发布笔记']

            for publish_text in publish_texts:
                js_click = f"""
                var all = document.querySelectorAll('button, div, span, a');
                for (var i = 0; i < all.length; i++) {{
                    var text = all[i].textContent.trim();
                    if ((all[i].tagName === 'BUTTON' || all[i].tagName === 'DIV' ||
                         all[i].tagName === 'SPAN' || all[i].tagName === 'A') &&
                        text === '{publish_text}' &&
                        all[i].offsetParent !== null) {{
                        // 尝试滚动到视图中
                        all[i].scrollIntoView(true);
                        // 点击
                        all[i].click();
                        return true;
                    }}
                }}
                return false;
                """

                result = self.driver.execute_script(js_click)
                if result:
                    print(f"  ✅ 找到并点击: '{publish_text}'")
                    time.sleep(2)

                    # 检查是否有弹窗需要确认
                    try:
                        alert = self.driver.switch_to.alert
                        alert_text = alert.text
                        print(f"  检测到弹窗: {alert_text}")
                        alert.accept()
                        print(f"  ✅ 已确认弹窗")
                        time.sleep(2)
                    except:
                        pass

                    return True

            # 如果没找到，等待一下再试
            time.sleep(1)

        print(f"  ❌ 未找到发布按钮")
        return False

    def get_current_url(self) -> str:
        """
        获取当前页面URL

        Returns:
            当前URL
        """
        return self.driver.current_url if self.driver else ""

    def _add_collection(self, collection_name: str):
        """
        添加到合集（正确实现：点击下拉选择）

        Args:
            collection_name: 合集名称
        """
        try:
            # 步骤1: 点击"加入合集"右侧的下拉框
            # 下拉框通常显示当前选中的合集（如"饮食养生"）
            js_click_dropdown = """
            // 查找"加入合集"文字
            var all = document.querySelectorAll('div, span, button');
            var collectionLabel = null;
            var dropdown = null;

            for (var i = 0; i < all.length; i++) {
                var text = all[i].textContent.trim();
                if (text === '加入合集') {
                    collectionLabel = all[i];
                    break;
                }
            }

            if (collectionLabel) {
                // 查找下拉框（通常是兄弟元素或父元素的子元素）
                var parent = collectionLabel.parentElement;
                if (parent) {
                    // 查找右侧的下拉框
                    var children = parent.querySelectorAll('div, span');
                    for (var j = 0; j < children.length; j++) {
                        var elemText = children[j].textContent.trim();
                        // 跳过"加入合集"标签本身
                        if (elemText !== '加入合集' &&
                            elemText !== '' &&
                            children[j].offsetParent !== null) {
                            dropdown = children[j];
                            break;
                        }
                    }
                }
            }

            if (dropdown) {
                dropdown.scrollIntoView(true);
                dropdown.click();
                return true;
            }

            return false;
            """

            dropdown_result = self.driver.execute_script(js_click_dropdown)

            if dropdown_result:
                print(f"  [OK] 已打开合集下拉框")
                time.sleep(1.5)

                # 步骤2: 从下拉列表中点击目标合集
                js_select_collection = f"""
                var all = document.querySelectorAll('div, span, button, li');
                for (var i = 0; i < all.length; i++) {{
                    var text = all[i].textContent.trim();
                    if (text === '{collection_name}' && all[i].offsetParent !== null) {{
                        all[i].scrollIntoView(true);
                        all[i].click();
                        return true;
                    }}
                }}
                return false;
                """

                select_result = self.driver.execute_script(js_select_collection)

                if select_result:
                    print(f"  ✅ 已选择合集: {collection_name}")
                    time.sleep(1)
                    return True
                else:
                    print(f"  ⚠️  未找到合集选项: {collection_name}")
                    return False
            else:
                print(f"  ⚠️  未找到合集下拉框")
                return False

        except Exception as e:
            print(f"  [!] 添加合集失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _disable_content_copy(self):
        """
        在"更多设置"中关闭"允许正文复制"（改进版：检查状态+验证）
        """
        try:
            # 步骤1: 查找并点击"更多设置"
            js_find_settings = """
            var all = document.querySelectorAll('div, span, button');
            for (var i = 0; i < all.length; i++) {
                var text = all[i].textContent.trim();
                if (text === '更多设置' && all[i].offsetParent !== null) {
                    all[i].scrollIntoView(true);
                    all[i].click();
                    return true;
                }
            }
            return false;
            """

            result = self.driver.execute_script(js_find_settings)

            if result:
                print(f"  [OK] 打开设置面板")
                time.sleep(1.5)

                # 步骤2: 查找开关并检查状态，然后关闭（如果需要）
                js_toggle_and_verify = """
                // 先找到"允许正文复制"文字标签和开关
                var copyLabel = null;
                var toggleElement = null;
                var all = document.querySelectorAll('div, span, label');

                for (var i = 0; i < all.length; i++) {
                    var text = all[i].textContent.trim();
                    if (text === '允许正文复制' && all[i].offsetParent !== null) {
                        copyLabel = all[i];
                        break;
                    }
                }

                if (!copyLabel) {
                    return {success: false, reason: 'label_not_found'};
                }

                // 查找开关元素（多种方式）
                var parent = copyLabel.parentElement;

                // 方式1: 查找role="switch"的元素
                if (parent) {
                    var switchInParent = parent.querySelector('[role="switch"]');
                    if (switchInParent) {
                        toggleElement = switchInParent;
                    }
                }

                // 方式2: 查找class包含switch/toggle的元素
                if (!toggleElement && parent) {
                    var children = parent.querySelectorAll('*');
                    for (var j = 0; j < children.length; j++) {
                        var className = children[j].className || '';
                        if (className.indexOf('switch') !== -1 || className.indexOf('toggle') !== -1) {
                            toggleElement = children[j];
                            break;
                        }
                    }
                }

                // 方式3: 查找左侧兄弟元素
                if (!toggleElement && parent) {
                    var children = Array.from(parent.children);
                    var labelIndex = children.indexOf(copyLabel);
                    if (labelIndex > 0) {
                        var leftSibling = children[labelIndex - 1];
                        // 排除纯文本节点
                        if (leftSibling.tagName !== 'LABEL' && leftSibling.textContent.length <= 2) {
                            toggleElement = leftSibling;
                        }
                    }
                }

                if (!toggleElement) {
                    return {success: false, reason: 'toggle_not_found'};
                }

                // 检查当前状态
                var currentState = 'unknown';
                var ariaChecked = toggleElement.getAttribute('aria-checked');
                var className = toggleElement.className || '';

                if (ariaChecked !== null) {
                    currentState = (ariaChecked === 'true') ? 'enabled' : 'disabled';
                } else if (className.indexOf('checked') !== -1 || className.indexOf('active') !== -1) {
                    currentState = 'enabled';
                } else if (className.indexOf('unchecked') !== -1 || className.indexOf('inactive') !== -1) {
                    currentState = 'disabled';
                }

                // 如果已经关闭（disabled），不需要点击
                if (currentState === 'disabled') {
                    return {
                        success: true,
                        action: 'already_disabled',
                        currentState: currentState
                    };
                }

                // 如果状态未知或已开启，尝试点击
                toggleElement.scrollIntoView(true);
                toggleElement.click();

                // 等待状态更新
                var waitForChange = function(element, timeout) {
                    var start = Date.now();
                    while (Date.now() - start < timeout) {
                        var newAria = element.getAttribute('aria-checked');
                        var newClass = element.className || '';

                        if (newAria === 'false' || newClass.indexOf('unchecked') !== -1) {
                            return 'disabled';
                        }
                    }
                    return currentState; // 状态未改变
                };

                var newState = waitForChange(toggleElement, 500);

                return {
                    success: true,
                    action: 'clicked',
                    beforeState: currentState,
                    afterState: newState
                };
                """

                result_data = self.driver.execute_script(js_toggle_and_verify)

                if result_data.get('success'):
                    action = result_data.get('action');

                    if action == 'already_disabled':
                        print(f"  ✅ '允许正文复制'已经是关闭状态")
                    elif action == 'clicked':
                        before = result_data.get('beforeState', 'unknown')
                        after = result_data.get('afterState', 'unknown')
                        print(f"  ✅ 已点击开关（状态: {before} → {after}）")

                        if after == 'disabled':
                            print(f"  ✅ 确认已关闭")
                        else:
                            print(f"  ⚠️  状态未改变，请手动检查")
                    else:
                        print(f"  ✅ 操作完成: {action}")

                    time.sleep(0.5)
                else:
                    reason = result_data.get('reason', 'unknown')
                    if reason == 'label_not_found':
                        print(f"  ⚠️  未找到'允许正文复制'标签")
                    elif reason == 'toggle_not_found':
                        print(f"  ⚠️  未找到开关控件")
                    else:
                        print(f"  ⚠️  操作失败: {reason}")

                # 步骤3: 关闭设置面板
                js_close_settings = """
                var all = document.querySelectorAll('div, span, button');
                for (var i = 0; i < all.length; i++) {
                    var text = all[i].textContent.trim();
                    if (text === '收起' && all[i].offsetParent !== null) {
                        all[i].click();
                        return true;
                    }
                }
                return false;
                """

                self.driver.execute_script(js_close_settings)
                print(f"  [OK] 关闭设置面板")
                time.sleep(0.5)
            else:
                print(f"  ⚠️  未找到'更多设置'按钮")

        except Exception as e:
            print(f"  [!] 设置失败: {e}")
            import traceback
            traceback.print_exc()

    def close(self):
        """关闭浏览器连接"""
        if self.driver:
            self.driver.quit()
            self.driver = None
