import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.sources.opencli_hackernews import OpenCLIHackerNewsSource
from src.sources.legacy_rss import LegacyRSSSource
from src.core.llm_engine import QwenEngine
from src.core.visual_engine import PillowVisualEngine
from src.publishers.wechat_adapter import WeChatPublisher

def main():
    print("==========================================================================")
    print("🌟 启动 Lilian [仅微信端] 追溯补发管线 🌟")
    print("==========================================================================\n")
    
    hn_source = OpenCLIHackerNewsSource()
    rss_source = LegacyRSSSource({
        "36Kr_AI": "https://36kr.com/feed", 
        "QbitAI": "https://www.qbitai.com/feed",
        "InfoQ": "https://www.infoq.cn/feed",
        "TechCrunch": "https://techcrunch.com/category/artificial-intelligence/feed/"
    })
    
    print("📡 [1] 开始重新提取今日顶流池...")
    hn_pool = hn_source.fetch(limit=15)
    rss_pool = rss_source.fetch(limit=25) 
    
    brain = QwenEngine()
    visual = PillowVisualEngine()
    wechat = WeChatPublisher()
    
    # 注意：这里我们刻意去掉了 state_manager 的拦截，为了强行补发今日的内容
    print("\n🧠 激活 Qwen 选择引擎（已绕过 SQLite 防撞拦截）...")
    top_hn = brain.select_top_articles(hn_pool, limit=3)
    top_rss = brain.select_top_articles(rss_pool, limit=5)
    
    final_events = top_hn + top_rss
    print(f"\n🚀 [2] 选定 {len(final_events)} 篇情报，专供微信分发：")
    
    for i, event in enumerate(final_events, 1):
        print(f"\n[任务 {i}/{len(final_events)}] ==========================")
        draft = brain.synthesize_single_article(event)
        lines = [l.strip() for l in draft.split('\n') if l.strip()]
        raw_title = lines[0] if lines else "AI行业新风向"
        raw_sub = lines[1] if len(lines) > 1 else "技术底座洗牌"
        
        title = raw_title.replace("【", "").replace("】", "").replace("[", "").replace("]", "").replace("*", "").strip()
        subtitle = raw_sub.replace("【", "").replace("】", "").replace("[", "").replace("]", "").replace("*", "").strip()
        
        if len(title) > 60: title = title[:58] + "…"
        if len(subtitle) > 40: subtitle = subtitle[:38] + "..."
        
        poster_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"poster_wx_{event.id}.jpg")
        visual.generate_poster(title=title, subtitle=subtitle, badge="Lilian甄选", output_path=poster_path, mode="wechat")
        
        print(f"🖼️ [分发准备] 微信版横版大图 (2.35:1) 生成完毕 -> {poster_path}")
        
        # 仅推送微信，不触发 XHS，防止小红书被发重复内容
        wechat.push(title=title, content_md=draft, poster_path=poster_path)
        
    print("\n✅ 微信专属补发通道运行完毕！")

if __name__ == "__main__":
    main()
