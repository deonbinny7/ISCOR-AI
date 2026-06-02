# ISCOR AI
## Explainable Mental Health Risk Screening and Personalized Wellness Recommendation System

**Working title:** ISCOR AI — *Intelligent Screening & Contextual Outcome Recommender*
**Domain:** Applied AI / ML / Explainable AI / LLM Integration
**Type:** MSc-level applied research + system-building project

---

## 1. Problem Statement & Scope

### 1.1 What this system IS
- A **risk-screening support tool** that estimates the likelihood of elevated stress, anxiety, or depressive symptom severity from validated questionnaire data.
- A system that **explains** its predictions using SHAP, and translates those explanations into **plain-language, non-clinical guidance** via an LLM.
- A **decision-support and self-awareness tool** — output is a *screening signal*, not a clinical result.

### 1.2 What this system IS NOT
- Not a diagnostic tool (no DSM-5/ICD-11 diagnostic claims).
- Not a crisis-response or emergency detection system (must explicitly route to professional/crisis resources if severe risk is flagged — see §9).
- Not a replacement for a therapist, psychiatrist, or counselor.

### 1.3 Why this scope refinement matters (for your defense/viva)
Examiners will immediately ask "how is this different from a chatbot that guesses if someone is depressed?" Your answer needs to be structural:
1. Prediction comes from a **validated, auditable ML model**, not the LLM.
2. Every prediction is **explainable at the feature level** (SHAP), before any language is generated.
3. The LLM is **constrained by a structured input contract** — it never sees raw data, only a risk category + top factors, and is explicitly prompted not to diagnose.
4. There is a designed **escalation path** for high-risk cases.

This four-part separation (data → ML → XAI → constrained LLM) is the actual research contribution — not "using an LLM for mental health," which reviewers will be skeptical of on its own.

---

## 2. Refined System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                           │
│         Web App (React) / Streamlit prototype / Mobile         │
└───────────────────────────┬──────────────────────────────────┘
                             │  HTTPS (auth token)
┌───────────────────────────▼──────────────────────────────────┐
│                        API GATEWAY (FastAPI)                   │
│   /submit-screening   /get-report   /chat   /history           │
└───────────────────────────┬──────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Validation &   │  │  Feature          │  │  Auth &          │
│ Preprocessing  │  │  Engineering      │  │  Session Service │
│ Service        │  │  Service          │  │                  │
└───────┬────────┘  └─────────┬────────┘  └──────────────────┘
        │                     │
        └──────────┬──────────┘
                    ▼
        ┌────────────────────────┐
        │   ML Inference Service  │
        │  (RF / XGBoost / LGBM)  │
        │  → risk_label,          │
        │    risk_probabilities   │
        └───────────┬────────────┘
                    ▼
        ┌────────────────────────┐
        │  Explainability Service │
        │      (SHAP values)      │
        │  → top_k contributing   │
        │    features + direction │
        └───────────┬────────────┘
                    ▼
        ┌────────────────────────┐
        │  Risk Gate / Safety     │
        │  Router                 │
        │  (severe risk → crisis  │
        │   resource flow, bypass │
        │   LLM wellness content) │
        └───────────┬────────────┘
                    ▼
        ┌────────────────────────┐
        │  Prompt Construction    │
        │  Engine (structured     │
        │  JSON contract only)    │
        └───────────┬────────────┘
                    ▼
        ┌────────────────────────┐
        │   LLM Service            │
        │  (explanation, wellness  │
        │   plan, constrained Q&A) │
        └───────────┬────────────┘
                    ▼
        ┌────────────────────────┐
        │  Report Assembly &      │
        │  Persistence            │
        └───────────┬────────────┘
                    ▼
              Client Dashboard
