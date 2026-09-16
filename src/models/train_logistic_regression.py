import os
import joblib
import pandas as pd
import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score
)

def train_and_evaluate(
    train_path: str,
    val_path: str,
    model_output_path: str,
    target_col: str = "DEFECT_LABEL",
    random_state: int = 42
) -> None:
    """
    Trains a Logistic Regression pipeline and evaluates on the validation split.
    """
    print("Loading train and validation datasets...")
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    
    # Separate features and target
    X_train = train_df.drop(columns=[target_col])
    y_train = train_df[target_col]
    
    X_val = val_df.drop(columns=[target_col])
    y_val = val_df[target_col]
    
    print(f"Features: {list(X_train.columns)}")
    print(f"Train size: {X_train.shape}, Val size: {X_val.shape}")
    
    # 1. Build Pipeline: Preprocessing + Model
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(
            class_weight='balanced',
            random_state=random_state,
            max_iter=1000
        ))
    ])
    
    # 2. Fit Pipeline
    print("\nTraining Logistic Regression with class_weight='balanced'...")
    pipeline.fit(X_train, y_train)
    
    # 3. Predict on Validation Set
    y_val_pred = pipeline.predict(X_val)
    y_val_proba = pipeline.predict_proba(X_val)[:, 1]
    
    # 4. Compute Metrics
    roc_auc = roc_auc_score(y_val, y_val_proba)
    pr_auc = average_precision_score(y_val, y_val_proba)
    precision = precision_score(y_val, y_val_pred, zero_division=0)
    recall = recall_score(y_val, y_val_pred, zero_division=0)
    f1 = f1_score(y_val, y_val_pred, zero_division=0)
    cm = confusion_matrix(y_val, y_val_pred)
    
    print("\n" + "=" * 50)
    print("      VALIDATION SET EVALUATION (BASELINE)      ")
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
    
    # 5. Inspect Model Coefficients (Interpretability)
    model = pipeline.named_steps['classifier']
    feature_names = X_train.columns
    coef_df = pd.DataFrame({
        'Feature': feature_names,
        'Coefficient': model.coef_[0]
    }).sort_values(by='Coefficient', ascending=False)
    
    print("\nTop Risk-Increasing Features (Positive Coefficients):")
    print(coef_df.head(5).to_string(index=False))
    
    print("\nTop Risk-Decreasing Features (Negative Coefficients):")
    print(coef_df.tail(5).to_string(index=False))
    
    # 6. Save Model Pipeline
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump(pipeline, model_output_path)
    print(f"\n[OK] Model pipeline saved to: {model_output_path}")

if __name__ == "__main__":
    TRAIN_PATH = os.path.join("data", "processed", "train.csv")
    VAL_PATH = os.path.join("data", "processed", "val.csv")
    MODEL_PATH = os.path.join("models", "logistic_regression.joblib")
    
    train_and_evaluate(TRAIN_PATH, VAL_PATH, MODEL_PATH)
