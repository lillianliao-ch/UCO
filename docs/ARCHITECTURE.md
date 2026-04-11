# Universal Content Orchestrator 架构文档

> 最后更新：2026-04-11
> 状态：v2.0 — 含视频引擎 + 声音克隆

本文档描述 `universal_content_orchestrator` 的当前运行结构。

它可以回答：

- 主要入口点是什么
- 数据如何流经系统
- 数据源、发布器、状态、API 和仪表盘在哪里

## 运行入口点

- 管线运行器：
  - `main.py`
- API 服务器：
  - `src/api_server.py`
- 仪表盘前端：
  - `web_dashboard/`
- 管线配置：
  - `config/pipelines.yaml`

## 当前目录结构

```text
universal_content_orchestrator/
├── config/
│   ├── pipelines.yaml              # 管线定义（数据源 → 处理 → 发布）
│   ├── video_engines.yaml          # 视频引擎选择与 TTS 配置
│   └── prompts/
│       └── video_script_lilian.md  # 视频口播稿 Prompt 模板
├── data/
│   └── voices/                     # 声音克隆资产
│       ├── lilian_reference.m4a    # 参考音频原始文件
│       ├── lilian_reference.wav    # FFmpeg 转换后的 WAV
│       └── cosyvoice_voice_id.json # 缓存的 voice_id
├── docs/
├── src/
│   ├── api_server.py
│   ├── core/
│   │   ├── llm_engine.py
│   │   ├── schemas.py
│   │   ├── state_manager.py
│   │   ├── visual_engine.py
│   │   ├── playwright_engine.py
│   │   ├── cdp_session_cloner.py
│   │   └── video_engine/                # 视频生成子系统
│   │       ├── __init__.py
│   │       ├── base_engine.py           # 抽象引擎接口 + 数据模型
│   │       ├── ffmpeg_engine.py         # 基于 FFmpeg 的本地渲染器
│   │       └── tts_providers/           # 可插拔 TTS 策略层
│   │           ├── base_tts.py          # 抽象 TTS 接口
│   │           ├── edge_tts_provider.py  # Microsoft Edge TTS（免费）
│   │           ├── gtts_provider.py      # Google TTS（免费兜底）
│   │           └── cosyvoice_provider.py # 阿里 CosyVoice 声音克隆
│   ├── publishers/
│   │   ├── base_publisher.py
│   │   ├── telegram_adapter.py
│   │   ├── feishu_adapter.py
│   │   ├── wecom_adapter.py
│   │   ├── wechat_adapter.py
│   │   └── opencli_xhs_adapter.py
│   └── sources/
│       ├── base_source.py
│       ├── db_talent_source.py
│       ├── live_footprint_source.py
│       ├── legacy_rss.py
│       ├── github_trending_source.py
│       ├── arxiv_source.py
│       ├── opencli_hackernews.py
│       ├── trendradar_source.py
│       ├── youtube_source.py           # YouTube 视频数据源
│       ├── v2ex_source.py              # V2EX 中文技术社区
│       └── reddit_source.py            # 实验性：Reddit 数据源
└── web_dashboard/
```

## 架构原则

### 1. 配置驱动的管线调度

`main.py` 读取 `config/pipelines.yaml` 并遍历活跃的管线定义。

这意味着：

- 新管线主要通过配置引入
- 运行器根据管线选择数据源、Prompt 模板和发布器引用

### 2. 数据源 -> 过滤 -> 合成 -> 发布 流程

当前运行流程：

1. 加载活跃管线定义
2. 从一个或多个数据源获取原始事件
3. 通过 `EventStateManager` 过滤已处理的事件
4. 让 LLM 对事件进行排名 / 筛选
5. 根据选定事件合成 Markdown 输出
6. 将结果路由到发布器或本地草稿存储

### 3. 直接通知与人工审核的分离

系统当前区分：

- 同步通知渠道
  - Telegram
  - 飞书
  - 企业微信
- 异步草稿 / 审核渠道
  - 微信
  - 小红书

高风险发布渠道被拦截到草稿中，而不是盲目推送。

### 4. 可插拔视频引擎（策略模式）

视频生成子系统设计为三层解耦架构：

- `BaseVideoEngine` 定义渲染合约
- 具体引擎（如 `FFmpegVideoEngine`）实现该合约
- TTS 是引擎内的独立策略层（`BaseTTSProvider`）
- 引擎选择通过 `config/video_engines.yaml` 配置驱动

这意味着：

- 替换视频后端只需要新的引擎类和配置更改
- 管线、Prompt 和发布器与渲染实现完全解耦
- TTS 提供商可以独立于视频引擎进行替换

当管线在 `publisher_refs` 中包含 `video_draft` 时，运行器：

1. 使用 LLM 生成结构化视频脚本（分段旁白）
2. 从配置加载活动视频引擎
3. 调用 `engine.render()` 生成 MP4
4. 将视频路径保存到草稿存储供人工审核

### 5. CosyVoice 声音克隆策略

`cosyvoice_provider.py` 实现了基于 DashScope CosyVoice v3.5-plus 的声音克隆，
允许使用 Lilian 本人的声音进行 TTS 合成。

**关键技术决策 — 「逐段注册」策略**：

