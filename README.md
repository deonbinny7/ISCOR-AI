# ISCOR AI 🧠

### Intelligent Screening & Contextual Outcome Recommender

**ISCOR AI** is a safety-oriented AI-based student mental wellness screening and wellness companion that combines **Machine Learning, Explainable AI, Retrieval-Augmented Generation (RAG), and Large Language Models (LLMs)** to provide personalized, evidence-grounded wellness guidance.

The system analyzes structured lifestyle and stress-related information to classify a student's wellness risk as **Low, Moderate, or High**, explains the prediction using **SHAP**, retrieves supporting information from curated wellness resources using **RAG**, and uses an LLM to communicate the results through personalized explanations, suggestions, weekly plans, and conversational support.

> ⚠️ **Important:** ISCOR AI is a screening, self-reflection, and wellness-support system. It is **not a medical diagnostic system**, does not prescribe medication, and does not replace psychologists, psychiatrists, counsellors, or other qualified professionals.

---

## ✨ Key Idea

ISCOR AI follows a fundamental safety principle:

> **Machine Learning determines the risk. Explainable AI explains the risk. RAG provides evidence. The LLM communicates the result.**

The LLM is **never responsible for determining the user's risk category**.

Instead, the system follows a controlled pipeline:

```text
User Input
    ↓
FastAPI Backend
    ↓
Normalization & Feature Engineering
    ↓
ML Risk Classification
    ↓
SHAP Explanation
    ↓
Risk Gate
    ├── High / Crisis → Fixed Crisis Response
    │
    └── Safe
         ↓
       RAG Retrieval
         ↓
      Prompt Builder
         ↓
      LLM Generation
         ↓
    Fernet Encryption
         ↓
      SQLite
         ↓
      React UI
```

This separation reduces the risks associated with using generative AI directly for sensitive risk classification.

---

# 🎯 Objectives

ISCOR AI was designed with the following objectives:

* Develop an ML-based student wellness risk classifier.
* Classify users into **Low, Moderate, and High** risk categories.
* Compare multiple ML algorithms and select the best-performing model using **Macro F1**.
* Apply preprocessing and feature engineering to lifestyle and stress variables.
* Explain individual predictions using **SHAP**.
* Ground generated wellness guidance using **Retrieval-Augmented Generation**.
* Use curated resources from organizations such as **WHO, CDC, NHS, and universities**.
* Use LLMs only as a controlled communication layer.
* Implement a deterministic **Risk Gate** for high-risk and crisis situations.
* Provide personalized wellness explanations and 7-day plans.
* Support conversational follow-up through a wellness companion.
* Enable mood check-ins and longitudinal wellness tracking.
* Protect sensitive stored information using **Fernet encryption**.
* Maintain a clear separation between deterministic risk assessment and generative communication.

---

# 🚀 Features

## 1. 📝 Student Wellness Screening

Students complete a structured multi-step screening form covering factors such as:

* Sleep
* Academic pressure
* Financial stress
* Social support
* Study hours
* Physical activity
* Major life events
* Protective factors
* Optional health context

The system processes these inputs and generates a wellness risk assessment.

---

## 2. 🤖 Machine Learning Risk Classification

ISCOR AI evaluates multiple machine learning models:

* Logistic Regression
* Random Forest
* XGBoost
* LightGBM

The models are compared using **Macro F1**, followed by hyperparameter tuning and model serialization.

The selected classifier predicts:

```text
Low Risk
Moderate Risk
High Risk
```

The model also returns class probabilities, which are used by the safety layer to determine whether a prediction is sufficiently close to the High-risk category to require intervention.

---

# 🧮 Feature Engineering

The system performs preprocessing and generates composite features from the standardized input variables.

### Stress Index

```text
Stress_Index =
Academic_Pressure + Financial_Stress - Sleep_Hours
```

### Lifestyle Score

```text
Lifestyle_Score =
Physical_Activity + Sleep_Hours + Social_Support
```

### Academic Load

```text
Academic_Load =
Study_Hours + Academic_Pressure
```

These features allow the model to represent combinations of related lifestyle and stress factors rather than relying exclusively on individual variables.

---

# 🔍 Explainable AI with SHAP

A major component of ISCOR AI is **Explainable AI**.

