"""
LLM Service — ISCOR AI
Orchestrates the three constrained generation pipelines (explanation, wellness, Q&A)
using the Gemini API with primary and fallback API keys.

Architecture:
  SHAP JSON → Risk Gate → Prompt Builder → LLM Service → Report Assembler
"""

import os
import json
import time
import logging
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv
from risk_gate import check_risk_gate, check_chat_safety, CRISIS_MESSAGE
from prompt_builder import (
    build_explanation_prompt, 
    build_wellness_prompt, 
    build_qa_system_prompt, 
    build_weekly_plan_prompt, 
    build_personality_summary_prompt,
    build_companion_prompt
)
from rag_service import retrieve_evidence, search_knowledge_base

# Load keys from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5"),
    os.getenv("GEMINI_API_KEY_6"),
    os.getenv("GEMINI_API_KEY_7"),
]



MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def _get_client(api_key: str):
    """Initialise a Gemini client with a given key."""
    return genai.Client(api_key=api_key)


FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
]

import random
import requests

def _call_llm(system_prompt: str, user_prompt: str) -> tuple[str, str]:
    """
    Calls an LLM API. Iterates through Gemini keys.
    Returns (response_text, provider_name).
    """
    combined_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
    last_error = None
    
    for i, key in enumerate(API_KEYS):
        if not key: continue
        try:
            client = _get_client(key)
            logging.info(f"[LLM] Firing Gemini call to {MODEL_NAME} (Key {i+1})...")
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=combined_prompt
            )
            return response.text, "Gemini"
        except Exception as e:
            last_error = e
            logging.warning(f"[LLM] Gemini (Key {i+1}) failed: {e}")

    raise RuntimeError(f"All Gemini keys failed. Last error: {last_error}")


def generate_explanation(shap_json: dict) -> tuple[str, str]:
    """
    Generation 1: Plain-language explanation of the top SHAP factors.
    """
    system_prompt, user_prompt = build_explanation_prompt(shap_json)
    return _call_llm(system_prompt, user_prompt)


def generate_wellness_suggestions(shap_json: dict) -> tuple[str, str]:
    """
    Generation 2: General wellness suggestions (lifestyle-level only).
    Only called if the Risk Gate has confirmed risk is NOT High.
    """
    system_prompt, user_prompt = build_wellness_prompt(shap_json)
    return _call_llm(system_prompt, user_prompt)


def generate_weekly_plan(shap_json: dict) -> tuple[str, str]:
    """
    Generation 4: Weekly micro-plan (7-day lifestyle plan).
    Only called if the Risk Gate has confirmed risk is NOT High.
    """
    system_prompt, user_prompt = build_weekly_plan_prompt(shap_json)
    return _call_llm(system_prompt, user_prompt)


def answer_user_question(question: str, shap_json: dict) -> tuple[str, str]:
    """
    Generation 3: Constrained Q&A with hard refusal rules.
    Checks for crisis-adjacent language before calling the LLM.
    """
    CRISIS_KEYWORDS = [
        "self-harm", "suicide", "kill myself", "end my life",
        "hurt myself", "don't want to live", "want to die"
    ]
    question_lower = question.lower()
    if any(kw in question_lower for kw in CRISIS_KEYWORDS):
        return (
            "This is beyond what I can help with here. Please contact a crisis support line immediately.\n\n"
            "In India:\n"
            "- **iCall:** 9152987821 (Mon-Sat, 8am-10pm)\n"
            "- **AASRA:** +91 22 2754 6669 (24/7)\n"
            "- **Vandrevala Foundation:** 1860-2662-345 (24/7)\n\n"
            "If you are in immediate danger, please go to your nearest hospital emergency room."
        ), "System (Crisis Trigger)"

    system_prompt = build_qa_system_prompt(shap_json)
    user_prompt = f"Student question: {question}"
    return _call_llm(system_prompt, user_prompt)


def generate_personality_summary(scores: dict) -> tuple[str, str]:
    """
    Generation 5: Short self-reflection summary for Big Five personality scores.
    """
    system_prompt, user_prompt = build_personality_summary_prompt(scores)
    return _call_llm(system_prompt, user_prompt)


def generate_companion_response(history: list, latest_report: dict, personality_summary: str, new_message: str) -> str:
    """
    Generation 6: Persistent Wellness Companion chat.
    Includes turn-by-turn crisis intercept.
    """
    safety_check = check_chat_safety(new_message)
    if safety_check["is_high_risk"]:
        return safety_check["response"]

    # PART 5 GAP FIX: Fetch RAG context based on chat topic
    retrieved_chunks = search_knowledge_base(new_message, top_k=3)

    system_prompt, user_prompt = build_companion_prompt(history, latest_report, personality_summary, new_message, retrieved_chunks)
    response_text, _ = _call_llm(system_prompt, user_prompt)
    return response_text


