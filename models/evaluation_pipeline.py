import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap
from sklearn.base import clone
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    brier_score_loss,
    f1_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
)
from sklearn.calibration import calibration_curve
from fairlearn.metrics import (
    demographic_parity_difference,
    equalized_odds_difference,
    true_positive_rate_difference,
)

from modeling_pipeline import engineer_features


REPORT_DIR = Path("reports")
FIGURE_DIR = REPORT_DIR / "figures"


def ensure_report_dirs():
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_model(model, X, y, dataset_name, out_file, save_primary_plots=False):
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)
    
    out_file.write(f"### {dataset_name}\\n")
    out_file.write("```\\n")
    out_file.write(classification_report(y, y_pred, labels=[0, 1, 2], target_names=['Low', 'Moderate', 'High'], zero_division=0))
    out_file.write("\\n```\\n")
    
    # Compute ROC AUC OvR
    try:
        roc_auc = roc_auc_score(y, y_proba, multi_class='ovr', average='macro')
        out_file.write(f"- **Macro ROC-AUC:** {roc_auc:.4f}\\n")
    except ValueError:
        pass
        
    # Calibration check (Brier score for the High Risk class)
    # y=2 is High Risk
    y_high = (y == 2).astype(int)
    prob_high = y_proba[:, 2]
    brier = brier_score_loss(y_high, prob_high)
    out_file.write(f"- **Brier Score (High Risk Calibration):** {brier:.4f} (Lower is better)\\n\\n")

    if save_primary_plots:
        cm = confusion_matrix(y, y_pred, labels=[0, 1, 2])
        disp = ConfusionMatrixDisplay(cm, display_labels=["Low", "Moderate", "High"])
        disp.plot(cmap="Purples", values_format="d")
        plt.title("Primary Test Confusion Matrix")
        plt.tight_layout()
        cm_path = FIGURE_DIR / "primary_confusion_matrix.png"
        plt.savefig(cm_path, dpi=160)
        plt.close()

        fraction_pos, mean_pred = calibration_curve(y_high, prob_high, n_bins=10, strategy="uniform")
        plt.figure(figsize=(7, 5))
        plt.plot(mean_pred, fraction_pos, marker="o", label="Model")
        plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect calibration")
        plt.xlabel("Mean predicted probability of High risk")
        plt.ylabel("Observed High-risk frequency")
        plt.title("Reliability Diagram: High Risk")
        plt.legend()
        plt.tight_layout()
        reliability_path = FIGURE_DIR / "high_risk_reliability_diagram.png"
        plt.savefig(reliability_path, dpi=160)
        plt.close()

        out_file.write("#### Saved primary evaluation figures\\n")
        out_file.write(f"- Confusion matrix: `{cm_path.as_posix()}`\\n")
        out_file.write(f"- Reliability diagram: `{reliability_path.as_posix()}`\\n\\n")

def run_fairness_audit(model, X, y, sensitive_features, out_file):
    y_pred = model.predict(X)
    
    # We will compute fairness metrics treating "High Risk" (2) as the positive class for the audit
    y_high = (y == 2).astype(int)
    y_pred_high = (y_pred == 2).astype(int)

    selection_rates = {}
    for group in sorted(pd.Series(sensitive_features).dropna().unique()):
        mask = pd.Series(sensitive_features).reset_index(drop=True) == group
        selection_rates[str(group)] = float(y_pred_high[mask].mean()) if mask.any() else 0.0

    nonzero_rates = [rate for rate in selection_rates.values() if rate > 0]
    disparate_impact = 0.0
    if nonzero_rates:
        disparate_impact = min(nonzero_rates) / max(nonzero_rates)

    spd = demographic_parity_difference(y_high, y_pred_high, sensitive_features=sensitive_features)
    eod = true_positive_rate_difference(y_high, y_pred_high, sensitive_features=sensitive_features)
    eo_diff = equalized_odds_difference(y_high, y_pred_high, sensitive_features=sensitive_features)

    out_file.write("### Fairness Audit (Across Gender for High Risk Classification)\\n")
    out_file.write(f"- **Disparate Impact Ratio:** {disparate_impact:.4f} (Closer to 1 is fairer)\\n")
    out_file.write(f"- **Statistical Parity Difference:** {spd:.4f} (Closer to 0 is fairer)\\n")
    out_file.write(f"- **Equal Opportunity Difference:** {eod:.4f} (Closer to 0 is fairer)\\n")
    out_file.write(f"- **Equalized Odds Difference:** {eo_diff:.4f} (Supplementary; closer to 0 is fairer)\\n")
    out_file.write(f"- **High-risk selection rates by encoded gender:** {selection_rates}\\n")
    out_file.write("\\n> Note: Gender is encoded as Male=0, Female=1, Other=2 in the harmonized schema.\\n\\n")


