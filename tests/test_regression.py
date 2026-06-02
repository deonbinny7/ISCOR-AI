import requests

def test_api():
    print("Testing backend via FastAPI...")
    
    session_response = requests.post("http://127.0.0.1:8000/session", json={"consent": True})
    if session_response.status_code != 200:
        print("Backend not running or session failed. Status code:", session_response.status_code)
        print("Response:", session_response.text)
        return
    token = session_response.json().get("session_token")
    print(f"Session created: {token}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Test High Risk Gate
    high_risk_data = {
        "age": 21,
        "gender": "Male",
        "family_history": "Yes",
        "sleep_hours": 8,
        "study_hours": 4,
        "physical_activity": 3,
        "academic_pressure": 2,
        "financial_stress": 2,
        "social_support": "High",
        "consent": True,
        "question": "How can I maintain my current routine?"
    }
    
    print("Submitting screening...")
    response = requests.post("http://127.0.0.1:8000/screen", json=high_risk_data, headers=headers)
    report = response.json()
    import json
    with open("test_output.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("Report written to test_output.json")
        
    print("Regression tests complete.")

if __name__ == "__main__":
    test_api()