def process_screening(shap_json_str: str, user_question: str = None) -> dict:
    """
    Main orchestration function. Takes the SHAP JSON contract and returns
    a complete report dictionary ready for the Report Assembler.
    
    This is the single integration point for the FastAPI backend.
    """
    shap_json = json.loads(shap_json_str) if isinstance(shap_json_str, str) else shap_json_str

    # --- STEP 1: Risk Gate (always runs first, before any LLM call) ---
    gate_result = check_risk_gate(shap_json)

    if gate_result["is_high_risk"]:
        return {
            "risk_label": shap_json["risk_label"],
            "risk_probabilities": shap_json["risk_probabilities"],
            "top_factors": shap_json["top_factors"],
            "explanation": gate_result["response"],
            "wellness_suggestions": None,
            "weekly_plan": None,
            "qa_response": None,
            "crisis_mode": True,
        }

    # --- STEP 1.5: Retrieve Evidence from Knowledge Base ---
    print("[LLM] Retrieving evidence from Knowledge Base...")
    evidence_result = retrieve_evidence(shap_json)
    shap_json["retrieved_evidence"] = evidence_result["chunks"]

    # --- STEP 2: Generate explanation (for Low and Moderate) ---
    explanation, provider = generate_explanation(shap_json)
    
    nudge = gate_result.get("response", "")
    if nudge:
        explanation = f"{nudge}\n\n{explanation}"

    # --- STEP 3: Generate wellness suggestions (for Low and Moderate only) ---
    wellness, _ = generate_wellness_suggestions(shap_json)

    # --- STEP 4: Generate weekly micro-plan (for Low and Moderate only) ---
    weekly_plan, _ = generate_weekly_plan(shap_json)

    # --- STEP 5: Answer optional user question (Q&A mode) ---
    qa_response = None
    if user_question:
        qa_response, _ = answer_user_question(user_question, shap_json)

    return {
        "risk_label": shap_json["risk_label"],
        "risk_probabilities": shap_json["risk_probabilities"],
        "top_factors": shap_json["top_factors"],
        "explanation": explanation,
        "wellness_suggestions": wellness,
        "weekly_plan": weekly_plan,
        "qa_response": qa_response,
        "llm_provider": provider,
        "crisis_mode": False,
        "retrieved_evidence": shap_json.get("retrieved_evidence", [])
    }


if __name__ == "__main__":
    # ---- TEST 1: High Risk — must be intercepted by Risk Gate ----
    print("=" * 60)
    print("TEST 1: High Risk Input (must be blocked by Risk Gate)")
    print("=" * 60)
    high_risk_json = {
        "risk_label": "High",
        "risk_probabilities": {"Low": 0.05, "Moderate": 0.15, "High": 0.80},
        "top_factors": [
            {"feature": "Sleep_Hours", "shap_value": 0.55, "direction": "increases_risk"},
            {"feature": "Financial_Stress", "shap_value": 0.43, "direction": "increases_risk"},
        ]
    }
    result = process_screening(high_risk_json)
    assert result["crisis_mode"] == True, "FAIL: High Risk was NOT intercepted!"
    assert result["wellness_suggestions"] is None, "FAIL: Wellness was generated for High Risk!"
    print("✅ PASSED: High Risk blocked — crisis message returned, LLM never called.")
    print(f"\nCrisis response preview:\n{result['explanation'][:300]}...\n")

    # ---- TEST 2: Moderate Risk — should go through LLM ----
    print("=" * 60)
    print("TEST 2: Moderate Risk Input (LLM generates explanation + wellness)")
    print("=" * 60)
    moderate_json = {
        "risk_label": "Moderate",
        "risk_probabilities": {"Low": 0.20, "Moderate": 0.60, "High": 0.20},
        "top_factors": [
            {"feature": "Academic_Pressure", "shap_value": 0.31, "direction": "increases_risk"},
            {"feature": "Sleep_Hours", "shap_value": 0.28, "direction": "increases_risk"},
            {"feature": "Social_Support", "shap_value": 0.18, "direction": "decreases_risk"},
        ]
    }
    result2 = process_screening(moderate_json)
    assert result2["crisis_mode"] == False
    assert result2["explanation"] is not None and len(result2["explanation"]) > 50
    assert result2["wellness_suggestions"] is not None
    print("✅ PASSED: Moderate Risk — LLM generated explanation and wellness suggestions.")
    print(f"\nExplanation preview:\n{result2['explanation'][:400]}")
    print(f"\nWellness preview:\n{result2['wellness_suggestions'][:400]}")
