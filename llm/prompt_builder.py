"""
Prompt Builder — ISCOR AI
Converts the structured SHAP JSON contract into the precise prompt payloads
that are passed to the LLM. The LLM NEVER sees raw questionnaire data.
"""

import json


# Human-readable names for feature columns
FEATURE_DISPLAY_NAMES = {
    "Age": "Age",
    "Gender": "Gender",
    "Sleep_Hours": "Sleep Duration",
    "Academic_Pressure": "Academic Pressure",
    "Financial_Stress": "Financial Stress",
    "Social_Support": "Social Support",
    "Study_Hours": "Study Hours",
    "Physical_Activity": "Physical Activity",
    "Family_History": "Family History of Mental Illness",
    "Stress_Index": "Overall Stress Index",
    "Lifestyle_Score": "Overall Lifestyle Score",
    "Academic_Load": "Academic Workload",
}


def format_top_factors(top_factors: list) -> str:
    """Formats the SHAP top_factors list into a readable bullet list for the prompt."""
    lines = []
    for f in top_factors:
        display_name = FEATURE_DISPLAY_NAMES.get(f["feature"], f["feature"])
        arrow = "↑ Increases" if f["direction"] == "increases_risk" else "↓ Reduces"
        lines.append(f"  - {display_name}: {arrow} mental health risk (strength: {f['shap_value']:.3f})")
    return "\n".join(lines)


def format_retrieved_knowledge(retrieved_evidence: list) -> str:
    """Formats retrieved RAG chunks into a structured prompt section."""
    if not retrieved_evidence:
        return "No specific evidence retrieved."
    lines = []
    for idx, chunk in enumerate(retrieved_evidence, 1):
        lines.append(f"Chunk {idx} (Source: {chunk['source']} - {chunk['document']}):\n{chunk['text']}")
    return "\n\n".join(lines)


def _format_extended_context(shap_json: dict) -> str:
    """Formats the optional new health context fields into a string for the LLM."""
    ext = shap_json.get("extended_context", {})
    if not ext:
        return ""
    
    lines = ["\n[User's Self-Reported Context - Use ONLY for Personalization]"]
    
    # Core Mental Wellness
    if ext.get("sleep_quality"): lines.append(f"- Sleep Quality: {ext['sleep_quality']}/5")
    if ext.get("mood"): lines.append(f"- Mood: {ext['mood']}/5")
    if ext.get("anxiety"): lines.append(f"- Anxiety Frequency: {ext['anxiety']}/5")
    if ext.get("energy_level"): lines.append(f"- Energy Level: {ext['energy_level']}/5")
    if ext.get("concentration"): lines.append(f"- Difficulty Concentrating: {ext['concentration']}/5")
    if ext.get("loneliness"): lines.append(f"- Loneliness: {ext['loneliness']}/5")
    if ext.get("appetite_changes"): lines.append(f"- Appetite Changes: {ext['appetite_changes']}")
    if ext.get("major_life_events") and len(ext["major_life_events"]) > 0: 
        lines.append(f"- Major Life Events (last 6mo): {', '.join(ext['major_life_events'])}")
    if ext.get("screen_time") is not None: lines.append(f"- Screen Time: {ext['screen_time']} hrs/day")
    
    # Protective Factors
    has_protective = any(k in ext and ext[k] is not None for k in ["family_support", "friend_support", "hobbies", "ability_to_relax", "life_satisfaction"])
    if has_protective:
        lines.append("- Protective Factors (1-5 scale): " + ", ".join([f"{k.replace('_', ' ')}: {ext[k]}" for k in ["family_support", "friend_support", "hobbies", "ability_to_relax", "life_satisfaction"] if ext.get(k)]))
        
    # Health Context
    health_items = []
    if ext.get("recent_illness"): health_items.append("Recent serious illness")
    if ext.get("chronic_condition"): health_items.append("Chronic medical condition")
    if ext.get("medication"): health_items.append("Medication affecting mood")
    if ext.get("surgery"): health_items.append("Recent surgery")
    if ext.get("substance_use"): health_items.append("Substance use")
    if health_items: lines.append(f"- Health Context Flags: {', '.join(health_items)}")
    
    if ext.get("health_notes"): lines.append(f"- Additional Health Notes: {ext['health_notes']}")
    
    # Female-specific
    female_items = []
    if ext.get("menstrual_status"): female_items.append(f"Status: {ext['menstrual_status']}")
    if ext.get("cycle_phase"): female_items.append(f"Phase: {ext['cycle_phase']}")
    if ext.get("pms_pmdd"): female_items.append("Experiences PMS/PMDD")
    if ext.get("pregnancy_status"): female_items.append("Pregnant")
    if ext.get("postpartum_status"): female_items.append("Postpartum")
    if ext.get("menopause"): female_items.append("Menopause/Perimenopause")
    if female_items: lines.append(f"- Specific Health Context: {', '.join(female_items)}")
    
    if len(lines) == 1:
        return "" # No actual context appended
        
    return "\n".join(lines)


