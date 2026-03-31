import asyncio
import json
import os
from typing import List
from src.core.schemas import RawContentEvent
from src.sources.base_source import BaseSourceAdapter
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

class TrendRadarSource(BaseSourceAdapter):
    """
    Adapter connecting to TrendRadar's MCP (Model Context Protocol) core engine via stdio.
    Supports dynamic fallback when data is missing or the server fails.
    """
    def __init__(self):
        self.uv_path = os.path.expanduser("~/.local/bin/uv")
        self.project_dir = os.path.expanduser("~/notion_rag/.agent/skills/trendradar")
        
    async def _async_fetch(self, limit: int, platforms: List[str] = None) -> List[RawContentEvent]:
        events = []
        try:
            server_params = StdioServerParameters(
                command=self.uv_path,
                args=[
                    "--directory", self.project_dir,
                    "run", "python", "-m", "mcp_server.server"
                ]
            )
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    # Request the latest global news trends
                    arguments = {"limit": limit, "include_url": True}
                    if platforms:
                        arguments["platforms"] = platforms
                    response = await session.call_tool("get_latest_news", arguments=arguments)
                    
                    # Parse the initial JSON response
                    result = None
                    for content_obj in response.content:
                        result = json.loads(content_obj.text)
                        break
                        
                    if result and not result.get("success", False):
                        # Attempt to auto-crawl if the database hasn't been warmed up today snippet
                        print(f"⚠️ [Source: TrendRadar] 未检测到当天的离线热搜库 ({result.get('error', {}).get('message', '')})")
                        print("🤖 [Source: MCP] 正远程唤醒 TrendRadar 内核执行全网深度测绘 (trigger_crawl)... 请保持耐心，此过程极其硬核。")
                        await session.call_tool("trigger_crawl", arguments={})
                        
                        # Re-request the latest news after crawler is done
                        response = await session.call_tool("get_latest_news", arguments=arguments)
                        for content_obj in response.content:
                            result = json.loads(content_obj.text)
                            break
                            
                    if result and result.get("success", False):
                        items = result.get("data", {}).get("news", [])
                        print(f"✅ [Source: MCP/TrendRadar] 成功解构 {len(items)} 条高维度脉冲情报...")

                        for item in items[:limit]:
                            # Build the schema carefully using fallback defaults
                            item_id = str(item.get("id", item.get("index", item.get("title", "unknown"))))
                            platform = item.get("platform", "global_radar")
                            
                            events.append(RawContentEvent(
                                id=f"trend_{platform}_{item_id}",
                                source_channel="mcp_trendradar",
                                title=item.get("title", ""),
                                content=item.get("summary", item.get("title", "")),
                                url=item.get("url", "")
                            ))
                    else:
                        print("⚠️ [Source: TrendRadar] 深度测绘未能返回有效序列。回退至被动模式。")

        except Exception as e:
            print(f"⚠️ [Source: TrendRadar] ⚠️ MCP 协议连接中断或通信失败: {e}")
            
        return events

    def fetch(self, limit: int = 15, platforms: List[str] = None) -> List[RawContentEvent]:
        print(f"📡 [Target: TrendRadar] 唤醒原生 MCP (STDIO 协议) 与雷达神经网握手... 锁定平台: {platforms if platforms else '全球全时段'}")
        return asyncio.run(self._async_fetch(limit, platforms))
