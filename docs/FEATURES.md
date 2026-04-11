# Universal Content Orchestrator 功能清单

> 最后更新：2026-04-11
> 状态：v2.0 — 含视频引擎 + 声音克隆

本文档列出了系统当前支持的所有功能。

它可以回答：

- 存在哪些数据源类型
- 存在哪些输出渠道
- 已有哪些操作功能
- 哪些功能仍在开发中

## 当前数据源能力

### 数据库 / 人才数据源

- 通过 `db_talent_source.py` 接入本地 AI 猎头数据库
- 与本地候选人数据库绑定的高管 / 人才监控流程

### Web / Feed 数据源

- 实时足迹监控
- 传统 RSS 订阅
- GitHub 热门项目抓取
- ArXiv 论文监控
- OpenCLI HackerNews 风格数据源
- TrendRadar 数据源
- **新增**：YouTube 视频内容抓取（字幕提取 + 元数据）
- **新增**：V2EX 中文技术社区监控
- **实验性**：Reddit 内容抓取（API 限制，暂时跳过）

## 当前处理能力

- 通过 `config/pipelines.yaml` 进行配置驱动的管线调度
- 基于 LLM 的事件筛选 / 优先级排序
- 通过 Prompt 模板驱动的内容合成
- 每个管线的去重机制（通过 `EventStateManager`）
- 运行追踪和产物持久化
- 草稿审核渠道的海报生成

## 当前输出能力

### 直接通知渠道

- Telegram
- 飞书
- 企业微信

这些渠道用于快速通知式分发。

### 草稿 / 审核渠道

- 微信
- 小红书

这些渠道目前通过草稿导向的审核流程处理，而非完全自动发布。

### 视频输出

通过可插拔的视频引擎生成 1080×1920 竖版短视频（MP4），用于抖音 / TikTok / 视频号等平台。

已实现能力：

- **视觉渲染**：渐变背景 + 毛玻璃质感面板 + 进度条 + 品牌水印
- **偏平化卡片设计**：
  - 标题卡：Badge + 标题 + 来源标签
  - 内容卡：上半关键词高亮（青色）+ 下半完整口播原文（白色）
- **TTS 语音合成**：
  - Edge TTS（免费、女声 XiaoxiaoNeural / 男声 YunxiNeural）
  - Google TTS（免费兜底）
  - **CosyVoice 声音克隆**（使用 Lilian 本人语音，基于 DashScope v3.5-plus）
- **音频节奏控制**：2.5s 标题卡静音开场 + 0.8s 段间呼吸停顿
- **视频草稿保存到本地存储**，供人工审核后分发

视频引擎设计为抽象层（`BaseVideoEngine`）。当前实现使用 FFmpeg 进行本地渲染。引擎可以更换而不影响管线或 Prompt。

## 开源技术栈 / 依赖项

以下是系统集成的开源项目和外部服务：

| 组件 | 开源项目 / 服务 | 用途 |
|------|-------------|------|
| 视频编码 | **FFmpeg** (`ffmpeg-python`) | 视频合成、音频拼接、格式转换 |
| 图像生成 | **Pillow** (PIL) | 视觉卡片渲染（渐变、面板、排版） |
| TTS 免费 | **edge-tts** | 微软 Edge 语音合成 API 封装 |
| TTS 兜底 | **gTTS** | Google Translate TTS |
| 声音克隆 | **DashScope SDK** (`dashscope`) | 阿里云 CosyVoice v3.5-plus 声音克隆 |
| 临时文件托管 | **tmpfiles.org** | 为 DashScope 提供参考音频的公开 URL |
| LLM 引擎 | **通义千问 Qwen** (DashScope) | 事件筛选、内容合成、视频脚本生成 |
| 配置管理 | **PyYAML** | 管线和视频引擎配置 |
| YouTube 数据 | **yt-dlp** | YouTube 视频元数据和字幕提取 |
| Web 抓取 | **Playwright / CDP** | 浏览器自动化和会话克隆 |

## 当前 UX / 平台能力

- 目标管线执行：
  - `python3 main.py <pipeline_id>`
- 位于 `src/api_server.py` 的 API 层
- 位于 `web_dashboard/` 的仪表盘前端
- 定时任务支持，详见 `docs/SCHEDULED_TASKS.md`

## 开发中 / 尚未完全完成

这些是活跃的架构和产品方向，而非完全“完成”的功能：

- 更深入的执行可观测性漏斗
- 更强的失败状态和追踪持久化
- 更正式的人工审核草稿工作流
- Web 仪表盘草稿箱中的视频预览
- 一键发布视频到抖音 / 微信视频号
- Fish Audio / 硅基流动 TTS 提供商接入
- 视频转场动画（fade / crossfade）

如果某个项目仍然主要被描述为未来的架构步骤或路线图项目，则应被视为计划中 / 开发中，而非完全完成的功能。
