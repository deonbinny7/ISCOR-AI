import pandas as pd
import numpy as np

def map_gender(val):
    if pd.isna(val): return np.nan
    val_str = str(val).lower()
    if 'female' in val_str: return 1
    elif 'male' in val_str: return 0
    else: return 2

def harmonize_primary(df):
    df_out = pd.DataFrame()
    df_out['Age'] = df['Age']
    df_out['Gender'] = df['Gender'].apply(map_gender)
    # Map Sleep_Quality to estimated Sleep_Hours
    sleep_map = {'Poor': 4.0, 'Average': 6.5, 'Good': 8.5}
    df_out['Sleep_Hours'] = df['Sleep_Quality'].map(sleep_map)
    # Proxy Academic Pressure (1-5) using Stress_Level or Semester_Credit_Load
    # We will use Stress_Level (0-5) mapped to 1-5
    df_out['Academic_Pressure'] = df['Stress_Level'].clip(1, 5)
    df_out['Financial_Stress'] = df['Financial_Stress'].clip(1, 5)
    
    soc_map = {'Low': 1, 'Moderate': 3, 'High': 5}
    df_out['Social_Support'] = df['Social_Support'].map(soc_map)
    
    # Proxy Study Hours using Semester Credit Load (~1.5 hours per credit)
    df_out['Study_Hours'] = df['Semester_Credit_Load'] * 1.5
    
    pa_map = {'Low': 2.0, 'Moderate': 5.0, 'High': 10.0}
    df_out['Physical_Activity'] = df['Physical_Activity'].map(pa_map)
    
    df_out['Family_History'] = df['Family_History'].map({'Yes': 1, 'No': 0}).fillna(0)
    
    return df_out

def harmonize_gen1(df):
    df_out = pd.DataFrame()
    df_out['Age'] = df['Age']
    df_out['Gender'] = df['Gender'].apply(map_gender)
    
    sleep_map = {'Less than 5 hours': 4.0, '5-6 hours': 5.5, '7-8 hours': 7.5, 'More than 8 hours': 9.0}
    df_out['Sleep_Hours'] = df['Sleep Duration'].map(sleep_map)
    df_out['Academic_Pressure'] = df['Academic Pressure']
    df_out['Financial_Stress'] = df['Financial Stress']
    
    # Social Support not directly present - will be imputed later or set to median 3
    df_out['Social_Support'] = 3 
    
    df_out['Study_Hours'] = df['Study Hours']
    # Physical Activity not directly present - will be imputed later or set to median 5
    df_out['Physical_Activity'] = 5.0
    
    df_out['Family_History'] = df['Family History of Mental Illness'].map({'Yes': 1, 'No': 0}).fillna(0)
    
    # Add proxy target for evaluation
    df_out['Target'] = df['Depression'].map({'Yes': 2, 'No': 0}).fillna(0)
    
    return df_out

def harmonize_gen2(df):
    df_out = pd.DataFrame()
    df_out['Age'] = df['age']
    df_out['Gender'] = df['gender'].apply(map_gender)
    df_out['Sleep_Hours'] = df['sleep_hours']
    
    ap_map = {'Low': 1, 'Medium': 3, 'High': 5}
    # Check if academic_pressure is string or numeric
    if df['academic_pressure'].dtype == 'O':
        df_out['Academic_Pressure'] = df['academic_pressure'].map(ap_map).fillna(3)
    else:
        df_out['Academic_Pressure'] = df['academic_pressure'].clip(1, 5)
        
    df_out['Financial_Stress'] = 3 # Impute median
    df_out['Social_Support'] = 3 # Impute median
    df_out['Study_Hours'] = df['study_hours']
    
    df_out['Physical_Activity'] = df['physical_activity'].map({'Yes': 5.0, 'No': 0.0}).fillna(0.0)
    df_out['Family_History'] = 0 # Impute median
    
    # Add proxy target for evaluation
    target_map = {'Low': 0, 'Medium': 1, 'High': 2}
    df_out['Target'] = df['stress_level'].map(target_map).fillna(0)
    
    return df_out

def process_and_save_all():
    print("Loading datasets...")
    primary_df = pd.read_csv('datasets/archive (30)/students_mental_health_survey.csv')
    gen1_df = pd.read_csv('datasets/archive (29)/Depression Student Dataset.csv')
    gen2_df = pd.read_csv('datasets/archive (28)/student_stress_sleep_screen.csv')
    
    print("Harmonizing datasets...")
    primary_harm = harmonize_primary(primary_df)
    gen1_harm = harmonize_gen1(gen1_df)
    gen2_harm = harmonize_gen2(gen2_df)
    
    # Let's save the RAW (unscaled) harmonized versions for Generalization 1 and 2
    # because the action plan says "keep them completely untouched otherwise"
    gen1_harm.to_csv('datasets/gen_test_1.csv', index=False)
    gen2_harm.to_csv('datasets/gen_test_2.csv', index=False)
    print("Saved gen_test_1.csv and gen_test_2.csv")
    
    # We return the primary to the next pipeline step
    return primary_df, primary_harm

if __name__ == '__main__':
    process_and_save_all()