def run_ablation(model, X_train, X_test, y_train, y_test, out_file):
    base_features = [
        col for col in X_train.columns
        if col not in ["Stress_Index", "Lifestyle_Score", "Academic_Load"]
    ]

    with_composites = clone(model)
    with_composites.fit(X_train, y_train)
    pred_with = with_composites.predict(X_test)
    f1_with = f1_score(y_test, pred_with, average="macro")

    without_composites = clone(model)
    without_composites.fit(X_train[base_features], y_train)
    pred_without = without_composites.predict(X_test[base_features])
    f1_without = f1_score(y_test, pred_without, average="macro")

    out_file.write("## 4. Feature Engineering Ablation\\n")
    out_file.write("| Feature set | Test Macro F1 | Delta vs. baseline |\\n")
    out_file.write("|---|---:|---:|\\n")
    out_file.write(f"| Base features only | {f1_without:.4f} | 0.0000 |\\n")
    out_file.write(f"| Base + composite features | {f1_with:.4f} | {f1_with - f1_without:+.4f} |\\n\\n")


def run_shap_stability(model, X, y, out_file):
    from sklearn.model_selection import StratifiedKFold

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    top_sets = []
    top_first = []

    sample_size = min(120, len(X))
    X_for_summary = X.sample(sample_size, random_state=42)

    for fold, (train_idx, _) in enumerate(cv.split(X, y), start=1):
        fold_model = clone(model)
        X_train = X.iloc[train_idx]
        y_train = y.iloc[train_idx]
        fold_model.fit(X_train, y_train)

        X_fold_sample = X_train.sample(min(80, len(X_train)), random_state=fold)
        explainer = shap.TreeExplainer(fold_model)
        shap_values = explainer.shap_values(X_fold_sample)
        high_class_shap = shap_values[2] if isinstance(shap_values, list) else shap_values[:, :, 2]
        mean_abs = np.abs(high_class_shap).mean(axis=0)
        ordered_idx = np.argsort(mean_abs)[::-1]
        ordered_features = list(X.columns[ordered_idx])
        top_sets.append(set(ordered_features[:3]))
        top_first.append(ordered_features[0])

    common_features = set.intersection(*top_sets)
    top_feature_match_rate = max(top_first.count(feature) for feature in set(top_first)) / len(top_first)
    pairwise_jaccards = []
    for i in range(len(top_sets)):
        for j in range(i + 1, len(top_sets)):
            pairwise_jaccards.append(len(top_sets[i] & top_sets[j]) / len(top_sets[i] | top_sets[j]))

    final_explainer = shap.TreeExplainer(model)
    final_shap_values = final_explainer.shap_values(X_for_summary)
    final_high_shap = final_shap_values[2] if isinstance(final_shap_values, list) else final_shap_values[:, :, 2]
    shap.summary_plot(final_high_shap, X_for_summary, show=False)
    plt.title("SHAP Summary Plot: High Risk")
    plt.tight_layout()
    summary_path = FIGURE_DIR / "shap_summary_high_risk.png"
    plt.savefig(summary_path, dpi=160, bbox_inches="tight")
    plt.close()

    stability_path = REPORT_DIR / "shap_stability_report.md"
    with open(stability_path, "w") as shap_file:
        shap_file.write("# SHAP Stability Report\\n\\n")
        shap_file.write("This check retrains the final estimator across five stratified folds and compares the top-3 SHAP features for the High-risk class.\\n\\n")
        for fold, features in enumerate(top_sets, start=1):
            shap_file.write(f"- Fold {fold}: {sorted(features)}\\n")
        shap_file.write("\\n")
        shap_file.write(f"- Consistently top-3 across all folds: {sorted(common_features)}\\n")
        shap_file.write(f"- Top-feature match rate: {top_feature_match_rate:.2%}\\n")
        shap_file.write(f"- Mean pairwise top-3 Jaccard overlap: {np.mean(pairwise_jaccards):.2%}\\n")
        shap_file.write(f"- Saved global summary plot: `{summary_path.as_posix()}`\\n")

    out_file.write("## 5. SHAP Stability\\n")
    out_file.write(f"- Top-feature match rate across folds: **{top_feature_match_rate:.2%}**\\n")
    out_file.write(f"- Mean pairwise top-3 Jaccard overlap: **{np.mean(pairwise_jaccards):.2%}**\\n")
    out_file.write(f"- Stability report: `{stability_path.as_posix()}`\\n")
    out_file.write(f"- Global SHAP summary plot: `{summary_path.as_posix()}`\\n\\n")

