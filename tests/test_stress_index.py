"""Unit tests for Task 1 -- Stress_Index scale correctness.

Each test follows the same data pipeline used at training-time and
inference-time:

  raw user values
      -> z-score using training-set statistics (same stats stored in
         integration/service.py::_scaling_stats)
      -> engineer_features()
      -> assert composite feature direction/magnitude

Training-set statistics (from harmonize_primary on archive-30 source):
  Sleep_Hours      : mean=7.2737, std=1.4377
  Academic_Pressure: mean=2.5843, std=1.4341
  Financial_Stress : mean=2.6282, std=1.4851
  Social_Support   : mean=3.2279, std=1.4041
  Study_Hours      : mean=33.016, std=6.5371
  Physical_Activity: mean=5.1107, std=2.7727
"""
import sys
import os

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Make modeling_pipeline importable from the tests directory
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "models"))

from modeling_pipeline import engineer_features  # noqa: E402


# ---------------------------------------------------------------------------
# Training-set statistics (population std, ddof=0) -- mirrors service.py
# ---------------------------------------------------------------------------
TRAIN_STATS = {
    "Sleep_Hours":       {"mean": 7.2737, "std": 1.4377},
    "Academic_Pressure": {"mean": 2.5843, "std": 1.4341},
    "Financial_Stress":  {"mean": 2.6282, "std": 1.4851},
    "Social_Support":    {"mean": 3.2279, "std": 1.4041},
    "Study_Hours":       {"mean": 33.016, "std": 6.5371},
    "Physical_Activity": {"mean": 5.1107, "std": 2.7727},
}

# Passthrough columns (binary / not z-scored by service.py)
PASSTHROUGH = {"Age": 0.0, "Gender": 0.0, "Family_History": 0.0}

SCALED_COLS = list(TRAIN_STATS.keys())


def _zscore(col, raw):
    s = TRAIN_STATS[col]
    return (raw - s["mean"]) / s["std"]


def _make_row(**raw_values):
    """Build a single-row DataFrame of z-scored features.

    Pass raw values for any subset of SCALED_COLS; missing ones default to
    the training mean (z-score = 0).  Passthrough columns are added with
    neutral values.
    """
    row = dict(PASSTHROUGH)
    for col in SCALED_COLS:
        raw = raw_values.get(col, TRAIN_STATS[col]["mean"])
        row[col] = _zscore(col, raw)
    return pd.DataFrame([row])


# ===========================================================================
# Acceptance criterion 1
#   High Sleep_Hours (9 hrs) + low Academic_Pressure (1) + low FS (1)
#   -> Stress_Index should be negative (well below the mid-point z-score of 0)
# ===========================================================================
class TestStressIndexLow:
    def test_high_sleep_low_pressures_gives_low_stress(self):
        """
        9 hrs sleep is above mean (7.27 hrs) -> z(sleep) ~ +1.2
        AP=1 and FS=1 are scale minimums -> z(AP) ~ -1.1, z(FS) ~ -1.1
        Stress_Index = z(AP) + z(FS) - z(sleep) ~ -1.1 -1.1 -1.2 = -3.4
        Must be strongly negative.
        """
        df = _make_row(
            Sleep_Hours=9.0,
            Academic_Pressure=1.0,
            Financial_Stress=1.0,
        )
        out = engineer_features(df)
        si = out.loc[0, "Stress_Index"]
        assert si < 0.0, (
            f"Expected a negative Stress_Index for low-pressure/high-sleep row, "
            f"got {si:.4f}"
        )

    def test_stress_index_not_dominated_by_sleep_raw_magnitude(self):
        """
        If Sleep_Hours dominated via raw scale, index would be huge and
        positive for sleep=9 (raw 9 >> 1-5 range).  Post-fix: sleep is
        subtracted in z-score space -> more sleep -> lower stress.
        """
        df_high_sleep = _make_row(Sleep_Hours=9.0, Academic_Pressure=3.0, Financial_Stress=3.0)
        df_low_sleep  = _make_row(Sleep_Hours=4.0, Academic_Pressure=3.0, Financial_Stress=3.0)

        si_high = engineer_features(df_high_sleep).loc[0, "Stress_Index"]
        si_low  = engineer_features(df_low_sleep).loc[0,  "Stress_Index"]

        assert si_low > si_high, (
            f"Less sleep should produce higher Stress_Index. "
            f"si_low={si_low:.4f}, si_high={si_high:.4f}"
        )


