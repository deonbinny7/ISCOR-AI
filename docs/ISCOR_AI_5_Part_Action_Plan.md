# ISCOR AI — 5-Part Execution Plan
### A "what do I actually do" companion to ISCOR_AI_Project_Plan.md

This splits the full project into **5 sequential parts**. Each part has a single job, a checklist, a "done when" definition, and the exact deliverable that feeds into the next part. Work through them in order — don't start Part 2 until Part 1's "done when" is met, because everything downstream (modeling, SHAP, LLM prompts) depends on the data foundation being solid.

---

## PART 1 — Data Foundation
**Goal:** Turn six messy downloaded files into one clean, labeled, harmonized training set plus two untouched generalization test sets.

### What to do
1. Dedupe `students_mental_health_survey.csv` (you have two copies) — confirm identical, delete one.
2. Build the **column-mapping layer**: one script/config that maps each dataset's raw columns into the unified feature schema (Age, Gender, Sleep Hours, Academic Pressure, Financial Stress, Social Support, Study Hours, Physical Activity, Family History).
3. Open `Data ERS_DASS 21.xlsx`, extract the actual DASS-21 item responses, and implement the **official DASS-21 severity cutoff scoring** (Normal / Mild / Moderate / Severe / Extremely Severe per subscale — you'll likely collapse this into your 3-tier Low/Moderate/High for the main target).
4. Apply that cutoff logic to derive the **target label** on `students_mental_health_survey.csv`. If it doesn't have raw DASS-21 items, use its existing numeric stress/depression/anxiety scores and map them onto equivalent severity bands — document exactly how you did this mapping, since it's the single most scrutinized methodological choice in the whole project.
5. Run preprocessing on the primary set only: missing values (median/mode), ordinal encoding for Likert items, scaling.
6. Harmonize (but do NOT retrain-balance) `Depression Student Dataset.csv` and `student_stress_sleep_screen.csv` into the same schema — keep them completely untouched otherwise, they're your held-out generalization tests.
7. Set aside `student_lifestyle_100k.csv` (synthetic, scale-testing only) and `Student Mental Health.csv` (too small, EDA-only) — don't process these yet.
8. Write a short EDA notebook: class balance, missingness, correlation heatmap, on the primary dataset.

### Deliverable
- `primary_dataset_clean.csv` (labeled, encoded, ready to split)
- `gen_test_1.csv`, `gen_test_2.csv` (harmonized, untouched)
- A written note (half a page) on how the DASS-21 cutoffs were derived and applied — you will reuse this almost verbatim in your report's Methodology section.

### Done when
You can load one clean primary CSV with a defensible target label, and two harmonized generalization CSVs in the same schema.

---

## PART 2 — Modeling & Fairness
**Goal:** A tuned, validated classifier with honest per-class metrics and a fairness audit — not just "an accuracy number."

### What to do
1. Build the composite features (Stress Index, Lifestyle Score, Academic Load) on the primary dataset — start with equal weighting, then optionally redo with AHP weights (reuse your PrivGuard-AI AHP method).
2. Split primary dataset: stratified train/test, and stratified k-fold CV (k=5 or 10) inside the training portion for model selection.
3. Train baseline (Logistic Regression) then Random Forest, XGBoost, LightGBM — same CV folds for all, so comparisons are fair.
4. Tune the best 1–2 candidates (GridSearchCV or Optuna) — log the search space, not just final hyperparameters.
5. Run the **feature-engineering ablation**: same model, with vs. without composite features, report the metric delta.
6. Evaluate on the held-out test split: Accuracy, per-class Precision/Recall/F1, ROC-AUC (one-vs-rest), confusion matrix. Call out High-class Recall specifically.
7. Check probability calibration (reliability diagram) — don't skip this, it directly matters once you're showing probabilities to a user.
8. Evaluate the SAME frozen model on `gen_test_1.csv` and `gen_test_2.csv` — no retraining. This is your cross-dataset robustness result.
9. Run the fairness audit (Disparate Impact, Statistical Parity Difference, Equal Opportunity Difference) across Gender on the primary test set.
10. Pick and freeze the final model + preprocessing pipeline as a single serializable artifact (e.g. a pickled sklearn pipeline).

### Deliverable
- `final_model.pkl` (or equivalent) + a metrics report (table of all metrics above, ablation results, generalization results, fairness results).

### Done when
You have one frozen model with a full metrics table you could put directly into a results chapter, including at least one generalization test and one fairness audit.

---

## PART 3 — Explainability (SHAP)
**Goal:** Every prediction comes with a stable, trustworthy, per-feature explanation.

### What to do
1. Load the frozen model from Part 2 into a SHAP `TreeExplainer`.
2. Generate the **global** summary plot (which features matter most overall) — for your report/defense slides.
3. Write the function that takes one input row → returns **local** SHAP values → extracts top-3 to top-5 features with sign (increases/decreases risk).
4. Wrap that into the exact JSON contract used downstream:
   ```json
   {"risk_label": "...", "risk_probabilities": {...}, "top_factors": [...]}
   ```
5. Run the **SHAP stability check**: recompute SHAP top-feature rankings across your k-fold models from Part 2, measure how much the top-3 features shift fold to fold. Report this as a number (e.g. % of folds where the top feature is the same).
6. Sanity-check a handful of individual predictions by hand — do the SHAP explanations make intuitive sense for those rows? Note 2–3 examples for your report/demo.

### Deliverable
- `explain(input_row) -> structured_json` function, a global SHAP summary plot image, and a stability metric.

### Done when
Any single prediction can be turned into the structured JSON contract, and you have a number quantifying explanation stability, not just an assumption of it.

---

## PART 4 — LLM Layer & Safety Router
**Goal:** Turn the structured JSON into safe, non-diagnostic, evaluated language — with a hard gate that intercepts high-risk cases before the LLM ever generates wellness content.

### What to do
1. Build the **Risk Gate** first, before any prompt engineering: a simple rule (`if risk_label == "High": return fixed_crisis_message`) that bypasses the LLM entirely for high-risk cases. Test it with synthetic high-risk JSON inputs to confirm it never falls through to the LLM.
2. Write the constrained system prompt (see Part 7 rules in the main plan: no diagnosis, no invented causes, always suggest professional consultation for Moderate/High, jargon-free tone).
3. Implement the three separate constrained generations as separate calls, not one big prompt:
   - Plain-language explanation of top factors
   - General wellness suggestions (lifestyle-level only)
   - Constrained Q&A (with its own refusal rules for diagnosis/medication/self-harm-adjacent questions — route those to the Risk Gate instead of answering)
4. Feed it only the structured JSON from Part 3 — never raw questionnaire data.
5. Build the **human evaluation rubric** (faithfulness to provided factors / clarity — Flesch-Kincaid score / safety compliance / helpfulness) and run it on a sample of outputs across Low, Moderate, and synthetic High inputs, with 3–5 raters if possible (classmates are fine).
6. Fix anything that fails the safety-compliance check before moving on — this is the one part of the project where "mostly working" isn't acceptable.

### Deliverable
- Working Risk Gate + 3 prompt templates + a small human-eval score sheet (even 10–15 sample outputs scored is enough for a report table).

### Done when
Every synthetic High-risk test case is intercepted by the Risk Gate with zero exceptions, and your human-eval sheet shows no safety-compliance failures on the sampled outputs.

---

## PART 5 — Integration, Reporting & Defense Prep
**Goal:** Wire Parts 1–4 into one working system, then turn the whole thing into a report and a demo you can defend.

### What to do
1. Stand up the FastAPI services: preprocessing → ML inference (Part 2 model) → SHAP (Part 3) → Risk Gate → prompt builder → LLM (Part 4) → report assembler.
2. Wire the database schema (Users, Screenings, Predictions, FeatureImportance, WellnessPlans, ConversationHistory, SafetyEvents) — SQLite is fine for a defense demo, don't over-invest in Postgres/Docker unless you have time left over.
3. Build the minimal frontend (Streamlit is enough) — questionnaire form → submit → report view with risk category, top factors, LLM explanation, wellness suggestions, disclaimer block.
4. Add the mandatory unskippable consent/disclaimer screen.
5. Run 3–5 full end-to-end test cases by hand (Low, Moderate, High, one edge case) and screenshot/record them for your slides.
6. Write up the report sections in this order (matches what examiners read first): Problem Statement & Scope → Data & Label Validation → Modeling & Fairness Results → Explainability Results → LLM Evaluation Results → Safety/Ethics Design → System Architecture → Future Work.
7. Prepare your viva answer to the "how is this different from a chatbot" question using the four-part separation argument (data → ML → XAI → constrained LLM) — have your generalization, fairness, SHAP-stability, and LLM-eval numbers ready to cite from memory.

### Deliverable
- A working end-to-end demo + a written report/manuscript + a defense-ready explanation of every design decision.

### Done when
You can run one full screening live in front of a panel, and answer "why did the model say that" and "what stops this from giving harmful advice" using numbers you've already generated, not hand-waving.

---

## At-a-glance dependency chain

```
Part 1 (Data)  →  Part 2 (Model + Fairness)  →  Part 3 (SHAP)  →  Part 4 (LLM + Safety)  →  Part 5 (Integration + Report)
```

Each part's deliverable is the next part's input. If you're short on time, Parts 1–3 are non-negotiable (they're the actual research contribution); Part 5's frontend/Docker polish is the first thing to cut if needed — a working backend + Streamlit + a strong report beats a polished UI with weak methodology.
