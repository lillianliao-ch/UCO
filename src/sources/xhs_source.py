import time
import hashlib
from datetime import datetime
from typing import List
from playwright.sync_api import sync_playwright

from src.sources.base_source import BaseSourceAdapter
from src.core.schemas import RawContentEvent

class XiaohongshuSource(BaseSourceAdapter):
    """
    Agent-Reach: 小红书 (Xiaohongshu) 爆款笔记搜寻探针。
    借用现存的 CDP Cookie 会话池，穿越风控墙，获取指定关键词下的高热度笔记列表。
    """
    def __init__(self, keyword="AI工具", port=9224):
        self.keyword = keyword
        self.port = port
        self.cdp_url = f"http://localhost:{self.port}"
        
    def fetch(self, limit: int = 15) -> List[RawContentEvent]:
        events = []
        print(f"🚀 [Source: XHS] 挂载 CDP 底座，准备浸入小红书搜集关键词: {self.keyword}")
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp(self.cdp_url)
                context = browser.contexts[0]
                page = context.new_page()
                
                # Navigate to XHS Search Result
                encoded_kw = self.keyword.replace(" ", "+")
                search_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_kw}&source=web_explore_feed"
                
                page.goto(search_url, timeout=20000)
                
                # Wait for the waterfall feed to load
                page.wait_for_selector('section.note-item', timeout=15000)
                
                # Sometimes we need to scroll to load pictures and data
                page.keyboard.press("PageDown")
                time.sleep(2)
                
                # Extract sections
                sections = page.locator('section.note-item').all()
                
                for sec in sections[:limit]:
                    try:
                        # Extract link
                        link_el = sec.locator('a.cover').first
                        if link_el.count() == 0: continue
                        href = link_el.get_attribute("href")
                        
                        # Extract Title
                        title_el = sec.locator('a.title span').first
                        if title_el.count() == 0: continue
                        title = title_el.inner_text().strip()
                        
                        # Extract Image Cover
                        img_el = sec.locator('a.cover img').first
                        cover = img_el.get_attribute("src") if img_el.count() > 0 else ""
                        
                        # Extract Likes
                        like_el = sec.locator('span.count').first
                        likes_text = like_el.inner_text().strip() if like_el.count() > 0 else "0"
                        
                        # Calculate raw score (e.g. 1.2w -> 12000)
                        score = 0
                        if "w" in likes_text.lower():
                            score = float(likes_text.lower().replace("w", "")) * 10000
                        elif "k" in likes_text.lower():
                            score = float(likes_text.lower().replace("k", "")) * 1000
                        else:
                            try:
                                score = float(likes_text)
                            except:
                                pass
                                
                        if href and title:
                            full_url = f"https://www.xiaohongshu.com{href}" if href.startswith("/") else href
                            unique_id = f"xhs_{hashlib.md5(full_url.encode()).hexdigest()[:8]}"
                            
                            event = RawContentEvent(
                                id=unique_id,
                                source_channel="xhs_monitor",
                                title=title,
                                content=f"【小红书爆款情报捕捉】\n标题：{title}\n\n当前热度点赞量：{likes_text}\n链接：{full_url}\n非常适合萃取或参考其排版套路，请深度评阅。",
                                url=full_url,
                                media_urls=[cover] if cover else [],
                                timestamp=datetime.now(),
                                score=score
                            )
                            events.append(event)
                    except Exception as parse_e:
                        print(f"   [Source: XHS] 跳过异常卡片结构: {parse_e}")
                        
                page.close()
                print(f"✅ [Source: XHS] 成功搜集到 {len(events)} 篇高相关笔记！")
                
            except Exception as e:
                print(f"❌ [Source: XHS] CDP 会话剥离失败或结构变更: {e}")
                
        return events

if __name__ == "__main__":
    x = XiaohongshuSource()
    res = x.fetch(limit=3)
    for r in res:
        print(f"标题: {r.title} | 热度: {r.score} | 链接: {r.url}")
