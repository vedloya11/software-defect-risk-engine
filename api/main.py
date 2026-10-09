import os
import sys
import json
from typing import Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, File, UploadFile, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.code_analysis.metric_bridge import CodeDefectEngine
from src.database.db import get_db, init_db
from src.database.models import ScanRecord
from api.schemas import (
    CodeAnalysisRequest,
    DefectRiskResponse,
    HealthResponse,
    ScanHistoryResponse,
    ScanHistoryItem,
    DeleteHistoryResponse
)

# Maximum allowed upload size (5 MB)
MAX_FILE_SIZE = 5 * 1024 * 1024

def persist_scan_record(result: dict, db: Session) -> ScanRecord:
    """
    Helper function to persist an analysis outcome into the database audit log.
    """
    raw_summary = result.get("raw_metrics_summary", {})
    loc = raw_summary.get("lines_of_code", 0)
    cc = raw_summary.get("cyclomatic_complexity", 0)
    branch_count = raw_summary.get("branch_count", 0)
    
    record = ScanRecord(
        filename=result.get("filename", "unknown.py"),
        defect_risk=result.get("defect_risk", "UNKNOWN"),
        risk_probability=result.get("risk_probability", "0.0%"),
        probability_score=result.get("probability_score", 0.0),
        lines_of_code=loc,
        cyclomatic_complexity=cc,
        branch_count=branch_count,
        most_suspicious_component=result.get("most_suspicious_component", "None"),
        main_risk_factors=json.dumps(result.get("main_risk_factors", [])),
        main_mitigating_factors=json.dumps(result.get("main_mitigating_factors", []))
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Loads ML models and AST engine once during startup and initializes Database.
    """
    print("Initializing Database tables...")
    try:
        init_db()
    except Exception as e:
        print(f"[WARN] Database initialization warning: {e}")

    print("Initializing Code Defect Risk Engine in FastAPI application...")
    try:
        app.state.engine = CodeDefectEngine(model_path="models/best_xgboost_model.joblib")
        print("[OK] Defect Engine successfully loaded and ready for inference.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize engine: {e}")
        app.state.engine = None
    yield
    print("Shutting down API server...")

app = FastAPI(
    title="Predictive Code Quality & Defect Risk Engine",
    description="Production REST API for automated software defect risk scoring, SHAP explainability, and database audit logs.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", tags=["Frontend"])
async def serve_dashboard():
    """
    Serves the primary Web Dashboard interface.
    """
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Defect Risk Engine API is active. Open /docs for Swagger UI."}

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """
    Service health check and model loading status.
    """
    is_loaded = hasattr(app.state, "engine") and app.state.engine is not None
    return {
        "status": "healthy" if is_loaded else "degraded",
        "version": "1.0.0",
        "engine": "XGBoost + TreeSHAP + Radon AST",
        "model_loaded": is_loaded
    }

@app.post("/api/v1/analyze", response_model=DefectRiskResponse, tags=["Inference"])
async def analyze_code(request: CodeAnalysisRequest, db: Session = Depends(get_db)):
    """
    Analyzes raw Python source code passed as a JSON text string and logs result to DB.
    """
    if not hasattr(app.state, "engine") or app.state.engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Defect Risk Engine model is not initialized."
        )

    try:
        result = app.state.engine.analyze_and_predict(
            code_str=request.source_code,
            filename=request.filename
        )
        # Persist scan to database audit trail
        try:
            persist_scan_record(result, db)
        except Exception as db_err:
            print(f"[WARN] Failed to persist scan record: {db_err}")

        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@app.post("/api/v1/analyze-file", response_model=DefectRiskResponse, tags=["Inference"])
async def analyze_file_upload(
    file: UploadFile = File(..., description="Python source code file (.py)"),
    db: Session = Depends(get_db)
):
    """
    Analyzes an uploaded physical Python (.py) file directly and logs result to DB.
    """
    if not hasattr(app.state, "engine") or app.state.engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Defect Risk Engine model is not initialized."
        )

    # 1. Validate file extension (.py only)
    filename = file.filename or "uploaded_module.py"
    if not filename.endswith(".py"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only Python (.py) files are supported, received: '{filename}'"
        )

    # 2. Read file content safely
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    # 3. Check file size limit (5MB)
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum allowed size is 5MB."
        )

    # 4. Decode file bytes to UTF-8 string
    try:
        code_str = contents.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding error. Please upload a valid UTF-8 text file."
        )

    # 5. Execute Defect Risk Engine Analysis
    try:
        result = app.state.engine.analyze_and_predict(
            code_str=code_str,
            filename=filename
        )
        # Persist scan to database audit trail
        try:
            persist_scan_record(result, db)
        except Exception as db_err:
            print(f"[WARN] Failed to persist scan record: {db_err}")

        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

# ==========================================
# Database Scan History Endpoints (Phase 17)
# ==========================================

@app.get("/api/v1/history", response_model=ScanHistoryResponse, tags=["Database History"])
async def get_scan_history(
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    risk: Optional[str] = Query(default=None, description="Filter by risk category: HIGH, MEDIUM, LOW"),
    db: Session = Depends(get_db)
):
    """
    Retrieves historical scan audit trail logs ordered by most recent first.
    """
    query = db.query(ScanRecord)
    if risk:
        query = query.filter(ScanRecord.defect_risk == risk.upper())
    
    total_count = query.count()
    records = query.order_by(ScanRecord.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total_count": total_count,
        "scans": [r.to_dict() for r in records]
    }

@app.get("/api/v1/history/{scan_id}", response_model=ScanHistoryItem, tags=["Database History"])
async def get_scan_by_id(scan_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a single historical scan record by its primary key ID.
    """
    record = db.query(ScanRecord).filter(ScanRecord.id == scan_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan record with ID {scan_id} not found."
        )
    return record.to_dict()

@app.delete("/api/v1/history/{scan_id}", response_model=DeleteHistoryResponse, tags=["Database History"])
async def delete_scan_record(scan_id: int, db: Session = Depends(get_db)):
    """
    Deletes an individual scan record from the database.
    """
    record = db.query(ScanRecord).filter(ScanRecord.id == scan_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan record with ID {scan_id} not found."
        )
    db.delete(record)
    db.commit()
    return {"message": f"Scan record {scan_id} deleted successfully.", "deleted_count": 1}

@app.delete("/api/v1/history", response_model=DeleteHistoryResponse, tags=["Database History"])
async def clear_all_history(db: Session = Depends(get_db)):
    """
    Clears all scan audit records from the database table.
    """
    deleted = db.query(ScanRecord).delete()
    db.commit()
    return {"message": "All scan records cleared successfully.", "deleted_count": deleted}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
