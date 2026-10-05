import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.code_analysis.metric_bridge import CodeDefectEngine
from api.schemas import CodeAnalysisRequest, DefectRiskResponse, HealthResponse

# Maximum allowed upload size (5 MB)
MAX_FILE_SIZE = 5 * 1024 * 1024

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Loads ML models and AST engine once during startup and attaches to app state.
    """
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
    description="Production REST API for automated software defect risk scoring and SHAP explainability.",
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
async def analyze_code(request: CodeAnalysisRequest):
    """
    Analyzes raw Python source code passed as a JSON text string.
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
async def analyze_file_upload(file: UploadFile = File(..., description="Python source code file (.py)")):
    """
    Analyzes an uploaded physical Python (.py) file directly.
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
            detail=f"File too large. Maximum allowed size is 5MB."
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
