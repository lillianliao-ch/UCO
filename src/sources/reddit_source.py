"""
Reddit Source — UCO 标准数据源适配器

从 Reddit 读取帖子和评论，用于监控技术社区的热门讨论。

依赖:
    pipx install rdt-cli

特性:
    - 无需登录即可读取
    - 支持按subreddit搜索
    - 支持按关键词搜索
    - 获取帖子全文和评论
    - 生成结构化的RawContentEvent
"""

import hashlib

import subprocess
import os

# 自动检测的rdt路径
RDT_PATH = "/Users/lillianliao/.local/bin/rdt"

from datetime import datetime
from typing import List, Optional
from src.core.schemas import RawContentEvent


class RedditSource:
    """
    Reddit 数据源适配器

    支持两种模式:
    1. Subreddit监控: 监控指定subreddit的热门帖子
    2. 关键词搜索: 搜索特定关键词的帖子
    """

    # AI/技术相关的热门subreddit
    DEFAULT_SUBREDDITS = [
        'MachineLearning',
        'programming',
        'Python',
        'learnprogramming',
        'compsci',
        'ArtificialIntelligence',
        'deeplearning',
        'LanguageTechnology',
        'datascience',
        'MLQuestions',
    ]

    def __init__(
        self,
        subreddits: Optional[List[str]] = None,
        search_queries: Optional[List[str]] = None
    ):
        """
        初始化 Reddit 数据源

        Args:
            subreddits: 要监控的subreddit列表
                        例如: ['MachineLearning', 'programming']
            search_queries: 搜索关键词列表
                           例如: ['LLM', 'fine-tuning', 'RAG']
        """
        self.subreddits = subreddits or self.DEFAULT_SUBREDDITS
        self.search_queries = search_queries or []

    def fetch(self, limit: int = 5) -> List[RawContentEvent]:
        """
        获取Reddit帖子内容

        Args:
            limit: 每个来源返回的最大帖子数

        Returns:
            RawContentEvent列表
        """
        events = []

        # 从subreddit获取帖子
        for subreddit in self.subreddits:
            print(f"📖 [Reddit Source] 正在获取 r/{subreddit} 的热门帖子...")
            subreddit_events = self._fetch_from_subreddit(subreddit, limit)
            events.extend(subreddit_events)

        # 从搜索获取帖子
        for query in self.search_queries:
            print(f"🔍 [Reddit Source] 正在搜索关键词: {query}")
            search_events = self._fetch_from_search(query, limit)
            events.extend(search_events)

        print(f"✅ [Reddit Source] 共获取 {len(events)} 个帖子")
        return events

    def _fetch_from_subreddit(self, subreddit: str, limit: int) -> List[RawContentEvent]:
        """
        从指定subreddit获取热门帖子

        Args:
            subreddit: subreddit名称
            limit: 返回帖子数上限

        Returns:
            RawContentEvent列表
        """
        # 使用rdt-cli获取热门帖子
        cmd = [
            RDT_PATH,
            'sub',
            subreddit,
            '--limit', str(limit),
            '--json'
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"⚠️ [Reddit Source] r/{subreddit} 获取失败: {result.stderr}")
                return []

            events = []
            # 解析JSON输出
            import json
            try:
                posts = json.loads(result.stdout)
            except json.JSONDecodeError:
                # 如果rdt输出不是JSON，尝试解析纯文本
                print(f"⚠️ [Reddit Source] r/{subreddit} JSON解析失败，尝试备用方案...")
                return self._parse_subreddit_text(result.stdout, subreddit)

            for post in posts:
                # 提取帖子数据
                title = post.get('title', '')
                content = post.get('selftext', '')
                url = post.get('url', '')
                author = post.get('author', '')
                score = post.get('score', 0)
                num_comments = post.get('num_comments', 0)
                created_utc = post.get('created_utc', 0)

                # 格式化内容
                formatted_content = self._format_post(
                    title, content, author, score, num_comments, created_utc
                )

                events.append(RawContentEvent(
                    id=f"rdt_{subreddit}_{hashlib.md5(url.encode()).hexdigest()[:12]}",
                    source_channel=f"reddit_r_{subreddit}",
                    title=title,
                    content=formatted_content,
                    url=url,
                    timestamp=datetime.fromtimestamp(created_utc).isoformat() if created_utc else datetime.now().isoformat(),
                    score=float(score)
                ))

            return events

        except subprocess.TimeoutExpired:
            print(f"⚠️ [Reddit Source] r/{subreddit} 请求超时")
            return []
        except FileNotFoundError:
            print(f"⚠️ [Reddit Source] rdt-cli 未安装，请运行: pipx install rdt-cli")
            return []
        except Exception as e:
            print(f"⚠️ [Reddit Source] r/{subreddit} 发生错误: {e}")
            return []

    def _fetch_from_search(self, query: str, limit: int) -> List[RawContentEvent]:
        """
        从搜索结果获取帖子

        Args:
            query: 搜索关键词
            limit: 返回帖子数上限

        Returns:
            RawContentEvent列表
        """
        cmd = [
            RDT_PATH,
            'search',
            query,
            '--limit', str(limit),
            '--json'
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"⚠️ [Reddit Source] 搜索 '{query}' 失败: {result.stderr}")
                return []

            events = []
            import json
            try:
                posts = json.loads(result.stdout)
            except json.JSONDecodeError:
                print(f"⚠️ [Reddit Source] 搜索 '{query}' JSON解析失败")
                return []

            for post in posts:
                title = post.get('title', '')
                content = post.get('selftext', '')
                url = post.get('url', '')
                subreddit = post.get('subreddit', '')
                author = post.get('author', '')
                score = post.get('score', 0)
                num_comments = post.get('num_comments', 0)

                formatted_content = self._format_post(
                    title, content, author, score, num_comments, subreddit
                )

                events.append(RawContentEvent(
                    id=f"rdt_search_{hashlib.md5(url.encode()).hexdigest()[:12]}",
                    source_channel=f"reddit_search_{hashlib.md5(query.encode()).hexdigest()[:8]}",
                    title=title,
                    content=formatted_content,
                    url=url,
                    timestamp=datetime.now().isoformat(),
                    score=float(score)
                ))

            return events

        except subprocess.TimeoutExpired:
            print(f"⚠️ [Reddit Source] 搜索 '{query}' 请求超时")
            return []
        except FileNotFoundError:
            print(f"⚠️ [Reddit Source] rdt-cli 未安装，请运行: pipx install rdt-cli")
            return []
        except Exception as e:
            print(f"⚠️ [Reddit Source] 搜索 '{query}' 发生错误: {e}")
            return []

    def _parse_subreddit_text(self, text: str, subreddit: str) -> List[RawContentEvent]:
        """
        解析纯文本格式的reddit输出（备用方案）

        Args:
            text: rdt-cli的纯文本输出
            subreddit: subreddit名称

        Returns:
            RawContentEvent列表
        """
        # 这是一个简化的解析器，实际使用时需要根据rdt-cli的输出格式调整
        events = []
        lines = text.split('\n')

        current_post = {}
        for line in lines:
            if line.startswith('Title:'):
                if current_post:
                    # 处理之前的帖子
                    events.append(self._create_event_from_dict(current_post, subreddit))
                current_post = {'title': line.split(':', 1)[1].strip()}
            elif line.startswith('URL:'):
                current_post['url'] = line.split(':', 1)[1].strip()
            elif line.startswith('Author:'):
                current_post['author'] = line.split(':', 1)[1].strip()
            # 可以添加更多字段解析...

        # 处理最后一个帖子
        if current_post:
            events.append(self._create_event_from_dict(current_post, subreddit))

        return events

    def _create_event_from_dict(self, post_dict: dict, subreddit: str) -> RawContentEvent:
        """从字典创建RawContentEvent"""
        return RawContentEvent(
            id=f"rdt_{subreddit}_{hashlib.md5(post_dict.get('url', '').encode()).hexdigest()[:12]}",
            source_channel=f"reddit_r_{subreddit}",
            title=post_dict.get('title', ''),
            content=post_dict.get('content', ''),
            url=post_dict.get('url', ''),
            timestamp=datetime.now().isoformat(),
            score=0.0
        )

    def _format_post(
        self,
        title: str,
        content: str,
        author: str,
        score: int,
        num_comments: int,
        extra: str
    ) -> str:
        """
        格式化帖子内容为Markdown

        Args:
            title: 帖子标题
            content: 帖子内容
            author: 作者
            score: 评分
            num_comments: 评论数
            extra: 额外信息（时间戳或subreddit）

        Returns:
            Markdown格式的内容
        """
        formatted = f"## {title}\n\n"
        formatted += f"👤 作者: {author} | "
        formatted += f"⭐ {score:,} points | "
        formatted += f"💬 {num_comments:,} comments | "
        formatted += f"📅 {extra}\n\n"

        if content:
            # 限制内容长度
            content_preview = content[:1000] + "..." if len(content) > 1000 else content
            formatted += f"**内容**:\n\n{content_preview}\n"

        return formatted


# 使用示例
if __name__ == "__main__":
    # 示例1: 监控默认的AI/技术subreddit
    source1 = RedditSource()

    # 示例2: 监控特定subreddit
    source2 = RedditSource(
        subreddits=['MachineLearning', 'programming']
    )

    # 示例3: 搜索特定关键词
    source3 = RedditSource(
        search_queries=['LLM', 'fine-tuning', 'RAG']
    )

    # 获取内容
    events = source1.fetch(limit=3)
    for event in events:
        print(f"Title: {event.title}")
        print(f"URL: {event.url}")
        print(f"Score: {event.score}")
        print(f"Content: {event.content[:200]}...")
        print("-" * 80)
