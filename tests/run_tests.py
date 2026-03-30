from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from api_server import app

client = TestClient(app)

def run_tests():
    print("Running API E2E Verification...")
    
    res = client.get("/api/health")
    assert res.status_code == 200
    print("✅ Health check passed")
    
    res = client.get("/api/session/status")
    assert res.status_code == 200
    print("✅ Session status passed")
    
    res = client.post("/api/publish", json={"content": "test", "platforms": ["xhs"]})
    assert res.status_code == 200
    assert res.json()["status"] == "queued"
    print("✅ Publish queued passed")
    
    res = client.get("/api/feed?target=unknown")
    assert res.status_code == 200
    assert res.json()["status"] == "error"
    print("✅ Feed unsupported handler passed")
    
    print("All backend unit tests passed successfully 🚀")

if __name__ == "__main__":
    run_tests()
