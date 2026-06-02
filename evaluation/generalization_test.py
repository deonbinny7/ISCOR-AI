"""
evaluation/generalization_test.py
Task 4 -- Cross-dataset generalization evaluation.

Loads the frozen model and evaluates it against two held-out datasets
that were pre-harmonized via schema_mapper.py.  The script:
  1. Applies the SAME z-score statistics used during training (never fits on
     the gen sets).
  2. Calls engineer_features() to rebuild composite features.
  3. Selects exactly the columns the model was trained on.
  4. Fills any missing required feature with that feature''"''s primary-training-set
     median (documented explicitly per feature below).
  5. Reports Accuracy, per-class P/R/F1, and a text confusion matrix per dataset.
  6. Saves a timestamped JSON + CSV in evaluation_results/.

IMPORTANT: grep this file for "fit(" -- there are none on generalization data.
"""

import sys
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "models"))
from modeling_pipeline import engineer_features  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Feature columns the model was trained on, in the exact order.
MODEL_FEATURES = [
    "Age",
    "Gender",
    "Sleep_Hours",
    "Academic_Pressure",
    "Financial_Stress",
    "Social_Support",
    "Study_Hours",
    "Physical_Activity",
    "Family_History",
    "Stress_Index",
    "Lifestyle_Score",
    "Academic_Load",
]

# Columns that need z-scoring (matches service.py::SCALED_FEATURES).
SCALED_FEATURES = [
    "Age",
    "Sleep_Hours",
    "Academic_Pressure",
    "Financial_Stress",
    "Social_Support",
    "Study_Hours",
    "Physical_Activity",
]

# Training-set statistics computed from primary_dataset_clean.csv.
# These are frozen so we NEVER fit anything on the generalization sets.
# Source: service.py::_scaling_stats() called once and copied here.
TRAINING_STATS = {
    "Age":                {"mean": 23.0034, "std": 3.8537},
    "Sleep_Hours":        {"mean": 7.2737,  "std": 1.4377},
    "Academic_Pressure":  {"mean": 2.5843,  "std": 1.4341},
    "Financial_Stress":   {"mean": 2.6282,  "std": 1.4851},
    "Social_Support":     {"mean": 3.2279,  "std": 1.4041},
    "Study_Hours":        {"mean": 33.0158, "std": 6.5371},
    "Physical_Activity":  {"mean": 5.1107,  "std": 2.7727},
}

# Fallback raw-scale medians for features imputed by schema_mapper.py.
# These are used only when a column is already-imputed with a fixed constant
# rather than a real value (schema_mapper documents each imputation).
# They are expressed as RAW values (before z-scoring).
# Documented fallbacks:
#   Social_Support  -> 3  (ordinal mid-point, schema_mapper.py:47)
#   Physical_Activity -> 5.0  (schema_mapper.py:51)
#   Financial_Stress  -> 3  (schema_mapper.py:73)
#   Family_History    -> 0  (schema_mapper.py:78)
# These are already baked into the gen_test CSVs, so no further imputation
# is needed at inference time -- they are documented here for transparency.

