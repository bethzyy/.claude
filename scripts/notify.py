# -*- coding: utf-8 -*-
# notify.py - Claude声音通知脚本（简化版）
import sys
import winsound

def main():
    if len(sys.argv) < 2:
        return

    # 统一使用 SystemAsterisk 声音（清脆提示音）
    try:
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
    except:
        pass

if __name__ == "__main__":
    main()
