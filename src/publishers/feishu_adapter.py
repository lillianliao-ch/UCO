import os
import json
import urllib.request
from typing import List

class FeishuPublisher:
    """
    Adapter to push content orchestrator results directly to a Feishu Custom Bot Webhook.
    Expects FEISHU_WEBHOOK_URL to be in the environment schema.
    """
    def __init__(self):
        # Fallback to local .env
        from dotenv import load_dotenv
        load_dotenv("/Users/lillianliao/notion_rag/.env")
        
        self.webhook_url = os.environ.get("FEISHU_WEBHOOK_URL", "")
        
    def _can_push(self):
        return bool(self.webhook_url)

    def push_draft(self, title: str, content_md: str, poster_path: str = None):
        if not self._can_push():
            print("⚠️ 未配置 FEISHU_WEBHOOK_URL 环境变量，跳过飞书 Webhook 投递。")
            return False
            
        print(f"📨 [Publisher: Feishu] 飞书群组全景触达正在发射: {title[:15]}...")
        
        try:
            # Using Feishu's interactive post/card or simple POST
            # Feishu requires some structure for rich text, but text is simplest
            # For formatting, text type allows rudimentary formatting. Or we can use 'post' type.
            # Here we use 'post' for better formatting
            
            post_content = []
            for line in content_md.split("\n"):
                if line.strip():
                    post_content.append([{"tag": "text", "text": line.strip() + "\n"}])

            payload = {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": title,
                            "content": post_content
                        }
                    }
                }
            }
            
            req = urllib.request.Request(
                self.webhook_url, 
                data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), 
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req)
            return True
            
        except Exception as e:
            print(f"❌ [Feishu 草稿] 投递失败: {e}")
            return False

    def push_summary(self, matched_articles: List[dict]):
        return True