def build_explanation_prompt(shap_json: dict) -> str:
    """
    Builds the system + user prompt for Generation 1: Plain-language explanation.
    """
    risk_label = shap_json["risk_label"]
    probabilities = shap_json["risk_probabilities"]
    top_factors_text = format_top_factors(shap_json["top_factors"])

    consultation_reminder = ""
    if risk_label in ["Moderate", "High"]:
        consultation_reminder = (
            "\n\nIMPORTANT: You MUST include a line at the end encouraging the user to "
            "speak with a mental health professional or campus counsellor."
        )

    system_prompt = (
        "You are a wellness communication assistant for a student mental health screening tool. "
        "You translate machine learning results into clear, supportive, non-clinical language.\n\n"
        "STRICT RULES — you must follow all of these:\n"
        "1. NEVER state or imply a clinical diagnosis (e.g. do not say 'you have depression').\n"
        "2. Always frame findings as 'the screening suggests' or 'your responses indicate', never as certainties.\n"
        "3. Base your explanation ONLY on the contributing factors listed below. Do NOT invent new causes.\n"
        "4. Use the Optional Health Context ONLY to personalize the tone. NEVER diagnose based on it.\n"
        "5. You MUST format your response using EXACTLY these Markdown headers:\n"
        "   ### Overall Wellness Summary\n"
        "   ### Potential Stress Contributors\n"
        "   ### Health Context Notes\n"
        f"6. Keep your response to 3–4 short paragraphs.{consultation_reminder}"
    )

    extended_context = _format_extended_context(shap_json)

    user_prompt = (
        f"A student has completed a mental health screening. Here are the results:\n\n"
        f"Risk Level: {risk_label}\n"
        f"Probability Breakdown: Low={probabilities['Low']:.0%}, "
        f"Moderate={probabilities['Moderate']:.0%}, High={probabilities['High']:.0%}\n\n"
        f"Key contributing factors identified by the model:\n{top_factors_text}\n"
        f"{extended_context}\n\n"
        f"Task:\nPlease write a plain-language explanation of these results using the required Markdown headers."
    )

    return system_prompt, user_prompt


def build_wellness_prompt(shap_json: dict) -> str:
    """
    Builds the system + user prompt for Generation 2: Wellness suggestions.
    Only called if risk_label is NOT High (enforced by risk_gate).
    """
    top_factors_text = format_top_factors(shap_json["top_factors"])
    risk_label = shap_json["risk_label"]

    system_prompt = (
        "You are a wellness communication assistant. You provide general, lifestyle-level wellness "
        "suggestions based on machine learning screening results. You are NOT a therapist or medical professional.\n\n"
        "STRICT RULES:\n"
        "1. Only suggest lifestyle-level interventions: sleep hygiene, physical activity, social connection, "
        "study habits, relaxation techniques. Do NOT recommend medications, therapy, or clinical treatments.\n"
        "2. Use ONLY the retrieved guidance below to generate general wellness recommendations. Paraphrase the guidance, do NOT quote at length.\n"
        "3. Do not invent recommendations beyond the retrieved evidence. If evidence is insufficient, state that additional professional guidance may be appropriate.\n"
        "4. Frame every suggestion as an option to explore, never as a prescription.\n"
        "5. Keep tone positive and empowering — focus on small, achievable steps.\n"
        "6. Provide exactly 4–5 specific, actionable suggestions.\n"
        "7. Do NOT diagnose or imply a clinical condition.\n"
        "8. You MUST format your response using EXACTLY these Markdown headers:\n"
        "   ### Protective Factors Summary\n"
        "   ### Lifestyle Balance\n"
        "   ### Personalized Strengths\n"
        "   ### Areas to Focus On\n"
        "   ### Personalized Wellness Suggestions\n"
        "   ### Healthy Habits Score (Provide a creative score out of 100 based on their protective factors)"
    )

    extended_context = _format_extended_context(shap_json)
    retrieved_text = format_retrieved_knowledge(shap_json.get("retrieved_evidence", []))

    user_prompt = (
        f"A student received a '{risk_label}' mental health risk screening result.\n\n"
        f"The key contributing factors were:\n{top_factors_text}\n"
        f"{extended_context}\n\n"
        f"Retrieved Knowledge:\n{retrieved_text}\n\n"
        f"Task:\nPlease provide general wellness suggestions following the STRICT RULES and Markdown headers."
    )

    return system_prompt, user_prompt


