import pandas as pd
import numpy as np
import pickle
import os

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, make_scorer, f1_score


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build composite features from z-scored base features.

    ALL input columns must already be z-score normalised (mean ≈ 0, std ≈ 1)
    before this function is called.  The training CSV
    (``datasets/primary_dataset_clean.csv``) is stored pre-normalised, and
    ``integration/service.py::normalize_answers`` z-scores live user input
    using the same training-set statistics before arriving here.

    Expected columns and their z-scored source scales (raw → z-scored):
      - ``Academic_Pressure`` : 1–5 ordinal  → z-scored, std ≈ 1
      - ``Financial_Stress``  : 1–5 ordinal  → z-scored, std ≈ 1
      - ``Social_Support``    : 1/3/5 ordinal → z-scored, std ≈ 1
      - ``Sleep_Hours``       : 4–8.5 raw hrs → z-scored, std ≈ 1
      - ``Study_Hours``       : 0–≥30 raw hrs → z-scored, std ≈ 1
      - ``Physical_Activity`` : 0–10 raw hrs  → z-scored, std ≈ 1

    Because every term is on the same z-score scale the composites are formed
    as direct linear sums — no further rescaling is needed or correct.
    Direction conventions (all "higher = more risk / load"):

      Stress_Index   = Academic_Pressure + Financial_Stress − Sleep_Hours
          (Sleep is *subtracted*: a z-score above the mean means more sleep,
          which lowers stress — negation captures the correct direction.)

      Lifestyle_Score = Physical_Activity + Sleep_Hours + Social_Support
          (All protective factors; higher composite = healthier lifestyle.)

      Academic_Load  = Study_Hours + Academic_Pressure
          (Both push in the same direction; higher = heavier academic burden.)
    """
    df = df.copy()

    # Each term is already on a comparable z-score scale (mean≈0, std≈1).
    # Stress_Index: higher AP or FS raises it; more sleep (higher z) lowers it.
    df["Stress_Index"] = (
        df["Academic_Pressure"] + df["Financial_Stress"] - df["Sleep_Hours"]
    )

    # Lifestyle_Score: more physical activity, more sleep, stronger social
    # support each independently lower mental-health risk.
    df["Lifestyle_Score"] = (
        df["Physical_Activity"] + df["Sleep_Hours"] + df["Social_Support"]
    )

    # Academic_Load: heavier study schedule and higher academic pressure
    # compound the cognitive burden.
    df["Academic_Load"] = df["Study_Hours"] + df["Academic_Pressure"]

    return df

def run_pipeline():
    os.makedirs('models', exist_ok=True)
    
    print("Loading data...")
    df = pd.read_csv('datasets/primary_dataset_clean.csv')
    df = engineer_features(df)
    
    # Encode target
    label_map = {'Low': 0, 'Moderate': 1, 'High': 2}
    df['Target'] = df['Risk_Category'].map(label_map)
    
    # Features
    X = df.drop(columns=['Risk_Category', 'Target'])
    y = df['Target']
    
    # Base features for ablation
    base_features = [col for col in X.columns if col not in ['Stress_Index', 'Lifestyle_Score', 'Academic_Load']]
    X_base = X[base_features]
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    
    # Cross-validation strategy
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    print("Evaluating Baseline Models...")
    models = {
        'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42),
        'RandomForest': RandomForestClassifier(random_state=42),
        'XGBoost': XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42),
        'LightGBM': LGBMClassifier(random_state=42, verbose=-1)
    }
    
    scorer = make_scorer(f1_score, average='macro')
    
    best_score = 0
    best_model_name = ""
    
    for name, model in models.items():
        scores = cross_val_score(model, X_train, y_train, cv=cv, scoring=scorer)
        mean_score = np.mean(scores)
        print(f"{name} Macro F1: {mean_score:.4f}")
        if mean_score > best_score:
            best_score = mean_score
            best_model_name = name
            
    print(f"\nBest Model: {best_model_name} (Macro F1: {best_score:.4f})")
    
    # Hyperparameter tuning the best model (using LightGBM as example if it wins, or XGBoost)
    print("Tuning Best Model...")
    
    final_model = models[best_model_name]
    
    if best_model_name == 'LightGBM':
        param_grid = {
            'n_estimators': [50, 100, 200],
            'learning_rate': [0.01, 0.1, 0.2],
            'max_depth': [3, 5, 7]
        }
    elif best_model_name == 'XGBoost':
        param_grid = {
            'n_estimators': [50, 100, 200],
            'learning_rate': [0.01, 0.1, 0.2],
            'max_depth': [3, 5, 7]
        }
    elif best_model_name == 'RandomForest':
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [None, 5, 10]
        }
    else:
        param_grid = {'C': [0.1, 1, 10]}
        
    grid = GridSearchCV(final_model, param_grid, cv=cv, scoring=scorer, n_jobs=-1)
    grid.fit(X_train, y_train)
    
    best_estimator = grid.best_estimator_
    print(f"Best parameters: {grid.best_params_}")
    
    # Ablation Study
    print("\nRunning Ablation Study (without composite features)...")
    grid_base = GridSearchCV(models[best_model_name], param_grid, cv=cv, scoring=scorer, n_jobs=-1)
    grid_base.fit(X_train[base_features], y_train)
    
    print(f"Macro F1 WITH composite features: {grid.best_score_:.4f}")
    print(f"Macro F1 WITHOUT composite features: {grid_base.best_score_:.4f}")
    
    # Retrain on full train and save
    best_estimator.fit(X_train, y_train)
    
    with open('models/final_model.pkl', 'wb') as f:
        pickle.dump(best_estimator, f)
        
    print("Model saved to models/final_model.pkl")
    
    print("\nRunning Fairness Audit...")
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, "evaluation/fairness_audit.py"])
    except subprocess.CalledProcessError:
        print("Modeling pipeline aborted: Fairness audit failed. Check the bounds!")
        sys.exit(1)
        
    print("\nRunning Generalization Tests...")
    try:
        subprocess.check_call([sys.executable, "evaluation/generalization_test.py"])
    except subprocess.CalledProcessError:
        print("Modeling pipeline aborted: Generalization test failed.")
        sys.exit(1)
    
if __name__ == '__main__':
    run_pipeline()
