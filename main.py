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

def process_single_dynamic_event(event, brain, visual, pipe, state_manager):
    # 动态挂载专属人设 (Prompt)
    draft = brain.synthesize_with_prompt(event, pipe.get("prompt_template", "xhs_style_a_lilian.md"))
    
    # 清洗文本以提取优雅的标题
    draft = draft.replace("\\n", "\n")
    lines = [l.strip() for l in draft.split('\n') if l.strip()]
    raw_title = lines[0] if lines else "全域管线新报"
    title = raw_title.replace("【", "").replace("】", "").replace("[", "").replace("]", "").replace("*", "").replace("#", "").strip()
    if len(title) > 22: title = title[:20] + "…"
    
    publishers = pipe.get("publisher_refs", [])
    
    # 1. 如果配了 Telegram，优先单通道定点投递汇报 (Private Inbox)
    if "telegram_log" in publishers or "telegram" in publishers:
        print("📲 [Telegram] 执行私人终端定点送达...")
        TelegramPublisher().push_draft(f"🎯 管线战报: {pipe['name']}", f"**{title}**\n\n{draft}\n\n🔗 来源: {event.url}", None)
        
    # 1.5 企微与飞书多端齐发
    if "wecom_notification" in publishers:
        from src.publishers.wecom_adapter import WeComPublisher
        WeComPublisher().push_draft(f"🎯 管线战报: {pipe['name']}", f"**{title}**\n\n{draft}\n\n🔗 来源: {event.url}", None)
        
    if "feishu_log" in publishers:
        from src.publishers.feishu_adapter import FeishuPublisher
        FeishuPublisher().push_draft(f"🎯 管线战报: {pipe['name']}", f"**{title}**\n\n{draft}\n\n🔗 来源: {event.url}", None)

    # 2. 如果配了小红书/微信，触发 HitL (生成图片，存入草稿箱拦截待审)
    if "xiaohongshu" in publishers or "wechat" in publishers:
        poster_path_xhs = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"poster_xhs_{event.id}.jpg")
        poster_path_wx = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"poster_wx_{event.id}.jpg")
        
        visual.generate_poster(title=title, subtitle=pipe['name'], badge="Lilian甄选", output_path=poster_path_xhs, mode="xhs")
        visual.generate_poster(title=title, subtitle=pipe['name'], badge="Lilian甄选", output_path=poster_path_wx, mode="wechat")
        
        draft_dir = os.path.join(os.path.dirname(__file__), "data", "drafts")
        os.makedirs(draft_dir, exist_ok=True)
        
        draft_id = f"{event.id}_{int(time.time())}"
        draft_payload = {
            "id": draft_id,
            "raw_event_id": event.id,
            "title": title,
            "content_md": draft,
            "poster_path_xhs": poster_path_xhs,
            "poster_path_wx": poster_path_wx,
            "status": "pending_review",
            "pipeline_id": pipe['id'],
            "generate_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        draft_file = os.path.join(draft_dir, f"{draft_id}.json")
        with open(draft_file, "w", encoding="utf-8") as f:
            json.dump(draft_payload, f, ensure_ascii=False, indent=2)
            
        print(f"📥 [HitL 拦截] 已生成发布级图文并落入审核池: {draft_file}")
        
    # 彻底告别盲目直发，标记为当前管线已处理
    state_manager.mark_success(event, pipe['id'])
    return {"title": title, "success": True}

def run_dynamic_pipeline(pipe):
    print(f"\n==========================================================================")
    print(f"🚀 启动泛用型管线: 【{pipe['name']}】 ID:{pipe['id']}")
    print(f"==========================================================================")
    
    events = []
    source_refs = pipe.get("source_refs", [])
    
    print("📡 [1] 开始从管线注册的源头抽水汇聚...")
    # 动态路由装载源头数据
    if "trendradar" in source_refs:
        from src.sources.trendradar_source import TrendRadarSource
        events.extend(TrendRadarSource().fetch(limit=15))
    if "rss_hacker_news" in source_refs:
        from src.sources.opencli_hackernews import OpenCLIHackerNewsSource
        events.extend(OpenCLIHackerNewsSource().fetch(limit=15))
    if "maimai_updates" in source_refs or "linkedin_monitor" in source_refs:
        from src.sources.db_talent_source import DBTalentSource
        events.extend(DBTalentSource().fetch(limit=10))
    if "producthunt_hunter" in source_refs:
        from src.sources.legacy_rss import LegacyRSSSource
        rss = LegacyRSSSource({
            "ProductHunt": "https://ph-rss.stephenou.com/",
            "Show_HackerNews": "https://hnrss.org/show"
        })
        events.extend(rss.fetch(limit=10))
    if "wsj_ai_finance" in source_refs or "sec_13f_filings" in source_refs:
        from src.sources.legacy_rss import LegacyRSSSource
        rss = LegacyRSSSource({"WSJ_Tech_Finance": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml"})
        events.extend(rss.fetch(limit=10))
    if "live_footprint_source" in source_refs:
        from src.sources.live_footprint_source import LiveFootprintSource
        events.extend(LiveFootprintSource().fetch(limit=3))
        
    state_manager = EventStateManager()
    print(f"🛡️ [1.5] 海马体记忆介入，当前原始情报池大小: {len(events)}。开始过滤...")
    
    new_events = [e for e in events if not state_manager.is_processed(e, pipe['id'])]
    print(f"🗂️ 过滤老旧去重后，剩余有效情报 {len(new_events)} 篇进入决胜轮。")
    
    if not new_events:
        print("📭 暂无待处理全新爆点情报。管线挂起休眠。")
        return
        
    brain = QwenEngine()
    visual = PillowVisualEngine()
    
    print("\n🧠 [2] 激活主编鉴赏淘汰赛...")
    # 由于生成成本高，由模型决定最终执行力最大的前N篇文章
    top_events = brain.select_top_articles(new_events, limit=3)
    
    print(f"\n🚀 [3] 锁定 {len(top_events)} 篇顶级锚点，开始逐点击破与分发：")
    for i, event in enumerate(top_events, 1):
        print(f"\n[任务 {i}/{len(top_events)}] ==========================")
        process_single_dynamic_event(event, brain, visual, pipe, state_manager)
        
    print(f"\n✅ 管线 [{pipe['name']}] 单圈战役闭环完结！")

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
