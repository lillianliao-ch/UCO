# 全域数据与分发定时任务指南 (Scheduled Tasks Directory)

本文档旨在统一记录并管理目前服务器（或本地环境）上正在运行的所有核心 AI 数据抓取、内容编排与自动化分发定时任务（Cron Jobs）。随着业务版图的扩张，日后新的自动化调度管线均应在此进行登记与说明。

---

## 🕒 1. 万物编排器 (Universal Content Orchestrator)
**执行频率**: 在管线大盘 UI 中**细粒度动态化配置**
**归属项目**: `universal_content_orchestrator`
**执行机制**: 由 FastAPI 引擎搭载 `python-crontab` 直连操作系统内核调度。

> [!WARNING] **配置范式迁移警告 (Phase 2 更新)**
> 自 2026-04 起，万物编排器的定时任务**已全面图形化**。请打开 Web Dashboard > 「管线编排面板」，在目标管线的“精细化配置”中设置「每日自动发射时钟」。
> 设定后系统会自动覆写您的 Mac `crontab -l`。**请勿再手动去 `crontab -e` 里面编写 `# uco_` 打头的野脚本，否则会被中枢抹除。**

### 🧠 任务新式流转架构 (Bifurcated HitL Gateway)：
1. **沙盒隔离触发**：不论是到达设定时钟，还是您在网页端按下【▶️ 立即运行】，都会以严格的沙盒参数拉起 `deploy_cron.sh <pipeline_id>`。
2. **全域情报打捞与漏斗落库**：探针启动，并将原始数据、LLM脱水数据、最终成稿数量严格打入 `pipeline_run` 漏斗中以便监控。
3. **红绿灯网关分发**：
   - **绿灯直发 (Sync Notify)**: Telegram / 飞书工作流等通讯渠道直接免查收弹窗。
   - **红灯拦截 (Async HitL Draft)**: 小红书 / 微信公众号等强宣发渠道**强行阻断**，数据带着渲染好的双比例海报落入底层的 `content_drafts` SQL 草稿池，系统进入挂机等待态。您可以在 UI 界面的「审核与发布」版图执行人肉审批发帖。

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
---

## 🔗 3. OPC 事件总线 (Event Bus)
**归属**：全局共享基础设施 (`/Users/lillianliao/notion_rag/opc_event_bus.py`)
**数据库**：`/Users/lillianliao/notion_rag/data/opc_event_bus.db`

> [!NOTE] **架构说明（2026-04 Sprint 1 新增）**
> 事件总线是连通 UCO (Layer 1) 和各业务 App (Layer 4) 的数据管道。
> UCO 探针采集到数据后，在生成管线内容的同时，通过总线广播事件。
> 猎头等业务 App 作为消费者独立订阅，互不干扰。

### 已注册的事件类型
| 事件类型 | 生产者 | 消费者 | 说明 |
|---------|--------|--------|------|
| `NEW_AI_TRENDING_REPO` | UCO `github_talent_radar` 管线 | 猎头 App（待接入） | GitHub 上 AI 相关热门项目 + 贡献者列表 |
| `NEW_ARXIV_CHINESE_AUTHOR` | UCO `arxiv_paper_radar` 管线 | 猎头 App（待接入） | 华人一作的新论文信息 |

### 已从猎头项目收编至 UCO 的探针
| 探针 | 旧位置 (headhunter) | 新位置 (UCO) | UCO 管线 ID |
|------|---------------------|-------------|-------------|
| GitHub Trending 监控 | `github_trending_monitor.py` | `src/sources/github_trending_source.py` | `github_talent_radar` |
| ArXiv 论文监控 | `arxiv_monitor.py` | `src/sources/arxiv_source.py` | `arxiv_paper_radar` |

### 仍留在猎头项目的脚本（纯业务逻辑）
- `daily_briefing.py` — 运营数据晨报（直接读取猎头 DB）
- `daily_planner.py` — 每日工作计划
- `gmail_reply_monitor.py` — 候选人邮件回复监控

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
- **事件总线调试**:
  ```python
  from opc_event_bus import EventBus
  bus = EventBus()
  print(bus.stats())        # 总线统计
  print(bus.peek(limit=5))  # 查看最近 5 条事件
  ```

