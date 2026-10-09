from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class CodeAnalysisRequest(BaseModel):
    filename: str = Field(default="module.py", description="Name of the source code file")
    source_code: str = Field(..., min_length=5, description="Raw Python source code string")

class RawMetricsSummary(BaseModel):
    lines_of_code: int
    cyclomatic_complexity: int
    branch_count: int
    external_dependencies_count: int
    total_operators: int
    total_operands: int

class FunctionComplexityInfo(BaseModel):
    name: str
    complexity: int
    type: str
    lineno: int

class DefectRiskResponse(BaseModel):
    filename: str
    defect_risk: str = Field(description="Risk category: LOW, MEDIUM, or HIGH")
    risk_probability: str = Field(description="Formatted risk percentage, e.g. 52.3%")
    probability_score: float = Field(description="Continuous risk score between 0.0 and 1.0")
    most_suspicious_component: str
    main_risk_factors: List[str]
    main_mitigating_factors: List[str]
    raw_metrics_summary: RawMetricsSummary
    external_dependencies: List[str]
    function_breakdown: List[FunctionComplexityInfo]

class HealthResponse(BaseModel):
    status: str
    version: str
    engine: str
    model_loaded: bool

class ScanHistoryItem(BaseModel):
    id: int
    filename: str
    defect_risk: str
    risk_probability: str
    probability_score: float
    lines_of_code: int
    cyclomatic_complexity: int
    branch_count: int
    most_suspicious_component: str
    main_risk_factors: List[str]
    main_mitigating_factors: List[str]
    created_at: str

class ScanHistoryResponse(BaseModel):
    total_count: int
    scans: List[ScanHistoryItem]

class DeleteHistoryResponse(BaseModel):
    message: str
    deleted_count: int
