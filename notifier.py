"""
通知模块
支持桌面通知、声音提醒等
"""

import os
import platform
from datetime import datetime
from typing import List
from dataclasses import dataclass


@dataclass
class Notification:
    """通知数据类"""
    title: str
    message: str
    icon: str = ""
    sound: bool = True


class Notifier:
    """通知器类"""
    
    def __init__(self, enable_desktop: bool = True, enable_sound: bool = True):
        self.enable_desktop = enable_desktop
        self.enable_sound = enable_sound
        self.system = platform.system()
    
    def send_desktop_notification(self, notification: Notification):
        """发送桌面通知"""
        if not self.enable_desktop:
            return
        
        if self.system == "Darwin":  # macOS
            self._send_macos_notification(notification)
        elif self.system == "Windows":
            self._send_windows_notification(notification)
        elif self.system == "Linux":
            self._send_linux_notification(notification)
    
    def _send_macos_notification(self, notification: Notification):
        """macOS 通知"""
        try:
            title = notification.title.replace('"', '\\"')
            message = notification.message.replace('"', '\\"')
            
            script = f'''
            display notification "{message}" with title "{title}" sound name "Glass"
            '''
            
            os.system(f'osascript -e \'{script}\'')
        except Exception as e:
            print(f"发送通知失败: {e}")
    
    def _send_windows_notification(self, notification: Notification):
        """Windows 通知"""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                notification.title,
                notification.message,
                duration=10,
                threaded=True
            )
        except ImportError:
            # 如果没有 win10toast，使用 PowerShell
            title = notification.title.replace('"', '`"')
            message = notification.message.replace('"', '`"')
            cmd = f'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show(\'{message}\', \'{title}\')"'
            os.system(cmd)
        except Exception as e:
            print(f"发送通知失败: {e}")
    
    def _send_linux_notification(self, notification: Notification):
        """Linux 通知"""
        try:
            title = notification.title.replace('"', '\\"')
            message = notification.message.replace('"', '\\"')
            os.system(f'notify-send "{title}" "{message}"')
        except Exception as e:
            print(f"发送通知失败: {e}")
    
    def play_sound(self, sound_type: str = "default"):
        """播放声音"""
        if not self.enable_sound:
            return
        
        if self.system == "Darwin":
            # macOS 系统声音
            sounds = {
                "default": "Glass",
                "success": "Hero",
                "alert": "Sosumi",
                "error": "Basso"
            }
            sound = sounds.get(sound_type, "Glass")
            os.system(f'afplay /System/Library/Sounds/{sound}.aiff')
        
        elif self.system == "Windows":
            import winsound
            sounds = {
                "default": winsound.MB_OK,
                "success": winsound.MB_ICONASTERISK,
                "alert": winsound.MB_ICONEXCLAMATION,
                "error": winsound.MB_ICONHAND
            }
            winsound.MessageBeep(sounds.get(sound_type, winsound.MB_OK))
        
        elif self.system == "Linux":
            os.system(f'paplay /usr/share/sounds/freedesktop/stereo/{sound_type}.oga')
    
    def notify_new_activity(self, count: int, repos: List[str]):
        """通知有新活动"""
        title = "GitHub 监控"
        
        if count == 1:
            message = f"在 {repos[0]} 发现 1 个新活动"
        else:
            repo_str = ", ".join(repos[:3])
            if len(repos) > 3:
                repo_str += f" 等 {len(repos)} 个仓库"
            message = f"在 {repo_str} 发现 {count} 个新活动"
        
        notification = Notification(
            title=title,
            message=message,
            sound=True
        )
        
        self.send_desktop_notification(notification)
        self.play_sound("success")
    
    def notify_daily_summary(self, total_events: int, summary: str):
        """发送每日摘要"""
        title = "GitHub 每日摘要"
        message = f"今天共有 {total_events} 个活动\n{summary}"
        
        notification = Notification(
            title=title,
            message=message,
            sound=False
        )
        
        self.send_desktop_notification(notification)


if __name__ == "__main__":
    # 测试通知
    notifier = Notifier()
    
    test_notification = Notification(
        title="GitHub 监控测试",
        message="这是一个测试通知",
        sound=True
    )
    
    notifier.send_desktop_notification(test_notification)
    notifier.play_sound("default")
    
    print("测试通知已发送")
