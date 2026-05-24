import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def load_and_clean_data(file_path):
    """
    Loads Medicare data and performs rigorous cleaning.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found at {file_path}")
        
    print(f"Reading {file_path}...")
    df = pd.read_csv(file_path)
    
    # 1. Standardize Currency Columns
    # CMS data often uses strings with symbols ($) or commas
    currency_cols = ['average_submitted_charges', 'average_medicare_payments']
    for col in currency_cols:
        if df[col].dtype == 'object':
            df[col] = df[col].replace(r'[\$,]', '', regex=True)
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 2. Handle Missing Data
    # Filling missing discharges with the median to avoid skewing by outliers
    if df['total_discharges'].isnull().any():
        median_val = df['total_discharges'].median()
        df['total_discharges'] = df['total_discharges'].fillna(median_val)
    
    # 3. Standardize Categorical Data
    # Mapping full names to abbreviations for consistency in grouping
    state_map = {'Minnesota': 'MN', 'New York': 'NY', 'California': 'CA'}
    df['provider_state'] = df['provider_state'].replace(state_map)
    
    # 4. Feature Engineering
    # Calculate Markup Ratio: How much the hospital bills vs. what they receive
    df['markup_ratio'] = df['average_submitted_charges'] / df['average_medicare_payments']
    
    print(f"Data cleaned. Shape: {df.shape}")
    return df

def perform_analysis(df):
    """
    Performs key business logic analysis on CMS data.
    """
    print("\n--- Performing Analysis ---")
    
    # A. State-level Analysis
    state_summary = df.groupby('provider_state').agg({
        'markup_ratio': 'mean',
        'average_medicare_payments': 'sum',
        'total_discharges': 'sum'
    }).round(2).sort_values(by='markup_ratio', ascending=False)
    
    print("\nTop 5 States by Average Markup Ratio:")
    print(state_summary.head())
    
    # B. Outlier Detection (Z-Score)
    # Finding hospitals whose charges are > 2 standard deviations from the mean for their specific procedure (DRG)
    df['drg_mean'] = df.groupby('drg_definition')['average_submitted_charges'].transform('mean')
    df['drg_std'] = df.groupby('drg_definition')['average_submitted_charges'].transform('std')
    df['z_score'] = (df['average_submitted_charges'] - df['drg_mean']) / df['drg_std']
    
    outliers = df[df['z_score'] > 2][['provider_name', 'drg_definition', 'average_submitted_charges', 'z_score']]
    
    print(f"\nIdentified {len(outliers)} statistical outliers in billing.")
    return state_summary, outliers

def generate_report(state_summary, outliers):
    """
    Saves analysis results to the outputs folder.
    """
    os.makedirs('outputs', exist_ok=True)
    
    state_summary.to_csv('outputs/state_summary.csv')
    outliers.to_csv('outputs/billing_outliers.csv', index=False)
    
    # Simple Visual: Markup Ratio by State
    plt.figure(figsize=(10, 6))
    sns.barplot(x=state_summary.index, y=state_summary['markup_ratio'], palette='viridis')
    plt.title('Average Hospital Markup Ratio by State (Medicare)')
    plt.ylabel('Markup Ratio (Charges / Payments)')
    plt.savefig('outputs/markup_distribution.png')
    
    print("\nReports generated in the 'outputs/' directory.")

def main():
    """
    Execution pipeline for the CMS Assessment.
    """
    print("=== CMS Medicare Analysis Assessment Tool ===")
    
    try:
        # 1. Ingestion & Cleaning
        data_path = 'data/medicare_practice.csv'
        df = load_and_clean_data(data_path)
        
        # 2. Analysis
        state_summary, outliers = perform_analysis(df)
        
        # 3. Reporting
        generate_report(state_summary, outliers)
        
        print("\n=== Assessment Script Completed Successfully ===")
        
    except Exception as e:
        print(f"Error during execution: {e}")

if __name__ == "__main__":
    main()
