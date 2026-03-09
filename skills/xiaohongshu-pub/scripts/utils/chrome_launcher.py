"""
Chrome启动器 - 检查和启动Chrome远程调试模式

Chrome launcher - Check and launch Chrome with remote debugging.
"""

import subprocess
import time
import sys
from pathlib import Path


class ChromeLauncher:
    """Chrome浏览器启动器"""

    def __init__(self, debug_port: int = 9222):
        """
        初始化启动器

        Args:
            debug_port: 远程调试端口
        """
        self.debug_port = debug_port
        self.chrome_exe = self._find_chrome()

    def _find_chrome(self) -> str:
        """
        查找Chrome可执行文件路径

        Returns:
            Chrome可执行文件路径
        """
        # Windows常见的Chrome路径
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(
                Path.home().stem
            ),
        ]

        for path in possible_paths:
            if Path(path).exists():
                return path

        # 如果找不到，返回'chrome.exe'（假设在PATH中）
        return "chrome.exe"

    def is_chrome_running(self) -> bool:
        """
        检查Chrome是否已在运行

        Returns:
            是否运行中
        """
        try:
            import psutil
            for proc in psutil.process_iter(['name', 'cmdline']):
                if proc.info['name'] and 'chrome.exe' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and f'--remote-debugging-port={self.debug_port}' in ' '.join(cmdline):
                        return True
            return False
        except ImportError:
            # 没有psutil，使用备用方法
            return False

    def launch_chrome(self, url: str = None) -> bool:
        """
        启动Chrome远程调试模式

        Args:
            url: 启动后打开的URL（可选）

        Returns:
            是否成功启动
        """
        if self.is_chrome_running():
            print(f"[OK] Chrome已在运行（端口{self.debug_port}）")
            return True

        print(f"[启动] Chrome远程调试模式（端口{self.debug_port}）...")

        # 构建启动命令
        cmd = [
            self.chrome_exe,
            f"--remote-debugging-port={self.debug_port}",
            "--profile-directory=Default"
        ]

        if url:
            cmd.append(url)

        try:
            # 启动Chrome（不等待）
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )

            # 等待Chrome启动
            print("  等待Chrome启动...")
            time.sleep(3)

            print("  [OK] Chrome已启动")
            return True

        except Exception as e:
            print(f"  [错误] 启动失败: {e}")
            return False

    def get_launch_command(self, url: str = None) -> str:
        """
        获取Chrome启动命令（供用户手动执行）

        Args:
            url: 启动后打开的URL（可选）

        Returns:
            启动命令字符串
        """
        cmd = f'"{self.chrome_exe}" --remote-debugging-port={self.debug_port}'
        if url:
            cmd += f' "{url}"'
        return cmd
