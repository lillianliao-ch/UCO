import sqlite3
import hashlib
import os
from datetime import datetime

class EventStateManager:
    """
    SQLite-based Singleton Repository tracking previously published content.
    Prevents duplicate pipeline dispatches on back-to-back crontab fires.
    """
    def __init__(self, db_path="/Users/lillianliao/notion_rag/universal_content_orchestrator/data/events.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # 老库格式保留用于兼容读取
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processed_events (
                    hash_id TEXT PRIMARY KEY,
                    title TEXT,
                    source TEXT,
                    timestamp TEXT
                )
            ''')
            # 建立多端追踪明细新表 (联合主键)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS publish_log (
                    hash_id TEXT,
                    platform TEXT,
                    timestamp TEXT,
                    PRIMARY KEY (hash_id, platform)
                )
            ''')

    def _get_hash(self, event):
        # URLs are the most stable identifiers across Hackernews and RSS plugins
        return hashlib.md5(event.url.encode('utf-8')).hexdigest()

    def is_processed(self, event, platform: str) -> bool:
        """Evaluate if the article has been rendered and posted successfully to a SPECIFIC platform."""
        hash_id = self._get_hash(event)
        with sqlite3.connect(self.db_path) as conn:
            # 向后兼容：如果存在于历史表里，则默认全部分散端点已发出
            cursor = conn.execute("SELECT 1 FROM processed_events WHERE hash_id=?", (hash_id,))
            if cursor.fetchone() is not None:
                return True
                
            cursor = conn.execute("SELECT 1 FROM publish_log WHERE hash_id=? AND platform=?", (hash_id, platform))
            return cursor.fetchone() is not None

    def mark_success(self, event, platform: str):
        """Permanent flush to DB ensuring future runs will ignore this content FOR A SPECIFIC PLATFORM."""
        hash_id = self._get_hash(event)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO publish_log (hash_id, platform, timestamp)
                VALUES (?, ?, ?)
            ''', (hash_id, platform, datetime.now().isoformat()))
