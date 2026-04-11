# Operations Guide

本文档说明UCO系统的日常运维操作。

## Web管理界面持久服务

UCO的Web管理界面（API Server + Dashboard）可通过macOS launchd配置为持久服务，实现开机自启和自动重启。

### 服务配置

**配置文件位置**:
- `~/Library/LaunchAgents/com.uco.api.server.plist` - API Server服务
- `~/Library/LaunchAgents/com.uco.dashboard.plist` - Dashboard服务

**启动脚本位置**:
- `~/.venv/bin/uco-api-server` - API Server启动脚本
- `~/.venv/bin/uco-dashboard` - Dashboard启动脚本

**日志文件位置**:
- `logs/api-server.log` - API Server标准输出
- `logs/api-server-error.log` - API Server错误输出
- `logs/dashboard.log` - Dashboard标准输出
- `logs/dashboard-error.log` - Dashboard错误输出

### 服务特性

- **RunAtLoad**: 用户登录时自动启动
- **KeepAlive**: 进程退出时自动重启（包括崩溃和手动kill）
- **ThrottleInterval**: 10秒（防止频繁重启）
- **ExitTimeOut**: 5秒（优雅退出等待时间）

### 服务管理命令

**查看服务状态**:
```bash
# 查看所有UCO服务
launchctl list | grep com.uco

# 输出示例：
# -	1	com.uco.dashboard
# -	1	com.uco.api.server
```

**查看端口占用**:
```bash
# API Server端口
lsof -i :8000

# Dashboard端口
lsof -i :3000
```

**查看实时日志**:
```bash
# API Server日志
tail -f logs/api-server.log

# Dashboard日志
tail -f logs/dashboard.log

# 错误日志
tail -f logs/api-server-error.log
tail -f logs/dashboard-error.log
```

**停止服务**:

临时停止（直到下次登录或重启）：
```bash
launchctl stop com.uco.api.server
launchctl stop com.uco.dashboard
```

完全卸载（不再自动启动）：
```bash
launchctl unload ~/Library/LaunchAgents/com.uco.api.server.plist
launchctl unload ~/Library/LaunchAgents/com.uco.dashboard.plist
```

**启动服务**:
```bash
# 如果服务已卸载，重新加载
launchctl load ~/Library/LaunchAgents/com.uco.api.server.plist
launchctl load ~/Library/LaunchAgents/com.uco.dashboard.plist

# 如果服务已加载但停止，手动启动
launchctl start com.uco.api.server
launchctl start com.uco.dashboard
```

**重启服务**:
```bash
# 方法1: 先停止再启动
launchctl stop com.uco.api.server && launchctl start com.uco.api.server
launchctl stop com.uco.dashboard && launchctl start com.uco.dashboard

# 方法2: 重新加载配置
launchctl unload ~/Library/LaunchAgents/com.uco.api.server.plist
launchctl load ~/Library/LaunchAgents/com.uco.api.server.plist
```

### 日常使用场景

**正常使用**:
- 登录macOS后，服务自动启动
- 无需任何手动操作
- 访问 http://localhost:3000 使用Web管理界面

**开发调试**:
```bash
# 1. 临时停止服务
launchctl stop com.uco.api.server
launchctl stop com.uco.dashboard

# 2. 手动启动进行调试
# API Server
cd /Users/lillianliao/notion_rag/universal_content_orchestrator
source venv/bin/activate
python src/api_server.py

# Dashboard（新终端）
cd /Users/lillianliao/notion_rag/universal_content_orchestrator/web_dashboard
npm run dev

# 3. 调试完成后，重新启动服务
launchctl start com.uco.api.server
launchctl start com.uco.dashboard
```

**完全禁用**:
```bash
# 卸载服务
launchctl unload ~/Library/LaunchAgents/com.uco.api.server.plist
launchctl unload ~/Library/LaunchAgents/com.uco.dashboard.plist

# 如需重新启用
launchctl load ~/Library/LaunchAgents/com.uco.api.server.plist
launchctl load ~/Library/LaunchAgents/com.uco.dashboard.plist
```

### 故障排查

**服务无法启动**:
```bash
# 1. 检查配置文件语法
plutil -lint ~/Library/LaunchAgents/com.uco.api.server.plist
plutil -lint ~/Library/LaunchAgents/com.uco.dashboard.plist

# 2. 检查启动脚本权限
ls -l ~/.venv/bin/uco-api-server
ls -l ~/.venv/bin/uco-dashboard
# 应该显示可执行权限（-rwxr-xr-x）

# 3. 查看错误日志
cat logs/api-server-error.log
cat logs/dashboard-error.log
```

