from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from api_server import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "engine": "running"}

def test_session_status():
    response = client.get("/api/session/status")
    assert response.status_code == 200
    assert "status" in response.json()

def test_publish_content():
    response = client.post(
        "/api/publish",
        json={"content": "Hello World Automation", "platforms": ["xhs"]}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "queued"

# Cannot test /api/feed synchronously in isolation without Playwright timing out,
# but we can test if it responds cleanly or fails gracefully on unsupported platform
def test_feed_unsupported():
    response = client.get("/api/feed?target=unknown")
    assert response.status_code == 200
    assert response.json()["status"] == "error"

def test_feed_xhs_timeout():
    # If the file 'session_state.json' is present, playwright may launch and timeout 
    # if it's headless and cannot resolve the URL. Given this is a local fast test, 
    # we just ensure the endpoint doesn't crash 500.
    response = client.get("/api/feed?target=xhs")
    assert response.status_code == 200
    assert response.json()["status"] in ["success", "error"]
