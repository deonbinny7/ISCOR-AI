import sys
import os
import pandas as pd
import sqlite3

sys.path.insert(0, 'integration')
sys.path.insert(0, 'models')
sys.path.insert(0, 'data_processing')

import service
from database import DB_PATH, persist_screening, init_db

def test_batch_fallback_rate_is_below_threshold():
    init_db()

    df = pd.read_csv('datasets/gen_test_1.csv')

    # Clear old SafetyEvents for clean test
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM SafetyEvents WHERE event_type = 'shap_fallback'")
        conn.commit()

    screened_ids = []
    for idx, row in df.head(60).iterrows():
        dummy_input = {
            'age': int(row['Age']),
            'gender': 'Male' if row['Gender'] == 0 else 'Female',
            'sleep_hours': float(row['Sleep_Hours']),
            'academic_pressure': int(row['Academic_Pressure']),
            'financial_stress': int(row['Financial_Stress']),
            'social_support': 'Moderate',
            'study_hours': float(row['Study_Hours']),
            'physical_activity': float(row['Physical_Activity']),
            'family_history': 'No' if row['Family_History'] == 0 else 'Yes'
        }
        
        report = service.assemble_report(dummy_input)
        ids = persist_screening(report)
        screened_ids.append(ids['screening_id'])

    # Check fallback rate
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        placeholders = ','.join('?' for _ in screened_ids)
        cur.execute(
            f"SELECT COUNT(*) FROM SafetyEvents WHERE event_type = 'shap_fallback' AND screening_id IN ({placeholders})",
            screened_ids
        )
        fallback_count = cur.fetchone()[0]

    rate = (fallback_count / len(screened_ids)) * 100
    print(f'Batch Size: {len(screened_ids)}')
    print(f'Fallback Count: {fallback_count}')
    print(f'Fallback Rate: {rate:.1f}%')
    assert rate < 5.0, f'Fallback rate {rate:.1f}% exceeds 5% threshold'

if __name__ == '__main__':
    test_batch_fallback_rate_is_below_threshold()
