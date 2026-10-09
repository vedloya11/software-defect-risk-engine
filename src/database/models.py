import datetime
import json
from sqlalchemy import Column, Integer, Float, String, Text, DateTime
from src.database.db import Base

class ScanRecord(Base):
    """
    SQLAlchemy model representing an automated code scan result audit log.
    Tracks every code analysis execution, risk assessment, and key metrics.
    """
    __tablename__ = "scan_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False, index=True)
    defect_risk = Column(String(50), nullable=False)  # "HIGH", "MEDIUM", "LOW"
    risk_probability = Column(String(50), nullable=False)  # "78.4%"
    probability_score = Column(Float, nullable=False)  # 0.784
    lines_of_code = Column(Integer, nullable=False)
    cyclomatic_complexity = Column(Integer, nullable=False)
    branch_count = Column(Integer, nullable=True, default=0)
    most_suspicious_component = Column(String(255), nullable=True)
    
    # Store top SHAP factors as JSON strings for rich history inspection
    main_risk_factors = Column(Text, nullable=True)
    main_mitigating_factors = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    def to_dict(self):
        """
        Converts the database record into a clean serializable dictionary.
        """
        risk_factors = []
        if self.main_risk_factors:
            try:
                risk_factors = json.loads(self.main_risk_factors)
            except Exception:
                risk_factors = [self.main_risk_factors]

        mitigating_factors = []
        if self.main_mitigating_factors:
            try:
                mitigating_factors = json.loads(self.main_mitigating_factors)
            except Exception:
                mitigating_factors = [self.main_mitigating_factors]

        return {
            "id": self.id,
            "filename": self.filename,
            "defect_risk": self.defect_risk,
            "risk_probability": self.risk_probability,
            "probability_score": round(self.probability_score, 4),
            "lines_of_code": self.lines_of_code,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "branch_count": self.branch_count or 0,
            "most_suspicious_component": self.most_suspicious_component or "None",
            "main_risk_factors": risk_factors,
            "main_mitigating_factors": mitigating_factors,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else ""
        }