DashScope 免费 Tier 的克隆声音在注册后几秒内就会变为 `UNDEPLOYED`，
导致复用同一个 `voice_id` 会返回 418 错误。

解决方案是对每个文本段落执行独立的「注册 → 立即合成」原子操作：

```text
对每段口播稿文本：
  1. 上传参考音频到临时公开 URL（仅首段执行，后续复用 URL）
  2. 向 DashScope 注册一个新的 voice_id（随机 prefix 避免冲突）
  3. 在 DEPLOYING 窗口内立即调用 SpeechSynthesizer.call()
  4. 写入 MP3 文件 → 返回音频时长
```

这种模式确保每次合成都使用刚注册的活跃声音，绕过了部署超时限制。

## 主要组件

### `main.py`

职责：

- 加载 `config/pipelines.yaml`
- 遍历活跃管线
- 调用数据源收集
- 触发 LLM 筛选和合成
- 通过 `EventStateManager` 更新运行追踪

### `src/core/llm_engine.py`

职责：

- 排名 / 筛选候选事件
- 使用 Prompt 模板合成 Markdown

### `src/core/state_manager.py`

职责：

- 去重已处理的事件
- 创建和完成管线运行记录
- 保存草稿
- 保存运行产物

这是编排器的主要持久化和执行记忆层。

### `src/core/visual_engine.py`

职责：

- 为草稿审核渠道生成海报素材

### `src/core/video_engine/`

职责：

- 将结构化视频脚本渲染为 1080×1920 竖版 MP4 文件
- 管理 TTS 音频合成（含声音克隆）
- 生成高品质视觉卡片（渐变背景 + 毛玻璃面板 + 进度条）
- 4 阶段渲染管线：TTS → 视觉卡片 → 音频拼接 → FFmpeg 合成

关键文件：

- `base_engine.py` — 抽象接口（`BaseVideoEngine`、`VideoRenderRequest`、`ScriptSegment`、`VideoRenderResult`）
- `ffmpeg_engine.py` — 使用 ffmpeg-python + Pillow 的具体实现（含标题卡 + 内容卡生成）
- `tts_providers/base_tts.py` — 抽象 TTS 接口（`BaseTTSProvider`）
- `tts_providers/edge_tts_provider.py` — Microsoft Edge TTS（免费、高质量、中文 / 英文）
- `tts_providers/gtts_provider.py` — Google TTS 备选方案
- `tts_providers/cosyvoice_provider.py` — 阿里 CosyVoice 声音克隆（使用 Lilian 本人语音）

FFmpeg 渲染管线 4 阶段：

```text
Stage 1: TTS 语音生成
  ├── 2.5s 标题卡静音开场
  ├── 每段口播稿独立注册+合成（CosyVoice）或直接合成（Edge TTS）
  └── 0.8s 段间呼吸停顿

Stage 2: 视觉卡片生成（Pillow）
  ├── 标题卡：渐变背景 + 品牌 Badge + 来源标签
  └── 内容卡：上半 → 关键词高亮面板（青色）/ 下半 → 完整口播原文正文

Stage 3: 音频拼接 → final_audio.mp3

Stage 4: FFmpeg 合成
  ├── 每张卡片按时长编码为独立 MP4 片段
  ├── Concat demuxer 拼接所有视频片段
  └── 最终 mux：视频 + 音频 → output.mp4（libx264 + AAC + faststart）
```

### `src/sources/*`

职责：

- 从配置的上游系统收集原始事件

当前数据源系列包括：

- 本地数据库支持的人才数据源
- 实时足迹收集
- 传统 RSS 收集
- GitHub 热门项目
- ArXiv 监控
- TrendRadar / OpenCLI 风格 feeds
- **新增**：YouTube 视频内容（yt-dlp）
- **新增**：V2EX 中文技术社区（API）
- **实验性**：Reddit（rdt-cli，API 限制）

### `src/publishers/*`

职责：

- 将合成内容适配到出站渠道

当前发布器系列包括：

- Telegram
- 飞书
- 企业微信
- 微信
- 小红书

## 仪表盘关系

`web_dashboard/` 是此项目的前端控制层。

应该理解为：

- `universal_content_orchestrator` 的 UI 子模块
- 不是具有自己独立后端真相的独立产品

此仪表盘的后端 / API 位于：

- `src/api_server.py`

## 当前数据流

简化形式：

```text
config/pipelines.yaml
  → 数据源适配器
  → 事件去重 / 运行追踪
  → LLM 筛选
  → Markdown 合成
  → 发布器路由
     → 直接通知或本地草稿保存
     → 视频渲染（当 publisher_refs 包含 video_draft 时）
        → 参考音频上传（CosyVoice 模式，仅首次）
        → 逐段声音注册 + TTS 合成（CosyVoice v3.5-plus）
           或 直接 TTS（Edge TTS / gTTS 降级方案）
        → 视觉卡片渲染（标题卡 + 内容卡，Pillow 生成）
        → 音频拼接（含标题静音 + 段间停顿）
        → FFmpeg 合成 → 1080×1920 MP4
        → 视频草稿保存供人工审核
```

## 真相源规则

当本文档与代码冲突时，信任：

1. `main.py`
2. `config/pipelines.yaml`
3. `src/api_server.py`
4. `src/core/`
5. 本文档
