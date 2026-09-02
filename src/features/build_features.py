import os
import pandas as pd
import numpy as np

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates new features from raw static metrics.
    Uses epsilon (1e-5) to prevent division-by-zero errors.
    """
    df = df.copy()
    eps = 1e-5
    
    print("Engineering new features...")
    
    # 1. Complexity Density: Cyclomatic complexity relative to lines of code
    df['COMPLEXITY_DENSITY'] = df['CYCLO'] / (df['LOC'] + eps)
    
    # 2. Operand density: Number of operands per line of code
    df['OPERAND_DENSITY'] = df['NUM_OPERANDS'] / (df['LOC'] + eps)
    
    # 3. Operator density: Number of operators per line of code
    df['OPERATOR_DENSITY'] = df['NUM_OPERATORS'] / (df['LOC'] + eps)
    
    # 4. Code Complexity Ratio: Cyclomatic complexity relative to total branching count
    df['COMPLEXITY_BRANCH_RATIO'] = df['CYCLO'] / (df['BRANCH_COUNT'] + eps)
    
    print("[OK] Feature engineering complete!")
    return df

def process_features(input_path: str, output_path: str) -> None:
    """
    Loads clean data, engineers features, and saves the engineered dataset.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Cleaned dataset not found at: {input_path}")
        
    df = pd.read_csv(input_path)
    print(f"Loaded dataset with shape: {df.shape}")
    
    # Apply feature engineering
    df_engineered = engineer_features(df)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save output
    df_engineered.to_csv(output_path, index=False)
    print(f"Engineered dataset saved to: {output_path}")
    print(f"New shape: {df_engineered.shape} (Added {df_engineered.shape[1] - df.shape[1]} features)")

if __name__ == "__main__":
    CLEANED_DATA_PATH = os.path.join("data", "processed", "cleaned_dataset.csv")
    ENGINEERED_DATA_PATH = os.path.join("data", "processed", "engineered_dataset.csv")
    
    process_features(CLEANED_DATA_PATH, ENGINEERED_DATA_PATH)
