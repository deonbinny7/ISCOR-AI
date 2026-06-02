import json
import os
import secrets
import sqlite3
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional


DB_PATH = Path(__file__).resolve().parents[1] / "iscor_demo.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consent_given INTEGER NOT NULL,
    consent_version TEXT NOT NULL DEFAULT 'demo-v1',
    region TEXT NOT NULL DEFAULT 'IN',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    FOREIGN KEY(user_id) REFERENCES Users(id)
);

CREATE TABLE IF NOT EXISTS Screenings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    input_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES Users(id)
);

CREATE TABLE IF NOT EXISTS Predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    screening_id INTEGER NOT NULL,
    risk_label TEXT NOT NULL,
    probabilities_json TEXT NOT NULL,
    crisis_mode INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(screening_id) REFERENCES Screenings(id)
);

CREATE TABLE IF NOT EXISTS FeatureImportance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL,
    feature TEXT NOT NULL,
    shap_value REAL NOT NULL,
    direction TEXT NOT NULL,
    rank INTEGER NOT NULL,
    FOREIGN KEY(prediction_id) REFERENCES Predictions(id)
);

CREATE TABLE IF NOT EXISTS WellnessPlans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL,
    explanation TEXT NOT NULL,
    suggestions TEXT,
    weekly_plan TEXT,
    llm_provider TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(prediction_id) REFERENCES Predictions(id)
);

CREATE TABLE IF NOT EXISTS ConversationHistory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    screening_id INTEGER NOT NULL,
    question TEXT,
    response TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(screening_id) REFERENCES Screenings(id)
);

CREATE TABLE IF NOT EXISTS SafetyEvents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    screening_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(screening_id) REFERENCES Screenings(id)
);

CREATE TABLE IF NOT EXISTS RetrievedEvidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    screening_id INTEGER NOT NULL,
    chunk_id TEXT NOT NULL,
    source TEXT NOT NULL,
    similarity_score REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(screening_id) REFERENCES Screenings(id)
);

CREATE TABLE IF NOT EXISTS PersonalityAssessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    answers_json TEXT NOT NULL,
    summary TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES Users(id)
);

CREATE TABLE IF NOT EXISTS CompanionHistory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES Users(id)
);

CREATE TABLE IF NOT EXISTS MoodCheckins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    mood_score INTEGER NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES Users(id)
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_fernet():
    key = os.getenv("ISCOR_DB_ENCRYPTION_KEY")
    if not key:
        return None
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        return None
    return Fernet(key.encode("utf-8"))


# ---------------------------------------------------------------------------
# Encryption Scope Documentation
# ---------------------------------------------------------------------------
# Only specific sensitive fields are encrypted at rest using Fernet:
# 1. Screenings: `input_json` (the raw user answers).
# 2. WellnessPlans: `explanation` and `suggestions` (free-text model outputs).
# 3. ConversationHistory: `question` (user queries) and `response` (LLM replies).
# 
# Fields NOT encrypted at rest (stored as plaintext for query/analytics routing):
# - Risk labels, probabilities, and crisis mode flags.
# - SHAP feature importance vectors.
# - Safety event logs and metadata.
# ---------------------------------------------------------------------------
def protect_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    fernet = _get_fernet()
    if not fernet:
        return value
    return "fernet:" + fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def reveal_text(value: Optional[str]) -> Optional[str]:
    if value is None or not value.startswith("fernet:"):
        return value
    fernet = _get_fernet()
    if not fernet:
        return "[encrypted: set ISCOR_DB_ENCRYPTION_KEY to decrypt]"
    return fernet.decrypt(value.removeprefix("fernet:").encode("utf-8")).decode("utf-8")


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _ensure_columns(conn: sqlite3.Connection) -> None:
    user_columns = {row[1] for row in conn.execute("PRAGMA table_info(Users)").fetchall()}
    if "consent_version" not in user_columns:
        conn.execute("ALTER TABLE Users ADD COLUMN consent_version TEXT NOT NULL DEFAULT 'demo-v1'")
    if "region" not in user_columns:
        conn.execute("ALTER TABLE Users ADD COLUMN region TEXT NOT NULL DEFAULT 'IN'")

    wellness_columns = {row[1] for row in conn.execute("PRAGMA table_info(WellnessPlans)").fetchall()}
    if "weekly_plan" not in wellness_columns:
        conn.execute("ALTER TABLE WellnessPlans ADD COLUMN weekly_plan TEXT")
    if "llm_provider" not in wellness_columns:
        conn.execute("ALTER TABLE WellnessPlans ADD COLUMN llm_provider TEXT")


