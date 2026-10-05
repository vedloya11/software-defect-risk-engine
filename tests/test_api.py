import os
import sys
import io

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from api.main import app

def test_api():
    print("Testing FastAPI endpoints using TestClient with Lifespan...")
    with TestClient(app) as client:
        # 1. Health check
        res = client.get("/health")
        print("\n[GET /health Response]:", res.status_code, res.json())
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"
        
        # 2. Analyze code endpoint (JSON text)
        sample_code = """
import os
import requests

def transfer_funds(account_id, amount, is_authenticated):
    if not is_authenticated:
        return {"error": "unauthorized"}
    if amount <= 0:
        return {"error": "invalid amount"}
    return {"status": "success", "amount": amount}
"""
        payload = {
            "filename": "transfer_service.py",
            "source_code": sample_code
        }
        res_analyze = client.post("/api/v1/analyze", json=payload)
        print("\n[POST /api/v1/analyze (JSON) Response]:", res_analyze.status_code, res_analyze.json()["defect_risk"])
        assert res_analyze.status_code == 200
        assert res_analyze.json()["filename"] == "transfer_service.py"

        # 3. Analyze file upload endpoint (Valid .py file)
        file_bytes = io.BytesIO(sample_code.encode("utf-8"))
        files = {
            "file": ("payment_logic.py", file_bytes, "text/x-python")
        }
        res_file = client.post("/api/v1/analyze-file", files=files)
        print("\n[POST /api/v1/analyze-file (Valid .py) Response]:", res_file.status_code, res_file.json()["defect_risk"])
        assert res_file.status_code == 200
        assert res_file.json()["filename"] == "payment_logic.py"
        assert "risk_probability" in res_file.json()
        assert "most_suspicious_component" in res_file.json()

        # 4. Analyze file upload with INVALID file extension (e.g. .txt or .png)
        invalid_file = io.BytesIO(b"Hello world text")
        files_invalid = {
            "file": ("notes.txt", invalid_file, "text/plain")
        }
        res_invalid = client.post("/api/v1/analyze-file", files=files_invalid)
        print("\n[POST /api/v1/analyze-file (Invalid .txt Rejection)]: Status", res_invalid.status_code, res_invalid.json())
        assert res_invalid.status_code == 400

    print("\n[OK] All Phase 15 & Phase 16 endpoints verified successfully!")

if __name__ == "__main__":
    test_api()
