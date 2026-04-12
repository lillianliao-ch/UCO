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
            # 建立管线全局执行历史表（监控漏斗）
            conn.execute('''
                CREATE TABLE IF NOT EXISTS pipeline_run_history (
                    run_id TEXT PRIMARY KEY,
                    pipeline_id TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    items_scraped INTEGER,
                    items_passed_llm INTEGER,
                    drafts_generated INTEGER,
                    status TEXT
                )
            ''')
            # 建立管线制品和各渠道状态明细表（提供完整可视性）
            conn.execute('''
                CREATE TABLE IF NOT EXISTS run_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    pipeline_id TEXT,
                    event_url TEXT,
                    title TEXT,
                    markdown_body TEXT,
                    channel_status_json TEXT,
                    created_at TEXT
                )
            ''')
            # 建立漏斗观测探针，追踪数据源的转化率与异常崩溃
            conn.execute('''
                CREATE TABLE IF NOT EXISTS run_source_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    source_name TEXT,
                    status TEXT,
                    items_fetched INTEGER DEFAULT 0,
                    items_selected INTEGER DEFAULT 0,
                    error_msg TEXT,
                    created_at TEXT
                )
            ''')
            # 建立人工审核草稿箱
            conn.execute('''
                CREATE TABLE IF NOT EXISTS content_drafts (
                    draft_id TEXT PRIMARY KEY,
                    pipeline_id TEXT,
                    hash_id TEXT,
                    title TEXT,
                    markdown_body TEXT,
                    status TEXT,
                    created_at TEXT,
                    poster_path_xhs TEXT,
                    poster_path_wx TEXT,
                    video_path TEXT
                )
            ''')
            # Backwards-compatible migration: add video_path if table already exists without it
            try:
                conn.execute('ALTER TABLE content_drafts ADD COLUMN video_path TEXT')
            except Exception:
                pass  # Column already exists

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
                
            # 2. 如果存在于草稿箱，无论是否发布，都视为已被系统收录，防止明天再次抓取浪费 LLM 资源
            cursor = conn.execute("SELECT 1 FROM content_drafts WHERE hash_id=?", (hash_id,))
            if cursor.fetchone() is not None:
                return True
                
            # 3. 检查单端点发布历史
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

    def create_pipeline_run(self, run_id: str, pipeline_id: str):
        """Log the start of a pipeline run to track funnel metrics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO pipeline_run_history (run_id, pipeline_id, start_time, status)
                VALUES (?, ?, ?, 'RUNNING')
            ''', (run_id, pipeline_id, datetime.now().isoformat()))

    def update_pipeline_run(self, run_id: str, items_scraped: int, items_passed_llm: int, drafts_generated: int, status: str):
        """Finalize funnel metrics when the pipeline finishes."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE pipeline_run_history
                SET end_time=?, items_scraped=?, items_passed_llm=?, drafts_generated=?, status=?
                WHERE run_id=?
            ''', (datetime.now().isoformat(), items_scraped, items_passed_llm, drafts_generated, status, run_id))

    def save_draft(self, draft_id: str, pipeline_id: str, event, title: str, markdown_body: str, poster_xhs: str = None, poster_wx: str = None, video_path: str = None):
        """Save intercepted content generated by LLM into isolated draft inbox."""
        hash_id = self._get_hash(event)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO content_drafts (draft_id, pipeline_id, hash_id, title, markdown_body, status, created_at, poster_path_xhs, poster_path_wx, video_path)
                VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?, ?, ?)
            ''', (draft_id, pipeline_id, hash_id, title, markdown_body, datetime.now().isoformat(), poster_xhs, poster_wx, video_path))

    def save_run_artifact(self, artifact_id: str, run_id: str, pipeline_id: str, event_url: str, title: str, markdown_body: str, channel_status_json: str):
        """Save final generated content and its delivery statuses to various channels during a specific run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO run_artifacts (artifact_id, run_id, pipeline_id, event_url, title, markdown_body, channel_status_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (artifact_id, run_id, pipeline_id, event_url, title, markdown_body, channel_status_json, datetime.now().isoformat()))

    def log_source_metric(self, run_id: str, source_name: str, status: str, items_fetched: int = 0, items_selected: int = 0, error_msg: str = None):
        """Monitor tracking metric for source ROI and silent failures."""
        # 允许后期 update items_selected，如果同一次 run 同一个 source 已有记录，则更新它
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, items_fetched, items_selected FROM run_source_metrics WHERE run_id=? AND source_name=?", (run_id, source_name))
            row = cursor.fetchone()
            if row:
                # Update existing (used during LLM filter pass)
                _id, old_fetched, old_selected = row
                new_fetched = old_fetched if items_fetched == 0 else items_fetched
                new_selected = old_selected if items_selected == 0 else items_selected
                conn.execute('''
                    UPDATE run_source_metrics 
                    SET status=?, items_fetched=?, items_selected=?, error_msg=? 
                    WHERE id=?
                ''', (status, new_fetched, new_selected, error_msg, _id))
            else:
                conn.execute('''
                    INSERT INTO run_source_metrics (run_id, source_name, status, items_fetched, items_selected, error_msg, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (run_id, source_name, status, items_fetched, items_selected, error_msg, datetime.now().isoformat()))

