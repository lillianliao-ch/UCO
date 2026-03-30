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

# 3. 引爆主板脑区 (切换为正确的系统活跃 Python 3.12)
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 main.py >> $LOG_FILE 2>&1

echo "🛑 Orchestrator Sequence Terminated at $(date)" >> $LOG_FILE
echo "======================================================" >> $LOG_FILE
