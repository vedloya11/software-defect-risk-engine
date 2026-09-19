import os
import joblib
import pandas as pd
import numpy as np

from xgboost import XGBClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score
)

def train_and_evaluate_xgb(
    train_path: str,
    val_path: str,
    model_output_path: str,
    target_col: str = "DEFECT_LABEL",
    random_state: int = 42
) -> None:
    """
    Trains an XGBoost Classifier with scale_pos_weight and evaluates on validation split.
    """
    print("Loading train and validation datasets...")
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    
    X_train = train_df.drop(columns=[target_col])
    y_train = train_df[target_col]
    
    X_val = val_df.drop(columns=[target_col])
    y_val = val_df[target_col]
    
    # 1. Calculate dynamic scale_pos_weight for class imbalance
    num_neg = (y_train == 0).sum()
    num_pos = (y_train == 1).sum()
    scale_pos_weight = num_neg / num_pos
    print(f"Class distribution in train set: Clean={num_neg}, Defective={num_pos}")
    print(f"Calculated scale_pos_weight: {scale_pos_weight:.2f}")
    
    # 2. Instantiate XGBoost Classifier
    xgb_model = XGBClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=random_state,
        n_jobs=-1
    )
    
    # 3. Fit Model
    print("\nTraining XGBoost Classifier...")
    xgb_model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=False
    )
    
    # 4. Predict on Validation Set
    y_val_pred = xgb_model.predict(X_val)
    y_val_proba = xgb_model.predict_proba(X_val)[:, 1]
    
    # 5. Compute Metrics
    roc_auc = roc_auc_score(y_val, y_val_proba)
    pr_auc = average_precision_score(y_val, y_val_proba)
    precision = precision_score(y_val, y_val_pred, zero_division=0)
    recall = recall_score(y_val, y_val_pred, zero_division=0)
    f1 = f1_score(y_val, y_val_pred, zero_division=0)
    cm = confusion_matrix(y_val, y_val_pred)
    
    print("\n" + "=" * 50)
    print("        VALIDATION SET EVALUATION (XGBOOST)       ")
    print("=" * 50)
    print(f"ROC-AUC Score:      {roc_auc:.4f}")
    print(f"PR-AUC Score:       {pr_auc:.4f}")
    print(f"Precision (Class 1): {precision:.4f}")
    print(f"Recall (Class 1):    {recall:.4f}")
    print(f"F1-Score (Class 1):  {f1:.4f}")
    print("\nConfusion Matrix:")
    print(f"  [True Clean: {cm[0,0]:3d} | False Alarm: {cm[0,1]:3d}]")
    print(f"  [Missed Bug: {cm[1,0]:3d} | Caught Bug:  {cm[1,1]:3d}]")
    print("\nDetailed Classification Report:")
    print(classification_report(y_val, y_val_pred, target_names=["Clean (0)", "Defective (1)"]))
    
    # 6. Feature Importances (Gain - Relative contribution of each feature to the model)
    feature_importances = pd.DataFrame({
        'Feature': X_train.columns,
        'Importance (Gain)': xgb_model.feature_importances_
    }).sort_values(by='Importance (Gain)', ascending=False)
    
    print("\nXGBoost Feature Importances (Gain):")
    print(feature_importances.head(10).to_string(index=False))
    
    # 7. Save Model Artifact
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump(xgb_model, model_output_path)
    print(f"\n[OK] Model saved to: {model_output_path}")

if __name__ == "__main__":
    TRAIN_PATH = os.path.join("data", "processed", "train.csv")
    VAL_PATH = os.path.join("data", "processed", "val.csv")
    MODEL_PATH = os.path.join("models", "xgboost_model.joblib")
    
    train_and_evaluate_xgb(TRAIN_PATH, VAL_PATH, MODEL_PATH)
