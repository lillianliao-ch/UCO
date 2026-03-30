import os
import json
import urllib.request
from typing import List

try:
    import requests
except ImportError:
    pass

class TelegramPublisher:
    """
    Adapter to push content orchestrator results directly to the user's Telegram.
    Expects TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to be in the environment schema.
    """
    def __init__(self):
        # Fallback to local .env if global is not sourced properly by cron
        from dotenv import load_dotenv
        load_dotenv("/Users/lillianliao/notion_rag/.env")
        
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        
    def _can_push(self):
        return bool(self.bot_token and self.chat_id)

    def push_raw_intelligence(self, hn_pool: List, rss_pool: List):
        if not self._can_push():
            return False
            
        print("📨 [Publisher: Telegram] 正在投递【全域情报晨报】大盘信息...")
        total = len(hn_pool) + len(rss_pool)
        if total == 0:
            return True
            
        text = f"🌅 <b>早安！【万物编排器】发现 {total} 篇今日全域高价值线索</b>\\n"
        text += "<i>已去重历史发布池，即将进入 LLM 筛选生成流水线...</i>\\n\\n"
        
        if hn_pool:
            text += "🔥 <b>[HackerNews 极客情报]</b>\\n"
            for e in hn_pool[:15]:
                text += f"▪ {e.title}\\n"
            text += "\\n"
            
        if rss_pool:
            text += "📡 <b>[RSS 商业观察]</b>\\n"
            for e in rss_pool[:15]:
                text += f"▪ {e.title}\\n"

        if total > 30:
            text += "\\n<i>(由于篇幅限制，仅展示前 30 条)</i>"
            
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps({"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"}).encode('utf-8')
        try:
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req)
            return True
        except Exception as e:
            print(f"❌ [Telegram 原始信报] 投递失败: {e}")
            return False

    def push_draft(self, title: str, content_md: str, poster_path: str):
        if not self._can_push():
            return False
            
        print(f"📨 [Publisher: Telegram] 正在投递文章: {title[:15]}...")
        
        try:
            # Step 1: Send Photo with title as caption
            caption = f"🎨 <b>【草稿审核区】</b>\\n<b>{title}</b>\\n\\n<i>配图海报如上，请检阅主体文字：</i>"
            url_photo = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
            
            with open(poster_path, 'rb') as photo_file:
                # Use requests for multipart/form-data
                resp = requests.post(
                    url_photo,
                    data={"chat_id": self.chat_id, "caption": caption, "parse_mode": "HTML"},
                    files={"photo": photo_file}
                )
                
            # Step 2: Send the Long Markdown Draft using reliable sendMessage
            url_msg = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            # Escape HTML characters for Telegram if we are sending Markdown? No, wait, if we send text, we can just not use parsing mode or use Markdown.
            # Let's send the raw markdown without parsing mode so telegram doesn't complain about unclosed tags.
            payload_msg = json.dumps({"chat_id": self.chat_id, "text": content_md[:4000]}).encode('utf-8')
            req = urllib.request.Request(url_msg, data=payload_msg, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req)
            return True
            
        except ImportError:
            # Fallback to text only if pip install requests is missing
            print("⚠️ 未安装 requests 库，自动降级为全白文本纯享投递...")
            url_msg = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            fallback_text = f"🖼️ [配图请看本地]\\n\\n" + content_md[:4000]
            payload_msg = json.dumps({"chat_id": self.chat_id, "text": fallback_text}).encode('utf-8')
            req = urllib.request.Request(url_msg, data=payload_msg, headers={'Content-Type': 'application/json'})
            try:
                urllib.request.urlopen(req)
                return True
            except:
                return False
        except Exception as e:
            print(f"❌ [Telegram 草稿] 图文连携失败: {e}")
            return False

    def push_summary(self, matched_articles: List[dict]):
        if not self._can_push():
            return False
        print("📨 [Publisher: Telegram] 发送总结汇总信标...")
        text = "🤖 <b>万物编排器 (Universal Orchestrator)</b> 落网完结汇总\\n\\n"
        for i, art in enumerate(matched_articles, 1):
            text += f"📌 <b>{art['title']}</b>\\n"
        text += "\\n🔗 <i>以上高优作品已分发至小红书阵地，并安全转存为微信草稿！</i>"
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps({"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"}).encode('utf-8')
        try:
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req)
            return True
        except:
            return False
