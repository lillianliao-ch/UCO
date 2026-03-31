# System Architecture (v1.5 Multi-Pipeline Era)

## 1. Design Philosophies (The Orchestrator Matrix)
- **Zero-Touch Dynamic Dispatch**: The core engine (`main.py`) no longer contains hard-coded business rules. Instead, it reads `config/pipelines.yaml` to dynamically spawn `Source`, inject `Prompt/Persona`, and route to `Publisher`. Adding a new business vector requires zero Python code changes.
- **Contract-first Validation**: Every cross-border pipeline interaction is type-checked using Pydantic models defined in `src/core/schemas.py` (`RawContentEvent`).
- **Human-in-the-Loop (HitL) Bifurcated Gateway**: 
  - **High-Risk (Async Drafts)**: Platforms requiring qualitative auditing (Xiaohongshu, WeChat Official Accounts) strictly route payloads to the SQLite `content_drafts` table, halting execution for manual GUI review.
  - **Low-Friction (Sync Alerts)**: Notification platforms (Telegram, Feishu, WeCom) bypass the draft lock and push autonomously to rapidly alert the human operator.
- **Strict Observability & Funnel Metrics**: Scrapers no longer silently yield text. They return `(content, stats_dict)` to strictly track the LLM's drop-off funnel (`scraped` -> `rejected` -> `accepted`) into `pipeline_run_history`, ensuring 100% transparent crawler health.
- **Fail-Safe Execution**: The global orchestration loop employs deterministic `try...finally` resource cleanups to ensure database state (`STATUS: FAILED`) is properly closed during severe third-party API timeouts.
- **Foreign Body Shielding (Adapter Pattern)**: Non-Python CLI scripts (`wecom-cli`) or erratic web services (`duckduckgo-search`) are wrapped in hyper-resilient adapter classes that will fail gracefully and sequentially without bringing down the global orchestration loop.

## 2. Directory Topography
```text
universal_content_orchestrator/
├── config/
│   ├── channels.yaml         # Legacy global channel toggles
│   ├── pipelines.yaml        # [NEW] Master Multiverse Pipeline definitions
│   └── prompts/              # Dynamic LLM Persona injects (e.g. live_footprint_analysis.md)
├── src/
│   ├── core/           
│   │   ├── llm_engine.py     # Qwen API integration & Prompt synthesis
│   │   ├── visual_engine.py  # Pillow typography and rendering
│   │   └── state_manager.py  # SQLite de-duplication and memory tracking
│   ├── sources/        
│   │   ├── base_source.py
│   │   ├── db_talent_source.py     # Deep link to AI Headhunter local SQLite
│   │   ├── live_footprint_source.py # DDGS-driven VIP internet scanner
│   │   └── _legacy_rss.py
│   ├── publishers/     
│   │   ├── telegram_adapter.py     # Direct Bot API
│   │   ├── wecom_adapter.py        # Subprocess wrapper for @wecom/cli
│   │   ├── feishu_adapter.py       # Custom Bot Webhook caller
│   │   └── opencli_xhs_adapter.py  
├── web_dashboard/            # Next.js UI for pipeline visibility and rule mapping
├── data/                     # State databases & image dumps
├── api_server.py             # Expressive REST interface linking local DB with Web Dashboard
└── main.py                   # Master Pipeline Event Loop Runner
```

## 3. Data Flow Execution Sequence
1. **Cron/LaunchAgent Trigger**: `python3 main.py` is invoked.
2. **Pipeline Iteration**: Reads `config/pipelines.yaml`, spawns active pipelines independently.
3. **Data Hydration (Source)**: Adapters (e.g., `LiveFootprintSource`) query external APIs/Databases mapping raw data to `RawContentEvent`.
4. **Hippocampus Check (EventStateManager)**: Rejects events processed in previous runs for the *specific pipeline ID*.
5. **Selection Matrix (Qwen Engine)**: The LLM rates events. Top `N` events survive.
6. **Synthesis (Brain)**: Fuses the chosen `Prompt` with the `Event` to generate Markdown content.
7. **Publishing (Publisher)**: Emits content iteratively to WeChat/Feishu/Telegram based on YAML refs.
