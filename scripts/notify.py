# -*- coding: utf-8 -*-
# claude_notify.py - Claude声音通知脚本
import sys
import winsound
import time

def play_sound(sound_type='SystemExclamation'):
    """播放Windows系统声音"""
    try:
        winsound.PlaySound(sound_type, winsound.SND_ALIAS)
        print(f"[Sound] Played: {sound_type}")
    except Exception as e1:
        print(f"[Sound] System sound failed: {e1}, trying beep...")
        try:
            winsound.Beep(1000, 500)  # 频率1000Hz，持续500ms
            print("[Sound] Beep played")
        except Exception as e2:
            print(f"[Sound] Beep failed: {e2}")

def send_toast(title, message, duration):
    """发送桌面通知"""
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(title, message, duration=duration, threaded=True)
        print(f"[Toast] Sent: {title} - {message}")
    except ImportError:
        print(f"[Toast] {title}: {message} (win10toast not installed)")
    except Exception as e:
        print(f"[Toast] Error: {e}")

def main():
    if len(sys.argv) < 2:
        print("[Error] Missing message parameter")
        return

    message = sys.argv[1]
    msg_lower = message.lower()

    # 场景判断
    # 1. 【任务完成】 - 立即提醒
    if "任务" in msg_lower and ("完成" in msg_lower or "结束" in msg_lower):
        title = "[Task Complete]"
        sound = "SystemAsterisk"
        play_sound(sound)
        send_toast(title, message, 3)

    # 2. 【等待输入】 - 立即提醒
    elif "等待" in msg_lower or "输入" in msg_lower:
        title = "[Waiting Input]"
        sound = "SystemQuestion"
        play_sound(sound)
        send_toast(title, message, 3)

    # 3. 【权限确认】 - 立即提醒
    elif "权限" in msg_lower or "确认" in msg_lower or "选择" in msg_lower:
        title = "[Permission Needed]"
        sound = "SystemHand"
        play_sound(sound)
        send_toast(title, message, 5)

    # 4. 【其他/默认】
    else:
        title = "[Claude Notification]"
        sound = "SystemExclamation"
        play_sound(sound)
        send_toast(title, message, 3)

if __name__ == "__main__":
    main()
