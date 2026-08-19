from typing import Literal, Optional, List

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

from .database import (
    create_session,
    fetch_latest_report,
    fetch_history,
    fetch_report_by_id,
    fetch_trend_data,
    init_db,
    persist_conversation,
    persist_screening,
    purge_expired_sessions,
    validate_session,
    save_personality_assessment,
    fetch_latest_personality_summary,
    add_companion_message,
    fetch_companion_history,
    add_mood_checkin,
    fetch_recent_moods
)
from .service import assemble_report


class ScreeningRequest(BaseModel):
    consent: bool = Field(..., description="Must be true before screening can run.")
    age: int = Field(..., ge=16, le=80)
    gender: Literal["Male", "Female", "Other"]
    sleep_hours: float = Field(..., ge=0, le=12)
    academic_pressure: int = Field(..., ge=1, le=5)
    financial_stress: int = Field(..., ge=1, le=5)
    social_support: Literal["Low", "Moderate", "High"]
    study_hours: float = Field(..., ge=0, le=18)
    physical_activity: float = Field(..., ge=0, le=14)
    family_history: Literal["No", "Yes"]
    question: Optional[str] = None
    
    # Part 1: Core Screening Questions (Optional for backward compatibility)
    sleep_quality: Optional[int] = Field(None, ge=1, le=5)
    mood: Optional[int] = Field(None, ge=1, le=5)
    anxiety: Optional[int] = Field(None, ge=1, le=5)
    energy_level: Optional[int] = Field(None, ge=1, le=5)
    concentration: Optional[int] = Field(None, ge=1, le=5)
    appetite_changes: Optional[Literal["No Change", "Eating Less", "Eating More"]] = None
    loneliness: Optional[int] = Field(None, ge=1, le=5)
    major_life_events: Optional[List[str]] = None
    screen_time: Optional[float] = Field(None, ge=0)
    
    # Part 2: Protective Factors
    family_support: Optional[int] = Field(None, ge=1, le=5)
    friend_support: Optional[int] = Field(None, ge=1, le=5)
    hobbies: Optional[int] = Field(None, ge=1, le=5)
    ability_to_relax: Optional[int] = Field(None, ge=1, le=5)
    life_satisfaction: Optional[int] = Field(None, ge=1, le=5)
    
    # Part 3: Optional Health Context
    recent_illness: Optional[bool] = None
    chronic_condition: Optional[bool] = None
    medication: Optional[bool] = None
    surgery: Optional[bool] = None
    substance_use: Optional[bool] = None
    health_notes: Optional[str] = None
    
    # Female-specific Optional Context
    menstrual_status: Optional[str] = None
    cycle_phase: Optional[str] = None
    pms_pmdd: Optional[bool] = None
    pregnancy_status: Optional[bool] = None
    postpartum_status: Optional[bool] = None
    menopause: Optional[bool] = None


class SessionRequest(BaseModel):
    consent: bool
    consent_version: str = "demo-v1"
    region: str = "IN"


class CompanionChatRequest(BaseModel):
    message: str


class MoodCheckinRequest(BaseModel):
    mood_score: int = Field(..., ge=1, le=5)
    note: Optional[str] = None


class BigFiveRequest(BaseModel):
    openness: int = Field(..., ge=1, le=5)
    conscientiousness: int = Field(..., ge=1, le=5)
    extraversion: int = Field(..., ge=1, le=5)
    agreeableness: int = Field(..., ge=1, le=5)
    neuroticism: int = Field(..., ge=1, le=5)


app = FastAPI(
    title="ISCOR AI Integration API",
    version="0.1.0",
    description="Part 5 API: preprocessing, inference, explainability, safety, and report assembly.",
)

