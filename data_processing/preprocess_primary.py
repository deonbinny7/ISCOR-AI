import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from schema_mapper import process_and_save_all
from dass21_logic import calculate_dass21_scores


def _reference_risk_proportions():
    dass = calculate_dass21_scores('datasets/Data ERS_DASS 21.xlsx')

    def tier_probs(severity_col):
        proportions = dass[severity_col].value_counts(normalize=True)
        return {
            'low': float(proportions.get('Normal', 0.0) + proportions.get('Mild', 0.0)),
            'moderate': float(proportions.get('Moderate', 0.0)),
            'high': float(proportions.get('Severe', 0.0) + proportions.get('Extremely Severe', 0.0)),
        }

    return {
        'Depression_Score': tier_probs('Depression_Severity'),
        'Anxiety_Score': tier_probs('Anxiety_Severity'),
        'Stress_Level': tier_probs('Stress_Severity'),
    }


def _map_to_risk_tier(series: pd.Series, proportions: dict) -> pd.Series:
    counts = series.value_counts(normalize=True).sort_index()
    cumulative = counts.cumsum()
    low_target = proportions['low']
    moderate_target = proportions['low'] + proportions['moderate']

    low_cutoff = counts.index[0]
    moderate_cutoff = counts.index[-1]

    low_candidates = cumulative[cumulative <= low_target]
    if len(low_candidates):
        low_cutoff = low_candidates.index.max()

    moderate_candidates = cumulative[cumulative <= moderate_target]
    if len(moderate_candidates):
        moderate_cutoff = moderate_candidates.index.max()
    else:
        moderate_cutoff = low_cutoff

    def assign_risk(value):
        if pd.isna(value):
            return 'Low'
        if value <= low_cutoff:
            return 'Low'
        if value <= moderate_cutoff:
            return 'Moderate'
        return 'High'

    return series.apply(assign_risk)


def derive_target_label(df_raw):
    """
    Derives a 3-tier Risk_Category from the 0-5 proxy scores in the primary dataset.
    Uses the DASS-21 reference dataset to align categories by relative proportions.
    """
    proportions = _reference_risk_proportions()
    dep = _map_to_risk_tier(df_raw['Depression_Score'], proportions['Depression_Score'])
    anx = _map_to_risk_tier(df_raw['Anxiety_Score'], proportions['Anxiety_Score'])
    stress = _map_to_risk_tier(df_raw['Stress_Level'], proportions['Stress_Level'])

    def max_risk(row):
        risks = [row['dep'], row['anx'], row['stress']]
        if 'High' in risks:
            return 'High'
        if 'Moderate' in risks:
            return 'Moderate'
        return 'Low'

    temp_df = pd.DataFrame({'dep': dep, 'anx': anx, 'stress': stress})
    return temp_df.apply(max_risk, axis=1)

def preprocess_primary():
    # 1. Run schema mapper to get harmonized primary features
    raw_primary, harm_primary = process_and_save_all()
    
    # 2. Derive target labels from raw primary
    target_labels = derive_target_label(raw_primary)
    
    # 3. Add target to the harmonized dataframe
    harm_primary['Risk_Category'] = target_labels
    
    # 4. Impute missing values (median for numeric)
    # The unified schema is entirely numeric/encoded now
    for col in harm_primary.columns:
        if col != 'Risk_Category':
            harm_primary[col] = harm_primary[col].fillna(harm_primary[col].median())
            
    # 5. Scaling
    # We apply StandardScaler to numeric features.
    scaler = StandardScaler()
    features_to_scale = ['Age', 'Sleep_Hours', 'Academic_Pressure', 'Financial_Stress', 
                         'Social_Support', 'Study_Hours', 'Physical_Activity']
    
    harm_primary[features_to_scale] = scaler.fit_transform(harm_primary[features_to_scale])
    
    # 6. Save clean primary dataset
    harm_primary.to_csv('datasets/primary_dataset_clean.csv', index=False)
    print("Saved primary_dataset_clean.csv")
    
if __name__ == '__main__':
    preprocess_primary()
