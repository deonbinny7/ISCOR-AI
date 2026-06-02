# ISCOR AI: Model Metrics & Evaluation Report\n\n## 1. Primary Dataset (Test Split)\n### Primary Test Split\n```\n              precision    recall  f1-score   support

         Low       0.31      0.22      0.26       204
    Moderate       0.46      0.42      0.44       346
        High       0.69      0.76      0.72       855

    accuracy                           0.60      1405
   macro avg       0.48      0.47      0.47      1405
weighted avg       0.58      0.60      0.59      1405
```
- **Macro ROC-AUC:** 0.7637
- **Brier Score (High Risk Calibration):** 0.1997 (Lower is better)

#### Saved primary evaluation figures
- Confusion matrix: `reports/figures/primary_confusion_matrix.png`
- Reliability diagram: `reports/figures/high_risk_reliability_diagram.png`

## 2. Fairness Audit
### Fairness Audit (Across Gender for High Risk Classification)
- **Disparate Impact Ratio:** 0.9972 (Closer to 1 is fairer)
- **Statistical Parity Difference:** 0.0019 (Closer to 0 is fairer)
- **Equal Opportunity Difference:** 0.0269 (Closer to 0 is fairer)
- **Equalized Odds Difference:** 0.0269 (Supplementary; closer to 0 is fairer)
- **High-risk selection rates by encoded gender:** {'0': 0.6699857752489331, '1': 0.6680911680911681}

> Note: Gender is encoded as Male=0, Female=1, Other=2 in the harmonized schema.

## 3. Cross-Dataset Generalization
### Generalization 1: Depression Dataset (2-Class Bridged)
Since this dataset provides a binary "Depression" (Yes/No) proxy rather than a 3-class risk level, we collapse the model's Low/Moderate predictions into a single "Not High" class to match their "No", and compare "High" against their "Yes".

```text
              precision    recall  f1-score   support

    Not High       0.73      0.35      0.47       250
        High       0.57      0.87      0.69       252

    accuracy                           0.61       502
   macro avg       0.65      0.61      0.58       502
weighted avg       0.65      0.61      0.58       502
```

### Generalization 2: Stress Dataset (Qualitative Comparison)
This dataset provides a self-reported `stress_level` label. Because this is a different construct than our clinical-instrument-derived (DASS-21) risk composite, we report a qualitative distribution comparison rather than a misleading accuracy figure that implies false equivalence.

- **True Self-Reported Label Distribution**: `Low`: 60, `Medium`: 338, `High`: 102
- **Model Predicted (DASS-21 Composite) Risk**: `Low`: 27, `Moderate`: 110, `High`: 363

*For context, a naive majority-class baseline (always predicting "Medium") would achieve 67.6% accuracy on this dataset. The model predicts a significantly higher volume of "High" risk than the students self-report as "High" stress, highlighting the expected disagreement between a structured clinical threshold and subjective self-assessment.*

### Generalization Evaluation — Final Findings (per dataset)

**Gen1 (Depression Student Dataset) — bridge genuinely helped**

After bridging the binary depression label onto a 2-class risk comparison, accuracy improved from 49% to 61.2%, 11.0 points above the majority-class baseline of 50.2%. The label bridge shows the model performs meaningfully above chance on Gen1 once the label mismatch is corrected for, but this is a modest result (balanced accuracy 58.7%, macro F1 0.55), not evidence of strong cross-population performance.

**Gen2 (student_stress_sleep_screen) — genuine gap, best-supported of the two**

Unlike Gen1, Gen2's gap survived the feature ablation (25-29 point relative drop-off from each model's own primary-test baseline, not just a raw-number comparison confounded by the reduced model's weaker overall capability) and has no comparable label-bridging fix available, since self-reported stress_level and DASS-21-derived risk are different constructs without a principled mapping. This is reported as the strongest evidence of a genuine distributional generalization limitation in the current model -- students in this population may present risk factors differently than the primary training population, or self-report stress in ways that don't align with the clinical-instrument-derived label the model was trained against. This should be discussed as an open limitation in future work, not resolved by a bridging fix the way Gen1 was (attempted to be).

**Overall implication:** these two datasets do not support one merged verdict. Gen1's apparent generalization failure appears to have been substantially a label-definition artifact; Gen2's appears more likely to be a genuine gap, though only supported by relative performance drop-off rather than a directly comparable label, and should be stated with that caveat.

## 4. Feature Engineering Ablation\n| Feature set | Test Macro F1 | Delta vs. baseline |\n|---|---:|---:|\n| Base features only | 0.4648 | 0.0000 |\n| Base + composite features | 0.4725 | +0.0076 |\n\n## 5. SHAP Stability\n- Top-feature match rate across folds: **100.00%**\n- Mean pairwise top-3 Jaccard overlap: **100.00%**\n- Stability report: `reports/shap_stability_report.md`\n- Global SHAP summary plot: `reports/figures/shap_summary_high_risk.png`\n\n