Instead of returning only:

```text
Moderate Risk
```

the system identifies the factors that contributed most strongly to the prediction.

For example:

```text
Top Factors

Academic Pressure   ↑
Sleep Hours         ↓
Study Hours         ↑
Social Support      ↓
```

SHAP values are used to determine how individual features influence the model's prediction.

The top contributing factors are also passed into the RAG retrieval process, meaning that the factors explaining the prediction help determine what evidence and guidance the system retrieves.

> **Note:** SHAP indicates model contribution, not causation.

---

# 🛡️ Safety-First Risk Gate

Safety is one of the central design principles of ISCOR AI.

The system includes a deterministic **Risk Gate** between the ML/SHAP layer and the LLM layer.

### Normal flow

```text
ML Prediction
     ↓
SHAP Explanation
     ↓
Risk Gate
     ↓
RAG
     ↓
LLM
```

### High-risk flow

```text
ML Prediction
     ↓
High Risk / Borderline High
     ↓
Risk Gate
     ↓
LLM BYPASSED
     ↓
Fixed Crisis Response
```

The Risk Gate activates when:

* The predicted class is **High**, or
* The High-risk probability is sufficiently close to the highest predicted probability.

The implementation also performs keyword-based safety checks on:

* Mood notes
* Follow-up questions
* Companion messages

This prevents crisis-related interactions from reaching the normal generative pipeline unchecked.

---

# 📚 Retrieval-Augmented Generation

ISCOR AI uses **RAG** to ground wellness guidance in curated evidence instead of relying exclusively on the LLM's internal knowledge.

### Knowledge Sources

The knowledge base contains curated resources from:

* World Health Organization (WHO)
* Centers for Disease Control and Prevention (CDC)
* National Health Service (NHS)
* University wellness resources

### RAG Pipeline

```text
PDF Sources
    ↓
PyMuPDF Extraction
    ↓
Text Cleaning
    ↓
Chunking
    ↓
Sentence Transformer Embeddings
    ↓
ChromaDB
    ↓
Similarity Retrieval
    ↓
Prompt Builder
    ↓
LLM
```

The system uses:

* **PyMuPDF** for PDF processing
* **all-MiniLM-L6-v2** for embeddings
* **ChromaDB** for vector storage

Approximately five relevant chunks can be retrieved based on the user's risk level and SHAP factors.

---

# 🧠 LLM Communication Layer

The LLM is deliberately restricted to **communication and personalization**.

It can:

* Explain screening results.
* Explain important contributing factors.
* Generate wellness suggestions.
* Create structured 7-day wellness plans.
* Answer follow-up questions.
* Power the wellness companion.
* Summarize personality information.
* Summarize wellness trends.

It **does not determine risk**.

### Primary LLM

The primary model is:

**Gemini 2.0 Flash**

The implementation also supports a cascading fallback architecture involving:

* Gemini models
* Groq-hosted Llama 3.3 70B
* Gemini Flash-Lite variants

This fallback mechanism is intended to improve availability during API failures, rate limits, or transient provider issues.

---

# 🧩 Prompt Engineering

ISCOR AI uses structured prompts to control the LLM's behavior.

The prompt contains separate contextual sections such as:

```text
[SCREENING RESULT]
[SHAP FACTORS]
[RETRIEVED KNOWLEDGE]
[USER CONTEXT]
[TASK]
```

The system prompt establishes boundaries such as:

* No diagnosis.
* No medication advice.
* Lifestyle-level suggestions only.
* Use retrieved evidence.
* Present suggestions as options rather than medical directives.
* Follow a structured response format.

This creates the following controlled generation pipeline:

```text
User Assessment
      ↓
ML Prediction
      ↓
SHAP Factors
      ↓
RAG Query
      ↓
Retrieved Evidence
      ↓
Prompt Builder
      ↓
LLM
      ↓
Grounded Wellness Response
```

---

# 📊 Wellness Report

After screening, users receive a structured report containing:

### Risk Overview

* Risk category
* Prediction probabilities
* Overall summary

### SHAP Factor Insights

* Important contributing factors
* Direction of contribution
* Visual factor representation

### Explanation

Natural-language interpretation of the ML prediction.

### Weekly Plan

A structured **7-day wellness plan** personalized using the user's assessment information.

