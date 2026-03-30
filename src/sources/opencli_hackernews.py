import subprocess
import json
import hashlib
from typing import List
from src.core.schemas import RawContentEvent
from src.sources.base_source import BaseSourceAdapter

class OpenCLIHackerNewsSource(BaseSourceAdapter):
    """
    A concrete implementation utilizing the OpenCLI Browser Bridge / Public API wrapper 
    to robustly fetch HackerNews datasets without the need to manage Node dependencies directly.
    """
    
    def fetch(self, limit: int = 3) -> List[RawContentEvent]:
        print(f"🌍 [Source: HackerNews] 唤醒 OpenCLI 无痕检索池，过滤出前 {limit} 篇涉猎 AI 的硬核情报...")
        # Fetch a deeper buffer (e.g. 30) to guarantee we find enough AI articles
        cmd = ["npx", "--yes", "@jackwener/opencli", "hackernews", "top", "--limit", "30", "-f", "json"]
        
        try:
            # We enforce shell isolation by spinning up a separate child process for the Node CLI
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            items = json.loads(result.stdout)
            
            # Simple heuristic AI filter before sending to Qwen
            ai_keys = ['AI', 'LLM', 'GPT', 'OPENAI', 'CLAUDE', 'MODEL', 'AGENT', 'GPU', 'NVIDIA']
            valid_items = [it for it in items if any(k in it.get("title", "").upper() for k in ai_keys)]
            
            # Fallback if no AI news are strictly trending right now
            if not valid_items:
                valid_items = items
                
            events = []
            for item in valid_items[:limit]:
                # Generate unique ID based on URL to prevent ingestion duplication
                stable_id = hashlib.md5(item.get("url", "").encode('utf-8')).hexdigest()[:12]
                
                events.append(RawContentEvent(
                    id=stable_id,
                    source_channel="opencli_hackernews",
                    title=item.get("title", "No Title"),
                    content=item.get("title", ""), # HackerNews only provides titles
                    url=item.get("url", ""),
                    score=float(item.get("score", 0))
                ))
                
            print(f"✅ [Source: HackerNews] 安全返回 {len(events)} 枚标准化 JSON 数据体包。")
            return events
            
        except subprocess.CalledProcessError as e:
            print(f"❌ [Source: HackerNews] CLI 子进程返回错误: {e.stderr}")
            return []
        except json.JSONDecodeError:
            print(f"❌ [Source: HackerNews] CLI 返回格式已损坏，触发熔断防护。")
            return []
