"""
GitHub API 客户端
处理与 GitHub API 的所有交互
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class GitHubClient:
    """GitHub API 客户端类"""
    
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        self.token = token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Monitor/1.0"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """发送 API 请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            return None
    
    def get_user_info(self) -> Optional[Dict]:
        """获取当前用户信息"""
        return self._make_request("/user")
    
    def get_user_repos(self, username: str, per_page: int = 100) -> List[Dict]:
        """获取用户的所有仓库"""
        repos = []
        page = 1
        
        while True:
            params = {
                "page": page,
                "per_page": per_page,
                "sort": "updated",
                "direction": "desc"
            }
            
            endpoint = f"/users/{username}/repos"
            data = self._make_request(endpoint, params)
            
            if not data:
                break
            
            repos.extend(data)
            
            if len(data) < per_page:
                break
            
            page += 1
        
        return repos
    
    def get_repo_commits(self, owner: str, repo: str, since: datetime = None) -> List[Dict]:
        """获取仓库的提交记录"""
        params = {"per_page": 100}
        if since:
            params["since"] = since.isoformat()
        
        endpoint = f"/repos/{owner}/{repo}/commits"
        data = self._make_request(endpoint, params)
        return data if data else []
    
    def get_repo_issues(self, owner: str, repo: str, state: str = "all") -> List[Dict]:
        """获取仓库的 Issues"""
        params = {
            "state": state,
            "per_page": 100,
            "sort": "updated",
            "direction": "desc"
        }
        
        endpoint = f"/repos/{owner}/{repo}/issues"
        data = self._make_request(endpoint, params)
        return data if data else []
    
    def get_repo_pulls(self, owner: str, repo: str, state: str = "all") -> List[Dict]:
        """获取仓库的 Pull Requests"""
        params = {
            "state": state,
            "per_page": 100,
            "sort": "updated",
            "direction": "desc"
        }
        
        endpoint = f"/repos/{owner}/{repo}/pulls"
        data = self._make_request(endpoint, params)
        return data if data else []
    
    def get_repo_releases(self, owner: str, repo: str) -> List[Dict]:
        """获取仓库的 Releases"""
        endpoint = f"/repos/{owner}/{repo}/releases"
        data = self._make_request(endpoint, {"per_page": 10})
        return data if data else []
    
    def get_notifications(self, all_notifications: bool = False) -> List[Dict]:
        """获取用户的 GitHub 通知"""
        params = {
            "all": all_notifications,
            "per_page": 50
        }
        
        endpoint = "/notifications"
        data = self._make_request(endpoint, params)
        return data if data else []
    
    def get_rate_limit(self) -> Optional[Dict]:
        """获取 API 限流信息"""
        return self._make_request("/rate_limit")


if __name__ == "__main__":
    # 测试代码
    import os
    
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        client = GitHubClient(token)
        user_info = client.get_user_info()
        if user_info:
            print(f"用户名: {user_info.get('login')}")
            print(f"仓库数: {user_info.get('public_repos')}")
    else:
        print("请设置 GITHUB_TOKEN 环境变量")