```

**Key design decision to defend:** the **Risk Gate / Safety Router** sits *between* the ML/XAI layer and the LLM layer. If predicted risk crosses a severity threshold, the system suppresses "wellness plan" generation and instead returns a fixed, pre-approved crisis-resource response — the LLM is not trusted to freelance in high-risk cases. This is a very defensible design point in a viva.

---

## 3. Data Layer

### 3.0 What you actually have — and what role each file should play

**No, you don't need to use all of it.** Using six datasets "because you have them" is a weakness, not a strength — a reviewer will ask "why six, and how did you reconcile six different feature sets and label definitions?" and "I downloaded them" isn't an answer. Instead, give each file a **specific, named job**. Most of them should only ever touch the project in one clearly stated role.

| File | Rows | Assigned Role | Why |
|---|---|---|---|
| `Data ERS_DASS 21.xlsx` | — | **Label-validation source** | This is your only dataset with an actual validated psychometric instrument (DASS-21). Use it to build/verify the clinical cutoff scoring logic (§3.2 below) — not necessarily as your main training data, but as the reference standard your target-label definition is checked against. |
| `students_mental_health_survey.csv` | 7,024 (you have 2 copies — delete one) | **Primary training dataset** | Largest genuinely-sized dataset with pre-existing numeric Stress/Depression/Anxiety scores plus a wide feature set (social support, counseling use, sleep, diet, substance use, financial stress). Big enough for a proper train/val/test split and stratified k-fold CV. This is your main model-training data. |
| `Depression Student Dataset.csv` | 504 | **Generalization / cross-dataset test set #1** | Different feature set, different population framing (depression + suicidal thoughts specifically). Train on the primary set, test how well the model transfers here. This is the "cross-dataset robustness" experiment mentioned below — don't retrain on it, just evaluate on it. |
| `student_stress_sleep_screen.csv` | 502 | **Generalization / cross-dataset test set #2**, or feature-engineering exploration | Narrower feature set (sleep, screen time, caffeine, stress) — useful either as a second held-out generalization test, or to sanity-check your Lifestyle Score composite feature against a dataset that isolates those exact variables. |
| `Student Mental Health.csv` | 103 | **Qualitative/EDA reference only** | Too small for training or reliable evaluation (103 rows won't give you a stable held-out test). Use it for exploratory comparison or a small case-study illustration in your report, not for any model that reports numbers. |
| `student_lifestyle_100k.csv` | 100,000 | **Use with caution — likely synthetic** | A 100k-row Kaggle "student lifestyle" dataset is almost certainly generated/simulated, not real survey responses. Treat its stress/depression labels as synthetic ground truth, not real psychometric outcomes. Good for: stress-testing your pipeline at scale, exploring feature engineering ideas, demonstrating the system handles volume. **Not good for**: any claim about real-world model accuracy — if you train or report metrics on this one, say explicitly in your report that the labels are synthetic, or a panel will (rightly) push back hard. |

**Net recommendation:**
1. Train + tune on `students_mental_health_survey.csv` (dedupe the two copies first).
2. Validate/derive your target-label cutoff logic against `Data ERS_DASS 21.xlsx`.
3. Evaluate generalization on `Depression Student Dataset.csv` and `student_stress_sleep_screen.csv` (no retraining — pure held-out evaluation).
4. Use `student_lifestyle_100k.csv` only for scale/robustness testing, clearly labeled as synthetic.
5. Use `Student Mental Health.csv` only as a small qualitative reference, not for any reported metric.

This gives you exactly the "cross-dataset robustness" story from §3.1 below, except now it's grounded in files you actually have rather than a generic recommendation.

### 3.1 Cross-dataset validation rationale

| Dataset | Type | Notes |
|---|---|---|
| DASS-21 (`Data ERS_DASS 21.xlsx`) | Validated psychometric instrument | Use for label-cutoff validation, not necessarily bulk training |
| `students_mental_health_survey.csv` | Large questionnaire dataset | Primary training/tuning data |
| `Depression Student Dataset.csv`, `student_stress_sleep_screen.csv` | Smaller questionnaire datasets | Held-out generalization tests |

**Recommendation:** Train on one primary dataset, and test generalization on at least one structurally different secondary dataset — this gives you a "cross-dataset robustness" experiment, which is a strong addition to a dissertation-style writeup (and mirrors what you already did with Adult Census + COMPAS in PrivGuard-AI — reviewers will recognize the same rigor).

**Important — column harmonization step (needed before any of this works):** each file uses different column names, scales, and Likert ranges (e.g. one may use 1–5 stress scores, another 0–10, another categorical bins). Before training or evaluating across datasets, you need a small **schema-mapping layer**: a mapping table (in code or a config file) that translates each dataset's raw columns into your unified feature schema below. Build this once, document it in your report as a "data harmonization" step — it's genuine methodological work worth writing up, not just cleanup.

### 3.2 Feature schema (unified target — map all datasets into this)

| Feature | Type | Range/Encoding |
|---|---|---|
| Age | Numeric | 15–60 |
| Gender | Categorical | Male=0, Female=1, Other=2 |
| Sleep Hours | Numeric | 0–12 |
| Academic/Work Pressure | Ordinal | 1–5 |
| Financial Stress | Ordinal | 1–5 |
| Social Support Score | Ordinal | 1–5 |
| Study/Work Hours | Numeric | 0–16 |
| Physical Activity (hrs/week) | Numeric | 0–20 |
| Family History of Mental Illness | Binary | Yes/No |
| Target: Risk Category | Categorical | Low / Moderate / High (derived from DASS-21 cutoff scores, not self-labeled) |

**Important methodological note:** Don't let the target label come from an unvalidated survey question like "do you feel depressed?" — derive it from **established clinical cutoff scoring** (e.g., DASS-21 severity bands) so the label itself has psychometric validity. This is the single most common weakness in student projects in this space, and fixing it is a strong point in your favor.

### 3.3 Preprocessing pipeline
1. **Dedupe first:** you have `students_mental_health_survey.csv` twice (from different zip archives) — confirm they're identical (`diff` or a pandas `.equals()` check) and drop one before anything else.
2. **Harmonize schemas:** apply the column-mapping layer from §3.1 so the primary dataset and both generalization datasets land in the same unified feature schema (§3.2) before any modeling touches them.
3. **Missing values:** median (numeric), mode (categorical); document missingness rate per feature, per dataset (missingness patterns often differ across the three questionnaire sources).
4. **Encoding:** ordinal encode Likert-scale items (preserve order — do NOT one-hot ordinal data, this is a common mistake); one-hot for nominal categorical (e.g. gender, if >2 categories).
5. **Scaling:** StandardScaler for tree-based models is optional but keep consistent for any linear baseline (Logistic Regression) you use for comparison.
6. **Class balancing:** check class distribution first, on the primary training set only (`students_mental_health_survey.csv`). Only apply SMOTE if the minority class is genuinely underrepresented (<20%) — document the before/after distribution. Do not apply SMOTE to the held-out generalization sets — they need to stay untouched to be a valid test.

---

## 4. Feature Engineering

Composite indices should be **theoretically justified**, not arbitrary sums — cite psychological literature for why these factors combine (e.g., sleep + workload + financial stress as components of an "allostatic load" proxy).

```
Stress_Index = w1*(Academic_Pressure) + w2*(Financial_Stress) + w3*(5 - Sleep_Score)
Lifestyle_Score = w4*(Physical_Activity_norm) + w5*(Sleep_Score) + w6*(Social_Support)
Academic_Load = Study_Hours_norm + Assignment_Load_norm
```

Determine `w1..w6` either via:
- Equal weighting (baseline, simplest to defend), or
- **AHP (Analytic Hierarchy Process)** weighting — you already have AHP experience from PrivGuard-AI's AIS score, so reusing that method here for weighting the composite indices gives you methodological consistency across your portfolio and is easy to explain in a viva.

Run ablation: train model with vs. without engineered features, report the metric delta. This turns "I engineered some features" into an actual experimental result.

---

## 5. Modeling

### 5.1 Candidate models
Logistic Regression (baseline/interpretable) → Random Forest → XGBoost → LightGBM → CatBoost

### 5.2 Protocol
- Stratified train/test split (e.g. 80/20), stratified k-fold CV (k=5 or 10) for model selection.
- Hyperparameter tuning via GridSearchCV or Optuna — document the search space, not just final params.
- **Report per-class metrics**, not just overall accuracy — risk screening is inherently a case where Low/Moderate/High have very different costs of misclassification (missing a "High" case is far worse than misclassifying "Low" as "Moderate"). Consider a cost-sensitive evaluation, or at minimum report Recall on the "High" class specifically and discuss it.

### 5.3 Metrics
- Accuracy, Precision, Recall, F1 (macro + per-class), ROC-AUC (one-vs-rest for multiclass), Confusion Matrix.
- **Calibration check**: are predicted probabilities well-calibrated? (reliability diagram) — matters a lot here since you're presenting a "probability" to a possibly anxious user; overconfident wrong probabilities are a real harm vector.

---

## 6. Explainability Layer (SHAP)

- Use **TreeExplainer** for the chosen tree-based model (fast, exact for RF/XGBoost/LightGBM).
- Generate:
  - Global feature importance (summary plot) — for your report/defense.
  - **Local, per-prediction SHAP values** — this is what feeds the LLM prompt.
- Extract top-k (e.g., top 3–5) features by absolute SHAP value for each prediction, with direction (increases/decreases risk).

Example structured output passed downstream:
```json
{
  "risk_label": "Moderate",
  "risk_probabilities": {"Low": 0.18, "Moderate": 0.55, "High": 0.27},
  "top_factors": [
    {"feature": "Sleep Hours", "shap_value": 0.43, "direction": "increases_risk"},
    {"feature": "Academic Pressure", "shap_value": 0.31, "direction": "increases_risk"},
    {"feature": "Social Support", "shap_value": -0.18, "direction": "decreases_risk"}
  ]
}
```

**Add a SHAP stability check**: compute SHAP values across CV folds and report variance of top-feature rankings. This answers the reviewer question "are your explanations even stable?" before it's asked.

---

## 7. LLM Layer — Constrained Generation

### 7.1 Hard architectural constraint
The LLM **only ever receives** the structured JSON above (risk label, probabilities, top factors) — never raw questionnaire answers, never free text the user wrote about themselves, unless that's explicitly the optional journal/Q&A feature, and even then it's isolated from the scoring pipeline. This is your strongest safety/privacy argument (also DPDP-relevant, which ties nicely to your PrivGuard-AI work if you want to cross-reference compliance thinking).

### 7.2 System prompt (constrained contract)
```
You are a wellness communication assistant. You will receive a risk category
and a list of contributing factors from a machine learning model.
Rules you must follow:
1. Never state or imply a clinical diagnosis.
2. Never claim certainty — always frame as "the screening suggests," not "you have."
3. Base your explanation ONLY on the factors provided. Do not infer new causes.
4. Always include a line encouraging professional consultation if risk is Moderate or High.
5. If risk is High, your ENTIRE response must be the fixed crisis-resource message
   provided to you — do not generate wellness content.
