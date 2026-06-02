import json
import logging
import os
import pickle
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
for relative in ("data_processing", "models", "llm"):
    path = str(ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)

from schema_mapper import harmonize_primary  # noqa: E402
from modeling_pipeline import engineer_features  # noqa: E402
from risk_gate import check_risk_gate  # noqa: E402
from prompt_builder import FEATURE_DISPLAY_NAMES, _format_extended_context  # noqa: E402


BASE_FEATURES = [
    "Age",
    "Gender",
    "Sleep_Hours",
    "Academic_Pressure",
    "Financial_Stress",
    "Social_Support",
    "Study_Hours",
    "Physical_Activity",
    "Family_History",
]

SCALED_FEATURES = [
    "Age",
    "Sleep_Hours",
    "Academic_Pressure",
    "Financial_Stress",
    "Social_Support",
    "Study_Hours",
    "Physical_Activity",
]

CLASS_NAMES = ["Low", "Moderate", "High"]


def _raw_training_frame() -> pd.DataFrame:
    raw_path = ROOT / "datasets" / "archive (30)" / "students_mental_health_survey.csv"
    return harmonize_primary(pd.read_csv(raw_path))


@lru_cache(maxsize=1)
def _scaling_stats() -> Dict[str, Dict[str, float]]:
    raw = _raw_training_frame()
    return {
        column: {
            "mean": float(raw[column].mean()),
            "std": float(raw[column].std(ddof=0) or 1.0),
        }
        for column in SCALED_FEATURES
    }


@lru_cache(maxsize=1)
def _load_model():
    with open(ROOT / "models" / "final_model.pkl", "rb") as f:
        return pickle.load(f)


@lru_cache(maxsize=1)
def _load_explainer():
    from shap_explainer import SHAPExplainer

    return SHAPExplainer(
        model_path=str(ROOT / "models" / "final_model.pkl"),
        data_path=str(ROOT / "datasets" / "primary_dataset_clean.csv"),
    )


def normalize_answers(raw_answers: Dict[str, Any]) -> Dict[str, float]:
    """Convert human form answers into the scaled feature space used by Part 2."""
    gender_map = {"Male": 0, "Female": 1, "Other": 2}
    family_map = {"No": 0, "Yes": 1}
    social_map = {"Low": 1, "Moderate": 3, "High": 5}

    features = {
        "Age": float(raw_answers["age"]),
        "Gender": float(gender_map.get(raw_answers["gender"], 2)),
        "Sleep_Hours": float(raw_answers["sleep_hours"]),
        "Academic_Pressure": float(raw_answers["academic_pressure"]),
        "Financial_Stress": float(raw_answers["financial_stress"]),
        "Social_Support": float(social_map.get(raw_answers["social_support"], 3)),
        "Study_Hours": float(raw_answers["study_hours"]),
        "Physical_Activity": float(raw_answers["physical_activity"]),
        "Family_History": float(family_map.get(raw_answers["family_history"], 0)),
    }

    stats = _scaling_stats()
    for column in SCALED_FEATURES:
        features[column] = (features[column] - stats[column]["mean"]) / stats[column]["std"]

    engineered = engineer_features(pd.DataFrame([features]))
    return engineered.iloc[0].astype(float).to_dict()


def _fallback_explain(model_input: Dict[str, float]) -> Dict[str, Any]:
    model = _load_model()
    frame = pd.DataFrame([model_input])
    probabilities = model.predict_proba(frame)[0]
    risk_index = int(probabilities.argmax())

    factor_candidates = [
        ("Stress_Index", abs(model_input.get("Stress_Index", 0.0)), "increases_risk"),
        ("Academic_Load", abs(model_input.get("Academic_Load", 0.0)), "increases_risk"),
        ("Lifestyle_Score", abs(model_input.get("Lifestyle_Score", 0.0)), "decreases_risk"),
        ("Sleep_Hours", abs(model_input.get("Sleep_Hours", 0.0)), "decreases_risk"),
    ]
    top_factors = sorted(factor_candidates, key=lambda item: item[1], reverse=True)[:4]

    return {
        "risk_label": CLASS_NAMES[risk_index],
        "risk_probabilities": {
            label: round(float(probabilities[i]), 4)
            for i, label in enumerate(CLASS_NAMES)
        },
        "top_factors": [
            {
                "feature": feature,
                "shap_value": round(float(value), 4),
                "direction": direction,
                "cohort_percentile": 50,
                "counterfactual": f"Decreasing your {feature.replace('_', ' ')} is associated with lower risk." if direction == "increases_risk" else f"Maintaining your {feature.replace('_', ' ')} helps protect against higher risk."
            }
            for feature, value, direction in top_factors
        ],
    }


def explain_prediction(model_input: Dict[str, float]) -> Dict[str, Any]:
    try:
        return json.loads(_load_explainer().explain(model_input))
    except Exception as e:
        import traceback
        traceback.print_exc()
        res = _fallback_explain(model_input)
        res["fallback_error"] = str(e)
        return res