# Allow CORS for local React development and production domains
import os
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()

    import os
    if os.getenv("ISCOR_USE_LLM", "0") == "1":
        if not any(os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 4)):
            import sys
            print(
                "\n[FATAL WARNING] ISCOR_USE_LLM=1 is set, but no GEMINI_API_KEY_1 (or 2/3) is reachable! "
                "The LLM features will fail. Set an API key in the .env file.\n",
                file=sys.stderr
            )
    
    # Report SHAP fallback rate over the last 100 screenings
    try:
        from .database import get_db, DB_PATH
        with get_db(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM Screenings ORDER BY id DESC LIMIT 100")
            rows = cur.fetchall()
            if not rows:
                print("[STARTUP] No screenings yet, cannot calculate SHAP fallback rate.")
                return
                
            screening_ids = [row["id"] for row in rows]
            placeholders = ",".join("%s" for _ in screening_ids)
            
            cur.execute(
                f"SELECT COUNT(DISTINCT screening_id) FROM SafetyEvents "
                f"WHERE event_type = 'shap_fallback' AND screening_id IN ({placeholders})",
                tuple(screening_ids)
            )
            fallback_count = cur.fetchone()[0]
            total = len(screening_ids)
            rate = (fallback_count / total) * 100
            
            print(f"[STARTUP] SHAP Fallback Rate (last {total} screenings): {rate:.1f}% ({fallback_count}/{total})")
            
            if rate > 5.0:
                print(f"[WARNING] SHAP Fallback rate {rate:.1f}% exceeds 5% threshold! Check logs for Explainer exceptions.")
                
    except Exception as e:
        print(f"[STARTUP ERROR] Failed to calculate SHAP fallback rate: {e}")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "iscor-ai"}


@app.post("/session")
def session(request: SessionRequest) -> dict:
    if not request.consent:
        return {
            "error": "Consent is required before creating a screening session.",
            "consent_required": True,
        }
    return create_session(
        consent_version=request.consent_version,
        region=request.region,
    )


@app.post("/screen")
def screen(request: ScreeningRequest, authorization: Optional[str] = Header(default=None)) -> dict:
    if not request.consent:
        raise HTTPException(status_code=400, detail="Consent is required before running the screening.")

    user_id = None
    if authorization:
        token = authorization.removeprefix("Bearer").strip()
        user_id = validate_session(token)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid or expired session token.")

    payload = request.model_dump()
    payload.pop("consent", None)
    question = payload.pop("question", None)
    
    previous_report = None
    if user_id:
        history = fetch_history(limit=1, user_id=user_id)
        if history:
            previous_report = history[0]
            
    report = assemble_report(payload, question=question, previous_report=previous_report)
    ids = persist_screening(report, user_id=user_id)
    report.update(ids)
    return report


@app.post("/submit-screening")
def submit_screening(request: ScreeningRequest, authorization: Optional[str] = Header(default=None)) -> dict:
    return screen(request, authorization=authorization)


@app.get("/latest")
def latest() -> dict:
    return {"latest": fetch_latest_report()}


@app.get("/history")
def history(limit: int = 20, authorization: Optional[str] = Header(default=None)) -> dict:
    user_id = None
    if authorization:
        token = authorization.removeprefix("Bearer").strip()
        user_id = validate_session(token)
        if user_id is None:
            return {"error": "Invalid or expired session token.", "session_required": True}
    return {"history": fetch_history(limit=limit, user_id=user_id)}


@app.get("/get-report/{screening_id}")
def get_report(screening_id: int) -> dict:
    report = fetch_report_by_id(screening_id)
    if report is None:
        return {"error": "Report not found."}
    return report