### Q&A

Users can ask follow-up questions about their result.

---

# 💬 Wellness Companion

ISCOR AI includes a persistent conversational wellness companion.

The companion can use contextual information such as:

* Recent conversation history
* Latest screening result
* Personality summary
* Retrieved evidence
* Relevant user context

This makes the companion more context-aware than a generic standalone chatbot.

---

# 🧘 Daily Check-In

The system provides a daily engagement interface for:

* Mood check-ins
* Wellness tracking
* Engagement streaks
* Guided breathing exercises
* Access to wellness resources

The check-in functionality extends the system beyond one-time screening toward longitudinal wellness monitoring.

---

# 🧠 Big Five Self-Reflection

ISCOR AI also includes a **Big Five personality self-reflection assessment**.

The assessment covers:

* Openness
* Conscientiousness
* Extraversion
* Agreeableness
* Neuroticism

The results are summarized through the controlled LLM communication layer.

This feature is intended for self-reflection rather than psychological diagnosis.

---

# 📈 Longitudinal Wellness Tracking

Users can access previous screenings and monitor changes over time.

The system supports:

* Historical screening reports
* Trend visualization
* Mood check-ins
* Persistent companion interactions
* Longitudinal wellness summaries

The trend dashboard can generate an LLM-based summary once sufficient screening history is available.

---

# 🏗️ System Architecture

ISCOR AI is organized into multiple layers:

```text
┌──────────────────────────────────────────────┐
│                 STUDENT                      │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│          React + Vite Frontend               │
│ Screening | Reports | Companion | Check-in  │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│              FastAPI Backend                 │
│         Authentication & Routing             │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│        Preprocessing & Normalization         │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│             Feature Engineering              │
│ Stress Index | Lifestyle Score | Academic    │
│ Load                                          │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│              ML Classifier                   │
│      Low | Moderate | High Risk              │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│               SHAP Explainer                 │
│          Feature Contributions               │
└──────────────────────┬───────────────────────┘
                       ↓
                 ┌─────┴─────┐
                 │ Risk Gate │
                 └─────┬─────┘
                       │
          ┌────────────┴────────────┐
          ↓                         ↓
   High / Crisis                  Safe
          ↓                         ↓
 Fixed Crisis Response         RAG Retrieval
                                    ↓
                              Prompt Builder
                                    ↓
                              Gemini / Groq
                                    ↓
                              Encryption
                                    ↓
                                 SQLite
                                    ↓
                              React UI
```

The architecture deliberately keeps safety-critical and deterministic processing separate from generative AI.

---

# 🛠️ Technology Stack

## Frontend

* React 19
* Vite
* React Router DOM
* Recharts
* Framer Motion
* CSS

## Backend

* Python
* FastAPI

## Machine Learning

* Scikit-learn
* Logistic Regression
* Random Forest
* XGBoost
* LightGBM

## Explainable AI

* SHAP
* TreeExplainer

## Generative AI

* Google Gemini
* Groq
* Llama 3.3 70B

## RAG

* Sentence Transformers
* all-MiniLM-L6-v2
* ChromaDB
* PyMuPDF

## Database

* SQLite

## Security

* Fernet symmetric encryption
* SHA-256 hashed session tokens

---

# 📂 Major System Components

| Component           | Technology                       | Responsibility                 |
| ------------------- | -------------------------------- | ------------------------------ |
| Frontend            | React + Vite                     | User interface                 |
| API                 | FastAPI                          | Backend communication          |
| Preprocessing       | Python                           | Data normalization             |
| Feature Engineering | Python                           | Composite feature creation     |
| Prediction          | ML Classifier                    | Risk classification            |
| Explainability      | SHAP                             | Feature contribution analysis  |
| Safety              | Risk Gate                        | Crisis interception            |
| Retrieval           | Sentence Transformers + ChromaDB | Evidence retrieval             |
| Generation          | Gemini / Groq                    | Natural-language communication |
| Persistence         | SQLite                           | Application data               |
| Security            | Fernet                           | Sensitive data encryption      |

---

# 📊 Dataset

The primary dataset is a de-identified student lifestyle and mental-health survey.

The dataset contains variables related to:

* Sleep
* Academic pressure
* Financial stress
* Social support
* Study hours
* Physical activity
* Related lifestyle factors

A schema mapping stage standardizes the raw variables so that the training pipeline and live inference pipeline use a consistent schema.

The target is represented using three categories:

```text
0 → Low
1 → Moderate
2 → High
```

The risk tiers are derived from DASS-21-related depression, anxiety, and stress proportions using the maximum severity across the three measures.

> The resulting classification should be interpreted as a computational screening category, **not a clinical diagnosis**.

---

# 🔐 Security & Privacy

Because ISCOR AI handles sensitive wellness information, security is incorporated into the architecture.

Sensitive fields are protected using **Fernet symmetric encryption**.

Examples of encrypted information include:

* Raw assessment answers
* Generated explanations
* Wellness suggestions
* Weekly plans
* Chat content
* Personality data
* Mood notes

The system also uses hashed bearer tokens with expiry for session validation.

---

# ⚡ Approximate Performance

The documented prototype reports the following approximate component latencies:

| Component           | Approximate Latency |
| ------------------- | ------------------: |
| ML inference + SHAP |           `< 50 ms` |
| RAG retrieval       |       `~100–300 ms` |
| LLM generation      |      `~2–8 seconds` |
| SQLite transaction  |            `< 5 ms` |

The primary latency bottleneck is external LLM generation rather than local ML inference, RAG retrieval, or database persistence.

> These figures represent prototype-level execution observations and should not be interpreted as production-scale benchmarks.

---

# 🖥️ Application Modules

ISCOR AI contains several major user-facing modules:

### 📝 Screening

Multi-step student wellness screening.

### 📊 Reports

Risk results, explanations, SHAP factors, weekly plans, and Q&A.

### 📚 My Reports

Historical screening results and trends.

### 🧠 Self-Reflection

Big Five personality self-reflection assessment.

### 💬 Companion

Context-aware AI wellness companion.

### 🧘 Check-In

Daily mood and wellness engagement with guided breathing.

### ℹ️ About / Trust

Information about the system's purpose, limitations, and responsible use.

The documented interface includes screenshots covering all of these workflows.

---

# 🔄 End-to-End Example

A typical screening interaction works as follows:

```text
1. Student enters lifestyle and stress information
                 ↓
2. FastAPI validates the session
                 ↓
3. Inputs are normalized
                 ↓
4. Composite features are generated
                 ↓
5. ML model predicts risk
                 ↓
6. SHAP identifies important factors
                 ↓
7. Risk Gate checks for high-risk/crisis conditions
                 ↓
8. If unsafe → fixed crisis response
                 ↓
9. If safe → RAG retrieves relevant evidence
                 ↓
10. Prompt Builder constructs structured context
                 ↓
11. Gemini/Groq generates communication
                 ↓
12. Sensitive information is encrypted
                 ↓
13. Result is stored
                 ↓
14. React displays the wellness report
```

---

# 🧪 Model Evaluation Approach

The ML pipeline compares:

```text
Logistic Regression
        │
        ├── Macro F1
        │
Random Forest
        │
        ├── Macro F1
        │
XGBoost
        │
        ├── Macro F1
        │
LightGBM
        │
        └── Macro F1
              ↓
       Best Model Selected
              ↓
       GridSearchCV Tuning
              ↓
       Feature Ablation
              ↓
       Final Model
```

The documented methodology uses an **80/20 train-test split** and **5-fold stratified cross-validation**.

The best model is subsequently tuned and serialized.

> The current project documentation does **not** report final accuracy, precision, recall, confusion matrix, or final Macro F1 values. These metrics should be added when the corresponding training/evaluation logs are available rather than being fabricated.

---

# ⚠️ Limitations

ISCOR AI is currently a **prototype/development system**, not a clinically validated production platform.

Important limitations include:

### Dataset

* Limited documentation of dataset provenance.
* Representativeness of the wider student population is uncertain.
* Risk labels are proxy-based.
* High-risk samples may be underrepresented.
* No external independent validation has been demonstrated.

### Explainability

* SHAP explains model contribution rather than causality.
* Current explanations are primarily focused on the High-risk class.

### RAG

* Retrieval quality depends on knowledge-base coverage.
* No formal retrieval precision/recall evaluation has been performed.
* Fixed-size chunking may separate logically connected information.

