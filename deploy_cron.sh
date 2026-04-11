#!/bin/bash

# ==========================================================
# 万物编排器（Universal Content Orchestrator）自动挂机引擎
# ==========================================================

LOG_FILE="/tmp/universal_orchestrator.log"
touch $LOG_FILE
echo "======================================================" >> $LOG_FILE
echo "🚀 Orchestrator Boot Sequence Initiated at $(date)" >> $LOG_FILE

# 1. 放弃挂载可能会导致 Bash 崩溃的 zshrc，直接精准导入底层 env 环境变量
if [ -f "/Users/lillianliao/notion_rag/.env" ]; then
    export $(grep -v '^#' "/Users/lillianliao/notion_rag/.env" | xargs)
fi

# 补充系统内核缺失的开发者 PATH (极其重要，否则脱机任务找不到 node/npx)
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# 2. 定位工作区
cd /Users/lillianliao/notion_rag/universal_content_orchestrator || exit 1

# 设置 PYTHONPATH
export PYTHONPATH="/Users/lillianliao/notion_rag/universal_content_orchestrator:$PYTHONPATH"

# 3. 接收管线参数，动态下发。如果不传参数，则 main.py 会执行全部默认管线
PIPELINE_ID=$1
echo "🎯 Target Pipeline ID Configured: ${PIPELINE_ID:-ALL_DEFAULT}" >> $LOG_FILE

# 4. 引爆主板脑区 (切换为工作区独立的 virtual environment)
if [ -n "$PIPELINE_ID" ]; then
    /Users/lillianliao/notion_rag/universal_content_orchestrator/venv/bin/python3 main.py "$PIPELINE_ID" >> $LOG_FILE 2>&1
else
    /Users/lillianliao/notion_rag/universal_content_orchestrator/venv/bin/python3 main.py >> $LOG_FILE 2>&1
fi

echo "🛑 Orchestrator Sequence Terminated at $(date)" >> $LOG_FILE
echo "======================================================" >> $LOG_FILE
