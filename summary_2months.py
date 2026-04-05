#!/usr/bin/env python3
"""
获取最近 2 个月的 GitHub 活动总结
"""

import json
import requests
from datetime import datetime, timedelta
from collections import defaultdict

# 读取配置
with open('config.json', 'r') as f:
    config = json.load(f)

headers = {
    'Authorization': f"token {config['github']['token']}",
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'GitHub-Monitor'
}

username = config['github']['username']
base_url = config['github']['base_url']

# 时间范围：最近 2 个月
since_date = (datetime.now() - timedelta(days=60)).isoformat()

print("=" * 70)
print(f"📊 GitHub 活动总结 ({username})")
print(f"📅 时间范围: 最近 2 个月 ({datetime.now().strftime('%Y-%m-%d')} 之前)")
print("=" * 70)
print()

# 获取用户所有仓库
print("🔍 获取仓库列表...")
repos = []
page = 1
while True:
    resp = requests.get(
        f"{base_url}/users/{username}/repos",
        headers=headers,
        params={"page": page, "per_page": 100, "sort": "updated"}
    )
    if resp.status_code != 200:
        print(f"❌ 获取仓库失败: {resp.status_code}")
        break
    
    data = resp.json()
    if not data:
        break
    
    repos.extend(data)
    if len(data) < 100:
        break
    page += 1

print(f"✅ 找到 {len(repos)} 个仓库\n")

# 统计信息
total_commits = 0
total_issues = 0
total_prs = 0
repo_activities = defaultdict(lambda: {"commits": 0, "issues": 0, "prs": 0, "last_update": ""})

# 检查每个仓库的活动
for repo in repos:
    owner = repo['owner']['login']
    name = repo['name']
    full_name = f"{owner}/{name}"
    
    print(f"📦 分析仓库: {name}...", end=" ")
    
    # 获取提交
    commits_resp = requests.get(
        f"{base_url}/repos/{owner}/{name}/commits",
        headers=headers,
        params={"since": since_date, "per_page": 100}
    )
    if commits_resp.status_code == 200:
        commits = commits_resp.json()
        total_commits += len(commits)
        repo_activities[name]["commits"] = len(commits)
    
    # 获取 Issues
    issues_resp = requests.get(
        f"{base_url}/repos/{owner}/{name}/issues",
        headers=headers,
        params={"state": "all", "since": since_date, "per_page": 100}
    )
    if issues_resp.status_code == 200:
        issues = [i for i in issues_resp.json() if 'pull_request' not in i]
        total_issues += len(issues)
        repo_activities[name]["issues"] = len(issues)
    
    # 获取 PRs
    prs_resp = requests.get(
        f"{base_url}/repos/{owner}/{name}/pulls",
        headers=headers,
        params={"state": "all", "per_page": 100}
    )
    if prs_resp.status_code == 200:
        prs = [p for p in prs_resp.json() 
               if datetime.fromisoformat(p['created_at'].replace('Z', '+00:00')) > 
                  datetime.fromisoformat(since_date)]
        total_prs += len(prs)
        repo_activities[name]["prs"] = len(prs)
    
    repo_activities[name]["last_update"] = repo['updated_at'][:10]
    print(f"✓ (提交:{repo_activities[name]['commits']}, Issues:{repo_activities[name]['issues']}, PRs:{repo_activities[name]['prs']})")

# 输出总结
print()
print("=" * 70)
print("📈 活动统计")
print("=" * 70)
print(f"📝 总提交数: {total_commits}")
print(f"🐛 总 Issues: {total_issues}")
print(f"🔀 总 Pull Requests: {total_prs}")
print(f"📦 活跃仓库数: {len([r for r in repo_activities.values() if sum(r.values()) > 0])}")
print()

# 找出最活跃的仓库
print("=" * 70)
print("🏆 最活跃的仓库 (Top 10)")
print("=" * 70)
sorted_repos = sorted(repo_activities.items(), 
                      key=lambda x: x[1]['commits'] + x[1]['issues'] + x[1]['prs'], 
                      reverse=True)

for i, (name, activity) in enumerate(sorted_repos[:10], 1):
    total = activity['commits'] + activity['issues'] + activity['prs']
    if total > 0:
        print(f"{i:2}. {name:30} | 提交:{activity['commits']:3} | Issues:{activity['issues']:3} | PRs:{activity['prs']:3} | 总计:{total}")

print()
print("=" * 70)
print("✅ 分析完成")
print("=" * 70)
