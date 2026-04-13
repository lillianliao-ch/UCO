import requests
import json
import hashlib
from typing import List
from datetime import datetime
from src.sources.base_source import BaseSourceAdapter
from src.core.schemas import RawContentEvent

class BilibiliAISource(BaseSourceAdapter):
    """
    Agent-Reach: 哔哩哔哩 (Bilibili) 深度视频预警探针。
    通过公开 API 直接检索 B站 AI 领域的最新高权重投稿（如教程、评测），无需强耦合 CDP。
    """
    def __init__(self, keyword="AI工具", route_id="bilibili_ai_search"):
        self.keyword = keyword
        self.route_id = route_id

    def fetch(self, limit: int = 10) -> List[RawContentEvent]:
        events = []
        try:
            # Bilibili web search API
            url = "https://api.bilibili.com/x/web-interface/wbi/search/all/v2"
            
            # Note: The true wbi sign requires client side hashing, but Bilibili allows the legacy app API
            # For robustness without wbi signing, we use the mobile app search API snippet or public hot hooks.
            # We'll use a direct basic v2 search without sign which currently permits limited open calls 
            # for public IPs, or fallback to the generic search API.
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Referer": "https://search.bilibili.com/"
            }
            
            params = {
                "keyword": self.keyword,
                "search_type": "video",
                "order": "pubdate",  # Sort by newest
            }
            
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    results = data.get("data", {}).get("result", [])
                    # The video results are nested in result array where result_type = 'video'
                    video_list = []
                    for group in results:
                        if group.get("result_type") == "video":
                            video_list.extend(group.get("data", []))
                            
                    for v in video_list[:limit]:
                        bvid = v.get("bvid")
                        title = v.get("title", "").replace('<em class="keyword">', "").replace('</em>', "")
                        desc = v.get("description", "")
                        author = v.get("author", "Unknown UP")
                        cover = "http:" + v.get("pic", "") if v.get("pic") else ""
                        pub_time = v.get("pubdate", 0)
                        
                        unique_id = f"bili_{bvid}"
                        
                        # Pack into the unified RawContentEvent
                        payload_body = f"【B站前沿视频提醒】\n标题：{title}\nUP主：{author}\n\n简介摘要：{desc}\n\n这可能是一个优质的 AI 工具或干货教程视频，需注意其内容含量。"
                        
                        event = RawContentEvent(
                            id=hashlib.md5(unique_id.encode()).hexdigest()[:12],
                            source_channel=self.route_id,
                            title=title,
                            content=payload_body,
                            url=f"https://www.bilibili.com/video/{bvid}",
                            media_urls=[cover] if cover else [],
                            timestamp=datetime.fromtimestamp(pub_time) if pub_time else datetime.now(),
                            score=float(v.get("play", 0))
                        )
                        events.append(event)
                else:
                    print(f"Bilibili API Warning: {data.get('message')}")
        except Exception as e:
            print(f"Bilibili Source fetch error: {e}")

        return events

if __name__ == "__main__":
    b = BilibiliAISource(keyword="AI 教程")
    res = b.fetch(5)
    for r in res:
         print(r.title, r.url)
