import sqlite3
import os
from typing import List
from src.core.schemas import RawContentEvent
from src.sources.base_source import BaseSourceAdapter

class DBTalentSource(BaseSourceAdapter):
    def fetch(self, limit=10) -> List[RawContentEvent]:
        db_path = "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db"
        if not os.path.exists(db_path):
            print(f"❌ 找不到猎头数据库: {db_path}")
            return []
            
        events = []
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # 专挑 AI 行业高管 (严格限制 S 和 A+ 级大牛)
            cursor.execute('''
                SELECT id, name, current_company, current_title, talent_tier, 
                       experience_years, raw_resume_text, linkedin_url
                FROM candidates
                WHERE raw_resume_text IS NOT NULL 
                  AND talent_tier IN ('S', 'A+')
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            for r in rows:
                c_id, name, comp, title, tier, exp, resume, link = r
                tier_str = tier if tier else "未定级"
                comp_str = comp if comp else "保密公司"
                title_str = title if title else "保密职位"
                
                content = f"姓名: {name}\n当前公司: {comp_str}\n当前职位: {title_str}\n人才层级: {tier_str}\n经验: {exp}年\n"
                if resume: content += f"\n履历与项目摘要:\n{resume[:800]}..."
                
                events.append(RawContentEvent(
                    id=f"talent_radar_{c_id}",
                    title=f"🚨 领军异动: {name} ({comp_str} | {title_str})",
                    url=link or "内部私有履历库 (未提供公开链接)",
                    content=content,
                    source_channel="Hunter DB"
                ))
            conn.close()
        except Exception as e:
            print(f"❌ [DBTalentSource] 数据库探针执行异常: {e}")
            
        return events
