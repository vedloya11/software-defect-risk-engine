import os
import json
import joblib
import pandas as pd
import numpy as np

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    brier_score_loss
)

def evaluate_on_test_set(
    test_path: str,
    model_path: str,
    output_report_path: str,
    target_col: str = "DEFECT_LABEL"
) -> None:
    """
    Evaluates the champion model on the unseen holdout test set,
    computes probability calibration (Brier score), and performs deep error analysis.
    """
    print(f"Loading holdout test dataset from: {test_path}")
    test_df = pd.read_csv(test_path)
    
    print(f"Loading champion model from: {model_path}")
    model = joblib.load(model_path)
    
    X_test = test_df.drop(columns=[target_col])
    y_test = test_df[target_col]
    
    # 1. Predictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # 2. Performance Metrics
    roc_auc = roc_auc_score(y_test, y_proba)
    pr_auc = average_precision_score(y_test, y_proba)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    brier = brier_score_loss(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)
    
    print("\n" + "=" * 60)
    print("      FINAL UNBIASED HOLDOUT TEST SET EVALUATION      ")
    print("=" * 60)
    print(f"Test Set Size:       {len(test_df)} samples")
    print(f"ROC-AUC Score:       {roc_auc:.4f}")
    print(f"PR-AUC Score:        {pr_auc:.4f}")
    print(f"Precision (Class 1): {precision:.4f}")
    print(f"Recall (Class 1):    {recall:.4f}")
    print(f"F1-Score (Class 1):   {f1:.4f}")
    print(f"Brier Score (Calib): {brier:.4f} (Lower is better, 0 = perfect probability)")
    
    print("\nConfusion Matrix:")
    print(f"  [True Clean: {cm[0,0]:3d} | False Alarm: {cm[0,1]:3d}]")
    print(f"  [Missed Bug: {cm[1,0]:3d} | Caught Bug:  {cm[1,1]:3d}]")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Clean (0)", "Defective (1)"]))
    
    # 3. Deep Error Analysis
    print("=" * 60)
    print("                 DEEP ERROR ANALYSIS                  ")
    print("=" * 60)
    
    analysis_df = X_test.copy()
    analysis_df['ACTUAL'] = y_test
    analysis_df['PREDICTED'] = y_pred
    analysis_df['RISK_PROBABILITY'] = y_proba
    
    # Categorize error types
    conditions = [
        (analysis_df['ACTUAL'] == 0) & (analysis_df['PREDICTED'] == 0),
        (analysis_df['ACTUAL'] == 0) & (analysis_df['PREDICTED'] == 1),
        (analysis_df['ACTUAL'] == 1) & (analysis_df['PREDICTED'] == 0),
        (analysis_df['ACTUAL'] == 1) & (analysis_df['PREDICTED'] == 1)
    ]
    categories = ['True Negative (Clean)', 'False Alarm (FP)', 'Missed Defect (FN)', 'Caught Defect (TP)']
    analysis_df['ERROR_TYPE'] = np.select(conditions, categories, default='Unknown')
    
    # Analyze why the model missed bugs (False Negatives) vs caught bugs (True Positives)
    print("\nComparison of Metric Means by Prediction Category:")
    key_metrics = ['LOC', 'CYCLO', 'VOLUME', 'COMPLEXITY_DENSITY', 'OPERATOR_DENSITY', 'RISK_PROBABILITY']
    group_means = analysis_df.groupby('ERROR_TYPE')[key_metrics].mean()
    print(group_means.to_string())
    
    # 4. Save Test Metrics
    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
    report_data = {
        "test_samples": int(len(test_df)),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "brier_score": float(brier),
        "confusion_matrix": {
            "true_negatives": int(cm[0,0]),
            "false_positives": int(cm[0,1]),
            "false_negatives": int(cm[1,0]),
            "true_positives": int(cm[1,1])
        }
    }
    
    with open(output_report_path, "w") as f:
        json.dump(report_data, f, indent=4)
        
    print(f"\n[OK] Test evaluation report saved to: {output_report_path}")

if __name__ == "__main__":
    TEST_PATH = os.path.join("data", "processed", "test.csv")
    MODEL_PATH = os.path.join("models", "best_xgboost_model.joblib")
    REPORT_PATH = os.path.join("models", "test_evaluation_report.json")
    
    evaluate_on_test_set(TEST_PATH, MODEL_PATH, REPORT_PATH)
