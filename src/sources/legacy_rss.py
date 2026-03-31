import feedparser
import hashlib
from typing import List, Dict
from src.core.schemas import RawContentEvent
from src.sources.base_source import BaseSourceAdapter

class LegacyRSSSource(BaseSourceAdapter):
    """
     Adapter porting the original ai_news_tracker RSS feed logic seamlessly 
    into the new Pydantic-based unified event bus without losing the rich history.
    """
    def __init__(self, rss_config_map: Dict[str, str]):
        self.rss_config_map = rss_config_map

    def fetch(self, limit: int = 5) -> List[RawContentEvent]:
        events = []
        for name, url in self.rss_config_map.items():
            print(f"📡 [Source: RSS] 正在接管历史 RSS 源并进行标准化封印: {name}")
            feed = feedparser.parse(url)
            for entry in feed.entries[:limit]:
                # Generate tracking ID
                stable_id = hashlib.md5(entry.link.encode('utf-8')).hexdigest()[:12]
                events.append(RawContentEvent(
                    id=stable_id,
                    source_channel=f"rss_{name.lower()}",
                    title=entry.title,
                    content=entry.get('summary', entry.title),
                    url=entry.link
                ))
        
        # Return all events collected from the configured sources, capped locally per source
        print(f"✅ [Source: RSS] 聚合完毕，输出 {len(events)} 篇综合资讯进入总线。")
        return events
