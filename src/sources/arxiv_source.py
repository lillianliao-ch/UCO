"""
ArXiv Monitor Source — UCO 标准数据源适配器

从 ArXiv API 拉取 cs.AI/cs.CL/cs.CV/cs.LG 最新论文。
采集到的数据同时：
  1. 作为 RawContentEvent 返回给 UCO 管线（用于 Telegram 推送）
  2. 通过 OPC Event Bus 广播 NEW_ARXIV_PAPER 事件（供猎头 App 的华人作者检测消费）
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict
from src.core.schemas import RawContentEvent

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

ARXIV_API = "http://export.arxiv.org/api/query"
CATEGORIES = ["cs.AI", "cs.CL", "cs.CV", "cs.LG"]

CHINESE_SURNAMES = {
    "wang", "li", "zhang", "liu", "chen", "yang", "huang", "zhao", "wu", "zhou",
    "xu", "sun", "ma", "zhu", "hu", "guo", "he", "lin", "luo", "gao",
    "zheng", "liang", "xie", "song", "tang", "han", "deng", "feng", "cao", "peng",
    "zeng", "xiao", "tian", "dong", "pan", "yuan", "cai", "jiang", "yu", "du",
    "ye", "cheng", "wei", "su", "lu", "ding", "ren", "shen", "yao", "zhong",
    "cui", "tan", "fan", "liao", "shi", "jin", "jia", "xia", "fu", "fang",
}


def is_likely_chinese(name: str) -> bool:
    parts = name.strip().lower().split()
    if not parts:
        return False
    return parts[0] in CHINESE_SURNAMES or parts[-1] in CHINESE_SURNAMES


def fetch_arxiv_papers(categories: List[str], days: int = 1, max_results: int = 200) -> List[Dict]:
    cat_query = "+OR+".join(f"cat:{c}" for c in categories)
    params = {
        "search_query": f"({cat_query})",
        "start": 0, "max_results": max_results,
        "sortBy": "submittedDate", "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            xml_data = resp.read()
    except Exception as e:
        print(f"⚠️ [ArXiv Source] API 请求失败: {e}")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_data)
    cutoff = datetime.now() - timedelta(days=days)
    papers = []

    for entry in root.findall("atom:entry", ns):
        published = entry.find("atom:published", ns)
        if published is None:
            continue
        pub_date = datetime.fromisoformat(published.text.replace("Z", "+00:00"))
        if pub_date.replace(tzinfo=None) < cutoff:
            continue
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        authors = [a.find("atom:name", ns).text.strip() for a in entry.findall("atom:author", ns)]
        arxiv_id = entry.find("atom:id", ns).text.split("/abs/")[-1]
        summary = entry.find("atom:summary", ns).text.strip()[:300]
        papers.append({
            "arxiv_id": arxiv_id, "title": title, "authors": authors,
            "first_author": authors[0] if authors else "",
            "published": pub_date.strftime("%Y-%m-%d"), "summary": summary,
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "is_chinese_first_author": is_likely_chinese(authors[0]) if authors else False,
        })
    return papers


class ArxivSource:
    """UCO 标准 Source 接口"""

    def fetch(self, limit: int = 15, days: int = 1, emit_events: bool = True) -> List[RawContentEvent]:
        print(f"🔍 [ArXiv Source] 拉取最近 {days} 天论文...")
        papers = fetch_arxiv_papers(CATEGORIES, days=days)
        print(f"   获取到 {len(papers)} 篇论文")

        # 广播到事件总线（华人一作的论文有猎头价值）
        if emit_events and papers:
            try:
                from opc_event_bus import EventBus
                bus = EventBus()
                chinese_papers = [p for p in papers if p.get("is_chinese_first_author")]
                for paper in chinese_papers:
                    bus.emit("NEW_ARXIV_CHINESE_AUTHOR", paper, source_system="uco_arxiv")
                if chinese_papers:
                    print(f"   📡 已向事件总线广播 {len(chinese_papers)} 条 NEW_ARXIV_CHINESE_AUTHOR 事件")
            except Exception as e:
                print(f"   ⚠️ 事件总线广播失败（不影响管线）: {e}")

        events = []
        for paper in papers[:limit]:
            authors_str = ", ".join(paper["authors"][:3])
            if len(paper["authors"]) > 3:
                authors_str += f" 等{len(paper['authors'])}人"
            chinese_tag = " 🇨🇳" if paper.get("is_chinese_first_author") else ""
            content = f"**{paper['title']}**{chinese_tag}\n\n"
            content += f"作者: {authors_str}\n"
            content += f"摘要: {paper['summary']}\n\n"
            content += f"🔗 {paper['url']}"

            events.append(RawContentEvent(
                id=f"arxiv_{paper['arxiv_id'].replace('.', '_')}",
                title=paper["title"][:80],
                content=content,
                url=paper["url"],
                source_channel="arxiv",
                timestamp=paper["published"],
            ))
        return events