# ===========================================================================
# Acceptance criterion 2
#   All inputs at "worst" values -> Stress_Index at/near theoretical max
# ===========================================================================
class TestStressIndexMax:
    def test_worst_case_stress_index_is_positive_and_above_midpoint(self):
        """
        Worst-case: AP=5, FS=5, Sleep=4 (minimum sleep in dataset).
        Must produce strongly positive Stress_Index.
        """
        df_worst = _make_row(Academic_Pressure=5.0, Financial_Stress=5.0, Sleep_Hours=4.0)
        df_mid   = _make_row()  # all at mean -> all z=0 -> SI=0

        si_worst = engineer_features(df_worst).loc[0, "Stress_Index"]
        si_mid   = engineer_features(df_mid).loc[0,   "Stress_Index"]

        assert si_worst > si_mid, (
            f"Worst-case should exceed mid-point. si_worst={si_worst:.4f}, si_mid={si_mid:.4f}"
        )
        assert si_worst > 0.0, f"Worst-case Stress_Index must be positive, got {si_worst:.4f}"

    def test_worst_case_greater_than_best_case(self):
        """Full range spans from negative to positive without sign reversal."""
        df_worst = _make_row(Academic_Pressure=5.0, Financial_Stress=5.0, Sleep_Hours=4.0)
        df_best  = _make_row(Academic_Pressure=1.0, Financial_Stress=1.0, Sleep_Hours=9.0)

        si_worst = engineer_features(df_worst).loc[0, "Stress_Index"]
        si_best  = engineer_features(df_best).loc[0,  "Stress_Index"]

        assert si_worst > si_best, (
            f"Expected worst > best. worst={si_worst:.4f}, best={si_best:.4f}"
        )

    def test_no_single_feature_dominates_by_raw_range(self):
        """
        Each feature moving across its full raw range should shift
        Stress_Index by a comparable amount (within a 3x ratio).
        Pre-fix: Sleep_Hours raw range (4-9 = 5 units) vs AP raw range (1-5 = 4 units)
        would have been incomparable; post-fix all contributions are in sigma units.
        """
        lo_ap = engineer_features(_make_row(Academic_Pressure=1.0, Financial_Stress=3.0, Sleep_Hours=7.0)).loc[0, "Stress_Index"]
        hi_ap = engineer_features(_make_row(Academic_Pressure=5.0, Financial_Stress=3.0, Sleep_Hours=7.0)).loc[0, "Stress_Index"]
        delta_ap = abs(hi_ap - lo_ap)

        lo_fs = engineer_features(_make_row(Academic_Pressure=3.0, Financial_Stress=1.0, Sleep_Hours=7.0)).loc[0, "Stress_Index"]
        hi_fs = engineer_features(_make_row(Academic_Pressure=3.0, Financial_Stress=5.0, Sleep_Hours=7.0)).loc[0, "Stress_Index"]
        delta_fs = abs(hi_fs - lo_fs)

        # Sleep inverted: min sleep -> max stress contribution
        lo_sl = engineer_features(_make_row(Academic_Pressure=3.0, Financial_Stress=3.0, Sleep_Hours=4.0)).loc[0, "Stress_Index"]
        hi_sl = engineer_features(_make_row(Academic_Pressure=3.0, Financial_Stress=3.0, Sleep_Hours=9.0)).loc[0, "Stress_Index"]
        delta_sl = abs(lo_sl - hi_sl)

        deltas = {"AP": delta_ap, "FS": delta_fs, "Sleep": delta_sl}
        max_d = max(deltas.values())
        min_d = min(deltas.values())

        assert max_d <= 3.0 * min_d, (
            f"Feature dominance: deltas={deltas}, ratio={max_d/min_d:.2f} > 3.0"
        )


# ===========================================================================
# Lifestyle_Score and Academic_Load direction sanity
# ===========================================================================
class TestLifestyleAndAcademicLoad:
    def test_lifestyle_score_increases_with_more_sleep(self):
        lo = engineer_features(_make_row(Sleep_Hours=4.0)).loc[0, "Lifestyle_Score"]
        hi = engineer_features(_make_row(Sleep_Hours=9.0)).loc[0, "Lifestyle_Score"]
        assert hi > lo, "More sleep should raise Lifestyle_Score"

    def test_lifestyle_score_increases_with_more_activity(self):
        lo = engineer_features(_make_row(Physical_Activity=0.0)).loc[0, "Lifestyle_Score"]
        hi = engineer_features(_make_row(Physical_Activity=10.0)).loc[0, "Lifestyle_Score"]
        assert hi > lo, "More physical activity should raise Lifestyle_Score"

    def test_academic_load_increases_with_study_hours(self):
        lo = engineer_features(_make_row(Study_Hours=0.0)).loc[0, "Academic_Load"]
        hi = engineer_features(_make_row(Study_Hours=60.0)).loc[0, "Academic_Load"]
        assert hi > lo, "More study hours should raise Academic_Load"

    def test_academic_load_increases_with_academic_pressure(self):
        lo = engineer_features(_make_row(Academic_Pressure=1.0)).loc[0, "Academic_Load"]
        hi = engineer_features(_make_row(Academic_Pressure=5.0)).loc[0, "Academic_Load"]
        assert hi > lo, "Higher pressure should raise Academic_Load"


# ===========================================================================
# Batch-compatibility regression guard
# ===========================================================================
class TestBatchCompatibility:
    def test_engineer_features_accepts_dataframe_batch(self):
        """
        _scale_to_band used float(Series) which raised TypeError on batches.
        This guard ensures the function handles multi-row DataFrames correctly.
        """
        rows = [
            _make_row(Sleep_Hours=4.0, Academic_Pressure=5.0, Financial_Stress=5.0),
            _make_row(Sleep_Hours=9.0, Academic_Pressure=1.0, Financial_Stress=1.0),
            _make_row(),
        ]
        batch = pd.concat(rows, ignore_index=True)
        out = engineer_features(batch)
        assert len(out) == 3
        assert "Stress_Index" in out.columns
        # Worst row (idx 0) must exceed best row (idx 1)
        assert out.loc[0, "Stress_Index"] > out.loc[1, "Stress_Index"]
