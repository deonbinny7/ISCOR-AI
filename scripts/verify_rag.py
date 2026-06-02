import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'llm')))

from llm.llm_service import process_screening

def run_test_case(test_name, input_json, f, question=None):
    f.write(f"\n{'='*80}\n")
    f.write(f"TEST CASE: {test_name}\n")
    f.write(f"{'='*80}\n")
    
    result = process_screening(input_json, user_question=question)
    
    f.write("\n--- RETRIEVED EVIDENCE CHUNKS ---\n")
    chunks = result.get("retrieved_evidence", [])
    if not chunks:
        f.write("No evidence retrieved.\n")
    else:
        for i, chunk in enumerate(chunks, 1):
            f.write(f"\nChunk {i}:\n")
            f.write(f"[{chunk.get('source', 'unknown')}] {chunk.get('text', '')}\n")
            
    f.write("\n--- RESULTING LLM OUTPUT (Wellness Suggestions/QA) ---\n")
    if question:
        f.write(f"Q&A Response:\n{result.get('qa_response', 'None')}\n")
    else:
        f.write(f"Wellness Suggestions:\n{result.get('wellness_suggestions', 'None')}\n")
        
    f.write("\n\n")
    f.flush()


if __name__ == "__main__":
    test_1 = {
        "risk_label": "Moderate",
        "risk_probabilities": {"Low": 0.20, "Moderate": 0.60, "High": 0.20},
        "top_factors": [
            {"feature": "Sleep_Hours", "shap_value": 0.35, "direction": "increases_risk"},
        ]
    }
    
    test_2 = {
        "risk_label": "Moderate",
        "risk_probabilities": {"Low": 0.40, "Moderate": 0.50, "High": 0.10},
        "top_factors": [
            {"feature": "Academic_Pressure", "shap_value": 0.30, "direction": "increases_risk"},
            {"feature": "Financial_Stress", "shap_value": 0.25, "direction": "increases_risk"},
        ]
    }

    test_3_qa = {
        "risk_label": "Low",
        "risk_probabilities": {"Low": 0.80, "Moderate": 0.15, "High": 0.05},
        "top_factors": [
            {"feature": "Social_Support", "shap_value": 0.20, "direction": "decreases_risk"},
        ]
    }

    with open("verification_output.md", "w", encoding="utf-8") as f:
        run_test_case("1. Sleep Issues (Moderate Risk)", test_1, f)
        run_test_case("2. Academic & Financial Stress (Moderate Risk)", test_2, f)
        run_test_case("3. General Anxiety Q&A (Low Risk)", test_3_qa, f, question="How can I calm down quickly when I feel a panic attack coming on?")
