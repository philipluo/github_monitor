#!/usr/bin/env python3
"""
GitHub 监控程序启动脚本
"""

import sys
import os

# 确保可以导入本地模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor import GitHubMonitor
from notifier import Notifier, Notification


def print_banner():
    """打印启动横幅"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║              GitHub 监控程序 v1.0                          ║
    ║                                                           ║
    ║  监控你的 GitHub 仓库活动，及时获取提交、Issues、PR 等通知   ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_config():
    """检查配置文件"""
    config_file = "config.json"
    
    if not os.path.exists(config_file):
        print(f"❌ 配置文件不存在: {config_file}")
        print("请复制 config.json.example 为 config.json 并填写你的 GitHub Token")
        return False
    
    import json
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    token = config.get("github", {}).get("token", "")
    if token == "你的GitHub Personal Access Token" or not token:
        print("❌ 请在 config.json 中配置你的 GitHub Token")
        print("获取 Token: https://github.com/settings/tokens")
        return False
    
    return True


def main():
    """主函数"""
    print_banner()
    
    if not check_config():
        print("\n配置检查失败，请检查 config.json")
        sys.exit(1)
    
    print("✅ 配置检查通过\n")
    
    try:
        monitor = GitHubMonitor()
        
        print("🔍 正在检查 GitHub 活动...")
        print("-" * 50)
        
        monitor.run_single_check()
        
        print("-" * 50)
        print("✅ 检查完成")
        
    except KeyboardInterrupt:
        print("\n\n👋 程序已终止")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
