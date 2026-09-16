import os
import pandas as pd
from sklearn.model_selection import train_test_split

def stratified_split(
    input_path: str, 
    output_dir: str, 
    target_col: str = "DEFECT_LABEL",
    train_size: float = 0.70,
    val_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42
) -> None:
    """
    Splits dataset into stratified Train (70%), Validation (15%), and Test (15%) sets.
    """
    assert round(train_size + val_size + test_size, 2) == 1.0, "Split sizes must sum to 1.0"
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input dataset not found at: {input_path}")
        
    df = pd.read_csv(input_path)
    print(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Check target column
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset")
        
    # Step 1: Split into Train (70%) and Temp (30%)
    temp_size = val_size + test_size
    train_df, temp_df = train_test_split(
        df,
        test_size=temp_size,
        stratify=df[target_col],
        random_state=random_state
    )
    
    # Step 2: Split Temp (30%) equally into Validation (15%) and Test (15%)
    val_ratio_of_temp = val_size / temp_size  # 0.15 / 0.30 = 0.50
    val_df, test_df = train_test_split(
        temp_df,
        test_size=(1.0 - val_ratio_of_temp),
        stratify=temp_df[target_col],
        random_state=random_state
    )
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save splits
    train_path = os.path.join(output_dir, "train.csv")
    val_path = os.path.join(output_dir, "val.csv")
    test_path = os.path.join(output_dir, "test.csv")
    
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    print("\n[OK] Stratified split completed successfully!")
    print(f"  - Train set:      {train_df.shape[0]} rows ({train_df.shape[0]/len(df):.1%}) | Defect rate: {train_df[target_col].mean():.2%}")
    print(f"  - Validation set: {val_df.shape[0]} rows ({val_df.shape[0]/len(df):.1%}) | Defect rate: {val_df[target_col].mean():.2%}")
    print(f"  - Test set:       {test_df.shape[0]} rows ({test_df.shape[0]/len(df):.1%}) | Defect rate: {test_df[target_col].mean():.2%}")

if __name__ == "__main__":
    ENGINEERED_DATA_PATH = os.path.join("data", "processed", "engineered_dataset.csv")
    OUTPUT_DIR = os.path.join("data", "processed")
    
    stratified_split(ENGINEERED_DATA_PATH, OUTPUT_DIR)