### LLM

* Generative models can still produce unsupported statements.
* External API availability is required.
* LLM generation is the primary latency bottleneck.

### Safety

* Keyword-based crisis detection cannot identify every possible expression of distress.
* Safety mechanisms are software controls and are not substitutes for professional crisis assessment.

### Infrastructure

* SQLite is not designed for high-volume concurrent writes.
* Local ChromaDB does not horizontally scale.
* Current authentication/session architecture is intended for prototype use.

---

# 🔮 Future Enhancements

Planned improvements include:

## Model & Data

* Expand and diversify the dataset.
* Improve dataset provenance documentation.
* Improve risk-target construction.
* Handle class imbalance.
* Perform independent external validation.
* Improve feature engineering.
* Extend explainability to complete multiclass analysis.

## RAG & LLM

* Semantic/section-aware chunking.
* Hybrid retrieval.
* Reranking.
* Source prioritization.
* Formal RAG evaluation.
* Expand and periodically refresh the knowledge base.
* Add LLM response validation.
* Evaluate factuality, groundedness, relevance, helpfulness, safety, empathy, and consistency.

## Security & Infrastructure

* Migrate SQLite → PostgreSQL.
* Migrate local ChromaDB → managed vector database.
* Introduce Redis caching.
* Replace anonymous sessions with stronger authentication.
* Improve token storage.
* Restrict CORS.
* Add API rate limiting.
* Implement secure logging.
* Dockerize the application.
* Deploy behind a load balancer.
* Add monitoring and model-drift detection.

## Validation

* Conduct formal user studies.
* Evaluate usability and explainability.
* Evaluate RAG and LLM usefulness.
* Perform fairness and bias evaluation.
* Add multilingual support.
* Strengthen localized crisis-resource management.

---

# 🗺️ Development Roadmap

```text
Phase 1
Model & Safety
│
├── Class imbalance handling
├── Improved crisis detection
├── External validation
└── Richer explainability
        ↓
Phase 2
AI & Infrastructure
│
├── Semantic chunking
├── Retrieval reranking
├── Multi-LLM evaluation
├── Response validation
├── PostgreSQL
├── Managed vector database
└── Redis caching
        ↓
Phase 3
Production Deployment
│
├── OAuth2 / JWT authentication
├── Secure token storage
├── Restricted CORS
├── API rate limiting
├── Docker
├── Load balancing
├── Monitoring
├── Model drift detection
└── Large-scale evaluation
```

---

# 📸 Application Screens

The project includes interfaces for:

* Multi-step wellness screening
* Wellness reports
* SHAP factor visualization
* AI-generated explanations
* 7-day wellness plans
* Follow-up Q&A
* Historical screening reports
* Big Five self-reflection
* Wellness companion
* Daily mood check-in
* Guided breathing exercises

---

# 🧠 Responsible AI Design

ISCOR AI was designed around several responsible AI principles:

### 1. Deterministic Risk Assessment

Risk classification is performed by a trained ML model rather than an LLM.

### 2. Explainability

SHAP provides insight into the features influencing a prediction.

### 3. Evidence Grounding

RAG provides external evidence to support generated wellness content.

### 4. Safety Interception

The Risk Gate can bypass the LLM during high-risk or crisis scenarios.

### 5. Clear Scope

The system explicitly avoids:

* Clinical diagnosis
* Medication prescription
* Replacement of professional care

### 6. Data Protection

Sensitive information is encrypted before persistence.

The central design philosophy is:

> **Predict with ML. Explain with XAI. Ground with RAG. Communicate with LLMs. Protect with deterministic safety controls.**

---

# 📁 Suggested Repository Structure

A conceptual organization of the project is:

```text
ISCOR-AI/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   └── ...
│
├── backend/
│   ├── services/
│   ├── models/
│   ├── routes/
│   ├── rag/
│   ├── safety/
│   └── ...
│
├── data/
│   └── primary_dataset_clean.csv
│
├── knowledge_base/
│   ├── CDC/
│   ├── NHS/
│   ├── WHO/
│   └── Universities/
│
├── models/
│   └── final_model.pkl
│
├── README.md
└── ...
```

> The exact repository structure may differ from this conceptual representation.

