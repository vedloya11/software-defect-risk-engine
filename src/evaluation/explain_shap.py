import os
import json
import joblib
import pandas as pd
import numpy as np
import shap
import matplotlib.pyplot as plt

def generate_shap_explanations(
    model_path: str,
    test_path: str,
    output_dir: str = "reports",
    target_col: str = "DEFECT_LABEL"
) -> None:
    """
    Initializes SHAP TreeExplainer on the champion XGBoost model,
    generates global summary plots, and demonstrates single-file local explanations.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Loading champion model from: {model_path}")
    model = joblib.load(model_path)
    
    print(f"Loading test dataset from: {test_path}")
    test_df = pd.read_csv(test_path)
    X_test = test_df.drop(columns=[target_col])
    
    # 1. Initialize TreeExplainer
    print("Computing SHAP values using TreeExplainer...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_test)
    
    # 2. Generate and Save Global Summary Plot
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_test, show=False)
    summary_plot_path = os.path.join(output_dir, "shap_summary_plot.png")
    plt.tight_layout()
    plt.savefig(summary_plot_path, dpi=300)
    plt.close()
    print(f"[OK] Global SHAP summary plot saved to: {summary_plot_path}")
    
    # 3. Local Explanation for a Single Sample (High-Risk File Simulation)
    sample_idx = 0
    sample_features = X_test.iloc[[sample_idx]]
    sample_shap = shap_values[sample_idx]
    
    predicted_prob = float(model.predict_proba(sample_features)[0, 1])
    base_val = float(explainer.expected_value) if np.isscalar(explainer.expected_value) else float(explainer.expected_value[1])
    
    # Extract feature contributions
    contributions = []
    for feat_name, val, s_val in zip(X_test.columns, sample_features.values[0], sample_shap.values):
        contributions.append({
            "feature": feat_name,
            "feature_value": round(float(val), 4),
            "shap_contribution": round(float(s_val), 4),
            "impact": "Increases Risk" if s_val > 0 else "Decreases Risk"
        })
        
    # Sort by absolute impact
    contributions = sorted(contributions, key=lambda x: abs(x["shap_contribution"]), reverse=True)
    
    explanation_output = {
        "sample_index": sample_idx,
        "predicted_defect_risk": f"{predicted_prob:.2%}",
        "risk_level": "HIGH" if predicted_prob > 0.60 else ("MEDIUM" if predicted_prob > 0.35 else "LOW"),
        "base_expected_value": round(base_val, 4),
        "top_risk_drivers": [c for c in contributions if c["shap_contribution"] > 0][:4],
        "top_mitigating_factors": [c for c in contributions if c["shap_contribution"] < 0][:3]
    }
    
    # Save local explanation to JSON
    json_path = os.path.join(output_dir, "sample_file_explanation.json")
    with open(json_path, "w") as f:
        json.dump(explanation_output, f, indent=4)
        
    print(f"[OK] Single file local explanation saved to: {json_path}")
    print("\n" + "=" * 55)
    print(f"  SAMPLE FILE EXPLANATION (Risk: {explanation_output['predicted_defect_risk']})")
    print("=" * 55)
    print("Top Risk Factors (Increasing Defect Probability):")
    for item in explanation_output["top_risk_drivers"]:
        print(f"  + {item['feature']} = {item['feature_value']} (SHAP Impact: +{item['shap_contribution']})")
        
    print("\nTop Mitigating Factors (Decreasing Defect Probability):")
    for item in explanation_output["top_mitigating_factors"]:
        print(f"  - {item['feature']} = {item['feature_value']} (SHAP Impact: {item['shap_contribution']})")

if __name__ == "__main__":
    MODEL_PATH = os.path.join("models", "best_xgboost_model.joblib")
    TEST_PATH = os.path.join("data", "processed", "test.csv")
    
    generate_shap_explanations(MODEL_PATH, TEST_PATH)
