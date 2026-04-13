"""
GitHub Trending Source — UCO 标准数据源适配器

从 GitHub Trending 页面抓取 AI/LLM 相关热门项目。
采集到的数据同时：
  1. 作为 RawContentEvent 返回给 UCO 管线（用于内容生成/Telegram 推送）
  2. 通过 OPC Event Bus 广播 NEW_AI_TRENDING_REPO 事件（供猎头等业务 App 消费）
"""

import re
import urllib.request
from datetime import datetime
from typing import List, Dict
from src.core.schemas import RawContentEvent

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

AI_KEYWORDS = {
    "llm", "gpt", "transformer", "diffusion", "langchain", "llamaindex",
    "rag", "agent", "chatbot", "copilot", "deep-learning", "machine-learning",
    "neural", "bert", "llama", "mistral", "qwen", "openai", "huggingface",
    "pytorch", "tensorflow", "mlops", "fine-tuning", "lora", "embedding",
    "vector", "multimodal", "vision", "nlp", "reinforcement-learning",
    "vllm", "ollama", "crewai", "autogen", "ai", "generative", "moe",
    "inference", "quantization",
}


def fetch_github_trending(since: str = "daily") -> List[Dict]:
    url = f"https://github.com/trending?since={since}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8")
    except Exception as e:
        print(f"⚠️ [GitHub Trending Source] 请求失败: {e}")
        return []
    return parse_trending_html(html)


def parse_trending_html(html: str) -> List[Dict]:
    repos = []
    articles = re.findall(r'<article class="Box-row">(.*?)</article>', html, re.DOTALL)
    for article in articles:
        repo_match = re.search(r'<h[12][^>]*>\s*<a[^>]*href="/([^"]+)"', article)
        if not repo_match:
            continue
        full_name = repo_match.group(1).strip().strip("/")
        if "/" not in full_name or full_name.startswith("login"):
            continue
        desc_match = re.search(r'<p class="[^"]*col-9[^"]*">(.*?)</p>', article, re.DOTALL)
        description = re.sub(r'<[^>]+>', '', desc_match.group(1).strip()) if desc_match else ""
        lang_match = re.search(r'itemprop="programmingLanguage"[^>]*>([^<]+)', article)
        language = lang_match.group(1).strip() if lang_match else ""
        stars_match = re.search(r'href="/[^"]*stargazers"[^>]*>\s*([\d,]+)', article)
        stars = int(stars_match.group(1).replace(",", "")) if stars_match else 0
        today_match = re.search(r'([\d,]+)\s*stars?\s*today', article)
        if not today_match:
            today_match = re.search(r'([\d,]+)\s*stars?\s*this\s*week', article)
        today_stars = int(today_match.group(1).replace(",", "")) if today_match else 0
        built_by = re.findall(r'alt="@([^"]+)"', article)
        repos.append({
            "full_name": full_name, "description": description,
            "language": language, "stars": stars, "today_stars": today_stars,
            "contributors": built_by[:5], "url": f"https://github.com/{full_name}",
        })
    return repos


def is_ai_related(repo: Dict) -> bool:
    text = f"{repo['full_name']} {repo['description']}".lower()
    return any(kw in text for kw in AI_KEYWORDS)


class GitHubTrendingSource:
    """UCO 标准 Source 接口"""

    def fetch(self, limit: int = 15, since: str = "daily", emit_events: bool = True, min_stars: int = 100) -> List[RawContentEvent]:
        print(f"🔍 [GitHub Trending Source] 抓取 {since} trending...")
        repos = fetch_github_trending(since=since)
        ai_repos = [r for r in repos if is_ai_related(r)]
        # Hard filter: reject repos below minimum star threshold
        quality_repos = [r for r in ai_repos if r["stars"] >= min_stars]
        rejected = len(ai_repos) - len(quality_repos)
        print(f"   获取 {len(repos)} 个项目，AI 相关 {len(ai_repos)} 个，star≥{min_stars} 质控后 {len(quality_repos)} 个（淘汰 {rejected} 个低星项目）")

        # 广播到事件总线
        if emit_events and ai_repos:
            try:
                from opc_event_bus import EventBus
                bus = EventBus()
                for repo in ai_repos:
                    bus.emit("NEW_AI_TRENDING_REPO", repo, source_system="uco_github_trending")
                print(f"   📡 已向事件总线广播 {len(ai_repos)} 条 NEW_AI_TRENDING_REPO 事件")
            except Exception as e:
                print(f"   ⚠️ 事件总线广播失败（不影响管线）: {e}")

        events = []
        for repo in quality_repos[:limit]:
            contributors_str = ", ".join(repo["contributors"][:3])
            content = f"**{repo['full_name']}** ⭐ {repo['stars']:,} (+{repo['today_stars']} today)\n\n"
            content += f"{repo['description']}\n\n"
            content += f"语言: {repo['language']} | 贡献者: {contributors_str}\n"
            content += f"🔗 {repo['url']}"

            events.append(RawContentEvent(
                id=f"gh_{repo['full_name'].replace('/', '_')}_{datetime.now().strftime('%Y%m%d')}",
                title=f"{repo['full_name']} — {repo['description'][:60]}",
                content=content,
                url=repo["url"],
                source_channel="github_trending",
                timestamp=datetime.now().isoformat(),
            ))
        return events
