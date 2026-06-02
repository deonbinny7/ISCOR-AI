import pandas as pd
import numpy as np

def calculate_dass21_scores(filepath):
    """
    Reads the DASS-21 Excel file, extracts the 21 items,
    calculates Depression, Anxiety, and Stress scores, and
    maps them to severity bands.
    """
    df = pd.read_excel(filepath, sheet_name='DASS ALL')
    
    # Standard DASS-21 Item mappings (1-indexed based on column names)
    # The dataset uses ITEM 1 to ITEM 21. Values are typically 0 to 3.
    # Note: DASS-21 scores are multiplied by 2 to map to DASS-42 severity cutoffs.
    
    depression_items = ['ITEM 3', 'ITEM 5', 'ITEM 10', 'ITEM 13', 'ITEM 16', 'ITEM 17', 'ITEM 21']
    anxiety_items = ['ITEM 2', 'ITEM 4', 'ITEM 7', 'ITEM 9', 'ITEM 15', 'ITEM 19', 'ITEM 20']
    stress_items = ['ITEM 1', 'ITEM 6', 'ITEM 8', 'ITEM 11', 'ITEM 12', 'ITEM 14', 'ITEM 18']
    
    # Convert item columns to numeric in case they are parsed as objects
    for col in depression_items + anxiety_items + stress_items:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Calculate sum and multiply by 2 for severity comparison
    df['Depression_Score'] = df[depression_items].sum(axis=1) * 2
    df['Anxiety_Score'] = df[anxiety_items].sum(axis=1) * 2
    df['Stress_Score'] = df[stress_items].sum(axis=1) * 2
    
    # DASS-42 Severity Cutoffs
    # Depression: Normal (0-9), Mild (10-13), Moderate (14-20), Severe (21-27), Extremely Severe (28+)
    # Anxiety: Normal (0-7), Mild (8-9), Moderate (10-14), Severe (15-19), Extremely Severe (20+)
    # Stress: Normal (0-14), Mild (15-18), Moderate (19-25), Severe (26-33), Extremely Severe (34+)
    
    def map_severity(score, cutoffs):
        if score <= cutoffs[0]: return 'Normal'
        elif score <= cutoffs[1]: return 'Mild'
        elif score <= cutoffs[2]: return 'Moderate'
        elif score <= cutoffs[3]: return 'Severe'
        else: return 'Extremely Severe'
        
    df['Depression_Severity'] = df['Depression_Score'].apply(lambda x: map_severity(x, [9, 13, 20, 27]))
    df['Anxiety_Severity'] = df['Anxiety_Score'].apply(lambda x: map_severity(x, [7, 9, 14, 19]))
    df['Stress_Severity'] = df['Stress_Score'].apply(lambda x: map_severity(x, [14, 18, 25, 33]))
    
    # Map to ISCOR AI 3-tier system: Low, Moderate, High
    # Low: Normal, Mild
    # Moderate: Moderate
    # High: Severe, Extremely Severe
    
    def map_3tier(severity):
        if severity in ['Normal', 'Mild']: return 'Low'
        elif severity == 'Moderate': return 'Moderate'
        else: return 'High'
        
    df['Depression_Risk'] = df['Depression_Severity'].apply(map_3tier)
    df['Anxiety_Risk'] = df['Anxiety_Severity'].apply(map_3tier)
    df['Stress_Risk'] = df['Stress_Severity'].apply(map_3tier)
    
    # Overall Risk: Maximum risk across the three subscales
    def overall_risk(row):
        risks = [row['Depression_Risk'], row['Anxiety_Risk'], row['Stress_Risk']]
        if 'High' in risks: return 'High'
        elif 'Moderate' in risks: return 'Moderate'
        else: return 'Low'
        
    df['Overall_Risk'] = df.apply(overall_risk, axis=1)
    
    return df

if __name__ == "__main__":
    df = calculate_dass21_scores('datasets/Data ERS_DASS 21.xlsx')
    print("DASS-21 Processing Complete. Sample Output:")
    print(df[['Depression_Score', 'Anxiety_Score', 'Stress_Score', 'Overall_Risk']].head())
    print("\nOverall Risk Distribution:")
    print(df['Overall_Risk'].value_counts())