def build_weekly_plan_prompt(shap_json: dict) -> str:
    """
    Builds the system + user prompt for Generation 4: Weekly micro-plan.
    Only called if risk_label is NOT High (enforced by risk_gate).
    """
    top_factors_text = format_top_factors(shap_json["top_factors"])
    risk_label = shap_json["risk_label"]

    system_prompt = (
        "You are a wellness communication assistant. You provide a simple 7-day lifestyle plan "
        "based on machine learning screening results. You are NOT a therapist or medical professional.\n\n"
        "STRICT RULES:\n"
        "1. Only suggest lifestyle-level interventions (e.g. sleep hygiene, light exercise, study breaks). "
        "Do NOT recommend medications, therapy, or clinical treatments.\n"
        "2. Use ONLY the retrieved guidance below to generate the plan. Paraphrase the guidance, do NOT quote at length. Do not invent recommendations beyond the retrieved evidence.\n"
        "3. Provide exactly 7 simple, achievable daily steps (Day 1 to Day 7).\n"
        "4. Do NOT diagnose or imply a clinical condition.\n"
        "5. Keep the plan highly actionable and very brief (one sentence per day)."
    )

    retrieved_text = format_retrieved_knowledge(shap_json.get("retrieved_evidence", []))

    user_prompt = (
        f"A student received a '{risk_label}' mental health risk screening result.\n\n"
        f"The key contributing factors were:\n{top_factors_text}\n\n"
        f"Retrieved Knowledge:\n{retrieved_text}\n\n"
        f"Task:\nPlease provide a simple 7-day lifestyle plan (Day 1 to Day 7) tailored to these factors, "
        f"grounded STRICTLY in the Retrieved Knowledge."
    )

    return system_prompt, user_prompt



def build_qa_system_prompt(shap_json: dict) -> str:
    """
    Returns the system prompt for Generation 3: Constrained Q&A.
    """
    retrieved_text = format_retrieved_knowledge(shap_json.get("retrieved_evidence", []))
    return (
        "You are a wellness information assistant for a student mental health screening tool. "
        "You answer general psychoeducation questions about mental health, stress, sleep, and wellness.\n\n"
        "STRICT RULES:\n"
        "1. NEVER answer questions that request or imply a clinical diagnosis.\n"
        "2. NEVER provide medication names, dosages, or advice about clinical treatments.\n"
        "3. If asked about self-harm, suicidal thoughts, or crisis situations, you MUST respond ONLY with: "
        "'This is beyond what I can help with here. Please contact a crisis support line immediately. "
        "In India: iCall at 9152987821 or AASRA at +91 22 2754 6669.'\n"
        "4. NEVER claim to be a therapist, doctor, or counsellor.\n"
        "5. If a question is outside general wellness/psychoeducation, politely decline and suggest "
        "speaking with a professional.\n"
        "6. Keep all answers to 2–3 short paragraphs maximum.\n"
        "USE ONLY the retrieved guidance below to generate your answer. Paraphrase the guidance, do NOT quote at length. If the answer is not in the text, say you don't know.\n\n"
        f"Retrieved Knowledge:\n{retrieved_text}"
    )


