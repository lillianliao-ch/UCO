# Universal Content Orchestrator

An enterprise-grade, Multi-Agent powered Orchestration Framework for capturing, processing, and distributing high-value technical content across disjointed data sources and platforms.

## Architecture Paradigm
This system strictly follows a 4-Layer Event-Driven Architecture (EDA) optimized for autonomous AI agent maintenance:
1. **Inbound Layer**: Headless integration of **TrendRadar** (Top-of-Funnel AI intelligence aggregator replacing legacy raw RSS) and modern OpenCLI adapters.
2. **Event Bus**: Structured SQLite integration via Pydantic Data schemas.
3. **Processing Layer**: LLM-driven graph routing, NLP style transfer (e.g. Qwen), and automated aesthetic typography synthesis (Pillow).
4. **Outbound Layer**: Highly decoupled "Shell-Wrap" adapters shielding the python core from varied publishing languages (Node.js/Go/Rust).

## Documentation Tree
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Deep dive into event flows and interface contracts.
- [FEATURES.md](docs/FEATURES.md) - Product backlog and supported integrations.

## Setup Instructions
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
