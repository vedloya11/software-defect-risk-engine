import os
import joblib
import pandas as pd
import numpy as np
import shap
from typing import Dict, Any, List

class DefectRiskPredictor:
    """
    Production-ready Defect Risk Prediction Engine.
    Handles raw metric input, automatic feature engineering, XGBoost inference,
    and real-time SHAP risk factor attribution.
    """
    
    EXPECTED_RAW_FEATURES = [
        'LOC', 'CYCLO', 'LENGTH', 'VOLUME', 'DIFFICULTY', 
        'INT_FAN_IN', 'INT_FAN_OUT', 'NUM_OPERATORS', 
        'NUM_OPERANDS', 'BRANCH_COUNT'
    ]
    
    FINAL_FEATURE_ORDER = [
        'LOC', 'CYCLO', 'LENGTH', 'VOLUME', 'DIFFICULTY', 
        'INT_FAN_IN', 'INT_FAN_OUT', 'NUM_OPERATORS', 
        'NUM_OPERANDS', 'BRANCH_COUNT', 'COMPLEXITY_DENSITY', 
        'OPERAND_DENSITY', 'OPERATOR_DENSITY', 'COMPLEXITY_BRANCH_RATIO'
    ]
    
    def __init__(self, model_path: str = "models/best_xgboost_model.joblib"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")
            
        print(f"Loading champion model from {model_path}...")
        self.model = joblib.load(model_path)
        self.explainer = shap.TreeExplainer(self.model)
        self.base_value = float(np.atleast_1d(self.explainer.expected_value)[0])
        print("[OK] Predictor initialized successfully!")

    def _engineer_features(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies exact domain feature engineering logic to raw metrics.
        """
        df = raw_df.copy()
        eps = 1e-5
        
        df['COMPLEXITY_DENSITY'] = df['CYCLO'] / (df['LOC'] + eps)
        df['OPERAND_DENSITY'] = df['NUM_OPERANDS'] / (df['LOC'] + eps)
        df['OPERATOR_DENSITY'] = df['NUM_OPERATORS'] / (df['LOC'] + eps)
        df['COMPLEXITY_BRANCH_RATIO'] = df['CYCLO'] / (df['BRANCH_COUNT'] + eps)
        
        # Ensure exact column ordering
        return df[self.FINAL_FEATURE_ORDER]

    def predict(self, raw_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Predicts defect risk and provides human-readable SHAP risk drivers for a single file.
        """
        # 1. Validate raw metrics
        for feat in self.EXPECTED_RAW_FEATURES:
            if feat not in raw_metrics:
                raise ValueError(f"Missing required metric '{feat}' in input metrics")
                
        raw_df = pd.DataFrame([raw_metrics])
        
        # 2. Engineer features
        processed_df = self._engineer_features(raw_df)
        
        # 3. Model Inference
        defect_prob = float(self.model.predict_proba(processed_df)[0, 1])
        predicted_class = int(defect_prob >= 0.5)
        
        # 4. Determine Risk Category
        if defect_prob >= 0.60:
            risk_level = "HIGH"
        elif defect_prob >= 0.35:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        # 5. SHAP Risk Factor Attribution
        shap_values = self.explainer(processed_df)
        feature_shap = shap_values[0].values
        
        drivers = []
        for feat_name, feat_val, s_val in zip(self.FINAL_FEATURE_ORDER, processed_df.values[0], feature_shap):
            drivers.append({
                "feature": feat_name,
                "feature_value": round(float(feat_val), 4),
                "shap_impact": round(float(s_val), 4),
                "direction": "Risk Increasing" if s_val > 0 else "Risk Decreasing"
            })
            
        # Sort drivers by absolute impact
        drivers = sorted(drivers, key=lambda x: abs(x["shap_impact"]), reverse=True)
        
        top_risk_factors = [d for d in drivers if d["shap_impact"] > 0][:3]
        top_mitigating_factors = [d for d in drivers if d["shap_impact"] < 0][:3]
        
        return {
            "defect_probability": round(defect_prob, 4),
            "defect_risk_percentage": f"{defect_prob:.1%}",
            "risk_level": risk_level,
            "predicted_defect": bool(predicted_class),
            "top_risk_factors": top_risk_factors,
            "top_mitigating_factors": top_mitigating_factors
        }

if __name__ == "__main__":
    # Test with sample raw metric dictionary
    sample_metrics = {
        'LOC': 0.75,
        'CYCLO': 0.80,
        'LENGTH': 0.65,
        'VOLUME': 0.70,
        'DIFFICULTY': 0.55,
        'INT_FAN_IN': 0.20,
        'INT_FAN_OUT': 0.40,
        'NUM_OPERATORS': 0.85,
        'NUM_OPERANDS': 0.60,
        'BRANCH_COUNT': 0.75
    }
    
    predictor = DefectRiskPredictor("models/best_xgboost_model.joblib")
    result = predictor.predict(sample_metrics)
    
    import json
    print("\n--- Production Predictor Test Output ---")
    print(json.dumps(result, indent=4))