@app.get("/trend-summary")
def get_trend_summary(authorization: Optional[str] = Header(default=None)) -> dict:
    user_id = None
    if authorization:
        token = authorization.removeprefix("Bearer").strip()
        user_id = validate_session(token)
        if user_id is None:
            return {"error": "Invalid or expired session token.", "session_required": True}
    
    trend_data = fetch_trend_data(user_id=user_id)
    if len(trend_data) < 3:
        return {"summary": "Keep tracking your screenings to see your risk trends over time."}

    from llm.llm_service import _call_llm
    system_prompt = (
        "You are a wellness assistant analysing a student's history of mental health screenings. "
        "You will receive a timeline of past screening results, including risk levels and top contributing factors. "
        "Write exactly ONE sentence summarising the overall trend (e.g. 'Your stress-related risk factors have been trending down over your last 3 screenings.'). "
        "Do NOT diagnose or provide clinical advice."
    )
    
    history_lines = []
    for i, data in enumerate(trend_data):
        date = data['created_at'][:10]
        label = data['risk_label']
        factors = ", ".join(f"{f['feature']} ({f['direction']})" for f in data['top_factors'])
        history_lines.append(f"Screening {i+1} ({date}): Risk = {label}, Key Factors = {factors}")
        
    user_prompt = "Screening History:\n" + "\n".join(history_lines)
    
    try:
        summary = _call_llm(system_prompt, user_prompt)
        return {"summary": summary}
    except Exception as e:
        return {"summary": "Trend analysis is currently unavailable."}


class ChatMessageRequest(BaseModel):
    message: str

@app.post("/chat/{screening_id}")
def chat(screening_id: int, request: ChatMessageRequest) -> dict:
    report = fetch_report_by_id(screening_id)
    if report is None:
        return {"error": "Screening report not found.", "screening_required": True}
    if report.get("crisis_mode"):
        return {"error": "Cannot chat about a high-risk result. Please encourage the user to seek crisis support."}

    from llm.llm_service import answer_user_question
    response, _ = answer_user_question(request.message, {
        "risk_label": report["risk_label"],
        "risk_probabilities": report["risk_probabilities"],
        "top_factors": report["top_factors"],
    })
    persist_conversation(report["screening_id"], request.message, response)
    return {"response": response}


@app.post("/assessment/big-five")
def submit_big_five(request: BigFiveRequest, authorization: Optional[str] = Header(default=None)) -> dict:
    user_id = None
    if authorization:
        token = authorization.removeprefix("Bearer").strip()
        user_id = validate_session(token)
        if user_id is None:
            return {"error": "Invalid or expired session token.", "session_required": True}
    else:
        return {"error": "Session token required for self-assessment.", "session_required": True}

    scores_dict = {
        "O": request.openness,
        "C": request.conscientiousness,
        "E": request.extraversion,
        "A": request.agreeableness,
        "N": request.neuroticism
    }

    # PART 0 GAP FIX: Check latest risk level before calling LLM
    from .database import fetch_history
    from llm.risk_gate import CRISIS_MESSAGE
    user_history = fetch_history(limit=1, user_id=user_id)
    latest_report = user_history[0] if user_history else None

    if latest_report and latest_report.get("risk_label") == "High":
        summary = "Based on your recent screening, we are unable to generate a wellness summary at this time.\n\n" + CRISIS_MESSAGE
        provider = "System (Risk Gate)"
    else:
        from llm.llm_service import generate_personality_summary
        try:
            summary, provider = generate_personality_summary(scores_dict)
        except Exception as e:
            import logging
            logging.error(f"Failed to generate personality summary: {e}")
            summary = "Personality summary is temporarily unavailable due to a backend error."
            provider = "None"

    save_personality_assessment(user_id, scores_dict, summary)

    return {
        "success": True,
        "scores": scores_dict,
        "summary": summary,
        "provider": provider
    }


@app.get("/assessment/latest")
def get_latest_assessment(authorization: Optional[str] = Header(default=None)) -> dict:
    user_id = None
    if authorization:
        token = authorization.removeprefix("Bearer").strip()
        user_id = validate_session(token)
        if user_id is None:
            return {"error": "Invalid or expired session token.", "session_required": True}
    
    result = fetch_latest_personality_summary(user_id)
    if not result:
        return {"assessment": None}
        
    return {"assessment": result}


