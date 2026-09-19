import os
import joblib
import pandas as pd
import numpy as np

from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score
)

def tune_xgboost(
    train_path: str,
    val_path: str,
    model_output_path: str,
    target_col: str = "DEFECT_LABEL",
    n_iter: int = 50,
    random_state: int = 42
) -> None:
    """
    Performs Stratified 5-Fold Cross-Validated Hyperparameter Tuning on XGBoost.
    Optimizes for PR-AUC (average_precision).
    """
    print("Loading train and validation datasets...")
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    
    X_train = train_df.drop(columns=[target_col])
    y_train = train_df[target_col]
    
    X_val = val_df.drop(columns=[target_col])
    y_val = val_df[target_col]
    
    num_neg = (y_train == 0).sum()
    num_pos = (y_train == 1).sum()
    scale_pos_weight = num_neg / num_pos
    print(f"Calculated scale_pos_weight: {scale_pos_weight:.2f}")
    
    # 1. Define Parameter Search Space
    param_distributions = {
        'n_estimators': [100, 150, 200, 250],
        'max_depth': [3, 4, 5, 6, 7],
        'learning_rate': [0.01, 0.03, 0.05, 0.08, 0.1],
        'subsample': [0.6, 0.7, 0.8, 0.9, 1.0],
        'colsample_bytree': [0.6, 0.7, 0.8, 0.9, 1.0],
        'min_child_weight': [1, 2, 3, 5, 7],
        'gamma': [0.0, 0.1, 0.2, 0.5, 1.0],
        'reg_alpha': [0.0, 0.01, 0.1, 0.5, 1.0],
        'reg_lambda': [0.5, 1.0, 2.0, 5.0]
    }
    
    # 2. Base Estimator
    base_xgb = XGBClassifier(
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=random_state,
        n_jobs=-1
    )
    
    # 3. Stratified 5-Fold Cross Validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    
    print(f"\nStarting RandomizedSearchCV ({n_iter} iterations across 5 folds = {n_iter * 5} total fits)...")
    print("Optimization Metric: PR-AUC (average_precision)")
    
    random_search = RandomizedSearchCV(
        estimator=base_xgb,
        param_distributions=param_distributions,
        n_iter=n_iter,
        scoring='average_precision',
        cv=cv,
        verbose=1,
        random_state=random_state,
        n_jobs=-1
    )
    
    # 4. Run Search
    random_search.fit(X_train, y_train)
    
    best_params = random_search.best_params_
    best_cv_score = random_search.best_score_
    print(f"\n[OK] Hyperparameter search complete!")
    print(f"Best Cross-Validation PR-AUC: {best_cv_score:.4f}")
    print("\nBest Hyperparameters:")
    for param, value in best_params.items():
        print(f"  - {param}: {value}")
        
    # 5. Evaluate Best Model on Validation Split
    best_model = random_search.best_estimator_
    y_val_pred = best_model.predict(X_val)
    y_val_proba = best_model.predict_proba(X_val)[:, 1]
    
    roc_auc = roc_auc_score(y_val, y_val_proba)
    pr_auc = average_precision_score(y_val, y_val_proba)
    precision = precision_score(y_val, y_val_pred, zero_division=0)
    recall = recall_score(y_val, y_val_pred, zero_division=0)
    f1 = f1_score(y_val, y_val_pred, zero_division=0)
    cm = confusion_matrix(y_val, y_val_pred)
    
    print("\n" + "=" * 55)
    print("   VALIDATION SET EVALUATION (TUNED XGBOOST CHAMPION)  ")
    print("=" * 55)
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
    
    # 6. Save Best Model
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump(best_model, model_output_path)
    print(f"\n[OK] Tuned model champion saved to: {model_output_path}")

if __name__ == "__main__":
    TRAIN_PATH = os.path.join("data", "processed", "train.csv")
    VAL_PATH = os.path.join("data", "processed", "val.csv")
    MODEL_PATH = os.path.join("models", "best_xgboost_model.joblib")
    
    tune_xgboost(TRAIN_PATH, VAL_PATH, MODEL_PATH)
