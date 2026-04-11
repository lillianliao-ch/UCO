# Universal Content Orchestrator - Session Start

> 新会话从这里开始

## Quick Start

如果你是新会话，请按以下顺序阅读：

1. **本项目是什么** → `README.md`
2. **当前能力** → `docs/FEATURES.md`
3. **当前状态** → `memory/CURRENT.md` ⬅️ **最重要！**

## Project Context

**UCO** 是一个多管道情报和发布系统，用于：
- 从多个数据源收集内容（RSS、GitHub、ArXiv、YouTube、V2EX等）
- 用LLM筛选和合成内容
- 发布到多个渠道（Telegram、微信、小红书等）

## Default Working Directory

```bash
cd /Users/lillianliao/notion_rag/universal_content_orchestrator
```

## Recent Changes (2026-04-11)

**新增数据源**：
- ✅ YouTube（AI技术视频）
- ✅ V2EX（中文技术社区）
- 已集成到 `main.py` 和 `config/pipelines.yaml`

详见：`memory/CURRENT.md`

## Key Files

- `main.py` - pipeline runner
- `config/pipelines.yaml` - pipeline配置
- `src/sources/` - 数据源实现
- `src/publishers/` - 发布渠道实现

## Documentation

- `docs/INDEX.md` - 文档索引
- `docs/ARCHITECTURE.md` - 架构说明
- `docs/FEATURES.md` - 功能清单
- `docs/SCHEDULED_TASKS.md` - 定时任务

## Running

```bash
# 运行所有pipeline
python main.py

# 运行指定pipeline
python main.py ai_tech_trends_monitor
```

---

**提示**: 新会话请先读 `memory/CURRENT.md` 了解最新状态！
