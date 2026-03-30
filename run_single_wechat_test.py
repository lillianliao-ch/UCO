import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.sources.opencli_hackernews import OpenCLIHackerNewsSource
from src.core.llm_engine import QwenEngine
from src.core.visual_engine import PillowVisualEngine
from src.publishers.wechat_adapter import WeChatPublisher

def main():
    print("======================================================")
    print("🌟 启动单篇微信横板海报 (2.35:1) 与注入联动测试 🌟")
    print("======================================================\n")
    
    hn_source = OpenCLIHackerNewsSource()
    
    print("📡 提取 1 篇最新的外网极客情报...")
    hn_pool = hn_source.fetch(limit=1)
    if not hn_pool:
        print("暂无情报。")
        return
        
    event = hn_pool[0]
    
    brain = QwenEngine()
    visual = PillowVisualEngine()
    wechat = WeChatPublisher()
    
    print(f"\n🧠 Qwen 引擎正在为【{event.title}】重写爆款解析文案...")
    draft = brain.synthesize_single_article(event)
    
    lines = [l.strip() for l in draft.split('\n') if l.strip()]
    raw_title = lines[0] if lines else "AI行业风向标"
    raw_sub = lines[1] if len(lines) > 1 else "底层架构思考"
    
    title = raw_title.replace("【", "").replace("】", "").replace("[", "").replace("]", "").replace("*", "").strip()
    subtitle = raw_sub.replace("【", "").replace("】", "").replace("[", "").replace("]", "").replace("*", "").strip()
    
    if len(title) > 60: title = title[:58] + "…"
    if len(subtitle) > 40: subtitle = subtitle[:38] + "..."
    
    poster_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"poster_wx_test.jpg")
    print(f"\n🎨 开始绘制 2.35:1 (1175x500) 原生微信横向海报...")
    visual.generate_poster(title=title, subtitle=subtitle, badge="Lilian首发", output_path=poster_path, mode="wechat")
    
    print(f"\n🚀 开始触发 Playwright 剪贴板伪装注入机制...")
    wechat.push(title=title, content_md=draft, poster_path=poster_path)
    
    print("\n✅ 单篇测试结束！请赴草稿箱查阅最终的排版与封面尺寸完美匹配度。")

if __name__ == "__main__":
    main()