6. Keep tone supportive, non-alarming, and jargon-free.
```

### 7.3 Outputs (three separate constrained generations, not one big freeform response)
1. **Plain-language explanation** of the top factors.
2. **General wellness suggestions** (lifestyle-level only — sleep hygiene, activity, social connection — never medication or clinical interventions).
3. **Constrained Q&A** — answers general wellness/psychoeducation questions, refuses to answer anything requesting diagnosis, medication advice, or self-harm-adjacent information (route those to the safety router instead).

### 7.4 Evaluation of the LLM layer
Don't just eyeball outputs — set up a small **human evaluation rubric** (even 3–5 raters, could be classmates) scoring each output on:
- Faithfulness to provided factors (did it hallucinate a cause not in the SHAP list?)
- Clarity / readability (Flesch-Kincaid score, for a numeric metric)
- Safety compliance (did it ever diagnose, prescribe, or minimize risk?)
- Helpfulness

This gives you a quantifiable LLM evaluation section instead of "the LLM seemed to work well," which is a common weak point in similar projects.

---

## 8. Report Generation (User-Facing Output)

1. Risk category (Low/Moderate/High) with probability breakdown.
2. Top contributing factors (from SHAP, in plain language).
3. LLM-generated explanation.
4. Wellness suggestions (only if Low/Moderate).
5. Optional 7-day lifestyle micro-plan.
6. **Mandatory disclaimer block** (see §9), same on every report, cannot be dismissed without acknowledgment.
7. Timestamp + option to compare against previous screenings (trend over time) if repeat use is supported.

---

## 9. Safety, Ethics & Escalation Design (do not skip this section in your writeup — it's often worth as much credit as the modeling)

- **Escalation path:** if risk = High, or if any single response indicates acute distress language (in optional journal/Q&A text, if implemented), the system:
  - Suppresses LLM wellness generation.
  - Displays a fixed, reviewed crisis-resource message (region-appropriate helplines).
  - Logs the event for review if there's a human-in-the-loop component (e.g., campus counseling integration).
- **No claims of confidentiality guarantees** without actually implementing the backing controls — be precise in your report about what is and isn't stored, and who could access it.
- **Consent and disclaimer:** explicit, unskippable consent screen before first screening, stating this is not diagnostic, not a crisis service, and data-handling practices.
- **DPDP-inspired data handling** (naturally connects to your PrivGuard-AI framework if you want a portfolio-level thread): data minimization, purpose limitation, and a stated retention/deletion policy for screening history.
- **Bias/fairness check on the ML model**: run the same fairness metrics you used in PrivGuard-AI (Disparate Impact, Statistical Parity Difference, Equal Opportunity Difference) across gender and any other sensitive attribute in the dataset. This is both good practice and an easy way to reuse work you've already built, while making the project stronger.

---

## 10. Backend & Database Design

### 10.1 Service flow
```
Frontend → FastAPI Gateway → Preprocessing Service → ML Inference Service
→ SHAP Service → Risk Gate → Prompt Builder → LLM Service → Report Assembler
→ Persistence (DB) → Frontend Dashboard
```

### 10.2 Database schema (relational, e.g. PostgreSQL/SQLite)

```
Users(user_id PK, created_at, consent_version, region)

