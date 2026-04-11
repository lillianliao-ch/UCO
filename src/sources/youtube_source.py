"""
YouTube Source — UCO 标准数据源适配器

从 YouTube 提取视频字幕和元数据，用于监控AI/技术频道并自动生成内容摘要。

依赖:
    pip install yt-dlp

特性:
    - 提取视频元数据（标题、描述、时长、观看数等）
    - 提取字幕（支持多语言）
    - 支持按频道ID或关键词搜索
    - 生成结构化的RawContentEvent
"""

import hashlib
import json
import subprocess
from datetime import datetime
from typing import List, Optional, Dict
from src.core.schemas import RawContentEvent


class YouTubeSource:
    """
    YouTube 数据源适配器

    支持两种模式:
    1. 频道监控: 监控指定频道的最新视频
    2. 关键词搜索: 搜索特定关键词的视频
    """

    def __init__(self, channel_ids: Optional[List[str]] = None, search_queries: Optional[List[str]] = None):
        """
        初始化 YouTube 数据源

        Args:
            channel_ids: 要监控的YouTube频道ID列表
                         例如: ['UCBJycsmduvYEL83R_U4JriQ'] (MrBeast)
            search_queries: 搜索关键词列表
                           例如: ['LLM tutorial', 'AI agent']
        """
        self.channel_ids = channel_ids or []
        self.search_queries = search_queries or []

    def fetch(self, limit: int = 5) -> List[RawContentEvent]:
        """
        获取YouTube视频内容

        Args:
            limit: 每个来源返回的最大视频数

        Returns:
            RawContentEvent列表
        """
        events = []

        # 从频道获取视频
        for channel_id in self.channel_ids:
            print(f"📺 [YouTube Source] 正在获取频道 {channel_id} 的最新视频...")
            channel_events = self._fetch_from_channel(channel_id, limit)
            events.extend(channel_events)

        # 从搜索获取视频
        for query in self.search_queries:
            print(f"🔍 [YouTube Source] 正在搜索关键词: {query}")
            search_events = self._fetch_from_search(query, limit)
            events.extend(search_events)

        print(f"✅ [YouTube Source] 共获取 {len(events)} 个视频")
        return events

    def _fetch_from_channel(self, channel_id: str, limit: int) -> List[RawContentEvent]:
        """
        从指定频道获取最新视频

        Args:
            channel_id: YouTube频道ID
            limit: 返回视频数上限

        Returns:
            RawContentEvent列表
        """
        # 使用yt-dlp获取频道最新视频
        cmd = [
            'yt-dlp',
            '--flat-playlist',
            '--print', '%(id)s||%(title)s||%(description)s||%(duration)s||%(view_count)s||%(upload_date)s',
            f'--playlist-end', str(limit),
            f'https://www.youtube.com/channel/{channel_id}/videos'
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"⚠️ [YouTube Source] 频道 {channel_id} 获取失败: {result.stderr}")
                return []

            events = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('||')
                if len(parts) < 6:
                    continue

                video_id, title, description, duration, view_count, upload_date = parts

                # 提取字幕
                transcript = self._get_transcript(video_id)

                # 生成内容
                content = self._format_content(
                    title, description, transcript, duration, view_count, upload_date
                )

                events.append(RawContentEvent(
                    id=f"yt_{video_id}",
                    source_channel=f"youtube_channel_{channel_id}",
                    title=title,
                    content=content,
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    timestamp=datetime.now().isoformat(),
                    score=int(view_count) if view_count.isdigit() else None
                ))

            return events

        except subprocess.TimeoutExpired:
            print(f"⚠️ [YouTube Source] 频道 {channel_id} 请求超时")
            return []
        except Exception as e:
            print(f"⚠️ [YouTube Source] 频道 {channel_id} 发生错误: {e}")
            return []

    def _fetch_from_search(self, query: str, limit: int) -> List[RawContentEvent]:
        """
        从搜索结果获取视频

        Args:
            query: 搜索关键词
            limit: 返回视频数上限

        Returns:
            RawContentEvent列表
        """
        cmd = [
            'yt-dlp',
            '--flat-playlist',
            '--print', '%(id)s||%(title)s||%(description)s||%(duration)s||%(view_count)s||%(channel)s',
            f'--playlist-end', str(limit),
            f'ytsearch:{query}'
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"⚠️ [YouTube Source] 搜索 '{query}' 失败: {result.stderr}")
                return []

            events = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('||')
                if len(parts) < 6:
                    continue

                video_id, title, description, duration, view_count, channel = parts

                # 提取字幕
                transcript = self._get_transcript(video_id)

                # 生成内容
                content = self._format_content(
                    title, description, transcript, duration, view_count, channel
                )

                events.append(RawContentEvent(
                    id=f"yt_{video_id}",
                    source_channel=f"youtube_search_{hashlib.md5(query.encode()).hexdigest()[:8]}",
                    title=title,
                    content=content,
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    timestamp=datetime.now().isoformat(),
                    score=int(view_count) if view_count.isdigit() else None
                ))

            return events

        except subprocess.TimeoutExpired:
            print(f"⚠️ [YouTube Source] 搜索 '{query}' 请求超时")
            return []
        except Exception as e:
            print(f"⚠️ [YouTube Source] 搜索 '{query}' 发生错误: {e}")
            return []

    def _get_transcript(self, video_id: str) -> str:
        """
        获取视频字幕并解析实际文本内容
        
        Args:
            video_id: YouTube视频ID

        Returns:
            字幕文本
        """
        import tempfile
        import os
        import platform

        # Determine temp directory properly
        temp_dir = tempfile.gettempdir()
        
        cmd = [
            'yt-dlp',
            '--write-subs',
            '--write-auto-subs',
            '--sub-lang', 'en,zh',  # 优先英文，其次中文
            '--skip-download',
            '--sub-format', 'json3',
            '--output', os.path.join(temp_dir, f'{video_id}.%(ext)s'),
            f'https://www.youtube.com/watch?v={video_id}'
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Find the generated JSON3 subtitle file
            sub_file_path = None
            for ext in ['.en.json3', '.zh.json3', '.en-US.json3', '.en-GB.json3']:
                candidate = os.path.join(temp_dir, f'{video_id}{ext}')
                if os.path.exists(candidate):
                    sub_file_path = candidate
                    break

            if not sub_file_path:
                return "未找到可用字幕"

            # Parse JSON3 structure to extract raw text
            with open(sub_file_path, 'r', encoding='utf-8') as f:
                sub_data = json.load(f)
                
            text_lines = []
            if 'events' in sub_data:
                for ev in sub_data['events']:
                    if 'segs' in ev:
                        line = "".join([seg.get('utf8', '') for seg in ev['segs']])
                        if line.strip() and line.strip() != '\n':
                            text_lines.append(line.strip())

            # Cleanup temp file
            try:
                os.remove(sub_file_path)
            except Exception:
                pass

            full_text = " ".join(text_lines)
            return full_text

        except subprocess.TimeoutExpired:
            print(f"⚠️ [YouTube Source] 字幕提取超时 (video_id: {video_id})")
            return "字幕提取超时"
        except Exception as e:
            print(f"⚠️ [YouTube Source] 字幕提取失败: {e}")
            return ""

    def _format_content(
        self,
        title: str,
        description: str,
        transcript: str,
        duration: str,
        view_count: str,
        extra: str
    ) -> str:
        """
        格式化视频内容为Markdown

        Args:
            title: 视频标题
            description: 视频描述
            transcript: 字幕文本
            duration: 视频时长（秒）
            view_count: 观看数
            extra: 额外信息（上传日期或频道名）

        Returns:
            Markdown格式的内容
        """
        content = f"## {title}\n\n"

        # 时长转换
        if duration.isdigit():
            minutes = int(duration) // 60
            seconds = int(duration) % 60
            content += f"⏱️ 时长: {minutes}:{seconds:02d} | "
        else:
            content += f"⏱️ 时长: {duration} | "

        # 观看数
        if view_count.isdigit():
            content += f"👁️ 观看: {int(view_count):,} | "
        content += f"📅 {extra}\n\n"

        # 描述
        if description:
            content += f"**视频描述**:\n{description[:500]}...\n\n"

        # 字幕
        if transcript:
            content += f"**字幕摘要**:\n{transcript[:500]}...\n"

        return content


# 使用示例
if __name__ == "__main__":
    # 示例1: 监控AI技术频道
    source1 = YouTubeSource(
        channel_ids=[
            'UCBJycsmduvYEL83R_U4JriQ',  # MrBeast (示例)
            # 添加更多AI/技术频道ID
        ]
    )

    # 示例2: 搜索AI相关内容
    source2 = YouTubeSource(
        search_queries=[
            'LLM tutorial',
            'AI agent development',
            'machine learning'
        ]
    )

    # 获取内容
    events = source1.fetch(limit=3)
    for event in events:
        print(f"Title: {event.title}")
        print(f"URL: {event.url}")
        print(f"Content: {event.content[:200]}...")
        print("-" * 80)