def run_evaluation():
    ensure_report_dirs()

    with open('models/final_model.pkl', 'rb') as f:
        model = pickle.load(f)
        
    # Load Primary Data
    df_primary = pd.read_csv('datasets/primary_dataset_clean.csv')
    df_primary = engineer_features(df_primary)
    
    label_map = {'Low': 0, 'Moderate': 1, 'High': 2}
    df_primary['Target'] = df_primary['Risk_Category'].map(label_map)
    
    X = df_primary.drop(columns=['Risk_Category', 'Target'])
    y = df_primary['Target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    
    with open('metrics_report.md', 'w') as f:
        f.write("# ISCOR AI: Model Metrics & Evaluation Report\\n\\n")
        
        f.write("## 1. Primary Dataset (Test Split)\\n")
        evaluate_model(model, X_test, y_test, "Primary Test Split", f, save_primary_plots=True)
        
        f.write("## 2. Fairness Audit\\n")
        run_fairness_audit(model, X_test, y_test, X_test['Gender'], f)
        
        f.write("## 3. Cross-Dataset Generalization\\n")
        # Load Gen 1
        df_gen1 = pd.read_csv('datasets/gen_test_1.csv')
        df_gen1 = engineer_features(df_gen1)
        y_gen1 = df_gen1['Target']
        X_gen1 = df_gen1.drop(columns=['Target'])
        # Handle columns mismatch or reorder to match X
        X_gen1 = X_gen1[X_test.columns]
        
        # Load Gen 2
        df_gen2 = pd.read_csv('datasets/gen_test_2.csv')
        df_gen2 = engineer_features(df_gen2)
        y_gen2 = df_gen2['Target']
        X_gen2 = df_gen2.drop(columns=['Target'])
        X_gen2 = X_gen2[X_test.columns]
        
        evaluate_model(model, X_gen1, y_gen1, "Generalization 1: Depression Dataset (Proxy Targets)", f)
        evaluate_model(model, X_gen2, y_gen2, "Generalization 2: Stress Dataset (Proxy Targets)", f)
        run_ablation(model, X_train, X_test, y_train, y_test, f)
        run_shap_stability(model, X, y, f)

    print("Metrics report generated at metrics_report.md")

if __name__ == '__main__':
    run_evaluation()
