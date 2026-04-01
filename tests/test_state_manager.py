import os
import sqlite3
import pytest
from datetime import datetime
from src.core.state_manager import EventStateManager
from src.core.schemas import RawContentEvent

@pytest.fixture
def test_db_path(tmp_path):
    db_file = tmp_path / "test_events.db"
    yield str(db_file)
    if os.path.exists(db_file):
        os.remove(db_file)

@pytest.fixture
def state_manager(test_db_path):
    return EventStateManager(db_path=test_db_path)

@pytest.fixture
def mock_event():
    return RawContentEvent(
        id="test_123",
        title="Test News",
        content="Test content body",
        url="https://example.com/test-news",
        timestamp=datetime.now().isoformat(),
        source_id="test_source",
        source_channel="test_channel"
    )

def test_pipeline_run_history(state_manager):
    # Test creating and updating a pipeline run
    state_manager.create_pipeline_run("run_123", "pipeline_A")
    
    with sqlite3.connect(state_manager.db_path) as conn:
        cursor = conn.execute("SELECT status FROM pipeline_run_history WHERE run_id='run_123'")
        assert cursor.fetchone()[0] == 'RUNNING'
        
    state_manager.update_pipeline_run("run_123", 100, 50, 5, "SUCCESS")
    
    with sqlite3.connect(state_manager.db_path) as conn:
        cursor = conn.execute("SELECT items_scraped, drafts_generated, status FROM pipeline_run_history WHERE run_id='run_123'")
        row = cursor.fetchone()
        assert row[0] == 100
        assert row[1] == 5
        assert row[2] == "SUCCESS"

def test_save_draft_and_is_processed(state_manager, mock_event):
    # Initially not processed
    assert not state_manager.is_processed(mock_event, "xhs")
    
    # Save a draft
    state_manager.save_draft("draft_1", "pipeline_A", mock_event, "Draft Title", "Draft Body")
    
    # Once saved in draft, it MUST be marked as processed to prevent duplicate crawling tomorrow
    assert state_manager.is_processed(mock_event, "xhs")
    assert state_manager.is_processed(mock_event, "wechat")
    
    # Check draft DB
    with sqlite3.connect(state_manager.db_path) as conn:
        cursor = conn.execute("SELECT status, title FROM content_drafts WHERE draft_id='draft_1'")
        row = cursor.fetchone()
        assert row[0] == "PENDING"
        assert row[1] == "Draft Title"