---

# 🔬 Research & Technical Contributions

The main technical contribution of ISCOR AI is the integration of multiple AI paradigms into a **safety-oriented architecture** rather than relying on a standalone LLM.

The project combines:

```text
Machine Learning
      +
Explainable AI
      +
Retrieval-Augmented Generation
      +
Large Language Models
      +
Deterministic Safety Logic
      +
Data Encryption
```

The distinguishing architectural principle is the separation of:

```text
WHAT IS THE RISK?
        ↓
      ML

WHY DID THE MODEL SAY THAT?
        ↓
      SHAP

WHAT EVIDENCE SUPPORTS THE GUIDANCE?
        ↓
      RAG

HOW SHOULD IT BE COMMUNICATED?
        ↓
      LLM
```

This separation is intended to make the system more interpretable, controllable, and safety-oriented than a standalone generative wellness chatbot.

---

# ⚠️ Disclaimer

ISCOR AI is an academic/prototype AI wellness project.

It is intended for:

* Self-reflection
* Wellness awareness
* Educational purposes
* Lifestyle-level guidance

It is **not intended to**:

* Diagnose mental health disorders.
* Provide medical diagnoses.
* Prescribe medication.
* Replace professional psychological or psychiatric care.
* Act as an emergency crisis assessment system.

If a user is experiencing a mental health emergency or immediate danger, professional and local emergency support should be sought.

---

# 👨💻 Project Information

**Project:** ISCOR AI  
**Full Form:** Intelligent Screening & Contextual Outcome Recommender  
**Domain:** Artificial Intelligence / Machine Learning / Generative AI  
**Focus:** Student Mental Wellness Screening & Wellness Support  
**Institution:** CHRIST (Deemed to be University)  
**Department:** Department of Computer Science  
**Course:** Principles of Large Language Models (MAI520-4)  
**Year:** 2026  

**Developer:** Deon Thomas Binny  

---

# 📚 References

The project documentation references research and technical resources including:

* World Health Organization (WHO)
* Centers for Disease Control and Prevention (CDC)
* National Health Service (NHS)
* Lundberg & Lee — SHAP
* Lewis et al. — Retrieval-Augmented Generation
* Reimers & Gurevych — Sentence-BERT
* XGBoost
* Random Forest
* LightGBM
* Scikit-learn
* Google Gemini
* Groq
* ChromaDB
* FastAPI
* React

---

# ⭐ Summary

**ISCOR AI** demonstrates how Machine Learning, Explainable AI, RAG, and Generative AI can be combined into a controlled student wellness platform.

Unlike a conventional chatbot, the system does not allow the LLM to independently determine risk. Instead:

```text
        STRUCTURED USER DATA
                 ↓
          ML RISK MODEL
                 ↓
             SHAP XAI
                 ↓
            SAFETY GATE
           ↙           ↘
      HIGH/CRISIS       SAFE
          ↓               ↓
   FIXED RESPONSE       RAG
                          ↓
                     PROMPT BUILDER
                          ↓
                         LLM
                          ↓
                PERSONALIZED GUIDANCE
```

The result is a prototype architecture that aims to be **predictive, explainable, evidence-grounded, personalized, conversational, and safety-oriented** while maintaining clear boundaries around clinical decision-making.

---

# 🚀 Deployment (Docker)

ISCOR AI is containerized and ready for production deployment using Docker Compose.

### 1. Prerequisites
Ensure you have [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed on your server.

### 2. Configuration
Create a `.env` file in the root directory and add your API keys:
```env
ISCOR_USE_LLM=1
GEMINI_API_KEY_1=your_api_key_here
ALLOWED_ORIGINS=https://your-domain.com
```

### 3. Build & Run
Run the following command to build the frontend and backend containers, and start the services in detached mode:
```bash
docker-compose up --build -d
```

The application will be available at `http://localhost` (or your server's IP/domain). The frontend React application is served by Nginx, which also acts as a reverse proxy for the FastAPI backend (`/api`), eliminating CORS issues.

---

<p align="center">
  <b>ISCOR AI</b><br>
  Intelligent Screening & Contextual Outcome Recommender
</p>

<p align="center">
  Built with Machine Learning • Explainable AI • RAG • LLMs
</p>