def build_personality_summary_prompt(scores: dict) -> str:
    """
    Builds the system + user prompt for generating a self-reflection summary from Big Five (OCEAN) scores.
    """
    system_prompt = (
        "You are an encouraging, non-clinical wellness companion helping a student reflect on their personality traits.\n\n"
        "STRICT RULES:\n"
        "1. Treat this as a self-reflection exercise, NOT a psychological diagnosis.\n"
        "2. Do NOT use clinical jargon or diagnose conditions (e.g. avoid 'you have anxiety' or 'you are clinically neurotic').\n"
        "3. Focus on how these traits might influence their university experience (e.g. study habits, social life, stress response).\n"
        "4. Frame both high and low scores as having potential strengths and challenges. (e.g. low extraversion can mean deep focus).\n"
        "5. Keep the response to 2-3 short, highly encouraging paragraphs.\n"
        "6. Always remind the user that personality is fluid and self-reported scores are just a snapshot."
    )

    user_prompt = (
        f"A student has completed a Big Five personality self-assessment with the following scores (1 to 5 scale, 3 being neutral):\n\n"
        f"- Openness: {scores.get('O', 3)}/5\n"
        f"- Conscientiousness: {scores.get('C', 3)}/5\n"
        f"- Extraversion: {scores.get('E', 3)}/5\n"
        f"- Agreeableness: {scores.get('A', 3)}/5\n"
        f"- Neuroticism: {scores.get('N', 3)}/5\n\n"
        f"Please write a short, encouraging self-reflection summary based on these scores."
    )

    return system_prompt, user_prompt


def build_companion_prompt(history: list, latest_report: dict, personality_summary: str, new_message: str, retrieved_evidence: list = None) -> tuple[str, str]:
    """
    Builds the system + user prompt for the persistent Wellness Companion chat.
    Incorporates past context if available.
    """
    system_prompt = (
        "You are a supportive, encouraging Wellness Companion for a university student.\n\n"
        "STRICT RULES:\n"
        "1. You are NOT a therapist or clinician. NEVER diagnose conditions or recommend medications.\n"
        "2. Keep responses highly conversational, warm, and relatively brief (1-3 short paragraphs).\n"
        "3. If the user discusses self-harm, suicide, or severe crisis, you MUST reply ONLY with: "
        "'This is beyond what I can help with here. Please contact a crisis support line immediately. "
        "In India: iCall at 9152987821 or AASRA at +91 22 2754 6669.'\n"
        "4. Draw softly on the user's context (screening results, personality traits) if relevant, but don't force it awkwardly.\n"
        "5. USE ONLY the retrieved guidance below to answer wellness questions. Paraphrase the guidance, do NOT quote at length. If the answer is not in the text, rely on general wellness knowledge but do NOT diagnose.\n"
    )

    if retrieved_evidence:
        evidence_str = "\n\n".join([f"Source {i+1}:\n{doc}" for i, doc in enumerate(retrieved_evidence)])
        system_prompt += f"\n[RETRIEVED KNOWLEDGE]\n{evidence_str}"

    context_lines = []
    if latest_report:
        context_lines.append(f"User's latest screening risk level: {latest_report.get('risk_label', 'Unknown')}.")
        if latest_report.get("top_factors"):
            factors = ", ".join(f["feature"].replace("_", " ") for f in latest_report["top_factors"][:2])
            context_lines.append(f"Top stress factors identified: {factors}.")
            
        ext_context_str = _format_extended_context({"extended_context": latest_report.get("input", {})})
        if ext_context_str:
            context_lines.append(ext_context_str)

    if personality_summary:
        context_lines.append(f"\nUser's self-reflection: {personality_summary}")

    context_str = "\n".join(context_lines) if context_lines else "No specific background context available."
    
    # Format chat history
    history_str = ""
    if history:
        history_lines = []
        for msg in history[-6:]: # Last 6 messages for context
            history_lines.append(f"{msg['role'].capitalize()}: {msg['content']}")
        history_str = "\n".join(history_lines) + "\n\n"

    user_prompt = (
        f"[SYSTEM BACKGROUND CONTEXT (Do not mention explicitly unless asked)]\n{context_str}\n\n"
        f"[CHAT HISTORY]\n{history_str}"
        f"User: {new_message}\n"
        f"Companion:"
    )

    return system_prompt, user_prompt
