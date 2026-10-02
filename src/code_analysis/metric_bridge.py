import os
import math
from typing import Dict, Any, List
import pandas as pd
import numpy as np

import sys
# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.code_analysis.analyzer import SourceCodeAnalyzer
from src.models.predictor import DefectRiskPredictor

class MetricBridge:
    """
    Normalizes raw source code metrics into the [0, 1] scaled domain expected
    by the NASA-trained XGBoost model using industry-standard benchmark baselines.
    """
    
    # Standard benchmark maximum ceilings for typical software modules
    METRIC_SCALING_REFERENCE = {
        'LOC': 500.0,            # Modules > 500 LOC are treated at max scale
        'CYCLO': 30.0,           # Cyclomatic complexity > 30 is very high
        'LENGTH': 600.0,         # Halstead length ceiling
        'VOLUME': 4000.0,        # Halstead volume ceiling
        'DIFFICULTY': 50.0,      # Halstead difficulty ceiling
        'INT_FAN_IN': 10.0,      # Internal definition count ceiling
        'INT_FAN_OUT': 15.0,     # External dependency ceiling
        'NUM_OPERATORS': 250.0,  # Total operator count ceiling
        'NUM_OPERANDS': 200.0,   # Total operand count ceiling
        'BRANCH_COUNT': 25.0     # Decision branch ceiling
    }

    @classmethod
    def normalize_metrics(cls, raw_metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Maps raw integer/float metrics to the [0, 1] continuous distribution
        using smooth non-linear saturation scaling: x / (x + ref_half_point) or min-max capping.
        """
        normalized = {}
        for k, raw_val in raw_metrics.items():
            if k in cls.METRIC_SCALING_REFERENCE:
                ref_max = cls.METRIC_SCALING_REFERENCE[k]
                # Bounded min-max scaling with soft upper cap
                scaled_val = min(1.0, max(0.0, raw_val / ref_max))
                normalized[k] = round(scaled_val, 4)
            else:
                normalized[k] = raw_val
        return normalized

class CodeDefectEngine:
    """
    End-to-End Software Defect Risk Engine.
    Combines AST Source Code Analysis, Normalization, XGBoost Inference,
    and Real-Time SHAP Risk Factor Attribution.
    """

    def __init__(self, model_path: str = "models/best_xgboost_model.joblib"):
        self.analyzer = SourceCodeAnalyzer()
        self.predictor = DefectRiskPredictor(model_path=model_path)
        self.bridge = MetricBridge()

    def analyze_and_predict(self, code_str: str, filename: str = "uploaded_file.py") -> Dict[str, Any]:
        """
        Analyzes raw Python source code and returns the complete defect risk report.
        """
        # Step 1: Extract raw code metrics using AST and Radon
        analysis_result = self.analyzer.analyze_source_code(code_str, filename=filename)
        raw_metrics = analysis_result["raw_metrics"]

        # Step 2: Normalize metrics to match model domain
        normalized_metrics = self.bridge.normalize_metrics(raw_metrics)

        # Step 3: Run ML model inference & SHAP explainability
        prediction_result = self.predictor.predict(normalized_metrics)

        # Step 4: Assemble comprehensive final risk report
        report = {
            "filename": filename,
            "defect_risk": prediction_result["risk_level"],
            "risk_probability": prediction_result["defect_risk_percentage"],
            "probability_score": prediction_result["defect_probability"],
            "most_suspicious_component": analysis_result["most_suspicious_component"],
            "main_risk_factors": [
                f"{f['feature']} ({f['direction']}, SHAP impact: +{f['shap_impact']})"
                for f in prediction_result["top_risk_factors"]
            ],
            "main_mitigating_factors": [
                f"{f['feature']} ({f['direction']}, SHAP impact: {f['shap_impact']})"
                for f in prediction_result["top_mitigating_factors"]
            ],
            "raw_metrics_summary": {
                "lines_of_code": int(raw_metrics["LOC"]),
                "cyclomatic_complexity": int(raw_metrics["CYCLO"]),
                "branch_count": int(raw_metrics["BRANCH_COUNT"]),
                "external_dependencies_count": int(raw_metrics["INT_FAN_OUT"]),
                "total_operators": int(raw_metrics["NUM_OPERATORS"]),
                "total_operands": int(raw_metrics["NUM_OPERANDS"])
            },
            "external_dependencies": analysis_result["external_dependencies"],
            "function_breakdown": analysis_result["function_breakdown"]
        }

        return report

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Reads a Python file from disk and produces the full defect risk assessment.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            code_str = f.read()

        return self.analyze_and_predict(code_str, filename=os.path.basename(file_path))

if __name__ == "__main__":
    # Test on a realistic complex Python module
    sample_payment_code = '''
import os
import requests
import json
import time

def process_payment(user_id, amount, is_vip, retry_count=3):
    """Processes user payment with complex discount logic and retry handling."""
    if amount <= 0:
        return {"status": "error", "msg": "Invalid amount"}
    
    final_amount = amount
    if is_vip:
        if amount > 1000:
            final_amount = amount * 0.85
        elif amount > 500:
            final_amount = amount * 0.90
        else:
            final_amount = amount * 0.95
            
    for attempt in range(retry_count):
        try:
            res = requests.post("https://payment.gateway.com/charge", json={"user": user_id, "amt": final_amount})
            if res.status_code == 200:
                return {"status": "success", "charge": final_amount}
            elif res.status_code == 429:
                time.sleep(1)
                continue
            else:
                break
        except Exception as e:
            if attempt == retry_count - 1:
                return {"status": "failed", "error": str(e)}
                
    return {"status": "timeout"}

def validate_user(user_id):
    if not user_id or len(user_id) < 5:
        return False
    return True
'''
    import json
    engine = CodeDefectEngine()
    result = engine.analyze_and_predict(sample_payment_code, "payment_service.py")
    
    print("\n" + "=" * 60)
    print("      END-TO-END CODE DEFECT RISK ASSESSMENT REPORT     ")
    print("=" * 60)
    print(f"File Name:                  {result['filename']}")
    print(f"Defect Risk Level:          {result['defect_risk']}")
    print(f"Defect Probability:         {result['risk_probability']}")
    print(f"Most Suspicious Component:  {result['most_suspicious_component']}")
    
    print("\nMain Risk Factors:")
    for rf in result['main_risk_factors']:
        print(f"  [+] {rf}")
        
    print("\nMain Mitigating Factors:")
    for mf in result['main_mitigating_factors']:
        print(f"  [-] {mf}")
        
    print("\nRaw Code Metrics:")
    for k, v in result['raw_metrics_summary'].items():
        print(f"  - {k:<25}: {v}")
