from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import sys
import subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import time
import yaml
import typing
from crontab import CronTab
import sqlite3
from core.cdp_session_cloner import clone_session
from core.playwright_engine import PlaywrightInterceptEngine
from core.state_manager import EventStateManager

app = FastAPI(title="Media Query Console API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "assets")
os.makedirs(assets_dir, exist_ok=True)
app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

videos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "videos")
os.makedirs(videos_dir, exist_ok=True)
app.mount("/videos", StaticFiles(directory=videos_dir), name="videos")

class CloneRequest(BaseModel):
    port: int = 9224

class PublishRequest(BaseModel):
    content: str
    platforms: list[str]

class ProbeRequest(BaseModel):
    target: str

@app.get("/api/health")
def health_check():
    return {"status": "ok", "engine": "running"}

@app.get("/api/sources")
def get_sources():
    # Return mock states + image paths
    # Front-end will call this to populate the Data Source Cards.
    pass

@app.get("/api/system/channels")
def get_system_channels():
    # Load authentic config
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "channels.yaml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return {"status": "success", "data": data}
    except Exception as e:
        print(f"Error reading YAML: {e}")
        return {"status": "error", "message": str(e)}

class ChannelToggleRequest(BaseModel):
    id: str
    active: bool
    type: str # 'inbound' or 'outbound'

@app.post("/api/system/channels")
def toggle_channel(req: ChannelToggleRequest):
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "channels.yaml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        target_list = data.get("inbound_sources", []) if req.type == "inbound" else data.get("outbound_publishers", [])
        
        updated = False
        for item in target_list:
            if item.get("id") == req.id:
                item["active"] = req.active
                updated = True
                break
                
        if updated:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            return {"status": "success", "message": f"Updated {req.id} to {req.active}"}
        return {"status": "error", "message": "Not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

class PromptUpdateRequest(BaseModel):
    content: str

@app.get("/api/system/prompts/{filename}")
def get_prompt(filename: str):
    prompt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "prompts", filename)
    if not os.path.exists(prompt_path):
        return {"status": "error", "message": "Prompt not found"}
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"status": "success", "content": content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/system/prompts/{filename}")
def update_prompt(filename: str, req: PromptUpdateRequest):
    prompt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "prompts", filename)
    try:
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"status": "success", "message": "Prompt successfully updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

class PipelineToggleRequest(BaseModel):
    id: str
    active: bool

class PipelineEditRequest(BaseModel):
    name: str
    description: str
    source_refs: list[str]
    prompt_template: str
    publisher_refs: list[str]
    active: bool
    schedule_time: typing.Optional[str] = ""

def sync_pipeline_cron(pipeline_id: str, active: bool, schedule_time: str):
    """Sync pipeline scheduling natively to OS crontab"""
    try:
        cron = CronTab(user=True)
        # Remove existing job for this pipeline based on exact comment tag
        cron.remove_all(comment=f"uco_{pipeline_id}")
        
        # Add new job if active and a valid HH:MM schedule is provided
        if active and schedule_time:
            parts = schedule_time.split(":")
            if len(parts) == 2:
                hh, mm = parts[0], parts[1]
                deploy_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "deploy_cron.sh")
                job = cron.new(command=f"/bin/bash {deploy_script} {pipeline_id}", comment=f"uco_{pipeline_id}")
                job.setall(mm, hh, '*', '*', '*')
        
        cron.write()
    except Exception as e:
        print(f"Failed to sync cron for {pipeline_id}: {e}")

@app.get("/api/system/pipelines")
def get_system_pipelines():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "pipelines.yaml")
    if not os.path.exists(config_path):
        return {"status": "error", "message": "pipelines.yaml not found"}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

class PipelineRunRequest(BaseModel):
    pipeline_id: str

@app.post("/api/system/pipelines/run")
def run_pipeline_manual(req: PipelineRunRequest):
    try:
        import subprocess
        log_path = "/tmp/pipeline_run.log"
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "deploy_cron.sh")
        # Run deploy_cron.sh <pipeline_id>
        subprocess.Popen(f"/bin/bash {script_path} {req.pipeline_id} > {log_path} 2>&1", shell=True)
        return {"status": "success", "message": f"已成功将运行指令注入调度核心。执行日志捕获于: {log_path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/system/pipelines/{pipeline_id}")
