import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path
import pickle

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from fairlearn.metrics import (
    demographic_parity_difference,
    true_positive_rate_difference
)

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "models"))
from modeling_pipeline import engineer_features

def run_audit():
    model_path = REPO_ROOT / 'models' / 'final_model.pkl'
    data_path = REPO_ROOT / 'datasets' / 'primary_dataset_clean.csv'
    
    if not model_path.exists() or not data_path.exists():
        print("Model or data not found. Run modeling_pipeline.py first.")
        sys.exit(1)
        
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
        
    df = pd.read_csv(data_path)
    df = engineer_features(df)
    
    label_map = {'Low': 0, 'Moderate': 1, 'High': 2}
    df['Target'] = df['Risk_Category'].map(label_map)
    
    X = df.drop(columns=['Risk_Category', 'Target'])
    y = df['Target']
    
    # Must match the split in modeling_pipeline.py EXACTLY
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    
    sensitive_features = X_test['Gender']
    y_pred = model.predict(X_test)
    
    # For fairness, we assess the "High Risk" class as the positive outcome we care about
    y_high = (y_test == 2).astype(int)
    y_pred_high = (y_pred == 2).astype(int)
    
    selection_rates = {}
    groups = sorted(sensitive_features.dropna().unique())
    for group in groups:
        mask = (sensitive_features == group)
        selection_rates[str(group)] = float(y_pred_high[mask].mean()) if mask.any() else 0.0
        
    nonzero_rates = [rate for rate in selection_rates.values() if rate > 0]
    disparate_impact = min(nonzero_rates) / max(nonzero_rates) if nonzero_rates else 0.0
    
    spd = demographic_parity_difference(y_high, y_pred_high, sensitive_features=sensitive_features)
    eod = true_positive_rate_difference(y_high, y_pred_high, sensitive_features=sensitive_features)
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "disparate_impact": disparate_impact,
        "statistical_parity_difference": spd,
        "equal_opportunity_difference": eod,
        "selection_rates_by_gender": selection_rates
    }
    
    # Print Table
    print("\n" + "="*50)
    print(" FAIRNESS AUDIT RESULTS (Gender)")
    print("="*50)
    print(f"Disparate Impact Ratio:        {disparate_impact:.4f} (Ideal: ~1.0, Bounds: 0.8-1.25)")
    print(f"Statistical Parity Difference: {spd:.4f} (Ideal: ~0.0, Bounds: -0.1 to 0.1)")
    print(f"Equal Opportunity Difference:  {eod:.4f} (Ideal: ~0.0, Bounds: -0.1 to 0.1)")
    print("-" * 50)
    print(f"High-risk selection rates by encoded gender (0=Male, 1=Female, 2=Other):")
    for g, rate in selection_rates.items():
        print(f"  Gender {g}: {rate:.2%}")
    print("="*50 + "\n")
    
    # Save Results
    out_dir = REPO_ROOT / 'evaluation_results'
    out_dir.mkdir(exist_ok=True)
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"fairness_audit_{timestamp_str}.json"
    with open(out_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {out_file.relative_to(REPO_ROOT)}\n")
    
    # Bounds check
    failures = []
    if not (0.8 <= disparate_impact <= 1.25):
        failures.append(f"Disparate Impact Ratio ({disparate_impact:.4f}) is outside acceptable bounds (0.8 - 1.25).")
    if abs(spd) > 0.1:
        failures.append(f"Statistical Parity Difference ({spd:.4f}) exceeds the 0.1 threshold.")
    if abs(eod) > 0.1:
        failures.append(f"Equal Opportunity Difference ({eod:.4f}) exceeds the 0.1 threshold.")
        
    if failures:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!! FAIRNESS AUDIT FAILED")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        for fail in failures:
            print(f"!! {fail}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        sys.exit(1)
        
    print("Fairness audit passed successfully.\n")

if __name__ == '__main__':
    run_audit()
