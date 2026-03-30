# System Architecture

## 1. Design Philosophies
- **Contract-first Validation**: Every cross-border pipeline interaction is type-checked using Pydantic models defined in `src/core/schemas.py`.
- **1-to-1 Content Factory Pattern**: Orchestrates bulk inbound data pools by feeding them through an LLM evaluation matrix (Qwen Selector) before strictly looping exactly via 8 independent event generations.
- **Foreign Body Shielding (Adapter Pattern)**: Non-Python CLI scripts or erratic open-source repositories found on GitHub must be executed purely via Python's `subprocess.run()`. No native dependency chains will intertwine outside the Python virtual environment.
- **Fail-Fast Routing**: If a specific platform push fails (e.g., XiaoHongShu rate limiting), the unified Event Bus gracefully marks the node as `FAILED_RETRY` and releases the thread.

## 2. Directory Topography
```text
universal_content_orchestrator/
├── src/
│   ├── core/           # Interfaces (Pydantic schemas), AI Engines (LLM/Vision)
│   ├── sources/        # Data injection plugins (TrendRadar MCP Webhooks, OpenCLI, Boss)
│   └── publishers/     # Output dispatchers (XHS, Telegram, WeChat)
├── docs/               # System tracking and feature ledgers
├── data/               # SQLite state tracking schemas
├── deploy_cron.sh      # MacOS Crontab automated bootstrap loader
└── main.py             # Event loop & multi-agent routing master
```
