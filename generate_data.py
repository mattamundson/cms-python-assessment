import pandas as pd
import numpy as np
import os

def generate_practice_data():
    """Generates a synthetic Medicare Inpatient dataset."""
    np.random.seed(42)
    n_rows = 100
    
    data = {
        'provider_id': [f"{i:06d}" for i in np.random.randint(100000, 999999, n_rows)],
        'provider_name': [f"Hospital {chr(65 + (i % 26))}" for i in range(n_rows)],
        'provider_state': np.random.choice(['NY', 'CA', 'TX', 'FL', 'IL', 'MN'], n_rows),
        'drg_definition': np.random.choice([
            '039 - EXTRACRANIAL PROCEDURES W/O CC/MCC',
            '190 - CHRONIC OBSTRUCTIVE PULMONARY DISEASE W MCC',
            '291 - HEART FAILURE & SHOCK W MCC',
            '392 - ESOPHAGITIS, GASTROENT & MISC DIGEST DISORDERS W/O MCC'
        ], n_rows),
        'total_discharges': np.random.randint(10, 500, n_rows),
        'average_submitted_charges': np.random.uniform(10000, 50000, n_rows).round(2),
        'average_medicare_payments': np.random.uniform(5000, 15000, n_rows).round(2)
    }
    
    # Introduce some "dirty" data for cleaning practice
    df = pd.DataFrame(data)
    df.loc[0, 'average_submitted_charges'] = "$55,000.00"  # String format
    df.loc[5, 'total_discharges'] = np.nan               # Missing value
    df.loc[10, 'provider_state'] = 'Minnesota'           # Non-standardized
    
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/medicare_practice.csv', index=False)
    print("Practice data generated at data/medicare_practice.csv")

if __name__ == "__main__":
    generate_practice_data()
