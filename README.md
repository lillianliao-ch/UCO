# Universal Content Orchestrator

Universal Content Orchestrator (`UCO`) is a multi-pipeline intelligence and publishing system.

It pulls signals from configured sources, lets an LLM rank and synthesize them, and then routes output to either:

- direct notification channels such as Telegram / Feishu / WeCom
- human-review draft flows such as WeChat and Xiaohongshu

## What This Repo Contains

- pipeline runner:
  - `main.py`
- pipeline config:
  - `config/pipelines.yaml`
- core engines:
  - `src/core/`
- video engine:
  - `src/core/video_engine/` — FFmpeg 渲染 + CosyVoice 声音克隆
- voice assets:
  - `data/voices/` — 参考音频 + 缓存的 voice_id
- sources:
  - `src/sources/`
- publishers:
  - `src/publishers/`
- API layer:
  - `src/api_server.py`
- frontend dashboard:
  - `web_dashboard/`

`web_dashboard/` is a frontend submodule of this project, not a separate product line.

## Read This First

- docs entry:
  - `docs/INDEX.md`
- current capabilities:
  - `docs/FEATURES.md`
- current architecture:
  - `docs/ARCHITECTURE.md`
- scheduling:
  - `docs/SCHEDULED_TASKS.md`

## Quick Start

### 方式1: Pipeline Runner（推荐，最常用）

```bash
# 1. 创建虚拟环境并安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. 运行所有pipeline
python3 main.py

# 3. 运行指定pipeline
python3 main.py ai_tech_trends_monitor
```

### 方式2: Web管理界面（可选）

**后端API Server**:
```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 安装Web服务器依赖
pip install fastapi uvicorn python-multipart crontab

# 3. 启动API Server
python3 src/api_server.py
```

**前端Dashboard**:
```bash
# 1. 进入前端目录
cd web_dashboard

# 2. 安装依赖（首次运行）
npm install

# 3. 启动Dashboard
npm run dev
```

**访问**: http://localhost:3000

**注意**: Web管理界面需要同时运行后端API和前端Dashboard，建议在不同终端运行。

**持久运行（可选）**:
如果希望Web管理界面开机自启并保持运行，可配置macOS launchd服务。详见 [docs/OPERATIONS.md](docs/OPERATIONS.md)。

---

## 常见问题

**Q: 第一次启动Web管理界面失败**
```bash
# 确保在正确的目录
cd /Users/lillianliao/notion_rag/universal_content_orchestrator

# 检查虚拟环境
source venv/bin/activate
pip install -r requirements.txt fastapi uvicorn

# 检查前端依赖
cd web_dashboard && npm install
```

**Q: 端口被占用**
```bash
# 检查端口8000（API）
lsof -i :8000

# 检查端口3000（Dashboard）
lsof -i :3000
```

**Q: 日常使用应该启动哪个？**
A: 推荐只用 `python3 main.py`，Web管理界面是可选的。

## Notes

- feature inventory belongs in `docs/FEATURES.md`
- runtime and module structure belongs in `docs/ARCHITECTURE.md`
- planning belongs in `docs/orchestrator_product_roadmap.md`
