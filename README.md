# GitHub 监控程序

监控你的 GitHub 仓库活动，及时获取提交、Issues、Pull Requests 等通知。

## 功能特性

- 📊 监控多个 GitHub 仓库
- 📝 跟踪提交记录
- 🐛 跟踪 Issues 状态
- 🔀 跟踪 Pull Requests
- 🚀 跟踪 Releases
- 🔔 桌面通知提醒
- 📈 生成活动报告

## 项目结构

```
github_monitor/
├── config.json          # 配置文件
├── github_client.py     # GitHub API 客户端
├── monitor.py          # 监控器主程序
├── notifier.py         # 通知模块
├── run.py              # 启动脚本
├── run.command         # 双击运行（macOS）
├── README.md           # 说明文档
├── data/               # 数据存储目录
└── logs/               # 日志目录
```

## 快速开始

### 1. 配置 GitHub Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择以下权限：
   - `repo` - 访问仓库
   - `notifications` - 访问通知
4. 复制生成的 Token

### 2. 修改配置文件

编辑 `config.json`：

```json
{
  "github": {
    "username": "你的GitHub用户名",
    "token": "你的GitHub Token"
  }
}
```

### 3. 运行程序

**方式一：双击运行**
- 双击 `run.command` 文件

**方式二：命令行运行**
```bash
cd /Users/philipluo/WorkBuddy/Claw/github_monitor
python3 run.py
```

## 配置说明

### 监控范围

在 `config.json` 中配置：

```json
{
  "monitor": {
    "repositories": [],  // 空数组表示监控所有仓库，或指定 ["owner/repo1", "owner/repo2"]
    "track_commits": true,      // 跟踪提交
    "track_issues": true,       // 跟踪 Issues
    "track_pull_requests": true, // 跟踪 PR
    "track_releases": true      // 跟踪 Releases
  }
}
```

### 通知设置

```json
{
  "notifications": {
    "desktop": true,      // 桌面通知
    "sound": true,        // 声音提醒
    "summary_report": true, // 每日摘要
    "summary_time": "18:00" // 摘要时间
  }
}
```

## 使用说明

### 单次检查
运行程序会执行一次检查并生成报告。

### 持续监控
修改 `run.py`，取消注释最后一行：
```python
monitor.run_continuous()  # 持续运行
```

### 查看报告
- 报告保存在 `data/` 目录
- 文件名格式：`report_YYYYMMDD_HHMM.txt`

## 常见问题

**Q: 提示 "API 请求数不足"**
A: GitHub API 有限流，未认证 60 次/小时，认证后 5000 次/小时。

**Q: 如何获取 GitHub Token？**
A: 访问 https://github.com/settings/tokens → Generate new token

**Q: 如何监控私有仓库？**
A: 确保 Token 有 `repo` 权限。

## License

MIT License
