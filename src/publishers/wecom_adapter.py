import os
import json
import subprocess
from typing import List

class WeComPublisher:
    """
    Adapter to push content orchestrator results directly to Enterprise WeChat (WeCom).
    Relies on the global Node.js CLI tool `wecom-cli`.
    """
    def __init__(self):
        # Allow override or fallback from .env
        from dotenv import load_dotenv
        load_dotenv("/Users/lillianliao/notion_rag/.env")
        
        # UserID to send to. Default to Lilian's ID if omitted, or we could fetch from env.
        # Assuming the target is "lillianliao" or similar, we'll try to get it from ENV or just use a placeholder
        self.target_user = os.environ.get("WECOM_TARGET_USER", "lillianliao")
        
    def _check_cli(self):
        try:
            subprocess.run(["wecom-cli", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def push_draft(self, title: str, content_md: str, poster_path: str = None):
        if not self._check_cli():
            print("⚠️ 未找到 wecom-cli，请执行: npm install -g @wecom/cli 并 wecom-cli init 配置。跳过 WeCom 投递。")
            return False
            
        print(f"📨 [Publisher: WeCom] 正在下发企微终端通报: {title[:15]}...")
        
        # 组装纯文本消息 (由于 WeCom 支持 markdown 和 text，我们这里发 text 或 markdown 均可)
        # wecom-cli send_message 支持 msgtype: "markdown"
        md_text = f"🎨 **{title}**\n\n{content_md[:2000]}"
        
        payload = {
            "chat_type": 1,
            "chatid": self.target_user,
            "msgtype": "markdown",
            "markdown": {
                "content": md_text
            }
        }
        
        cmd = ["wecom-cli", "msg", "send_message", json.dumps(payload, ensure_ascii=False)]
        try:
            # Wecom CLI requires strict string execution or array execution
            subprocess.run(cmd, check=True, text=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ [WeCom 草稿] 推送失败，返回: {e.stderr}")
            return False

    def push_summary(self, matched_articles: List[dict]):
        return True # Not strictly necessary for summary now
