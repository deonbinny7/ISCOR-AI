"""
Risk Gate / Safety Router — ISCOR AI
This module sits between the SHAP explainability layer and the LLM.
It is the FIRST thing that runs after a prediction is made.

Key rule: If risk_label == 'High', the LLM is NEVER called.
The system returns a pre-approved, fixed crisis-resource message instead.
This ensures no hallucinated or minimising responses can reach a High Risk user.
"""

import logging

# Margin for close-call probabilities where 'High' risk is escalated
HIGH_RISK_MARGIN = 0.1

CRISIS_MESSAGE = """
🚨 **Important: Please Seek Support**

The screening tool has identified indicators that suggest you may be experiencing significant distress right now. 

**This is not a diagnosis**, but based on your responses, we strongly encourage you to speak with a mental health professional or crisis support service as soon as possible.

---

**Immediate Support Resources:**

- **iCall (India):** 9152987821 — Mon-Sat, 8am-10pm
- **Vandrevala Foundation Helpline:** 1860-2662-345 (24/7)
- **AASRA (India):** +91 22 2754 6669 (24/7)
- **International Association for Suicide Prevention:** https://www.iasp.info/resources/Crisis_Centres/

---

**Please remember:**
- You are not alone.
- Professional support is available and effective.
- This tool is a screening aid only — a qualified professional can give you real, personalised help.

If you are in immediate danger, please contact emergency services or go to your nearest hospital emergency room.
"""

WELLNESS_BLOCKED_MESSAGE = """
Based on your responses, our screening tool suggests elevated risk indicators. 

Wellness suggestions are not appropriate at this level of risk. Instead, please refer to the support resources above, or speak to a campus counsellor or mental health professional.
"""


# Fail-safe philosophy: when uncertain, treat as High — false positives here cost far less than false negatives.
def check_risk_gate(shap_json: dict) -> dict:
    """
    Evaluates the SHAP JSON contract from the ML/SHAP layer.
    
    Returns a gate_result dict:
      - is_high_risk (bool): whether the gate intercepted the request
      - response (str | None): the crisis message if intercepted, else None
    """
    risk_label = shap_json.get("risk_label", "").strip()
    
    if risk_label not in ("Low", "Moderate", "High"):
        logging.warning(f"Anomaly detected: Unexpected risk_label '{risk_label}'. Defaulting to High risk.")
        risk_label = "High"
        
    if risk_label != "High":
        probs = shap_json.get("risk_probabilities", {})
        if probs:
            high_prob = probs.get("High", 0.0)
            max_prob = max(probs.values())
            if max_prob - high_prob <= HIGH_RISK_MARGIN:
                logging.warning(f"Close-call detected: High probability ({high_prob}) is within {HIGH_RISK_MARGIN} of max probability ({max_prob}). Escalating to High risk.")
                risk_label = "High"
    
    is_trending_up = shap_json.get("is_trending_up", False)
    
    if risk_label == "High":
        return {
            "is_high_risk": True,
            "response": CRISIS_MESSAGE.strip(),
            "wellness_blocked": True,
            "risk_label": risk_label,
            "is_trending_up": is_trending_up
        }
        
    if risk_label == "Moderate" and is_trending_up:
        nudge = "**Note on your trend**: Based on your recent screenings, your risk indicators appear to be increasing. While not currently at a crisis level, we strongly recommend discussing these feelings with a campus counsellor."
        return {
            "is_high_risk": False,
            "response": nudge,
            "wellness_blocked": False,
            "risk_label": risk_label,
            "is_trending_up": is_trending_up
        }
    
    return {
        "is_high_risk": False,
        "response": None,
        "wellness_blocked": False,
        "risk_label": risk_label,
        "is_trending_up": is_trending_up
    }


def check_chat_safety(user_message: str) -> dict:
    """
    Evaluates a user chat message for acute distress or crisis language.
    If detected, returns a high risk response to bypass the LLM.
    """
    distress_keywords = [
        "suicide", "kill myself", "want to die", "end it all",
        "hurt myself", "self-harm", "panic attack", "can't breathe",
        "overdose", "give up on life"
    ]
    
    msg_lower = user_message.lower()
    for kw in distress_keywords:
        if kw in msg_lower:
            logging.warning(f"Chat Safety Gate triggered by keyword: {kw}")
            return {
                "is_high_risk": True,
                "response": CRISIS_MESSAGE.strip(),
            }
            
    return {
        "is_high_risk": False,
        "response": None
    }



if __name__ == "__main__":
    # --- TEST: High Risk should be intercepted ---
    test_high = {
        "risk_label": "High",
        "risk_probabilities": {"Low": 0.05, "Moderate": 0.15, "High": 0.80},
        "top_factors": [
            {"feature": "Sleep_Hours", "shap_value": 0.55, "direction": "increases_risk"}
        ]
    }
    result = check_risk_gate(test_high)
    assert result["is_high_risk"] == True, "FAILED: High Risk was NOT intercepted!"
    print("✅ Test PASSED: High Risk correctly intercepted by Risk Gate.")
    print(f"\n--- Crisis Message Preview ---\n{result['response'][:200]}...\n")

    # --- TEST: Moderate Risk should pass through ---
    test_moderate = {
        "risk_label": "Moderate",
        "risk_probabilities": {"Low": 0.20, "Moderate": 0.60, "High": 0.20},
        "top_factors": []
    }
    result2 = check_risk_gate(test_moderate)
    assert result2["is_high_risk"] == False, "FAILED: Moderate Risk was incorrectly intercepted!"
    print("✅ Test PASSED: Moderate Risk correctly passed through the Risk Gate.")

    # --- TEST: Low Risk should pass through ---
    test_low = {
        "risk_label": "Low",
        "risk_probabilities": {"Low": 0.85, "Moderate": 0.10, "High": 0.05},
        "top_factors": []
    }
    result3 = check_risk_gate(test_low)
    assert result3["is_high_risk"] == False, "FAILED: Low Risk was incorrectly intercepted!"
    print("✅ Test PASSED: Low Risk correctly passed through the Risk Gate.")

    # --- TEST: Malformed/unexpected label string ---
    test_malformed = {
        "risk_label": "UnknownLabel",
        "risk_probabilities": {"Low": 0.5, "Moderate": 0.3, "High": 0.2},
        "top_factors": []
    }
    result4 = check_risk_gate(test_malformed)
    assert result4["is_high_risk"] == True, "FAILED: Malformed label was NOT escalated to High!"
    print("✅ Test PASSED: Malformed label correctly escalated to High (Fail-safe).")

    # --- TEST: Close-call probability distribution ---
    test_close_call = {
        "risk_label": "Moderate",
        "risk_probabilities": {"Low": 0.1, "Moderate": 0.5, "High": 0.4},
        "top_factors": []
    }
    result5 = check_risk_gate(test_close_call)
    assert result5["is_high_risk"] == True, "FAILED: Close-call probability was NOT escalated to High!"
    print("✅ Test PASSED: Close-call probability correctly escalated to High.")

    print("\n🛡️  All Risk Gate tests passed. Zero exceptions possible.")
