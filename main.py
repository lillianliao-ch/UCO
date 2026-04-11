import sys
import os
import time
import json
import yaml

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.llm_engine import QwenEngine
from src.core.visual_engine import PillowVisualEngine
from src.publishers.opencli_xhs_adapter import OpenCLIXiaohongshuPublisher
from src.publishers.telegram_adapter import TelegramPublisher
from src.publishers.wechat_adapter import WeChatPublisher
from src.core.state_manager import EventStateManager

def _load_video_engine(pipe):
    """Load the configured video engine from config/video_engines.yaml."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "video_engines.yaml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            ve_config = yaml.safe_load(f)
    except Exception as e:
        print(f"⚠️ 无法读取视频引擎配置: {e}")
        return None, {}

    # Pipeline-level override or global default
    video_cfg = pipe.get("video_config", {})
    engine_name = video_cfg.get("engine", ve_config.get("active_engine", "ffmpeg_local"))
    engine_spec = ve_config.get("engines", {}).get(engine_name, {})

    # Currently only ffmpeg_local is implemented
    if engine_name == "ffmpeg_local":
        from src.core.video_engine.ffmpeg_engine import FFmpegVideoEngine
        engine = FFmpegVideoEngine()
    else:
        print(f"⚠️ 未实现的视频引擎: {engine_name}，回退到 ffmpeg_local")
        from src.core.video_engine.ffmpeg_engine import FFmpegVideoEngine
        engine = FFmpegVideoEngine()

    # Merge config: pipeline video_config > engine defaults > hardcoded defaults
    merged = {
        "tts": video_cfg.get("tts", engine_spec.get("default_tts", "edge_tts")),
        "voice": video_cfg.get("voice", engine_spec.get("default_voice", "zh-CN-XiaoxiaoNeural")),
        "resolution": video_cfg.get("resolution", engine_spec.get("default_resolution", [1080, 1920])),
    }
    return engine, merged


def _parse_video_script(draft_text: str) -> dict:
    """Parse LLM output as a structured video script JSON."""
    # Extract JSON from possible markdown code fences
    import re
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', draft_text)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_str = draft_text.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Fallback: treat entire draft as a single narration segment
        return {
            "title_card": "AI 情报速递",
            "segments": [{"text": draft_text[:300], "visual_text": "今日要闻"}]
        }


def process_single_dynamic_event(event, run_id, brain, visual, pipe, state_manager):
    # 动态挂载专属人设 (Prompt)
    draft = brain.synthesize_with_prompt(event, pipe.get("prompt_template", "xhs_style_a_lilian.md"))
    
    # 清洗文本以提取优雅的标题
    draft = draft.replace("\\n", "\n")
    lines = [l.strip() for l in draft.split('\n') if l.strip()]
    raw_title = lines[0] if lines else "全域管线新报"
    title = raw_title.replace("【", "").replace("】", "").replace("[", "").replace("]", "").replace("*", "").replace("#", "").strip()
    if len(title) > 22: title = title[:20] + "…"
    
    publishers = pipe.get("publisher_refs", [])
    is_drafted = False
    
    # 1. 绿灯网关：如果配了 Telegram，立刻免审送达 (Sync Notify)
    channel_status = {}
    
    if "telegram_log" in publishers or "telegram" in publishers:
        print("📲 [Telegram] 命中免审白名单，执行私人终端定点送达...")
        try:
            TelegramPublisher().push_draft(f"🎯 管线战报: {pipe['name']}", f"**{title}**\n\n{draft}\n\n🔗 来源: {event.url}", None)
            channel_status["telegram"] = {"status": "success"}
        except Exception as e:
            print(f"❌ [Telegram] 推送失败: {e}")
            channel_status["telegram"] = {"status": "error", "message": str(e)}
        
    if "wecom_notification" in publishers:
        from src.publishers.wecom_adapter import WeComPublisher
        try:
            WeComPublisher().push_draft(f"🎯 管线战报: {pipe['name']}", f"**{title}**\n\n{draft}\n\n🔗 来源: {event.url}", None)
            channel_status["wecom"] = {"status": "success"}
        except Exception as e:
            print(f"❌ [WeCom] 推送失败: {e}")
            channel_status["wecom"] = {"status": "error", "message": str(e)}
        
    if "feishu_log" in publishers:
        from src.publishers.feishu_adapter import FeishuPublisher
        try:
            FeishuPublisher().push_draft(f"🎯 管线战报: {pipe['name']}", f"**{title}**\n\n{draft}\n\n🔗 来源: {event.url}", None)
            channel_status["feishu"] = {"status": "success"}
        except Exception as e:
            print(f"❌ [Feishu] 推送失败: {e}")
            channel_status["feishu"] = {"status": "error", "message": str(e)}

    # 2. 视频渲染网关：如果配了 video_draft，触发视频引擎生成 MP4
    if "video_draft" in publishers:
        draft_id = f"draft_{event.id}_{int(time.time())}"
        videos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "videos")
        os.makedirs(videos_dir, exist_ok=True)

        try:
            from src.core.video_engine.base_engine import VideoRenderRequest, ScriptSegment

            engine, vcfg = _load_video_engine(pipe)
            if engine is None:
                raise RuntimeError("Video engine load failed")

            # Parse the LLM output as a structured video script
            script_data = _parse_video_script(draft)
            title_card_text = script_data.get("title_card", title)
            segments_raw = script_data.get("segments", [])

            if not segments_raw:
                segments_raw = [{"text": draft[:300], "visual_text": "今日要闻"}]

            script_segments = [
                ScriptSegment(
                    text=seg.get("text", ""),
                    visual_text=seg.get("visual_text", None),
                )
                for seg in segments_raw
            ]

            output_path = os.path.join(videos_dir, f"{draft_id}.mp4")
            resolution = tuple(vcfg.get("resolution", [1080, 1920]))

            render_request = VideoRenderRequest(
                title=title_card_text,
                script_segments=script_segments,
                output_path=output_path,
                resolution=resolution,
                tts_provider=vcfg.get("tts", "edge_tts"),
                tts_voice=vcfg.get("voice", "zh-CN-XiaoxiaoNeural"),
                badge_text=pipe.get("name", ""),
                subtitle_text=f"来源: {event.source_channel}",
            )

            result = engine.render(render_request)

            if result.success:
                video_rel_path = f"/videos/{draft_id}.mp4"
                state_manager.save_draft(
                    draft_id, pipe['id'], event, title, draft,
                    poster_xhs=None, poster_wx=None, video_path=video_rel_path
                )
                channel_status["video_draft"] = {
                    "status": "draft_saved",
                    "video_path": video_rel_path,
                    "duration": f"{result.duration_seconds:.1f}s",
                    "segments": result.segments_rendered,
                }
                is_drafted = True
                print(f"📥 [Video Draft] 短视频已生成并落入草稿待审区: {draft_id} ({result.duration_seconds:.1f}s)")
            else:
                channel_status["video_draft"] = {"status": "error", "message": result.error_message}
                print(f"❌ [Video Draft] 渲染失败: {result.error_message}")

        except Exception as e:
            print(f"❌ [Video Draft] 视频生成管线异常: {e}")
            import traceback
            traceback.print_exc()
            channel_status["video_draft"] = {"status": "error", "message": str(e)}

    # 3. 红灯网关：高危社交平台 (Xiaohongshu/WeChat) 强制拦截落入草稿箱 (Async HitL Draft)
    if "xiaohongshu" in publishers or "wechat" in publishers:
        draft_id = f"draft_{event.id}_{int(time.time())}"
        
        # Draw dynamic posters via the Pillow engine
        from src.core.visual_engine import PillowVisualEngine
        visual_inst = PillowVisualEngine()
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "assets")
        os.makedirs(assets_dir, exist_ok=True)
        
        poster_xhs, poster_wx = None, None
        badge = pipe["name"]
        
        try:
            if "xiaohongshu" in publishers:
                p = os.path.join(assets_dir, f"{draft_id}_xhs.jpg")
                visual_inst.generate_poster(title, "全域管线新报 | Universal Content Orchestrator", badge, p, mode="xhs")
                poster_xhs = f"/assets/{draft_id}_xhs.jpg"
                channel_status["xiaohongshu"] = {"status": "draft_saved", "notice": "强制落本地草稿待审"}
                
            if "wechat" in publishers:
                p = os.path.join(assets_dir, f"{draft_id}_wx.jpg")
                visual_inst.generate_poster(title, "全域管线新报 | Universal Content Orchestrator", badge, p, mode="wechat")
                poster_wx = f"/assets/{draft_id}_wx.jpg"
                channel_status["wechat"] = {"status": "draft_saved", "notice": "强制落本地草稿待审"}
                
            state_manager.save_draft(draft_id, pipe['id'], event, title, draft, poster_xhs, poster_wx)
            print(f"📥 [HitL 拦截] 高危长图文已切断直发！强制落入 SQL 草稿待审区: {draft_id}")
            is_drafted = True
        except Exception as e:
            print(f"❌ [HitL 拦截] 生成长图文或保存草稿失败: {e}")
            if "xiaohongshu" in publishers:
                channel_status["xiaohongshu"] = {"status": "error", "message": f"Poster generation/db error: {e}"}
            if "wechat" in publishers:
                channel_status["wechat"] = {"status": "error", "message": f"Poster generation/db error: {e}"}

    # 对于免审通知渠道，我们需要标记其已发布，防止Telegram明天又弹一遍
    if not is_drafted:
        state_manager.mark_success(event, pipe['id'])
        
    # 保存执行制品记录
    artifact_id = f"art_{event.id}_{int(time.time())}"
    state_manager.save_run_artifact(
        artifact_id, 
        run_id, 
        pipe['id'], 
        event.url, 
        title, 
        draft, 
        json.dumps(channel_status, ensure_ascii=False)
    )
        
    return {"title": title, "success": True, "is_drafted": is_drafted}

def run_dynamic_pipeline(pipe):
    print(f"\n==========================================================================")
    print(f"🚀 启动泛用型管线: 【{pipe['name']}】 ID:{pipe['id']}")
    print(f"==========================================================================")
    
    state_manager = EventStateManager()
    run_id = f"run_{pipe['id']}_{int(time.time())}"
    state_manager.create_pipeline_run(run_id, pipe['id'])
    
    items_scraped = 0
    items_passed_llm = 0
    drafts_generated = 0
    run_status = "SUCCESS"
    
    try:
        events = []
        source_refs = pipe.get("source_refs", [])
        
        print("📡 [1] 开始从管线注册的源头抽水汇聚...")
        # 动态路由装载源头数据
        # 1. TrendRadar
        tr_platforms = [src.replace("tr_", "") for src in source_refs if src.startswith("tr_")]
        if "trendradar" in source_refs or tr_platforms:
            from src.sources.trendradar_source import TrendRadarSource
            kwargs = {"limit": 15}
            if tr_platforms: kwargs["platforms"] = tr_platforms
            events.extend(TrendRadarSource().fetch(**kwargs))

        # 2. OpenCLI HackerNews
        if "opencli_hackernews" in source_refs or "rss_hacker_news" in source_refs:
            from src.sources.opencli_hackernews import OpenCLIHackerNewsSource
            events.extend(OpenCLIHackerNewsSource().fetch(limit=15))

        # 3. DB Talent Source
        if "maimai_updates" in source_refs or "linkedin_monitor" in source_refs:
            from src.sources.db_talent_source import DBTalentSource
            events.extend(DBTalentSource().fetch(limit=10))

        # 4. Legacy RSS
        rss_map_active = {}
        if "producthunt_hunter" in source_refs:
            rss_map_active["ProductHunt"] = "https://ph-rss.stephenou.com/"
            rss_map_active["Show_HackerNews"] = "https://hnrss.org/show"
        if "wsj_ai_finance" in source_refs or "sec_13f_filings" in source_refs:
            rss_map_active["WSJ_Tech_Finance"] = "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml"
            rss_map_active["TechCrunch_AI"] = "https://techcrunch.com/category/artificial-intelligence/feed/"
        if "chinese_tech_media" in source_refs:
            rss_map_active["36Kr"] = "https://36kr.com/feed"
            rss_map_active["Jiqizhixin"] = "https://www.jiqizhixin.com/rss"
        
        if "rss_36kr" in source_refs: rss_map_active["36Kr"] = "https://36kr.com/feed"
        if "rss_hackernews" in source_refs: rss_map_active["HackerNews"] = "https://hnrss.org/newest?q=AI"
        
        if rss_map_active:
            from src.sources.legacy_rss import LegacyRSSSource
            events.extend(LegacyRSSSource(rss_map_active).fetch(limit=15))
            
        if "live_footprint_source" in source_refs:
            from src.sources.live_footprint_source import LiveFootprintSource
            events.extend(LiveFootprintSource().fetch(limit=3))

        # 5. GitHub Trending (新: UCO 标准源 + 事件总线广播)
        if "github_trending" in source_refs:
            from src.sources.github_trending_source import GitHubTrendingSource
            events.extend(GitHubTrendingSource().fetch(limit=15))

        # 6. ArXiv 论文监控 (新: UCO 标准源 + 事件总线广播)
        if "arxiv_monitor" in source_refs:
            from src.sources.arxiv_source import ArxivSource
            events.extend(ArxivSource().fetch(limit=15))

        # 7. YouTube AI技术视频监控 (新: Agent-Reach集成)
        if "youtube_ai_trends" in source_refs:
            from src.sources.youtube_source import YouTubeSource
            youtube = YouTubeSource(
                search_queries=['LLM tutorial', 'AI agent development', 'RAG implementation']
            )
            events.extend(youtube.fetch(limit=3))

        # 8. V2EX中文技术社区监控 (新: Agent-Reach集成)
        if "v2ex_ai_discussions" in source_refs:
            from src.sources.v2ex_source import V2EXSource
            v2ex = V2EXSource(node_ids=['678', '1135'])  # ML 和 OpenAI 节点
            events.extend(v2ex.fetch(limit=5))

        items_scraped = len(events)
        print(f"🛡️ [1.5] 海马体记忆介入，当前原始情报池大小: {items_scraped}。开始过滤...")
        
        new_events = [e for e in events if not state_manager.is_processed(e, pipe['id'])]
        print(f"🗂️ 过滤老旧去重后，剩余有效情报 {len(new_events)} 篇进入决胜轮。")
        
        if not new_events:
            print("📭 暂无待处理全新爆点情报。管线挂起休眠。")
            return
            
        brain = QwenEngine()
        visual = PillowVisualEngine() # Pre-load just in case
        
        print("\n🧠 [2] 激活主编鉴赏淘汰赛...")
        filter_tpl = pipe.get("filter_template", "filter_priority.md")
        top_events = brain.select_top_articles(new_events, limit=3, filter_template=filter_tpl)
        items_passed_llm = len(top_events)
        
        print(f"\n🚀 [3] 锁定 {items_passed_llm} 篇顶级锚点，开始逐点击破与分发：")
        for i, event in enumerate(top_events, 1):
            print(f"\n[任务 {i}/{len(top_events)}] ==========================")
            res = process_single_dynamic_event(event, run_id, brain, visual, pipe, state_manager)
            if res.get("is_drafted"):
                drafts_generated += 1
                
        print(f"\n✅ 管线 [{pipe['name']}] 单圈战役闭环完结！")

    except Exception as e:
        run_status = f"FAILED: {str(e)}"
        print(f"❌ 管线严重崩溃 (已记录至数据库): {run_status}")
        raise e
    finally:
        # Guarantee funnel metrics are saved to the SQLite run tracking table
        state_manager.update_pipeline_run(run_id, items_scraped, items_passed_llm, drafts_generated, run_status)

def main():
    print("==========================================================================")
    print("🌟 启动 Lilian 多路智能分发大矩阵 (Multiverse Orchestrator) 🌟")
    print("==========================================================================\n")
    
    config_path = os.path.join(os.path.dirname(__file__), "config", "pipelines.yaml")
    if not os.path.exists(config_path):
        print("❌ 未找到配置文件 config/pipelines.yaml")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    target_pipe = sys.argv[1] if len(sys.argv) > 1 else None
    
    for pipe in data.get("pipelines", []):
        if target_pipe and pipe["id"] != target_pipe:
            continue
            
        if not pipe.get("active", False):
            print(f"⏸️  管线 [{pipe['name']}] 节点开关处于【已休眠】状态，智能切断供能。")
            continue
            
        # 调用泛化工厂彻底解除以前的硬编码耦合
        try:
            run_dynamic_pipeline(pipe)
        except Exception as e:
            print(f"❌ 管线 {pipe['id']} 发生毁灭性致命异常: {e}")
            
    print("\n🏁 全域并发管线扫描与调度结束。")

if __name__ == "__main__":
    main()