Screenings(screening_id PK, user_id FK, submitted_at, raw_answers_json)

Predictions(prediction_id PK, screening_id FK, risk_label, prob_low, prob_moderate,
            prob_high, model_version, created_at)

FeatureImportance(id PK, prediction_id FK, feature_name, shap_value, direction)

WellnessPlans(plan_id PK, prediction_id FK, explanation_text, suggestions_text,
              weekly_plan_json, llm_model_version, generated_at)

ConversationHistory(msg_id PK, user_id FK, screening_id FK, role, content, created_at)

SafetyEvents(event_id PK, user_id FK, screening_id FK, trigger_reason, resolved_flag,
             created_at)
```

Keep `raw_answers_json` and any free-text fields encrypted at rest if you want to make a genuine DPDP-alignment claim, not just a stated one.

---

## 11. Technology Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React (production) or Streamlit (fast prototype) | Streamlit for MVP/demo speed, React if you want a polished defense demo |
| Backend | FastAPI | Async, easy to layer services, good for microservice-style separation |
| ML | scikit-learn, XGBoost, LightGBM | Standard, well-documented, fast to justify in a viva |
| Explainability | SHAP | Industry-standard, TreeExplainer is efficient |
| LLM | OpenAI API or open-weight model via Ollama (e.g. Llama 3, Mistral) | Open-weight gives you a stronger "no data leaves infra" privacy argument if that matters for your DPDP framing |
| Database | PostgreSQL (prod) / SQLite (dev) | |
| Deployment | Docker + docker-compose | Optional but strengthens the "system," not just "notebook," framing |

---

## 12. Evaluation Plan Summary

| Component | Metric(s) |
|---|---|
| ML model | Accuracy, per-class Precision/Recall/F1, ROC-AUC, calibration |
| Fairness | Disparate Impact, Statistical Parity Difference, Equal Opportunity Difference (by gender / other sensitive attribute) |
| Explainability | SHAP stability across folds, human-rated relevance of top factors |
| LLM layer | Faithfulness, readability, safety-compliance rate, helpfulness (human eval rubric) |
| System | End-to-end latency, escalation-path correctness (test with synthetic high-risk cases) |

---

## 13. Suggested Timeline (12–14 weeks, adjust to your semester)

| Weeks | Milestone |
|---|---|
| 1–2 | Literature review, dataset finalization, ethics/consent design |
| 3–4 | Preprocessing pipeline, EDA, feature engineering + ablation setup |
| 5–6 | Model training, tuning, comparison, fairness audit |
| 7–8 | SHAP integration, stability testing |
| 9–10 | LLM prompt engineering, safety router, escalation logic |
| 11 | Backend integration (FastAPI services, DB) |
| 12 | Frontend + end-to-end demo |
| 13 | Human evaluation of LLM outputs, metrics writeup |
| 14 | Report/paper writing, defense prep |

---

## 14. Future Enhancements (keep as "future work," don't over-scope for the core deliverable)
- Longitudinal mood tracking with trend visualization.
- Wearable data integration (sleep/activity).
- Multilingual support (relevant given your Malayalam/Manglish work — could even be a natural extension later).
- RAG grounding LLM responses in vetted mental health resources instead of relying on parametric knowledge.
- Counselor-facing dashboard with human-in-the-loop review for High-risk flags.

---

## 15. What Makes This a Strong (not just a working) Project

The difference between a demo and a defensible research project is that every design choice above has a **stated reason and a way to measure whether it worked**:
- ML predicts, SHAP explains, LLM communicates — each layer independently testable.
- The safety router is an architectural decision, not an afterthought bullet point.
- Fairness and explainability stability are measured, not assumed.
- The LLM is evaluated against a rubric, not just "read the output and it sounded fine."

That's the version of this project that survives a tough panel.
