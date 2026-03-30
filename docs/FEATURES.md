# Supported Features Ledger (v1.5 Baseline)

## 📡 Inbound Sourcing (Sources)
- ✅ **Live VIP Footprint Radar (`duckduckgo-search`)**: Actively grabs S/A+ tier candidates from the local AI Headhunter internal SQLite database, formats targeted queries, and scours the internet for their last 30 days of public news, podcasts, PRs, and GitHub activity.
- ✅ **CRM Cross-Talk (AI Headhunter DB)**: Taps into `personal-ai-headhunter/data/headhunter_dev.db` to extract executive talent intel for tracking.
- ✅ **Legacy RSS Ingestion**: Smoothly ports high-quality tech feeds (InfoQ, 36Kr, Jiqizhixin) and financial filings (WSJ, SEC 13F) via feedparser.
- ✅ **HackerNews & ProductHunt Firehose**: Leverages legacy APIs to aggregate deep-tech solopreneur insights and globally trending repos.

## 🧠 Core Processing (Brains)
- ✅ **Dynamic Persona Injection**: Moves away from hard-coded single-persona structures. The LLM Engine acts as a director dynamically loading Markdown personas (`org_chart_analysis.md`, `finance_hardcore_report.md`, `live_footprint_analysis.md`) per pipeline requirement.
- ✅ **Intelligent Priority Selector**: Evaluates raw context dumps to bubble up the top 3 highest-value signals per pipeline run.
- ✅ **Aesthetic Typography Engine**: A robust, pure-python `Pillow` deterministic canvas renderer for Social Media posters (Xiaohongshu & WeChat Covers).

## 📭 Outbound Distro (Publishers)
- ✅ **Feishu Custom Bot Webhook (`feishu_adapter.py`)**: Seamless, real-time push to private Lark/Feishu workgroups, supporting text and post payloads mapping to `FEISHU_WEBHOOK_URL`.
- ✅ **Enterprise WeChat (WeCom) CLI Bridge (`wecom_adapter.py`)**: Highly integrated `subprocess` wrapper utilizing `wecom-cli` to bypass strict proxy requirements and inject intelligence directly into WeCom.
- ✅ **Telegram Global Beacon**: Mobile broadcast pipeline dynamically routing plain-text "Ice Breaker" templates and debugging logs straight to Lilian's mobile.
- ✅ **Native WeChat MP Publisher (CDP/Playwright)**: Bypass bridge to inject LLM rendered payloads directly into the UEditor iframe via CDP.
- ✅ **OpenCLI Xiaohongshu Dispatcher**: Native draft injection avoiding manual staging.

## ⚙️ System Execution (Orchestration & UX)
- ✅ **Next.js Web Dashboard**: Modern React interface (`web_dashboard/`) running on `api_server.py`. Provides real-time visibility into channel toggle states (`pipelines.yaml`) and allows live Markdown editing of Prompt constraints.
- ✅ **Targeted Pipeline Runner**: `python3 main.py <pipeline_id>` support for isolating specific agent workflows (e.g. `live_footprint_monitor`) for testing.
- ✅ **Isolated State Management**: `EventStateManager` now tracks deduplication on a strictly per-pipeline basis, allowing identical root articles to be processed differently by different pipelines without causing memory collisions.
