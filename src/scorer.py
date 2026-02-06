"""Combined risk scoring engine."""

from dataclasses import dataclass
from typing import List, Dict

CATEGORY_WEIGHTS = {
    "content": 0.40,
    "structure": 0.20,
    "domain": 0.25,
    "author": 0.15,
}


@dataclass
class SignalResult:
    signal_name: str
    category: str
    triggered: bool
    confidence: float
    detail: str


def calculate_risk_score(analysis_results: Dict) -> Dict:
    """Calculate overall risk score from all analysis categories.

    Args:
        analysis_results: Dict mapping category name to analysis result dict.
            Expected keys: 'content', 'structure', 'domain', 'author'.

    Returns:
        Dict with overall_score, risk_level, category_scores, triggered_signals,
        total_signals_checked, and recommendation.
    """
    category_scores = {}
    all_signals: List[SignalResult] = []

    for category, weight in CATEGORY_WEIGHTS.items():
        result = analysis_results.get(category, {})
        category_scores[category] = result.get("score", 0)

        for signal in result.get("signals", []):
            all_signals.append(
                SignalResult(
                    signal_name=signal["name"],
                    category=category,
                    triggered=signal.get("triggered", False),
                    confidence=signal.get("confidence", 0),
                    detail=signal.get("detail", ""),
                )
            )

    overall = sum(
        category_scores.get(cat, 0) * weight
        for cat, weight in CATEGORY_WEIGHTS.items()
    )
    overall = round(overall, 3)

    risk_level = _get_risk_level(overall)

    return {
        "overall_score": overall,
        "risk_level": risk_level,
        "category_scores": category_scores,
        "triggered_signals": [s for s in all_signals if s.triggered],
        "all_signals": all_signals,
        "total_signals_checked": len(all_signals),
        "recommendation": _get_recommendation(risk_level),
    }


def _get_risk_level(score: float) -> str:
    """Convert numeric score to risk level label."""
    if score < 0.25:
        return "LOW"
    elif score < 0.50:
        return "MEDIUM"
    elif score < 0.75:
        return "HIGH"
    else:
        return "CRITICAL"


def _get_recommendation(risk_level: str) -> str:
    """Get human-readable recommendation based on risk level."""
    recs = {
        "LOW": "This site appears legitimate. Standard caution applies.",
        "MEDIUM": (
            "Some suspicious signals detected. "
            "Verify the site independently before sharing personal information."
        ),
        "HIGH": (
            "Multiple red flags detected. This site may be AI-generated or a scam. "
            "Avoid sharing personal data."
        ),
        "CRITICAL": (
            "Strong indicators of a scam or AI-generated site. "
            "Do not interact with this site."
        ),
    }
    return recs.get(risk_level, "Unable to assess.")