def _factor_text(top_factors: List[Dict[str, Any]]) -> str:
    lines = []
    for factor in top_factors:
        name = FEATURE_DISPLAY_NAMES.get(factor["feature"], factor["feature"])
        direction = (
            "pushed risk upward"
            if factor["direction"] == "increases_risk"
            else "acted as a protective signal"
        )
        lines.append(f"- {name}: {direction}.")
    return "\n".join(lines)


def _deterministic_report(shap_json: Dict[str, Any], gate_result: Dict[str, Any]) -> Dict[str, Any]:
    risk_label = shap_json["risk_label"]
    probabilities = shap_json["risk_probabilities"]

    if gate_result["is_high_risk"]:
        return {
            "explanation": gate_result["response"],
            "wellness_suggestions": None,
            "qa_response": None,
            "crisis_mode": True,
        }

    factors = _factor_text(shap_json["top_factors"])
    
    nudge = gate_result.get("response", "") if not gate_result["is_high_risk"] else ""
    if nudge:
        nudge += "\n\n"
        
    explanation = (
        f"{nudge}The screening suggests a {risk_label.lower()} current risk pattern. "
        f"The model estimated Low {probabilities['Low']:.0%}, "
        f"Moderate {probabilities['Moderate']:.0%}, and High {probabilities['High']:.0%}. "
        "This is not a diagnosis; it is a structured screening result.\n\n"
        f"The main model signals were:\n{factors}\n\n"
        "If this result feels concerning or does not match your lived experience, "
        "consider speaking with a campus counsellor or mental health professional."
    )

    # Append the extended user context to the deterministic explanation so it's not lost
    ext_context_str = _format_extended_context(shap_json)
    if ext_context_str:
        explanation += "\n\n### Your Provided Context\n" + ext_context_str.replace("[User's Self-Reported Context - Use ONLY for Personalization]", "").strip()

    suggestions = (
        "- Pick one sleep routine change for the next week, such as a consistent wake time.\n"
        "- Break academic work into one focused 25-minute block before expanding the plan.\n"
        "- Add a short walk, stretch, or light activity on study days.\n"
        "- Share the result with a trusted person if support feels useful.\n"
        "- Re-take the screening later only as a check-in, not as a diagnosis."
    )

    return {
        "explanation": explanation,
        "wellness_suggestions": suggestions,
        "weekly_plan": None,
        "qa_response": None,
        "crisis_mode": False,
    }


def assemble_report(raw_answers: Dict[str, Any], question: str | None = None, previous_report: Dict[str, Any] | None = None) -> Dict[str, Any]:
    model_input = normalize_answers(raw_answers)
    shap_json = explain_prediction(model_input)
    
    is_trending_up = False
    if previous_report:
        curr_label = shap_json["risk_label"]
        prev_label = previous_report.get("risk_label")
        if prev_label == "Low" and curr_label == "Moderate":
            is_trending_up = True
        elif prev_label == "Moderate" and curr_label == "High":
            is_trending_up = True
        elif shap_json["risk_probabilities"].get("High", 0) - previous_report.get("risk_probabilities", {}).get("High", 0) > 0.1:
            is_trending_up = True
            
    shap_json["is_trending_up"] = is_trending_up
    
    # Inject the extended context (the new optional fields) for the LLM prompt builder
    shap_json["extended_context"] = raw_answers
    
    gate_result = check_risk_gate(shap_json)

    report_parts = None
    llm_was_used = False
    
    if os.getenv("ISCOR_USE_LLM", "0") == "1" and not gate_result["is_high_risk"]:
        logging.info("Taking 'llm' path for screening report generation.")
        try:
            from llm_service import process_screening
            report_parts = process_screening(shap_json, user_question=question)
            llm_was_used = True
        except Exception as e:
            logging.error(f"LLM path failed ({e}), falling back to deterministic.")
            report_parts = None
    else:
        if gate_result["is_high_risk"]:
            logging.info("Taking 'deterministic_fallback' path because risk is High (safety gate).")
        else:
            logging.info("Taking 'deterministic_fallback' path because ISCOR_USE_LLM != 1.")

    if report_parts is None:
        report_parts = _deterministic_report(shap_json, gate_result)

    return {
        "input": raw_answers,
        "model_input": model_input,
        "risk_label": shap_json["risk_label"],
        "risk_probabilities": shap_json["risk_probabilities"],
        "top_factors": shap_json["top_factors"],
        "explanation": report_parts["explanation"],
        "wellness_suggestions": report_parts.get("wellness_suggestions"),
        "weekly_plan": report_parts.get("weekly_plan"),
        "qa_response": report_parts.get("qa_response"),
        "question": question,
        "crisis_mode": bool(report_parts["crisis_mode"]),
        "llm_mode": llm_was_used,
        "fallback_error": shap_json.get("fallback_error"),
        "retrieved_evidence": report_parts.get("retrieved_evidence", [])
    }