**端口被占用**:
```bash
# 查看占用端口的进程
lsof -i :8000
lsof -i :3000

# 如果是其他进程占用，手动结束
kill -9 <PID>
```

**服务频繁重启**:
```bash
# 查看错误日志确定原因
tail -n 50 logs/api-server-error.log
tail -n 50 logs/dashboard-error.log

# 常见原因：
# - 依赖缺失（重新安装：pip install -r requirements.txt）
# - 虚拟环境问题（重新创建：python -m venv venv）
# - 配置文件错误（检查config/pipelines.yaml）
```

### 验证服务健康

**API Server健康检查**:
```bash
curl http://localhost:8000/api/health
# 预期输出：{"status":"ok","engine":"running"}
```

**Dashboard可访问性**:
```bash
curl http://localhost:3000
# 预期输出：HTML内容（包含"Media Query Console"或类似标题）
```

### 配置修改

如需修改服务配置（如更换端口、更改日志路径）：

1. 编辑plist文件：
```bash
vim ~/Library/LaunchAgents/com.uco.api.server.plist
vim ~/Library/LaunchAgents/com.uco.dashboard.plist
```

2. 重新加载服务使配置生效：
```bash
launchctl unload ~/Library/LaunchAgents/com.uco.api.server.plist
launchctl load ~/Library/LaunchAgents/com.uco.api.server.plist
```

## Pipeline Runner运维

### 手动运行Pipeline

**运行所有Pipeline**:
```bash
cd /Users/lillianliao/notion_rag/universal_content_orchestrator
source venv/bin/activate
python main.py
```

**运行指定Pipeline**:
```bash
python main.py ai_tech_trends_monitor
```

### 查看Pipeline日志

Pipeline运行日志会输出到终端，如需持久化日志可重定向：
```bash
python main.py > logs/pipeline.log 2>&1
```

### 定时任务

UCO使用crontab调度Pipeline，配置文件：`config/pipelines.yaml`

**查看当前定时任务**:
```bash
crontab -l
```

**编辑定时任务**:
```bash
crontab -e
```

**验证定时任务日志**:
```bash
# 查看cron执行日志（macOS）
log show --predicate 'process == "cron"' --last 1h
```

## 数据备份

### 数据库备份

UCO使用SQLite数据库，位置：`data/headhunter_dev.db`

**备份数据库**:
```bash
# 创建带时间戳的备份
cp data/headhunter_dev.db "data/headhunter_dev.db.backup_$(date +%Y%m%d_%H%M%S)"
```

**恢复数据库**:
```bash
# 停止服务
launchctl stop com.uco.api.server

# 恢复备份
cp data/headhunter_dev.db.backup_YYYYMMDD_HHMMSS data/headhunter_dev.db

# 重启服务
launchctl start com.uco.api.server
```

### 配置文件备份

**备份配置**:
```bash
tar -czf "config_backup_$(date +%Y%m%d_%H%M%S).tar.gz" config/
```

**恢复配置**:
```bash
tar -xzf config_backup_YYYYMMDD_HHMMSS.tar.gz
```

## 监控建议

### 日志监控

定期检查错误日志：
```bash
# 最近50行错误
tail -n 50 logs/api-server-error.log
tail -n 50 logs/dashboard-error.log

# 实时监控
tail -f logs/api-server-error.log
```

### 磁盘空间

监控日志文件大小：
```bash
# 查看logs目录大小
du -sh logs/

# 清理旧日志（保留最近7天）
find logs/ -name "*.log" -mtime +7 -delete
```

### 服务状态检查

创建健康检查脚本：
```bash
#!/bin/bash
# health_check.sh

echo "=== UCO Health Check ==="
echo ""

# 检查服务状态
echo "Services:"
launchctl list | grep com.uco

echo ""

# 检查端口
echo "Ports:"
lsof -i :8000 | grep LISTEN || echo "API Server: NOT RUNNING"
lsof -i :3000 | grep LISTEN || echo "Dashboard: NOT RUNNING"

echo ""

# 检查API健康
echo "API Health:"
curl -s http://localhost:8000/api/health || echo "API: NOT RESPONDING"

echo ""

# 检查最近错误
echo "Recent Errors:"
tail -n 5 logs/api-server-error.log
tail -n 5 logs/dashboard-error.log
```

定期运行：
```bash
bash health_check.sh
```
