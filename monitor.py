"""
GitHub 监控器主程序
监控仓库活动并生成报告
"""

import json
import time
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from dataclasses import dataclass, asdict
from pathlib import Path

from github_client import GitHubClient


@dataclass
class ActivityEvent:
    """活动事件数据类"""
    timestamp: str
    type: str  # commit, issue, pull_request, release
    repo: str
    title: str
    url: str
    author: str
    description: str = ""


class GitHubMonitor:
    """GitHub 监控器"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.client = None
        self.data_dir = Path(self.config["storage"]["data_dir"])
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        log_file = self.config["storage"]["log_file"]
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 初始化客户端
        self._init_client()
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _init_client(self):
        """初始化 GitHub 客户端"""
        token = self.config["github"]["token"]
        # 支持环境变量引用 ${VAR_NAME}
        if token.startswith("${") and token.endswith("}"):
            env_var = token[2:-1]
            token = os.environ.get(env_var, "")
            if not token:
                self.logger.error(f"环境变量 {env_var} 未设置")
                return

        if token == "你的GitHub Personal Access Token":
            self.logger.error("请在 config.json 中配置你的 GitHub Token")
            return

        base_url = self.config["github"]["base_url"]
        self.client = GitHubClient(token, base_url)
        self.logger.info("GitHub 客户端初始化成功")
    
    def _save_data(self, data: Dict, filename: str):
        """保存数据到本地"""
        filepath = self.data_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_data(self, filename: str) -> Dict:
        """从本地加载数据"""
        filepath = self.data_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def check_rate_limit(self) -> bool:
        """检查 API 限流状态"""
        if not self.client:
            return False
        
        rate_limit = self.client.get_rate_limit()
        if rate_limit:
            remaining = rate_limit["resources"]["core"]["remaining"]
            limit = rate_limit["resources"]["core"]["limit"]
            self.logger.info(f"API 剩余请求数: {remaining}/{limit}")
            return remaining > 100
        return False
    
    def get_all_repos(self) -> List[Dict]:
        """获取所有监控的仓库"""
        if not self.client:
            return []
        
        username = self.config["github"]["username"]
        if not username or username == "你的GitHub用户名":
            self.logger.error("请在 config.json 中配置你的 GitHub 用户名")
            return []
        
        # 如果配置了特定仓库，使用配置的
        configured_repos = self.config["monitor"]["repositories"]
        if configured_repos:
            repos = []
            for repo_full_name in configured_repos:
                parts = repo_full_name.split('/')
                if len(parts) == 2:
                    owner, repo = parts
                    repo_data = self.client._make_request(f"/repos/{owner}/{repo}")
                    if repo_data:
                        repos.append(repo_data)
            return repos
        
        # 否则获取用户的所有仓库
        return self.client.get_user_repos(username)
    
    def check_repo_activity(self, owner: str, repo: str) -> List[ActivityEvent]:
        """检查单个仓库的活动"""
        events = []
        
        # 获取上次检查时间
        last_check_file = f"{owner}_{repo}_last_check.json"
        last_check_data = self._load_data(last_check_file)
        last_check_time = last_check_data.get("last_check")
        
        if last_check_time:
            since = datetime.fromisoformat(last_check_time)
        else:
            since = datetime.now() - timedelta(days=1)
        
        # 检查提交
        if self.config["monitor"]["track_commits"]:
            commits = self.client.get_repo_commits(owner, repo, since)
            for commit in commits:
                event = ActivityEvent(
                    timestamp=commit["commit"]["committer"]["date"],
                    type="commit",
                    repo=f"{owner}/{repo}",
                    title=commit["commit"]["message"][:50] + "..." if len(commit["commit"]["message"]) > 50 else commit["commit"]["message"],
                    url=commit["html_url"],
                    author=commit["commit"]["author"]["name"],
                    description=f"提交到 {repo}"
                )
                events.append(event)
        
        # 检查 Issues
        if self.config["monitor"]["track_issues"]:
            issues = self.client.get_repo_issues(owner, repo, state="all")
            for issue in issues:
                created_at = datetime.fromisoformat(issue["created_at"].replace('Z', '+00:00'))
                if created_at > since:
                    event = ActivityEvent(
                        timestamp=issue["created_at"],
                        type="issue",
                        repo=f"{owner}/{repo}",
                        title=issue["title"][:50] + "..." if len(issue["title"]) > 50 else issue["title"],
                        url=issue["html_url"],
                        author=issue["user"]["login"],
                        description=f"状态: {issue['state']}"
                    )
                    events.append(event)
        
        # 检查 Pull Requests
        if self.config["monitor"]["track_pull_requests"]:
            pulls = self.client.get_repo_pulls(owner, repo, state="all")
            for pr in pulls:
                created_at = datetime.fromisoformat(pr["created_at"].replace('Z', '+00:00'))
                if created_at > since:
                    event = ActivityEvent(
                        timestamp=pr["created_at"],
                        type="pull_request",
                        repo=f"{owner}/{repo}",
                        title=pr["title"][:50] + "..." if len(pr["title"]) > 50 else pr["title"],
                        url=pr["html_url"],
                        author=pr["user"]["login"],
                        description=f"状态: {pr['state']}"
                    )
                    events.append(event)
        
        # 更新上次检查时间
        self._save_data({"last_check": datetime.now().isoformat()}, last_check_file)
        
        return events
    
    def generate_report(self, events: List[ActivityEvent]) -> str:
        """生成活动报告"""
        if not events:
            return "📭 暂无新活动"
        
        report = f"📊 GitHub 活动报告 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n"
        report += "=" * 50 + "\n\n"
        
        # 按类型分组
        by_type = {}
        for event in events:
            if event.type not in by_type:
                by_type[event.type] = []
            by_type[event.type].append(event)
        
        for event_type, type_events in by_type.items():
            emoji = {
                "commit": "📝",
                "issue": "🐛",
                "pull_request": "🔀",
                "release": "🚀"
            }.get(event_type, "📌")
            
            report += f"{emoji} {event_type.upper()} ({len(type_events)})\n"
            report += "-" * 30 + "\n"
            
            for event in type_events[:5]:  # 只显示前5个
                time_str = event.timestamp[:10] if len(event.timestamp) > 10 else event.timestamp
                report += f"  [{time_str}] {event.title}\n"
                report += f"  👤 {event.author} | 🔗 {event.url}\n\n"
        
        return report
    
    def run_single_check(self):
        """运行单次检查"""
        if not self.client:
            self.logger.error("GitHub 客户端未初始化，请检查配置")
            return
        
        self.logger.info("开始检查 GitHub 活动...")
        
        # 检查 API 限流
        if not self.check_rate_limit():
            self.logger.warning("API 请求数不足，跳过本次检查")
            return
        
        # 获取所有仓库
        repos = self.get_all_repos()
        self.logger.info(f"找到 {len(repos)} 个仓库")
        
        all_events = []
        
        for repo in repos:
            owner = repo["owner"]["login"]
            name = repo["name"]
            self.logger.info(f"检查仓库: {owner}/{name}")
            
            events = self.check_repo_activity(owner, name)
            all_events.extend(events)
        
        # 保存所有事件
        if all_events:
            events_data = [asdict(e) for e in all_events]
            self._save_data(events_data, f"events_{datetime.now().strftime('%Y%m%d')}.json")
            
            # 生成报告
            report = self.generate_report(all_events)
            print("\n" + report)
            
            # 保存报告
            report_file = self.data_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.logger.info(f"报告已保存到: {report_file}")
        else:
            self.logger.info("没有新活动")
    
    def run_continuous(self):
        """持续运行监控"""
        interval = self.config["monitor"]["check_interval_minutes"]
        self.logger.info(f"开始持续监控，检查间隔: {interval} 分钟")
        
        while True:
            self.run_single_check()
            self.logger.info(f"下次检查时间: {(datetime.now() + timedelta(minutes=interval)).strftime('%H:%M')}")
            time.sleep(interval * 60)


if __name__ == "__main__":
    monitor = GitHubMonitor()
    
    # 运行单次检查
    monitor.run_single_check()
    
    # 或者持续运行（取消下面注释）
    # monitor.run_continuous()
