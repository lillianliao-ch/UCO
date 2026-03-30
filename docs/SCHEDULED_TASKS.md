# 全域数据与分发定时任务指南 (Scheduled Tasks Directory)

本文档旨在统一记录并管理目前服务器（或本地环境）上正在运行的所有核心 AI 数据抓取、内容编排与自动化分发定时任务（Cron Jobs）。随着业务版图的扩张，日后新的自动化调度管线均应在此进行登记与说明。

---

## 🕒 1. 万物编排器 (Universal Content Orchestrator)
**执行频率**: `0 8 * * *` (每天早晨 08:00 执行)
**归属项目**: `universal_content_orchestrator`
**执行脚本**: `/bin/bash /Users/lillianliao/notion_rag/universal_content_orchestrator/deploy_cron.sh` (会拉起 `main.py`)

### 🧠 任务流转说明：
1. **全域情报打捞 (08:00 ~ 08:02)**：系统根据 `config/channels.yaml` 中标记为 `active: true` 的数据源（默认走 `TrendRadar` 宏观热点源）自动抓取最新资讯。
2. **Telegram 大盘预警**：立刻将当天捕获的所有原始情报组装成**【晨报情报池】**汇总信标，发送至您的 Telegram 端。
3. **大模型筛选与重构 (08:02 ~ 08:05)**：唤醒 Qwen Engine。读取本地 `config/prompts/filter_priority.md` 挑选出最优的若干篇内容，并依照 `config/prompts/xhs_style_a_lilian.md` 中定义的 Lilian人设 重新编排撰写爆款文案。
4. **生成配套海报**：调用 `PillowVisualEngine`，针对小红书(3:4比例)和微信(2.35:1) 生成携带“Lilian首发 / 甄选”角标的高清宣传图片。
5. **分发至小红书与 Telegram草稿群**：直接自动化将内容带图推入小红书排期草稿，同步发送 Telegram 图文合并草稿让您在手机端审阅。
6. **分发至微信草稿箱 (纯净去图版)**：为避开微信 UEditor 严厉防灰产审查，向微信草稿箱推送最纯粹的一版带有硅谷排版基线的极简纯文本。提示您后续去微信内手工放图。

> [!TIP] **架构去黑盒化说明**
> 万物编排器的底层逻辑已与 Python 死代码解耦。如需修改**执行渠道**，请直接编辑 `universal_content_orchestrator/config/channels.yaml`。如需修改**人设与生成话术**，请直接编辑 `config/prompts/` 目录下的 Markdown 文件。

---

## 🕒 2. 猎头数据监控预警阵列
**归属项目**: `personal-ai-headhunter` (全天候驻守进程)

### 2.1 每日数据简报 (Daily Briefing)
- **触发时间**: `0 5 * * *` (每天 05:00)
- **执行命令**: `python3 daily_briefing.py`
- **做啥用**: 提取 AI 猎头雷达管线中昨天的各类动作，发往 Telegram 提供每日跟进提醒大盘。

### 2.2 学术科研与社区监控预警
- **ArXiv 每日论文追踪监控**:
  - 触发时间: `10 5 * * *` (每天早晨 05:10)
  - 执行命令: `python3 arxiv_monitor.py`
  - 目的: 探测顶会、顶刊或前沿作者的最新论文发布，第一时间捕获潜在学术界人才线索并送往大模型脱水。
- **GitHub Trending 监控**:
  - 触发时间: `15 5 * * *` (每天早晨 05:15)
  - 执行命令: `python3 github_trending_monitor.py`
  - 目的: 嗅探每日最火爆的人工智能技术仓，扫描贡献者清单挖掘代码新秀。

### 2.3 猎头邮件监控系统 (Gmail Monitor)
- **触发时间**: `*/30 * * * *` (每 30 分钟轮询一次)
- **执行命令**: `python3 gmail_reply_monitor.py`
- **做啥用**: 高频定期检查与候选人沟通的外置邮箱回信，将复联的简历数据结构化回填或向系统发出强提醒。

### 2.4 主脑日历中枢 (Daily Planner)
- **触发时间**: `0 7 * * *` (每天 07:00)
- **执行命令**: `python3 daily_planner.py`
- **做啥用**: 根据昨晚及清晨捕获的所有离散事件，为 Agent 系统制定一整天的抓取、聊骚、猎聘调度计划表。

---

## 🛠️ 运维与调试操作指南

### 1. 查看与激活当前电脑上的所有定时任务
打开 macOS / Linux 终端，输入以下命令即可查看所有在案配置的调度进程表：
```bash
crontab -l
```

### 2. 编辑或新增挂机定时任务
如果需要新增业务管线或调整启动时间，请在控制台输入：
```bash
crontab -e
```
进入类似 Vim 的编辑器界面后，按 `i` 键即可进行修改操作。修改完毕后按 `Esc`，输入 `:wq` 即可保存生效。

### 3. 排障及系统日志去哪找？
- **万物编排器日志**: 排查小红书/微信断连断发情况
  统一路由保存在: `/tmp/universal_orchestrator.log`
  可以输入：`tail -f /tmp/universal_orchestrator.log` 实时盯着它干活。
- **猎头与监控组件日志**:
  绝大部分日志保存在 `personal-ai-headhunter/logs/` 目录下（如 `gmail_reply_monitor.log` 等）。