@app.post("/companion/chat")
def companion_chat(request: CompanionChatRequest, authorization: Optional[str] = Header(default=None)) -> dict:
    user_id = None
    if authorization:
        token = authorization.removeprefix("Bearer").strip()
        user_id = validate_session(token)
        if user_id is None:
            return {"error": "Invalid or expired session token.", "session_required": True}
    else:
        return {"error": "Session token required for companion chat.", "session_required": True}

    # Fetch context
    history = fetch_companion_history(user_id, limit=6)
    history.reverse() # chronological
    
    # We can fake the latest report fetching from DB using existing function, 
    # but we need to fetch by user_id. Wait, fetch_history gets the user's history!
    user_history = fetch_history(limit=1, user_id=user_id)
    latest_report = user_history[0] if user_history else None
    
    personality_summary = fetch_latest_personality_summary(user_id)

    # Save user message
    add_companion_message(user_id, "user", request.message)

    from llm.llm_service import generate_companion_response
    try:
        response_text = generate_companion_response(history, latest_report, personality_summary, request.message)
    except Exception as e:
        import logging
        logging.error(f"Failed to generate companion response: {e}")
        response_text = "I'm sorry, I'm having trouble connecting right now. Please try again later."

    # Save companion response
    add_companion_message(user_id, "companion", response_text)

    return {"response": response_text}


@app.get("/companion/history")
def companion_history(authorization: Optional[str] = Header(default=None)) -> dict:
    user_id = None
    if authorization:
        token = authorization.removeprefix("Bearer").strip()
        user_id = validate_session(token)
        if user_id is None:
            return {"error": "Invalid or expired session token.", "session_required": True}
    else:
        return {"error": "Session token required.", "session_required": True}
        
    history = fetch_companion_history(user_id, limit=50)
    return {"history": history}


@app.post("/checkin/mood")
def submit_mood(request: MoodCheckinRequest, authorization: Optional[str] = Header(default=None)) -> dict:
    user_id = None
    if authorization:
        token = authorization.removeprefix("Bearer").strip()
        user_id = validate_session(token)
        if user_id is None:
            return {"error": "Invalid or expired session token.", "session_required": True}
    else:
        return {"error": "Session token required.", "session_required": True}

    crisis_intercept = False
    crisis_message = None

    if request.note:
        from llm.risk_gate import check_chat_safety
        safety_check = check_chat_safety(request.note)
        if safety_check["is_high_risk"]:
            crisis_intercept = True
            crisis_message = safety_check["response"]
            # Still save the check-in, but log the event
            from .database import DB_PATH
            import sqlite3
            from .database import now_iso, init_db
            init_db(DB_PATH)
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO SafetyEvents (screening_id, event_type, message, created_at) VALUES (?, ?, ?, ?)",
                    (0, "mood_checkin_crisis", request.note[:100], now_iso())
                )
                conn.commit()

    add_mood_checkin(user_id, request.mood_score, request.note)
    
    if crisis_intercept:
        return {"success": True, "crisis_intercept": True, "message": crisis_message}
    return {"success": True}


@app.get("/checkin/history")
def get_mood_history(authorization: Optional[str] = Header(default=None)) -> dict:
    user_id = None
    if authorization:
        token = authorization.removeprefix("Bearer").strip()
        user_id = validate_session(token)
        if user_id is None:
            return {"error": "Invalid or expired session token.", "session_required": True}
    else:
        return {"error": "Session token required.", "session_required": True}

    moods = fetch_recent_moods(user_id, days=14)
    return {"history": moods}


@app.post("/maintenance/purge-expired-sessions")
def purge_sessions() -> dict:
    return {"revoked_sessions": purge_expired_sessions()}


@app.post("/maintenance/purge-old-screenings")
def purge_screenings(retention_days: int = 30) -> dict:
    return {"deleted_screenings": purge_old_screenings(retention_days=retention_days)}