def init_db(db_path: Path = DB_PATH) -> None:
    """Initialize the SQLite schema and validate encryption settings."""
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        _ensure_columns(conn)

    # Startup Check: Ensure DB encryption aligns with environment flags
    import sys
    key = os.getenv("ISCOR_DB_ENCRYPTION_KEY")
    require_encryption = os.getenv("ISCOR_REQUIRE_ENCRYPTION", "0") == "1"

    if not key:
        if require_encryption:
            print(
                "\n[FATAL] ISCOR_REQUIRE_ENCRYPTION=1 is set, but ISCOR_DB_ENCRYPTION_KEY "
                "is missing! The app refuses to start because it cannot guarantee DPDP-aligned "
                "encrypted storage. Set the key or unset the requirement flag.\n",
                file=sys.stderr
            )
            sys.exit(1)
        else:
            print(
                "\n[WARNING] ISCOR_DB_ENCRYPTION_KEY is unset! "
                "Raw screening answers (input_json), free-text explanations, and "
                "conversation history will be stored in plaintext. This is not DPDP-aligned.\n",
                file=sys.stderr
            )


def create_session(
    consent_version: str = "demo-v1",
    region: str = "IN",
    ttl_hours: int = 12,
    db_path: Path = DB_PATH,
) -> Dict[str, Any]:
    init_db(db_path)
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(hours=ttl_hours)
    token = secrets.token_urlsafe(32)

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Users (consent_given, consent_version, region, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (1, consent_version, region, created_at.isoformat()),
        )
        user_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO Sessions (user_id, token_hash, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, hash_token(token), created_at.isoformat(), expires_at.isoformat()),
        )
        conn.commit()

    return {
        "user_id": int(user_id),
        "session_token": token,
        "expires_at": expires_at.isoformat(),
    }


def validate_session(token: str, db_path: Path = DB_PATH) -> Optional[int]:
    init_db(db_path)
    token_digest = hash_token(token)
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT user_id FROM Sessions
            WHERE token_hash = ?
              AND revoked_at IS NULL
              AND expires_at > ?
            """,
            (token_digest, now),
        ).fetchone()
    return int(row[0]) if row else None


def persist_screening(
    report: Dict[str, Any],
    user_id: Optional[int] = None,
    db_path: Path = DB_PATH,
) -> Dict[str, int]:
    init_db(db_path)
    created_at = now_iso()

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        if user_id is None:
            cur.execute(
                """
                INSERT INTO Users (consent_given, consent_version, region, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (1, "demo-v1", "IN", created_at),
            )
            user_id = cur.lastrowid

        cur.execute(
            "INSERT INTO Screenings (user_id, input_json, created_at) VALUES (?, ?, ?)",
            (user_id, protect_text(json.dumps(report["input"], sort_keys=True)), created_at),
        )
        screening_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO Predictions
            (screening_id, risk_label, probabilities_json, crisis_mode, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                screening_id,
                report["risk_label"],
                json.dumps(report["risk_probabilities"], sort_keys=True),
                int(report["crisis_mode"]),
                created_at,
            ),
        )
        prediction_id = cur.lastrowid

        for rank, factor in enumerate(report["top_factors"], start=1):
            cur.execute(
                """
                INSERT INTO FeatureImportance
                (prediction_id, feature, shap_value, direction, rank)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    prediction_id,
                    factor["feature"],
                    float(factor["shap_value"]),
                    factor["direction"],
                    rank,
                ),
            )

        cur.execute(
            """
            INSERT INTO WellnessPlans
            (prediction_id, explanation, suggestions, weekly_plan, llm_provider, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                prediction_id,
                protect_text(report["explanation"]),
                protect_text(report.get("wellness_suggestions")),
                protect_text(report.get("weekly_plan")),
                report.get("llm_provider"),
                created_at,
            ),
        )

        if report.get("qa_response"):
            cur.execute(
                """
                INSERT INTO ConversationHistory
                (screening_id, question, response, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    screening_id,
                    protect_text(report.get("question")),
                    protect_text(report["qa_response"]),
                    created_at,
                ),
            )

        if report.get("retrieved_evidence"):
            for chunk in report["retrieved_evidence"]:
                cur.execute(
                    """
                    INSERT INTO RetrievedEvidence
                    (screening_id, chunk_id, source, similarity_score, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        screening_id,
                        chunk["chunk_id"],
                        chunk["source"],
                        chunk["similarity_score"],
                        created_at,
                    ),
                )

        if report["crisis_mode"]:
            cur.execute(
                """
                INSERT INTO SafetyEvents
                (screening_id, event_type, message, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    screening_id,
                    "risk_gate_intercept",
                    "High-risk report returned fixed support resources; wellness generation skipped.",
                    created_at,
                ),
            )

        if report.get("fallback_error"):
            cur.execute(
                """
                INSERT INTO SafetyEvents
                (screening_id, event_type, message, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    screening_id,
                    "shap_fallback",
                    f"SHAP Explainer failed: {report['fallback_error']}",
                    created_at,
                ),
            )

        conn.commit()

    return {
        "user_id": int(user_id),
        "screening_id": int(screening_id),
        "prediction_id": int(prediction_id),
    }


