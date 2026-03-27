"""Tests for report module."""

import json
import pytest
from src.report import export_json, _score_to_level, _plain_report
from src.scorer import calculate_risk_score, SignalResult


def make_score_result(overall=0.3, risk_level="MEDIUM", triggered=None):
    """Helper to create a mock score result dict."""
    if triggered is None:
        triggered = []
    return {
        "overall_score": overall,
        "risk_level": risk_level,
        "category_scores": {
            "content": 0.4,
            "structure": 0.2,
            "domain": 0.3,
            "author": 0.1,
        },
        "triggered_signals": triggered,
        "all_signals": triggered,
        "total_signals_checked": len(triggered),
        "recommendation": "Test recommendation.",
    }


class TestExportJson:
    def test_returns_string(self):
        score_result = make_score_result()
        result = export_json("https://example.com", score_result, {})
        assert isinstance(result, str)

    def test_valid_json(self):
        score_result = make_score_result()
        result = export_json("https://example.com", score_result, {})
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_contains_url(self):
        score_result = make_score_result()
        result = export_json("https://example.com", score_result, {})
        parsed = json.loads(result)
        assert parsed["url"] == "https://example.com"

    def test_contains_risk_level(self):
        score_result = make_score_result(risk_level="HIGH")
        result = export_json("https://example.com", score_result, {})
        parsed = json.loads(result)
        assert parsed["risk_level"] == "HIGH"

    def test_contains_overall_score(self):
        score_result = make_score_result(overall=0.65)
        result = export_json("https://example.com", score_result, {})
        parsed = json.loads(result)
        assert parsed["overall_score"] == 0.65

    def test_contains_category_scores(self):
        score_result = make_score_result()
        result = export_json("https://example.com", score_result, {})
        parsed = json.loads(result)
        assert "category_scores" in parsed
        assert "content" in parsed["category_scores"]

    def test_contains_recommendation(self):
        score_result = make_score_result()
        result = export_json("https://example.com", score_result, {})
        parsed = json.loads(result)
        assert "recommendation" in parsed

    def test_triggered_signals_serialized(self):
        triggered = [
            SignalResult(
                signal_name="test_signal",
                category="content",
                triggered=True,
                confidence=0.6,
                detail="Test detail",
            )
        ]
        score_result = make_score_result(triggered=triggered)
        result = export_json("https://example.com", score_result, {})
        parsed = json.loads(result)
        assert len(parsed["triggered_signals"]) == 1
        assert parsed["triggered_signals"][0]["signal_name"] == "test_signal"

    def test_category_details_included(self):
        score_result = make_score_result()
        analysis = {
            "content": {
                "score": 0.4,
                "signals": [{"name": "test", "triggered": True, "confidence": 0.4, "detail": "d"}],
                "stats": {"word_count": 100},
            }
        }
        result = export_json("https://example.com", score_result, analysis)
        parsed = json.loads(result)
        assert "category_details" in parsed
        assert "content" in parsed["category_details"]

    def test_empty_analysis_results(self):
        score_result = make_score_result()
        result = export_json("https://example.com", score_result, {})
        parsed = json.loads(result)
        assert parsed["category_details"] == {}

    def test_total_signals_checked(self):
        score_result = make_score_result()
        result = export_json("https://example.com", score_result, {})
        parsed = json.loads(result)
        assert "total_signals_checked" in parsed


class TestScoreToLevel:
    def test_low_score_low_level(self):
        assert _score_to_level(0.1) == "LOW"

    def test_medium_score_medium_level(self):
        assert _score_to_level(0.3) == "MEDIUM"

    def test_high_score_high_level(self):
        assert _score_to_level(0.6) == "HIGH"

    def test_critical_score_critical_level(self):
        assert _score_to_level(0.8) == "CRITICAL"

    def test_exact_boundary_medium(self):
        assert _score_to_level(0.25) == "MEDIUM"

    def test_exact_boundary_high(self):
        assert _score_to_level(0.50) == "HIGH"

    def test_exact_boundary_critical(self):
        assert _score_to_level(0.75) == "CRITICAL"


class TestPlainReport:
    def test_plain_report_runs_without_error(self, capsys):
        score_result = make_score_result()
        _plain_report("https://example.com", score_result, {})
        captured = capsys.readouterr()
        assert "example.com" in captured.out

    def test_plain_report_shows_risk_level(self, capsys):
        score_result = make_score_result(risk_level="HIGH")
        _plain_report("https://example.com", score_result, {})
        captured = capsys.readouterr()
        assert "HIGH" in captured.out

    def test_plain_report_shows_score(self, capsys):
        score_result = make_score_result(overall=0.65)
        _plain_report("https://example.com", score_result, {})
        captured = capsys.readouterr()
        assert "65" in captured.out  # 65% in output

    def test_plain_report_shows_triggered_signals(self, capsys):
        triggered = [
            SignalResult(
                signal_name="my_signal",
                category="content",
                triggered=True,
                confidence=0.6,
                detail="Found suspicious pattern",
            )
        ]
        score_result = make_score_result(triggered=triggered)
        _plain_report("https://example.com", score_result, {})
        captured = capsys.readouterr()
        assert "my_signal" in captured.out
