# UCO 管理平台启动指南

> Universal Content Orchestrator 有三个可启动的部分

## 🎯 你想启动哪个部分？

### 1️⃣ Pipeline Runner（命令行）- 推荐先用这个

**用途**: 执行数据收集和内容发布pipeline

**启动方式**:
```bash
cd /Users/lillianliao/notion_rag/universal_content_orchestrator

# 激活虚拟环境（如果还没激活）
source .venv/bin/activate

# 运行所有pipeline
python main.py

# 运行指定pipeline（例如：AI技术趋势监控）
python main.py ai_tech_trends_monitor
```

**说明**:
- 这是最常用的部分
- 执行配置在 `config/pipelines.yaml` 中的pipeline
- 支持定时调度

---

### 2️⃣ Web Dashboard（前端管理界面）

**用途**: 可视化管理界面（Next.js）

**启动方式**:
```bash
cd /Users/lillianliao/notion_rag/universal_content_orchestrator/web_dashboard

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```

**访问地址**: http://localhost:3000

**说明**:
- Next.js应用
- 热重载支持
- 端口：3000

---

### 3️⃣ API Server（后端API）

**用途**: FastAPI后端服务

**启动方式**:
```bash
cd /Users/lillianliao/notion_rag/universal_content_orchestrator

# 激活虚拟环境
source .venv/bin/activate

# 启动API服务器
python src/api_server.py
```

**访问地址**: http://localhost:8000

**API文档**: http://localhost:8000/docs

**说明**:
- FastAPI应用
- 自动重载
- 端口：8000

---

## 🚀 推荐启动流程

### 首次使用

1. **安装依赖**:
```bash
cd /Users/lillianliao/notion_rag/universal_content_orchestrator

# Python依赖
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 前端依赖
cd web_dashboard
npm install
cd ..
```

2. **测试Pipeline Runner**:
```bash
# 运行新集成的YouTube+V2EX pipeline
python main.py ai_tech_trends_monitor
```

3. **（可选）启动Web Dashboard**:
```bash
cd web_dashboard
npm run dev
# 访问 http://localhost:3000
```

---

## 📝 日常使用

### 场景1: 执行pipeline（最常用）

```bash
cd /Users/lillianliao/notion_rag/universal_content_orchestrator
source .venv/bin/activate

# 运行所有pipeline
python main.py

# 或运行指定pipeline
python main.py ai_tech_trends_monitor
```

### 场景2: 使用Web管理界面

```bash
# 终端1: 启动后端API
cd /Users/lillianliao/notion_rag/universal_content_orchestrator
source .venv/bin/activate
python src/api_server.py

# 终端2: 启动前端界面
cd /Users/lillianliao/notion_rag/universal_content_orchestrator/web_dashboard
npm run dev

# 访问 http://localhost:3000
```

---

## 🔍 检查端口占用

```bash
# 检查端口8000（API）
lsof -i :8000

# 检查端口3000（Dashboard）
lsof -i :3000
```

如果有端口冲突，可以：
1. 杀掉占用进程
2. 或修改配置中的端口号

---

## ❓ 常见问题

**Q: 我应该先启动哪个？**
A: 先用 Pipeline Runner（`python main.py`），确保功能正常

**Q: Web Dashboard是必须的吗？**
A: 不是必须的，Pipeline Runner可以独立工作

**Q: API Server是做什么的？**
A: 为Web Dashboard提供后端API支持

**Q: 可以同时运行多个吗？**
A: 可以，但需要在不同终端窗口运行

---

## 📚 相关文档

- `docs/ARCHITECTURE.md` - 架构说明
- `docs/FEATURES.md` - 功能清单
- `docs/SCHEDULED_TASKS.md` - 定时任务配置
- `memory/CURRENT.md` - 当前工作状态
