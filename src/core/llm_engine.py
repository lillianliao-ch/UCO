import os
import json
import urllib.request
from typing import List
from src.core.schemas import RawContentEvent

class QwenEngine:
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv("/Users/lillianliao/notion_rag/.env")
        self.api_key = os.environ.get("DASHSCOPE_API_KEY", "sk-4e2bb9108e1541f9b7dd88855922c7a3")

    def call_qwen(self, prompt: str) -> str:
        data = {
            "model": "qwen-plus",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4
        }
        req = urllib.request.Request(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            data=json.dumps(data).encode('utf-8'),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"❌ LLM API 故障: {e}")
            return ""

    def select_top_articles(self, events: List[RawContentEvent], limit: int, filter_template: str = "filter_priority.md") -> List[RawContentEvent]:
        """
        AI-driven heuristic filter. Prompts the LLM to select the most relevant events.
        """
        if len(events) <= limit: return events
        
        print(f"🧠 [Brain: Selector] 正在对 {len(events)} 篇底料执行深度 AI 排序 ({filter_template})，提取 Top {limit}...")
        
        # Build catalogue
        catalogue = ""
        for i, e in enumerate(events):
            catalogue += f"[{i}] {e.title}\\n"
            
        try:
            prompt_template_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "prompts", filter_template)
            with open(prompt_template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
            prompt = prompt_template.format(catalogue=catalogue, limit=limit)
        except Exception as e:
            print(f"⚠️ 无法读取外部 Prompt 文件，回退到系统默认模板: {e}")
            prompt = f"""你是一个顶级的AI科技新闻主编。
这是今天从各种渠道获取的新闻池：
{catalogue}

请根据以下【优先级】帮我挑选出最有价值的 {limit} 篇文章以供发布：
1）硬核模型、产品更新
2）大牛专家讲话和观点
3）vibe coding相关的开发技能
4）新的github工具
5）其他

【输出格式】
只输出逗号分隔的编号组合，绝对不要输出任何其他解释。例如: 0, 4, 7"""
        
        reply = self.call_qwen(prompt)
        
        # Parse logic
        selected_events = []
        try:
            indices = [int(x.strip()) for x in reply.replace('[', '').replace(']', '').split(',') if x.strip().isdigit()]
            for idx in indices[:limit]:
                if 0 <= idx < len(events):
                    selected_events.append(events[idx])
        except Exception as e:
            print("⚠️ 大模型编号解析失败，采用默认截流策略。")
        
        # Fallback if LLM failed to return enough
        if len(selected_events) < limit:
            for e in events:
                if e not in selected_events:
                    selected_events.append(e)
                if len(selected_events) == limit: break
                
        return selected_events

    def synthesize_single_article(self, event: RawContentEvent) -> str:
        # Legacy fallback method for backwards compatibility
        return self.synthesize_with_prompt(event, "xhs_style_a_lilian.md")

    def synthesize_with_prompt(self, event: RawContentEvent, prompt_file: str) -> str:
        print(f"🧠 [Brain: Writer] 正在为【{event.title[:15]}...】注入专属管线人设({prompt_file})...")
        import urllib.request
        import json
        import os
        from dotenv import load_dotenv
        
        load_dotenv("/Users/lillianliao/notion_rag/.env")
        api_key = os.environ.get("DASHSCOPE_API_KEY", "sk-4e2bb9108e1541f9b7dd88855922c7a3")
        
        try:
            prompt_template_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "prompts", prompt_file)
            with open(prompt_template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
                
            # Safely format strings if the template contains {title} etc (most custom prompts might just append it)
            if "{title}" in prompt_template:
                prompt = prompt_template.format(title=event.title, content=event.content, url=event.url)
            else:
                prompt = f"{prompt_template}\n\n=============================\n【待分析源素材】\n标题：{event.title}\n内容：{event.content}\n链接：{event.url}\n=============================\n\n请严格履行你的设定，进行深度提炼与多维外发格式重写："
        except Exception as e:
            print(f"⚠️ 无法读取外部 Prompt 文件 {prompt_file}，由于安全回退触发空处理: {e}")
            return f"【{event.title[:15]}】\n极客新情报送达。\n\n由于系统提示词模板丢失，生成终止。 ({event.url})"
            
        data = {
            "model": "qwen-plus",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4
        }
        req = urllib.request.Request(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            data=json.dumps(data).encode('utf-8'),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"❌ LLM API 故障: {e}")
            return f"【{event.title[:15]}】\n极客新情报送达。\n\n👉 解读:\n底层通信异常，请阅读原文。\n\n💡 启示:\n保持敏锐。 ({event.url})"