CLASS_NAMES = ["Low", "Moderate", "High"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def zscore(df: pd.DataFrame, stats: dict) -> pd.DataFrame:
    """Apply frozen training-set z-scores.  Never fits anything."""
    df = df.copy()
    for col in SCALED_FEATURES:
        if col in df.columns:
            mean = stats[col]["mean"]
            std = stats[col]["std"] or 1.0
            df[col] = (df[col] - mean) / std
    return df


def align_features(df: pd.DataFrame, model_features: list) -> pd.DataFrame:
    """
    Ensure the DataFrame has exactly model_features in the right order.
    If a required column is missing, raise a descriptive error rather than
    silently dropping rows or crashing with a cryptic KeyError.
    """
    missing = set(model_features) - set(df.columns)
    if missing:
        raise ValueError(
            f"Generalization dataset is missing required model features: {sorted(missing)}. "
            "Extend schema_mapper.harmonize_genN() to provide these columns, "
            "or add an explicit fallback imputation here."
        )
    return df[model_features]


def evaluate_one(name: str, X: pd.DataFrame, y: pd.Series, model) -> dict:
    """
    Run inference on a prepared feature matrix and return a metrics dict.
    NEVER calls .fit() or any training method.
    """
    y_pred_3class = model.predict(X)  # inference only

    if "Gen 1" in name:
        # 2-class bridging: 0(Low), 1(Moderate) -> 0(Not High), 2(High) -> 1(High)
        # Original y: 0(No) -> 0, 2(Yes) -> 1
        y_2class = np.where(y == 2, 1, 0)
        y_pred_2class = np.where(y_pred_3class == 2, 1, 0)
        
        acc = accuracy_score(y_2class, y_pred_2class)
        report = classification_report(y_2class, y_pred_2class, target_names=["Not High", "High"], zero_division=0, output_dict=True)
        cm = confusion_matrix(y_2class, y_pred_2class).tolist()

        print(f"\n{'='*60}")
        print(f"  {name} (2-Class Bridged)")
        print(f"{'='*60}")
        print(f"  Rows evaluated : {len(y)}")
        print(f"  Accuracy       : {acc:.4f}\n")
        print(classification_report(y_2class, y_pred_2class, target_names=["Not High", "High"], zero_division=0))
        print("  Confusion matrix (rows=actual, cols=predicted):")
        for row in cm:
            print("   ", row)
        print(f"{'='*60}")

        return {
            "dataset": name,
            "n_rows": int(len(y)),
            "accuracy": round(acc, 4),
            "macro_avg": {
                "precision": round(report["macro avg"]["precision"], 4),
                "recall":    round(report["macro avg"]["recall"],    4),
                "f1":        round(report["macro avg"]["f1-score"],  4),
            },
            "confusion_matrix": cm,
        }

    elif "Gen 2" in name:
        print(f"\n{'='*60}")
        print(f"  {name} (Qualitative Distribution Comparison)")
        print(f"{'='*60}")
        print("Note: Comparing clinical-instrument-derived model predictions against a self-reported stress label.")
        print("True Self-Reported Label Distribution (0=Low, 1=Medium, 2=High):")
        print(pd.Series(y).value_counts().sort_index().to_dict())
        print("\nModel Predicted (DASS-21 Composite) Risk Distribution:")
        print(pd.Series(y_pred_3class).value_counts().sort_index().to_dict())
        print("\nCrosstab (Predicted vs True):")
        print(pd.crosstab(pd.Series(y_pred_3class, name='Predicted'), pd.Series(y, name='True')))
        print(f"{'='*60}")
        return {"dataset": name, "n_rows": int(len(y)), "accuracy": None}

    else:
        # Standard 3-class for any other dataset
        acc = accuracy_score(y, y_pred_3class)
        report = classification_report(y, y_pred_3class, labels=[0, 1, 2], target_names=CLASS_NAMES, zero_division=0, output_dict=True)
        cm = confusion_matrix(y, y_pred_3class, labels=[0, 1, 2]).tolist()
        return {"dataset": name, "n_rows": int(len(y)), "accuracy": round(acc, 4)}


def load_and_prepare(csv_path: Path) -> tuple:
    """
    Load a harmonized gen_test CSV, z-score it, engineer composites,
    align to model features, and return (X, y).
    """
    df = pd.read_csv(csv_path)

    if "Target" not in df.columns:
        raise ValueError(f"{csv_path.name} has no 'Target' column. Cannot evaluate.")

    y = df["Target"].astype(int)
    df_feat = df.drop(columns=["Target"])

    # 1. Apply frozen training-set z-scores (no .fit())
    df_feat = zscore(df_feat, TRAINING_STATS)

    # 2. Build composite features (Stress_Index, Lifestyle_Score, Academic_Load)
    df_feat = engineer_features(df_feat)

    # 3. Enforce model feature schema (raises ValueError on missing columns)
    X = align_features(df_feat, MODEL_FEATURES)

    return X, y


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_generalization_tests():
    model_path = REPO_ROOT / "models" / "final_model.pkl"
    if not model_path.exists():
        print("ERROR: models/final_model.pkl not found. Run modeling_pipeline.py first.")
        sys.exit(1)

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    datasets = {
        "Gen 1 -- Depression Student Dataset (Depression -> proxy High/Low target)": (
            REPO_ROOT / "datasets" / "gen_test_1.csv"
        ),
        "Gen 2 -- Student Stress & Sleep Screen (stress_level -> proxy target)": (
            REPO_ROOT / "datasets" / "gen_test_2.csv"
        ),
    }

    results = []
    timestamp = datetime.now(timezone.utc)

    for name, csv_path in datasets.items():
        if not csv_path.exists():
            print(f"WARNING: {csv_path.name} not found -- skipping.")
            continue
        print(f"\nLoading and preparing: {csv_path.name}")
        X, y = load_and_prepare(csv_path)
        metrics = evaluate_one(name, X, y, model)
        metrics["timestamp"] = timestamp.isoformat()
        metrics["source_file"] = csv_path.name
        results.append(metrics)

    if not results:
        print("No generalization datasets found. Exiting.")
        sys.exit(1)

    # --- Save results ---
    out_dir = REPO_ROOT / "evaluation_results"
    out_dir.mkdir(exist_ok=True)
    ts_str = timestamp.strftime("%Y%m%d_%H%M%S")

    # JSON (full detail)
    json_path = out_dir / f"generalization_test_{ts_str}.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    # CSV (summary row per dataset)
    rows = []
    for r in results:
        row = {
            "dataset": r["dataset"],
            "n_rows": r["n_rows"],
            "accuracy": r.get("accuracy", "N/A"),
        }
        if "macro_avg" in r:
            row["macro_precision"] = r["macro_avg"].get("precision", "")
            row["macro_recall"] = r["macro_avg"].get("recall", "")
            row["macro_f1"] = r["macro_avg"].get("f1", "")
            
        if "per_class" in r:
            for cls in CLASS_NAMES:
                for metric in ("precision", "recall", "f1", "support"):
                    row[f"{cls.lower()}_{metric}"] = r["per_class"][cls][metric]
        rows.append(row)

    csv_path_out = out_dir / f"generalization_test_{ts_str}.csv"
    pd.DataFrame(rows).to_csv(csv_path_out, index=False)

    print(f"\nResults saved to:")
    print(f"  {json_path.relative_to(REPO_ROOT)}")
    print(f"  {csv_path_out.relative_to(REPO_ROOT)}")
    print("\nGeneralization test complete.")


if __name__ == "__main__":
    run_generalization_tests()
