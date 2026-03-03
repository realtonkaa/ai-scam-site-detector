"""Tests for scorer module."""

import pytest
from src.scorer import (
    calculate_risk_score,
    _get_risk_level,
    _get_recommendation,
    CATEGORY_WEIGHTS,
    SignalResult,
)


class TestCalculateRiskScoreBasics:
    def test_returns_dict(self, minimal_analysis_results):
        result = calculate_risk_score(minimal_analysis_results)
        assert isinstance(result, dict)

    def test_has_required_keys(self, minimal_analysis_results):
        result = calculate_risk_score(minimal_analysis_results)
        assert "overall_score" in result
        assert "risk_level" in result
        assert "category_scores" in result
        assert "triggered_signals" in result
        assert "recommendation" in result
        assert "total_signals_checked" in result

    def test_overall_score_is_float(self, minimal_analysis_results):
        result = calculate_risk_score(minimal_analysis_results)
        assert isinstance(result["overall_score"], float)

    def test_overall_score_in_range(self, minimal_analysis_results):
        result = calculate_risk_score(minimal_analysis_results)
        assert 0.0 <= result["overall_score"] <= 1.0

    def test_triggered_signals_is_list(self, minimal_analysis_results):
        result = calculate_risk_score(minimal_analysis_results)
        assert isinstance(result["triggered_signals"], list)

    def test_empty_results_handled(self):
        result = calculate_risk_score({})
        assert isinstance(result, dict)
        assert result["overall_score"] == 0.0

    def test_partial_results_handled(self):
        result = calculate_risk_score({"content": {"score": 0.5, "signals": []}})
        assert isinstance(result, dict)


class TestWeightCalculation:
    def test_weights_sum_to_one(self):
        total = sum(CATEGORY_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_content_has_highest_weight(self):
        assert CATEGORY_WEIGHTS["content"] >= max(
            v for k, v in CATEGORY_WEIGHTS.items() if k != "content"
        )

    def test_all_categories_have_weight(self):
        for cat in ["content", "structure", "domain", "author"]:
            assert cat in CATEGORY_WEIGHTS
            assert CATEGORY_WEIGHTS[cat] > 0

    def test_weighted_score_calculation(self):
        """Verify the weighted sum is correct."""
        results = {
            "content": {"score": 1.0, "signals": []},
            "structure": {"score": 0.0, "signals": []},
            "domain": {"score": 0.0, "signals": []},
            "author": {"score": 0.0, "signals": []},
        }
        result = calculate_risk_score(results)
        # content weight is 0.40, so overall should be ~0.40
        assert abs(result["overall_score"] - CATEGORY_WEIGHTS["content"]) < 0.01

    def test_all_max_score_is_one(self):
        results = {
            cat: {"score": 1.0, "signals": []}
            for cat in CATEGORY_WEIGHTS
        }
        result = calculate_risk_score(results)
        assert abs(result["overall_score"] - 1.0) < 0.01


class TestRiskLevelThresholds:
    def test_zero_score_is_low(self):
        assert _get_risk_level(0.0) == "LOW"

    def test_0_24_is_low(self):
        assert _get_risk_level(0.24) == "LOW"

    def test_0_25_is_medium(self):
        assert _get_risk_level(0.25) == "MEDIUM"

    def test_0_49_is_medium(self):
        assert _get_risk_level(0.49) == "MEDIUM"

    def test_0_50_is_high(self):
        assert _get_risk_level(0.50) == "HIGH"

    def test_0_74_is_high(self):
        assert _get_risk_level(0.74) == "HIGH"

    def test_0_75_is_critical(self):
        assert _get_risk_level(0.75) == "CRITICAL"

    def test_1_0_is_critical(self):
        assert _get_risk_level(1.0) == "CRITICAL"

    def test_boundary_low_medium(self):
        assert _get_risk_level(0.249) == "LOW"
        assert _get_risk_level(0.250) == "MEDIUM"

    def test_boundary_medium_high(self):
        assert _get_risk_level(0.499) == "MEDIUM"
        assert _get_risk_level(0.500) == "HIGH"

    def test_boundary_high_critical(self):
        assert _get_risk_level(0.749) == "HIGH"
        assert _get_risk_level(0.750) == "CRITICAL"


class TestRiskLevelFromScorer:
    def test_low_scores_give_low_level(self):
        results = {cat: {"score": 0.05, "signals": []} for cat in CATEGORY_WEIGHTS}
        result = calculate_risk_score(results)
        assert result["risk_level"] == "LOW"

    def test_high_scores_give_high_level(self):
        results = {cat: {"score": 0.8, "signals": []} for cat in CATEGORY_WEIGHTS}
        result = calculate_risk_score(results)
        assert result["risk_level"] in ("HIGH", "CRITICAL")

    def test_critical_scores_give_critical_level(self):
        results = {cat: {"score": 1.0, "signals": []} for cat in CATEGORY_WEIGHTS}
        result = calculate_risk_score(results)
        assert result["risk_level"] == "CRITICAL"


class TestRecommendations:
    def test_low_has_recommendation(self):
        rec = _get_recommendation("LOW")
        assert len(rec) > 0

    def test_medium_has_recommendation(self):
        rec = _get_recommendation("MEDIUM")
        assert len(rec) > 0

    def test_high_has_recommendation(self):
        rec = _get_recommendation("HIGH")
        assert len(rec) > 0

    def test_critical_has_recommendation(self):
        rec = _get_recommendation("CRITICAL")
        assert len(rec) > 0

    def test_low_recommendation_is_reassuring(self):
        rec = _get_recommendation("LOW")
        assert "legitimate" in rec.lower() or "caution" in rec.lower()

    def test_critical_recommendation_warns(self):
        rec = _get_recommendation("CRITICAL")
        assert "scam" in rec.lower() or "do not" in rec.lower()

    def test_unknown_risk_level_handled(self):
        rec = _get_recommendation("UNKNOWN")
        assert isinstance(rec, str)


class TestSignalAggregation:
    def test_triggered_signals_filtered(self):
        results = {
            "content": {
                "score": 0.5,
                "signals": [
                    {"name": "test_signal", "triggered": True, "confidence": 0.5, "detail": "test"},
                    {"name": "not_triggered", "triggered": False, "confidence": 0.0, "detail": "nope"},
                ],
            },
            "structure": {"score": 0.1, "signals": []},
            "domain": {"score": 0.1, "signals": []},
            "author": {"score": 0.1, "signals": []},
        }
        result = calculate_risk_score(results)
        assert len(result["triggered_signals"]) == 1
        assert result["triggered_signals"][0].signal_name == "test_signal"

    def test_total_signals_count(self):
        results = {
            "content": {
                "score": 0.5,
                "signals": [
                    {"name": "sig1", "triggered": True, "confidence": 0.5, "detail": "d1"},
                    {"name": "sig2", "triggered": False, "confidence": 0.0, "detail": "d2"},
                ],
            },
            "structure": {"score": 0.1, "signals": []},
            "domain": {"score": 0.1, "signals": []},
            "author": {"score": 0.1, "signals": []},
        }
        result = calculate_risk_score(results)
        assert result["total_signals_checked"] == 2

    def test_signal_result_dataclass(self):
        sig = SignalResult(
            signal_name="test",
            category="content",
            triggered=True,
            confidence=0.5,
            detail="test detail",
        )
        assert sig.signal_name == "test"
        assert sig.triggered is True
