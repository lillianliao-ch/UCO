from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import subprocess
import time
import yaml

from core.cdp_session_cloner import clone_session
from core.playwright_engine import PlaywrightInterceptEngine

app = FastAPI(title="Media Query Console API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
                updated = True
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
                break
                
        if updated:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            return {"status": "success", "message": f"Updated pipeline {req.id} to {req.active}"}
        return {"status": "error", "message": "Pipeline not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
