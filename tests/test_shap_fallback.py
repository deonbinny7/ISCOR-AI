"""Unit tests for Task 2 -- SHAP Explainer fallback monitoring.
"""
import sys
import os
import json
import sqlite3
from unittest import mock

import pytest
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "integration"))
sys.path.insert(0, os.path.join(REPO_ROOT, "models"))
sys.path.insert(0, os.path.join(REPO_ROOT, "data_processing"))

import service
from database import DB_PATH, persist_screening


@pytest.fixture
def mock_db(tmp_path):
    """Provide a temporary database for testing."""
    test_db = tmp_path / "test.db"
    from database import init_db
    init_db(test_db)
    yield test_db


def test_shap_fallback_produces_report_and_logs_event(mock_db):
    """
    Deliberately break the SHAP explainer to verify that:
    1. A usable deterministic report is still produced.
    2. The fallback event is logged to the SafetyEvents table.
    """
    # 1. Setup dummy user input
    raw_answers = {
        'age': 20,
        'gender': 'Male',
        'sleep_hours': 7,
        'academic_pressure': 3,
        'financial_stress': 3,
        'social_support': 'Moderate',
        'study_hours': 10,
        'physical_activity': 5,
        'family_history': 'No'
    }

    # 2. Mock the explainer to raise an exception
    with mock.patch("service._load_explainer") as mock_load:
        mock_explainer = mock.Mock()
        mock_explainer.explain.side_effect = Exception("Simulated TreeExplainer crash")
        mock_load.return_value = mock_explainer

        # 3. Assemble the report (this should catch the exception and use fallback)
        report = service.assemble_report(raw_answers)
        
        # Verify the report is still usable
        assert "risk_label" in report
        assert "top_factors" in report
        assert "explanation" in report
        # The fallback sets 4 specific factors
        assert len(report["top_factors"]) == 4

        # 4. Persist the screening to DB (this should log the fallback event)
        ids = persist_screening(report, db_path=mock_db)
        screening_id = ids["screening_id"]

        # 5. Verify the event was logged
        with sqlite3.connect(mock_db) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT event_type, message FROM SafetyEvents WHERE screening_id = ?",
                (screening_id,)
            )
            events = cur.fetchall()
            
            assert len(events) >= 1, "Expected at least one safety event to be logged"
            
            fallback_events = [e for e in events if e[0] == "shap_fallback"]
            assert len(fallback_events) == 1, "Expected exactly one shap_fallback event"
            
            msg = fallback_events[0][1]
            assert "Simulated TreeExplainer crash" in msg, "Exception message not in DB log"
