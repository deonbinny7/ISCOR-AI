import os
import sys
from pathlib import Path

# Add llm directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "llm"))

from llm_service import API_KEYS, GROQ_KEYS, MODEL_NAME
from prompt_builder import build_wellness_prompt

test_shap = {
    "risk_label": "Moderate",
    "risk_probabilities": {"Low": 0.20, "Moderate": 0.60, "High": 0.20},
    "top_factors": [
        {"feature": "Academic_Pressure", "shap_value": 0.31, "direction": "increases_risk"},
        {"feature": "Sleep_Hours", "shap_value": 0.28, "direction": "increases_risk"},
    ],
    "retrieved_evidence": [
        {
            "chunk_id": "cdc_stress_1",
            "source": "CDC",
            "document": "Stress Management",
            "text": "Taking breaks during study sessions can improve focus and reduce academic pressure. Aim for 7-9 hours of sleep.",
            "similarity_score": 0.85
        }
    ]
}

def check_providers():
    print("Running Provider Consistency Check...\n")
    system_prompt, user_prompt = build_wellness_prompt(test_shap)
    
    # 1. Gemini
    if API_KEYS[0]:
        print(f"--- Testing Gemini ({MODEL_NAME}) ---")
        try:
            from google import genai
            client = genai.Client(api_key=API_KEYS[0])
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=f"{system_prompt}\n\n---\n\n{user_prompt}"
            )
            print(response.text)
        except Exception as e:
            print(f"Gemini failed: {e}")
    else:
        print("Gemini Key 1 not found.")
        
    print("\n\n")
    
    # 2. Groq
    if GROQ_KEYS[0]:
        print(f"--- Testing Groq (llama-3.3-70b-versatile) ---")
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {GROQ_KEYS[0]}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            print(resp.json()["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"Groq failed: {e}")
    else:
        print("Groq Key 1 not found.")

if __name__ == "__main__":
    check_providers()
