# Universal Content Orchestrator (Lilian's Multiverse Pipeline)

An enterprise-grade, Multi-Agent powered Orchestration Framework for capturing, processing, and distributing high-value technical content and talent intelligence across disjointed data sources and platforms.

## Core Identity
This system has evolved from a simple news scraper (`ai_news_tracker`) into a **Multi-Pipeline Intelligence Factory**. It now operates on a "Zero-Touch" configuration paradigm driven by YAML, capable of tracking S/A+ tier AI talent, discovering deep-tech solopreneur insights, and aggregating finance/compute trends—all routed seamlessly through LLM-driven personas to various endpoints.

## Ecosystem Quick Glance
- **Zero-Touch Config (`config/pipelines.yaml`)**: Define new business logic without touching python core code.
- **Dynamic Content Engine**: LLMs dynamically adopt custom markdown personas (`org_chart_analysis.md`, `live_footprint_analysis.md`, etc.).
- **Global Footprint Radar**: Leverages DuckDuckGo (`ddgs`) to monitor live internet footprints of VIP executives.
- **Multi-IM Dispatch**: Sends "Ice-Breaker" intelligence directly to Telegram, Enterprise WeChat (WeCom), and Feishu Webhooks.
- **Visual Control Center**: A Next.js Web Dashboard (`web_dashboard/`) for real-time visual monitoring and prompt management.

## Documentation Tree
Please refer to our refined documentation system for detailed overviews:
- [📖 FEATURES.md](docs/FEATURES.md) - Comprehensive ledger of all inbound, processing, and outbound capabilities.
- [🏗️ ARCHITECTURE.md](docs/ARCHITECTURE.md) - Deep dive into event flows, the pipeline factory pattern, and interface contracts.
- [⏰ SCHEDULED_TASKS.md](docs/SCHEDULED_TASKS.md) - Overview of macOS LaunchAgents and scheduling.

## Standard Setup Instructions
```bash
# 1. Environment prep
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. For Web Footprint Radar
pip install ddgs duckduckgo-search

# 3. For Enterprise WeChat Delivery
npm install -g @wecom/cli
wecom-cli init

# 4. Bootstrap Execution (Run a specific pipeline)
python3 main.py live_footprint_monitor
```
