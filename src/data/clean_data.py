import os
import pandas as pd
import numpy as np

def validate_data(df: pd.DataFrame) -> None:
    """
    Performs assertions to validate schema, types, and value boundaries.
    """
    print("Running data validation checks...")
    
    # 1. Check for expected columns
    expected_cols = [
        'LOC', 'CYCLO', 'LENGTH', 'VOLUME', 'DIFFICULTY', 
        'INT_FAN_IN', 'INT_FAN_OUT', 'NUM_OPERATORS', 
        'NUM_OPERANDS', 'BRANCH_COUNT', 'DEFECT_LABEL'
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing required column: {col}"
        
    # 2. Check for target label validity
    unique_labels = df['DEFECT_LABEL'].unique()
    assert set(unique_labels).issubset({0, 1}), f"Invalid target labels found: {unique_labels}"
    
    # 3. Check for boundary conditions (e.g. LOC and complexities must be non-negative)
    non_negative_cols = ['LOC', 'CYCLO', 'LENGTH', 'VOLUME', 'DIFFICULTY', 'BRANCH_COUNT']
    for col in non_negative_cols:
        min_val = df[col].min()
        assert min_val >= 0, f"Column {col} has negative values: {min_val}"
        
    print("OK: All validation checks passed successfully!")

def clean_dataset(input_path: str, output_path: str) -> None:
    """
    Loads raw data, cleans anomalies/duplicates, validates, and saves processed data.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Raw data file not found at: {input_path}")
        
    print(f"Loading raw data from: {input_path}")
    df = pd.read_csv(input_path)
    initial_shape = df.shape
    print(f"Initial shape: {initial_shape}")
    
    # 1. Handle Missing Values
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        print(f"Found missing values:\n{null_counts[null_counts > 0]}")
        df = df.dropna()
        print(f"Dropped rows with missing values. New shape: {df.shape}")
    else:
        print("No missing values detected.")
        
    # 2. Handle Duplicate Rows (Crucial to prevent data leakage)
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        print(f"Found {duplicate_count} duplicate rows. Removing duplicates...")
        df = df.drop_duplicates()
        print(f"Removed duplicates. New shape: {df.shape}")
    else:
        print("No duplicate rows detected.")
        
    # 3. Validate before saving
    validate_data(df)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save cleaned data
    df.to_csv(output_path, index=False)
    print(f"Cleaned dataset successfully saved to: {output_path}")
    print(f"Removed {initial_shape[0] - df.shape[0]} rows in total during cleaning.")

if __name__ == "__main__":
    # Define relative paths from the project root
    RAW_DATA_PATH = os.path.join("data", "raw", "SoftwareDefectDataset.csv")
    PROCESSED_DATA_PATH = os.path.join("data", "processed", "cleaned_dataset.csv")
    
    clean_dataset(RAW_DATA_PATH, PROCESSED_DATA_PATH)
