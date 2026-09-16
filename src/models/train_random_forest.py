import os
import joblib
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score
)

def train_and_evaluate_rf(
    train_path: str,
    val_path: str,
    model_output_path: str,
    target_col: str = "DEFECT_LABEL",
    random_state: int = 42
) -> None:
    """
    Trains a Random Forest Classifier and evaluates on the validation split.
    """
    print("Loading train and validation datasets...")
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    
    X_train = train_df.drop(columns=[target_col])
    y_train = train_df[target_col]
    
    X_val = val_df.drop(columns=[target_col])
    y_val = val_df[target_col]
    
    print(f"Features ({len(X_train.columns)}): {list(X_train.columns)}")
    print(f"Train size: {X_train.shape}, Val size: {X_val.shape}")
    
    # 1. Instantiate Random Forest Classifier
    # Tree models do not require feature scaling
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced_subsample',
        random_state=random_state,
        n_jobs=-1
    )
    
    # 2. Fit Model
    print("\nTraining Random Forest (100 trees, class_weight='balanced_subsample')...")
    rf_model.fit(X_train, y_train)
    
    # 3. Predict on Validation Set
    y_val_pred = rf_model.predict(X_val)
    y_val_proba = rf_model.predict_proba(X_val)[:, 1]
    
    # 4. Compute Metrics
    roc_auc = roc_auc_score(y_val, y_val_proba)
    pr_auc = average_precision_score(y_val, y_val_proba)
    precision = precision_score(y_val, y_val_pred, zero_division=0)
    recall = recall_score(y_val, y_val_pred, zero_division=0)
    f1 = f1_score(y_val, y_val_pred, zero_division=0)
    cm = confusion_matrix(y_val, y_val_pred)
    
    print("\n" + "=" * 50)
    print("     VALIDATION SET EVALUATION (RANDOM FOREST)    ")
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
    
    # 5. Feature Importances (MDI - Mean Decrease in Impurity)
    feature_importances = pd.DataFrame({
        'Feature': X_train.columns,
        'Importance': rf_model.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    
    print("\nFeature Importances (Top 10):")
    print(feature_importances.head(10).to_string(index=False))
    
    # 6. Save Model Artifact
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump(rf_model, model_output_path)
    print(f"\n[OK] Model saved to: {model_output_path}")

if __name__ == "__main__":
    TRAIN_PATH = os.path.join("data", "processed", "train.csv")
    VAL_PATH = os.path.join("data", "processed", "val.csv")
    MODEL_PATH = os.path.join("models", "random_forest.joblib")
    
    train_and_evaluate_rf(TRAIN_PATH, VAL_PATH, MODEL_PATH)