def update_full_pipeline(pipeline_id: str, req: PipelineEditRequest):
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "pipelines.yaml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        updated = False
        for p in data.get("pipelines", []):
            if p.get("id") == pipeline_id:
                p["name"] = req.name
                p["description"] = req.description
                p["source_refs"] = req.source_refs
                p["prompt_template"] = req.prompt_template
                p["publisher_refs"] = req.publisher_refs
                p["active"] = req.active
                p["schedule_time"] = req.schedule_time
                updated = True
                
                # Sync cron instantly
                sync_pipeline_cron(pipeline_id, req.active, req.schedule_time)
                break
                
        if updated:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            return {"status": "success", "message": f"Pipeline {pipeline_id} fully configured and saved."}
        return {"status": "error", "message": "Pipeline not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/system/pipelines")
def toggle_pipeline(req: PipelineToggleRequest):
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "pipelines.yaml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        updated = False
        for p in data.get("pipelines", []):
            if p.get("id") == req.id:
                p["active"] = req.active
                updated = True
                
                # Sync cron instantly with existing schedule
                sync_pipeline_cron(req.id, req.active, p.get("schedule_time", ""))
                break
                
        if updated:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            return {"status": "success", "message": f"Updated pipeline {req.id} to {req.active}"}
        return {"status": "error", "message": "Pipeline not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}



class DraftUpdateRequest(BaseModel):
    markdown_body: str
    title: str

@app.get("/api/history")
def get_pipeline_history():
    sm = EventStateManager()
    with sqlite3.connect(sm.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM pipeline_run_history ORDER BY start_time DESC LIMIT 100")
        rows = cursor.fetchall()
        history = [dict(row) for row in rows]
    return {"status": "success", "data": history}

@app.get("/api/history/{run_id}/metrics")
def get_pipeline_metrics(run_id: str):
    sm = EventStateManager()
    try:
        with sqlite3.connect(sm.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM run_source_metrics WHERE run_id = ? ORDER BY items_fetched DESC", (run_id,))
            rows = cursor.fetchall()
            metrics = [dict(row) for row in rows]
        return {"status": "success", "data": metrics}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/analytics/sources")
def get_source_roi_analytics():
    sm = EventStateManager()
    try:
        with sqlite3.connect(sm.db_path) as conn:
            conn.row_factory = sqlite3.Row
            # Aggregating source metrics across runs
            cursor = conn.execute('''
                SELECT 
                    source_name,
                    COUNT(DISTINCT run_id) as run_count,
                    SUM(items_fetched) as total_fetched,
                    SUM(items_selected) as total_selected,
                    SUM(CASE WHEN status='ERROR' THEN 1 ELSE 0 END) as error_count
                FROM run_source_metrics
                GROUP BY source_name
                ORDER BY total_selected DESC, total_fetched DESC
            ''')
            rows = cursor.fetchall()
            stats = []
            for r in rows:
                d = dict(r)
                hit_rate = (d["total_selected"] / d["total_fetched"] * 100) if d["total_fetched"] > 0 else 0
                d["hit_rate_pct"] = round(hit_rate, 2)
                stats.append(d)
        return {"status": "success", "data": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/history/{run_id}/artifacts")
def get_pipeline_artifacts(run_id: str):
    sm = EventStateManager()
    try:
        with sqlite3.connect(sm.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM run_artifacts WHERE run_id = ? ORDER BY created_at DESC", (run_id,))
            rows = cursor.fetchall()
            
            # Need to parse JSON for frontend
            artifacts = []
            for row in rows:
                d = dict(row)
                d["channel_status"] = json.loads(d["channel_status_json"]) if d.get("channel_status_json") else {}
                artifacts.append(d)
        return {"status": "success", "data": artifacts}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/drafts")
def get_all_drafts():
    sm = EventStateManager()
    with sqlite3.connect(sm.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM content_drafts WHERE status='PENDING' ORDER BY created_at DESC")
        rows = cursor.fetchall()
        drafts = [dict(row) for row in rows]
    return {"status": "success", "data": drafts}

@app.put("/api/drafts/{draft_id}")
def update_draft(draft_id: str, req: DraftUpdateRequest):
    sm = EventStateManager()
    with sqlite3.connect(sm.db_path) as conn:
        conn.execute("UPDATE content_drafts SET markdown_body=?, title=? WHERE draft_id=?", (req.markdown_body, req.title, draft_id))
    return {"status": "success", "message": "Draft updated"}

@app.post("/api/drafts/{draft_id}/publish")
def publish_draft(draft_id: str):
    sm = EventStateManager()
    with sqlite3.connect(sm.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM content_drafts WHERE draft_id=?", (draft_id,))
        draft = cursor.fetchone()
        
    if not draft:
        return {"status": "error", "message": "Draft not found"}
        
    d_dict = dict(draft)
    title, content = d_dict["title"], d_dict["markdown_body"]
    poster_xhs, poster_wx = d_dict.get("poster_path_xhs"), d_dict.get("poster_path_wx")
    pipeline_id = d_dict["pipeline_id"]
    
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "pipelines.yaml")
    publishers = []
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        for p in data.get("pipelines", []):
            if p["id"] == pipeline_id:
                publishers = p.get("publisher_refs", [])
                break
                
    successes, errors = [], []
    
    if "xiaohongshu" in publishers:
        from publishers.opencli_xhs_adapter import OpenCLIXiaohongshuPublisher
        try:
            video_path = d_dict.get("video_path")
            real_m = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "videos", video_path.replace("/videos/", "")) if video_path else None
            if not real_m:
                 real_m = os.path.join(assets_dir, poster_xhs.replace("/assets/", "")) if poster_xhs else None
                 
            is_ok = OpenCLIXiaohongshuPublisher().push(content, title, [real_m] if real_m else [])
            if is_ok:
                successes.append("xiaohongshu")
            else:
                errors.append("xhs: OpenCLI 跨边界执行返回 False (Cookie可能丢失或格式失败)")
        except Exception as e:
            errors.append(f"xhs: {e}")
            
    if "wechat" in publishers:
        from publishers.wechat_adapter import WeChatPublisher
        try:
            real_p = os.path.join(assets_dir, poster_wx.replace("/assets/", "")) if poster_wx else None
            is_ok = WeChatPublisher().push(title, content, real_p)
            if is_ok:
                successes.append("wechat")
            else:
                errors.append("wechat: 驱动执行返回 False")
        except Exception as e:
            errors.append(f"wechat: {e}")

    if not errors:
        with sqlite3.connect(sm.db_path) as conn:
            conn.execute("UPDATE content_drafts SET status='PUBLISHED' WHERE draft_id=?", (draft_id,))
        return {"status": "success", "message": f"Published to {','.join(successes)}"}
    else:
        return {"status": "error", "message": "; ".join(errors)}

@app.post("/api/drafts/{draft_id}/discard")
def discard_draft(draft_id: str):
    sm = EventStateManager()
    with sqlite3.connect(sm.db_path) as conn:
        conn.execute("UPDATE content_drafts SET status='DISCARDED' WHERE draft_id=?", (draft_id,))
    return {"status": "success", "message": "Draft discarded"}

@app.get("/api/news/trend")
def get_trend_news():
    """
    Architectural Entrypoint: Fetches the AI filtered macroscopic top trends 
    from the decoupled TrendRadar cluster and pipes them to the internal event bus.
    """
    from sources.trendradar_source import TrendRadarAdapter
    adapter = TrendRadarAdapter()
    events = adapter.fetch(limit=5)
    
    return {
        "status": "success",
        "message": f"Successfully pulled {len(events)} high-quality AI filtered items from TrendRadar",
        "data": [e.dict() for e in events]
    }

@app.post("/api/session/probe")
def session_probe(req: ProbeRequest):
    print(f"🕵️ [Probe Initiated] Target: {req.target}")
    state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "session_state.json")
    
    # Map target keys to physical URLs
    url_map = {
        "jike": "https://web.okjike.com/",
        "linkedin": "https://www.linkedin.com/feed/"
    }
    
    target_url = url_map.get(req.target, "https://example.com")
    
    # Screenshot path in the next.js public folder
    shot_filename = f"{req.target}.png"
    shot_path_abs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web_dashboard", "public", "shots", shot_filename)
    
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Inject HTTP cookie state if available
            if os.path.exists(state_file):
                context = browser.new_context(storage_state=state_file, viewport={"width": 1280, "height": 800})
            else:
                context = browser.new_context(viewport={"width": 1280, "height": 800})
                
            page = context.new_page()
            try:
                page.goto(target_url, timeout=15000)
                # Let react settle
                page.wait_for_timeout(3000)
            except Exception as nav_e:
                print(f"Warning on navigation: {nav_e}")
                
            page.screenshot(path=shot_path_abs)
            browser.close()
            
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        return {
            "status": "success", 
            "target": req.target, 
            "imageUrl": f"/shots/{shot_filename}?t={int(time.time())}", 
            "lastCheck": timestamp
        }
    except Exception as e:
        print(f"❌ Probe Failed: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/session/sync")
def sync_session(req: CloneRequest):
    # Direct port CDP clone
    success = clone_session(cdp_url=f"http://localhost:{req.port}", output_file="session_state.json")
    if success:
        return {"status": "success", "message": "Latest browser session mirrored to system storage!"}
    return {"status": "error", "message": "Failed to connect to browser CDP port."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