def fetch_conversation_history(screening_id: int, db_path: Path = DB_PATH) -> list[Dict[str, Any]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT question, response, created_at FROM ConversationHistory "
            "WHERE screening_id = ? ORDER BY created_at",
            (screening_id,),
        ).fetchall()
        return [
            {
                "question": reveal_text(row["question"]),
                "response": reveal_text(row["response"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]


def fetch_latest_report(db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT s.id AS screening_id, s.input_json, s.created_at AS screened_at,
                   p.id AS prediction_id, p.risk_label,
                   p.probabilities_json, p.crisis_mode, w.explanation,
                   w.suggestions, w.weekly_plan
            FROM Screenings s
            JOIN Predictions p ON p.screening_id = s.id
            JOIN WellnessPlans w ON w.prediction_id = p.id
            ORDER BY s.id DESC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return None
        latest = dict(row)
        latest["input"] = json.loads(reveal_text(latest.pop("input_json")))
        latest["risk_probabilities"] = json.loads(latest.pop("probabilities_json"))
        latest["explanation"] = reveal_text(latest["explanation"])
        latest["suggestions"] = reveal_text(latest["suggestions"])
        latest["weekly_plan"] = reveal_text(latest.pop("weekly_plan"))
        latest["crisis_mode"] = bool(latest["crisis_mode"])
        latest["screened_at"] = latest.pop("screened_at")
        latest["prediction_id"] = int(latest["prediction_id"])
        latest["conversation_history"] = fetch_conversation_history(latest["screening_id"], db_path=db_path)
        
        factors_rows = conn.execute(
            "SELECT feature, shap_value, direction FROM FeatureImportance WHERE prediction_id = ? ORDER BY rank",
            (latest["prediction_id"],)
        ).fetchall()
        latest["top_factors"] = [dict(r) for r in factors_rows]
        
        evidence_rows = conn.execute(
            "SELECT chunk_id, source, similarity_score, created_at FROM RetrievedEvidence WHERE screening_id = ? ORDER BY similarity_score DESC",
            (latest["screening_id"],)
        ).fetchall()
        latest["retrieved_evidence"] = [dict(r) for r in evidence_rows]
        
        return latest


def fetch_report_by_id(screening_id: int, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT s.id AS screening_id, s.input_json, s.created_at AS screened_at,
                   p.id AS prediction_id, p.risk_label,
                   p.probabilities_json, p.crisis_mode, w.explanation,
                   w.suggestions, w.weekly_plan, w.llm_provider
            FROM Screenings s
            JOIN Predictions p ON p.screening_id = s.id
            JOIN WellnessPlans w ON w.prediction_id = p.id
            WHERE s.id = ?
            LIMIT 1
            """,
            (screening_id,),
        ).fetchone()
        if not row:
            return None
        report = dict(row)
        report["input"] = json.loads(reveal_text(report.pop("input_json")))
        report["risk_probabilities"] = json.loads(report.pop("probabilities_json"))
        report["explanation"] = reveal_text(report["explanation"])
        report["suggestions"] = reveal_text(report["suggestions"])
        report["weekly_plan"] = reveal_text(report.pop("weekly_plan"))
        report["crisis_mode"] = bool(report["crisis_mode"])
        report["screened_at"] = report.pop("screened_at")
        report["prediction_id"] = int(report["prediction_id"])
        report["conversation_history"] = fetch_conversation_history(report["screening_id"], db_path=db_path)

        factors_rows = conn.execute(
            "SELECT feature, shap_value, direction FROM FeatureImportance WHERE prediction_id = ? ORDER BY rank",
            (report["prediction_id"],)
        ).fetchall()
        report["top_factors"] = [dict(r) for r in factors_rows]
        
        evidence_rows = conn.execute(
            "SELECT chunk_id, source, similarity_score, created_at FROM RetrievedEvidence WHERE screening_id = ? ORDER BY similarity_score DESC",
            (report["screening_id"],)
        ).fetchall()
        report["retrieved_evidence"] = [dict(r) for r in evidence_rows]
        
        return report


def persist_conversation(
    screening_id: int,
    question: str,
    response: str,
    db_path: Path = DB_PATH,
) -> None:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO ConversationHistory (screening_id, question, response, created_at) VALUES (?, ?, ?, ?)",
            (screening_id, protect_text(question), protect_text(response), now_iso()),
        )
        conn.commit()


def fetch_history(limit: int = 20, user_id: Optional[int] = None, db_path: Path = DB_PATH) -> list[Dict[str, Any]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if user_id is not None:
            rows = conn.execute(
                """
                SELECT s.id AS screening_id, s.created_at AS screened_at,
                       p.risk_label, p.probabilities_json, p.crisis_mode, w.explanation
                FROM Screenings s
                JOIN Predictions p ON p.screening_id = s.id
                JOIN WellnessPlans w ON w.prediction_id = p.id
                WHERE s.user_id = ?
                ORDER BY s.id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT s.id AS screening_id, s.created_at AS screened_at,
                       p.risk_label, p.probabilities_json, p.crisis_mode, w.explanation
                FROM Screenings s
                JOIN Predictions p ON p.screening_id = s.id
                JOIN WellnessPlans w ON w.prediction_id = p.id
                ORDER BY s.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "screening_id": int(row["screening_id"]),
                "screened_at": row["screened_at"],
                "risk_label": row["risk_label"],
                "risk_probabilities": json.loads(row["probabilities_json"]),
                "crisis_mode": bool(row["crisis_mode"]),
                "explanation": reveal_text(row["explanation"]),
            }
            for row in rows
        ]


def fetch_trend_data(user_id: Optional[int] = None, db_path: Path = DB_PATH) -> list[Dict[str, Any]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        
        if user_id is not None:
            query = """
                SELECT p.id, p.risk_label, p.probabilities_json, s.created_at
                FROM Predictions p
                JOIN Screenings s ON p.screening_id = s.id
                WHERE s.user_id = ?
                ORDER BY s.created_at ASC
            """
            rows = conn.execute(query, (user_id,)).fetchall()
        else:
            query = """
                SELECT p.id, p.risk_label, p.probabilities_json, s.created_at
                FROM Predictions p
                JOIN Screenings s ON p.screening_id = s.id
                ORDER BY s.created_at ASC
            """
            rows = conn.execute(query).fetchall()

        results = []
        for row in rows:
            pred_id = row["id"]
            factors_rows = conn.execute(
                "SELECT feature, direction FROM FeatureImportance WHERE prediction_id = ? ORDER BY rank",
                (pred_id,)
            ).fetchall()
            
            results.append({
                "created_at": row["created_at"],
                "risk_label": row["risk_label"],
                "risk_probabilities": json.loads(row["probabilities_json"]),
                "top_factors": [{"feature": f["feature"], "direction": f["direction"]} for f in factors_rows]
            })
            
        return results


def purge_expired_sessions(db_path: Path = DB_PATH) -> int:
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "UPDATE Sessions SET revoked_at = ? WHERE expires_at <= ? AND revoked_at IS NULL",
            (now, now),
        )
        conn.commit()
        return cur.rowcount


def purge_old_screenings(retention_days: int = 30, db_path: Path = DB_PATH) -> int:
    """Delete screening-linked records older than the configured retention window."""
    init_db(db_path)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    with sqlite3.connect(db_path) as conn:
        screening_rows = conn.execute(
            "SELECT id FROM Screenings WHERE created_at < ?",
            (cutoff,),
        ).fetchall()
        screening_ids = [row[0] for row in screening_rows]
        if not screening_ids:
            return 0

        placeholders = ",".join("?" for _ in screening_ids)
        prediction_rows = conn.execute(
            f"SELECT id FROM Predictions WHERE screening_id IN ({placeholders})",
            screening_ids,
        ).fetchall()
        prediction_ids = [row[0] for row in prediction_rows]
        if prediction_ids:
            prediction_placeholders = ",".join("?" for _ in prediction_ids)
            conn.execute(f"DELETE FROM FeatureImportance WHERE prediction_id IN ({prediction_placeholders})", prediction_ids)
            conn.execute(f"DELETE FROM WellnessPlans WHERE prediction_id IN ({prediction_placeholders})", prediction_ids)
            conn.execute(f"DELETE FROM Predictions WHERE id IN ({prediction_placeholders})", prediction_ids)

        conn.execute(f"DELETE FROM RetrievedEvidence WHERE screening_id IN ({placeholders})", screening_ids)
        conn.execute(f"DELETE FROM ConversationHistory WHERE screening_id IN ({placeholders})", screening_ids)
        conn.execute(f"DELETE FROM SafetyEvents WHERE screening_id IN ({placeholders})", screening_ids)
        conn.execute(f"DELETE FROM Screenings WHERE id IN ({placeholders})", screening_ids)
        conn.commit()
        return len(screening_ids)


def save_personality_assessment(user_id: int, answers: dict, summary: str, db_path: Path = DB_PATH) -> int:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO PersonalityAssessments (user_id, answers_json, summary, created_at) VALUES (?, ?, ?, ?)",
            (user_id, protect_text(json.dumps(answers)), protect_text(summary), now_iso())
        )
        conn.commit()
        return cur.lastrowid


def fetch_latest_personality_summary(user_id: int, db_path: Path = DB_PATH) -> Optional[str]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT summary FROM PersonalityAssessments WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        return reveal_text(row[0]) if row else None


def add_companion_message(user_id: int, role: str, content: str, db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO CompanionHistory (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (user_id, role, protect_text(content), now_iso())
        )
        conn.commit()


def fetch_companion_history(user_id: int, limit: int = 50, db_path: Path = DB_PATH) -> list[Dict[str, str]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT role, content FROM (SELECT id, role, content FROM CompanionHistory WHERE user_id = ? ORDER BY id DESC LIMIT ?) ORDER BY id ASC",
            (user_id, limit)
        ).fetchall()
        return [{"role": row["role"], "content": reveal_text(row["content"])} for row in rows]


def add_mood_checkin(user_id: int, mood_score: int, note: Optional[str], db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO MoodCheckins (user_id, mood_score, note, created_at) VALUES (?, ?, ?, ?)",
            (user_id, mood_score, protect_text(note), now_iso())
        )
        conn.commit()


def fetch_recent_moods(user_id: int, days: int = 7, db_path: Path = DB_PATH) -> list[Dict[str, Any]]:
    init_db(db_path)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT mood_score, note, created_at FROM MoodCheckins WHERE user_id = ? AND created_at >= ? ORDER BY created_at ASC",
            (user_id, cutoff)
        ).fetchall()
        return [{"mood_score": row["mood_score"], "note": reveal_text(row["note"]), "created_at": row["created_at"]} for row in rows]

