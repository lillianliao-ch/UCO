"""
V2EX Source — UCO 标准数据源适配器

从 V2EX 中文技术社区获取热门帖子和节点内容，用于监控中文技术社区的讨论。

V2EX API 参考:
    - https://www.v2ex.com/p/7v9TEcI5
    - 最新消息: /api/topics/latest.json
    - 热门节点: /api/nodes/show.json?id=1

特性:
    - 获取最新帖子
    - 按节点获取帖子
    - 获取帖子详情和回复
    - 生成结构化的RawContentEvent
"""

import hashlib
import json
import urllib.request
from datetime import datetime
from typing import List, Optional
from src.core.schemas import RawContentEvent


class V2EXSource:
    """
    V2EX 数据源适配器

    支持两种模式:
    1. 最新帖子: 获取全站最新帖子
    2. 节点监控: 监控特定节点的帖子
    """

    # V2EX API 基础URL
    API_BASE = "https://www.v2ex.com/api"

    # 常用技术节点
    DEFAULT_NODES = [
        '1',      # 技术
        '4',      # Python
        '5',      # Java
        '6',      # Node.js
        '8',      # 分享创造
        '9',      # Apple
        '10',     # 工作
        '63',     # 程序员
        '678',    # 机器学习 (ML)
        '1135',   # OpenAI
        '90',     # 职场话题
    ]

    def __init__(self, node_ids: Optional[List[str]] = None):
        """
        初始化 V2EX 数据源

        Args:
            node_ids: 要监控的节点ID列表
                     例如: ['68']  # 人工智能节点
        """
        self.node_ids = node_ids or self.DEFAULT_NODES

    def fetch(self, limit: int = 10) -> List[RawContentEvent]:
        """
        获取V2EX帖子内容

        Args:
            limit: 每个来源返回的最大帖子数

        Returns:
            RawContentEvent列表
        """
        events = []

        # 从各节点获取帖子
        for node_id in self.node_ids:
            print(f"📖 [V2EX Source] 正在获取节点 {node_id} 的帖子...")
            node_events = self._fetch_from_node(node_id, limit)
            events.extend(node_events)

        print(f"✅ [V2EX Source] 共获取 {len(events)} 个帖子")
        return events

    def _fetch_from_node(self, node_id: str, limit: int) -> List[RawContentEvent]:
        """
        从指定节点获取帖子

        Args:
            node_id: 节点ID
            limit: 返回帖子数上限

        Returns:
            RawContentEvent列表
        """
        # 先获取节点信息
        node_info = self._get_node_info(node_id)
        node_name = node_info.get('title', f'Node-{node_id}') if node_info else f'Node-{node_id}'

        # 获取该节点的最新帖子
        url = f"{self.API_BASE}/topics/show.json?node_id={node_id}"
        try:
            posts = self._fetch_json(url)
            if not posts:
                return []

            events = []
            for post in posts[:limit]:
                # 提取帖子数据
                title = post.get('title', '')
                content = post.get('content', '')
                topic_id = post.get('id', '')
                url = f"https://www.v2ex.com/t/{topic_id}"
                author = post.get('member', {}).get('username', '')
                replies = post.get('replies', 0)
                created = post.get('created', 0)
                last_modified = post.get('last_modified', 0)

                # 格式化内容
                formatted_content = self._format_post(
                    title, content, author, replies, created, node_name
                )

                events.append(RawContentEvent(
                    id=f"v2ex_{node_id}_{topic_id}",
                    source_channel=f"v2ex_node_{node_id}",
                    title=title,
                    content=formatted_content,
                    url=url,
                    timestamp=datetime.fromtimestamp(created).isoformat() if created else datetime.now().isoformat(),
                    score=float(replies)
                ))

            return events

        except Exception as e:
            print(f"⚠️ [V2EX Source] 节点 {node_id} 获取失败: {e}")
            return []

    def _get_node_info(self, node_id: str) -> Optional[dict]:
        """
        获取节点信息

        Args:
            node_id: 节点ID

        Returns:
            节点信息字典
        """
        url = f"{self.API_BASE}/nodes/show.json?id={node_id}"
        return self._fetch_json(url)

    def _fetch_json(self, url: str) -> Optional[dict]:
        """
        通用的JSON获取方法

        Args:
            url: API URL

        Returns:
            解析后的JSON数据
        """
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
        })

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read().decode('utf-8')
                return json.loads(data)
        except urllib.error.HTTPError as e:
            print(f"⚠️ [V2EX Source] HTTP错误: {e.code}")
            return None
        except urllib.error.URLError as e:
            print(f"⚠️ [V2EX Source] URL错误: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            print(f"⚠️ [V2EX Source] JSON解析错误: {e}")
            return None
        except Exception as e:
            print(f"⚠️ [V2EX Source] 请求失败: {e}")
            return None

    def _format_post(
        self,
        title: str,
        content: str,
        author: str,
        replies: int,
        created: int,
        node_name: str
    ) -> str:
        """
        格式化帖子内容为Markdown

        Args:
            title: 帖子标题
            content: 帖子内容
            author: 作者
            replies: 回复数
            created: 创建时间戳
            node_name: 节点名称

        Returns:
            Markdown格式的内容
        """
        formatted = f"## {title}\n\n"
        formatted += f"👤 作者: @{author} | "
        formatted += f"💬 回复: {replies} | "
        formatted += f"📂 节点: {node_name} | "
        formatted += f"📅 {datetime.fromtimestamp(created).strftime('%Y-%m-%d %H:%M')}\n\n"

        # 清理HTML标签
        if content:
            # 简单的HTML标签清理
            import re
            content_clean = re.sub(r'<[^>]+>', '', content)
            content_clean = content_clean.strip()

            # 限制内容长度
            content_preview = content_clean[:800] + "..." if len(content_clean) > 800 else content_clean
            formatted += f"**内容**:\n\n{content_preview}\n"

        return formatted


# 使用示例
if __name__ == "__main__":
    # 示例1: 监控默认的技术节点
    source1 = V2EXSource()

    # 示例2: 监控特定节点
    source2 = V2EXSource(
        node_ids=['68', '63', '8']  # AI、程序员、分享创造
    )

    # 获取内容
    events = source1.fetch(limit=5)
    for event in events:
        print(f"Title: {event.title}")
        print(f"URL: {event.url}")
        print(f"Score: {event.score}")
        print(f"Content: {event.content[:200]}...")
        print("-" * 80)
