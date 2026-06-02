import os
import json
from integration.service import assemble_report

def main():
    test_cases = [
        {
            "id": 1,
            "desc": "Low Risk (Healthy Sleep & Low Stress)",
            "payload": {
                "age": 20,
                "gender": "Female",
                "sleep_hours": 8.0,
                "academic_pressure": 1,
                "financial_stress": 1,
                "social_support": "High",
                "study_hours": 3.0,
                "physical_activity": 5.0,
                "family_history": "No"
            }
        },
        {
            "id": 2,
            "desc": "Moderate Risk (Moderate Academic Pressure)",
            "payload": {
                "age": 21,
                "gender": "Male",
                "sleep_hours": 6.5,
                "academic_pressure": 3,
                "financial_stress": 2,
                "social_support": "Moderate",
                "study_hours": 6.0,
                "physical_activity": 2.0,
                "family_history": "No"
            }
        },
        {
            "id": 3,
            "desc": "Moderate Risk (Poor Sleep & High Study)",
            "payload": {
                "age": 19,
                "gender": "Other",
                "sleep_hours": 5.0,
                "academic_pressure": 4,
                "financial_stress": 1,
                "social_support": "Moderate",
                "study_hours": 9.0,
                "physical_activity": 1.0,
                "family_history": "No"
            }
        },
        {
            "id": 4,
            "desc": "High Risk (Crisis Mode)",
            "payload": {
                "age": 24,
                "gender": "Female",
                "sleep_hours": 3.0,
                "academic_pressure": 5,
                "financial_stress": 5,
                "social_support": "Low",
                "study_hours": 12.0,
                "physical_activity": 0.0,
                "family_history": "Yes"
            }
        }
    ]

    os.makedirs("evaluation_results", exist_ok=True)
    results = []

    for case in test_cases:
        print(f"Running Case {case['id']}: {case['desc']}")
        try:
            report = assemble_report(case["payload"], question=None, previous_report=None)
            results.append({
                "id": case["id"],
                "desc": case["desc"],
                "risk_label": report.get("risk_label"),
                "top_factors": [f["feature"] for f in report.get("top_factors", [])],
                "explanation": report.get("explanation", ""),
                "wellness_suggestions": report.get("wellness_suggestions", ""),
                "weekly_plan": report.get("weekly_plan", ""),
                "crisis_mode": report.get("crisis_mode", False)
            })
        except Exception as e:
            print(f"Error on Case {case['id']}: {e}")

    with open("evaluation_results/eval_outputs.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
        
    print("Evaluation set generated successfully.")

if __name__ == "__main__":
    main()
