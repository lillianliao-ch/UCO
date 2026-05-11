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
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processed_events (
                    hash_id TEXT PRIMARY KEY,
                    title TEXT,
                    source TEXT,
                    timestamp TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS pipeline_run_history (
                    run_id TEXT PRIMARY KEY,
                    pipeline_id TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    duration_seconds REAL,
                    items_scraped INTEGER DEFAULT 0,
                    items_passed_llm INTEGER DEFAULT 0,
                    items_selected INTEGER DEFAULT 0,
                    drafts_generated INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'RUNNING',
                    error_message TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS run_source_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    source_name TEXT,
                    items_fetched INTEGER DEFAULT 0,
                    items_selected INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'SUCCESS',
                    error_message TEXT,
                    created_at TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS run_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    pipeline_id TEXT,
                    title TEXT,
                    markdown_body TEXT,
                    event_url TEXT,
                    channel_status_json TEXT,
                    selection_reason TEXT,
                    starred INTEGER DEFAULT 0,
                    archived INTEGER DEFAULT 0,
                    created_at TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS content_drafts (
                    draft_id TEXT PRIMARY KEY,
                    pipeline_id TEXT,
                    hash_id TEXT,
                    event_hash TEXT,
                    title TEXT,
                    markdown_body TEXT,
                    status TEXT DEFAULT 'PENDING',
                    poster_path_xhs TEXT,
                    poster_path_wx TEXT,
                    video_path TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            self._ensure_columns(conn, "pipeline_run_history", {
                "duration_seconds": "REAL",
                "items_passed_llm": "INTEGER DEFAULT 0",
                "items_selected": "INTEGER DEFAULT 0",
                "error_message": "TEXT",
            })
            self._ensure_columns(conn, "run_source_metrics", {
                "error_message": "TEXT",
                "error_msg": "TEXT",
            })
            self._ensure_columns(conn, "run_artifacts", {
                "selection_reason": "TEXT",
                "starred": "INTEGER DEFAULT 0",
                "archived": "INTEGER DEFAULT 0",
            })
            self._ensure_columns(conn, "content_drafts", {
                "hash_id": "TEXT",
                "event_hash": "TEXT",
                "poster_path_xhs": "TEXT",
                "poster_path_wx": "TEXT",
                "video_path": "TEXT",
                "updated_at": "TEXT",
            })

    def _ensure_columns(self, conn, table_name: str, columns: dict[str, str]):
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})")}
        for name, definition in columns.items():
            if name not in existing:
                try:
                    conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {name} {definition}")
                except sqlite3.OperationalError as exc:
                    if "duplicate column name" not in str(exc).lower():
                        raise

    def _get_hash(self, event):
        # URLs are the most stable identifiers across Hackernews and RSS plugins
        return hashlib.md5(event.url.encode('utf-8')).hexdigest()

    def is_processed(self, event, channel=None) -> bool:
        """Evaluate if the article has been rendered and posted successfully in the past."""
        hash_id = self._get_hash(event)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM processed_events WHERE hash_id=?", (hash_id,))
            if cursor.fetchone() is not None:
                return True
            cursor = conn.execute(
                "SELECT 1 FROM content_drafts WHERE event_hash=? OR hash_id=?",
                (hash_id, hash_id),
            )
            return cursor.fetchone() is not None

    def mark_success(self, event, channel=None):
        """Permanent flush to DB ensuring future runs will ignore this content."""
        hash_id = self._get_hash(event)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR IGNORE INTO processed_events (hash_id, title, source, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (hash_id, event.title, self._event_source(event), datetime.now().isoformat()))

    def create_pipeline_run(self, run_id: str, pipeline_id: str):
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO pipeline_run_history
                    (run_id, pipeline_id, start_time, status)
                VALUES (?, ?, ?, 'RUNNING')
            ''', (run_id, pipeline_id, now))

    def update_pipeline_run(
        self,
        run_id: str,
        items_scraped: int = 0,
        items_selected: int = 0,
        drafts_generated: int = 0,
        status: str = "SUCCESS",
        error_message: str | None = None,
    ):
        end_time = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            start_row = conn.execute(
                "SELECT start_time FROM pipeline_run_history WHERE run_id=?",
                (run_id,),
            ).fetchone()
            duration = None
            if start_row and start_row[0]:
                try:
                    start_time = datetime.fromisoformat(start_row[0])
                    duration = (datetime.fromisoformat(end_time) - start_time).total_seconds()
                except ValueError:
                    duration = None
            conn.execute('''
                UPDATE pipeline_run_history
                SET end_time=?, duration_seconds=?, items_scraped=?,
                    items_passed_llm=?, items_selected=?, drafts_generated=?,
                    status=?, error_message=?
                WHERE run_id=?
            ''', (
                end_time,
                duration,
                items_scraped,
                items_selected,
                items_selected,
                drafts_generated,
                status,
                error_message,
                run_id,
            ))

    def save_draft(
        self,
        draft_id: str,
        pipeline_id: str,
        event,
        title: str,
        markdown_body: str,
        poster_path_xhs: str | None = None,
        poster_path_wx: str | None = None,
        video_path: str | None = None,
    ):
        now = datetime.now().isoformat()
        event_hash = self._get_hash(event)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO content_drafts
                    (draft_id, pipeline_id, hash_id, event_hash, title, markdown_body, status,
                     poster_path_xhs, poster_path_wx, video_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?)
            ''', (
                draft_id,
                pipeline_id,
                event_hash,
                event_hash,
                title,
                markdown_body,
                poster_path_xhs,
                poster_path_wx,
                video_path,
                now,
                now,
            ))
        self.mark_success(event)

    def save_run_artifact(
        self,
        artifact_id: str,
        run_id: str,
        pipeline_id: str,
        event_url: str,
        title: str,
        markdown_body: str,
        channel_status_json: str,
        selection_reason: str | None = None,
    ):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO run_artifacts
                    (artifact_id, run_id, pipeline_id, event_url, title, markdown_body,
                     channel_status_json, selection_reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                artifact_id,
                run_id,
                pipeline_id,
                event_url,
                title,
                markdown_body,
                channel_status_json,
                selection_reason,
                datetime.now().isoformat(),
            ))

    def log_source_metric(
        self,
        run_id: str,
        source_name: str,
        status: str,
        items_fetched: int = 0,
        items_selected: int = 0,
        error_msg: str | None = None,
    ):
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id, items_fetched, items_selected FROM run_source_metrics WHERE run_id=? AND source_name=?",
                (run_id, source_name),
            ).fetchone()
            if row:
                metric_id, old_fetched, old_selected = row
                conn.execute('''
                    UPDATE run_source_metrics
                    SET status=?, items_fetched=?, items_selected=?,
                        error_message=?, error_msg=?
                    WHERE id=?
                ''', (
                    status,
                    items_fetched or old_fetched,
                    items_selected or old_selected,
                    error_msg,
                    error_msg,
                    metric_id,
                ))
            else:
                conn.execute('''
                    INSERT INTO run_source_metrics
                        (run_id, source_name, status, items_fetched, items_selected,
                         error_message, error_msg, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    run_id,
                    source_name,
                    status,
                    items_fetched,
                    items_selected,
                    error_msg,
                    error_msg,
                    datetime.now().isoformat(),
                ))

    def _event_source(self, event) -> str:
        return (
            getattr(event, "source", None)
            or getattr(event, "source_channel", None)
            or getattr(event, "source_id", None)
            or "unknown"
        )
