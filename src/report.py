"""Output formatting for analysis results."""

import json
from typing import Dict

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None


def format_report(url: str, score_result: Dict, analysis_results: Dict) -> None:
    """Print a rich terminal report of the analysis results.

    Args:
        url: The URL that was analyzed.
        score_result: Output from scorer.calculate_risk_score().
        analysis_results: Dict of per-category analysis results.
    """
    if not RICH_AVAILABLE:
        _plain_report(url, score_result, analysis_results)
        return

    overall = score_result["overall_score"]
    risk_level = score_result["risk_level"]

    # Color mapping
    risk_colors = {
        "LOW": "green",
        "MEDIUM": "yellow",
        "HIGH": "red",
        "CRITICAL": "bold red",
    }
    color = risk_colors.get(risk_level, "white")

    # Header panel
    title = Text(f"AI Scam Site Detector", style="bold blue")
    console.print(Panel(title, expand=False))
    console.print(f"[bold]URL:[/bold] {url}\n")

    # Risk score panel
    score_text = Text()
    score_text.append(f"Risk Level: ", style="bold")
    score_text.append(f"{risk_level}", style=f"bold {color}")
    score_text.append(f"  ({overall:.1%} confidence)", style="dim")
    console.print(Panel(score_text, title="Overall Risk Assessment", border_style=color))

    # Category scores table
    cat_table = Table(title="Category Breakdown", box=box.ROUNDED)
    cat_table.add_column("Category", style="cyan", width=15)
    cat_table.add_column("Score", justify="right", width=10)
    cat_table.add_column("Risk", width=10)

    for category, cat_score in score_result["category_scores"].items():
        cat_level = _score_to_level(cat_score)
        cat_color = risk_colors.get(cat_level, "white")
        cat_table.add_row(
            category.title(),
            f"{cat_score:.3f}",
            Text(cat_level, style=cat_color),
        )

    console.print(cat_table)

    # Triggered signals
    triggered = score_result.get("triggered_signals", [])
    if triggered:
        sig_table = Table(title="Triggered Signals", box=box.ROUNDED)
        sig_table.add_column("Category", style="cyan", width=12)
        sig_table.add_column("Signal", style="yellow", width=30)
        sig_table.add_column("Confidence", justify="right", width=12)
        sig_table.add_column("Detail", width=50)

        for signal in triggered:
            conf = signal.confidence
            conf_color = "red" if conf >= 0.6 else "yellow" if conf >= 0.3 else "green"
            sig_table.add_row(
                signal.category.title(),
                signal.signal_name.replace("_", " ").title(),
                Text(f"{conf:.0%}", style=conf_color),
                signal.detail[:60],
            )

        console.print(sig_table)
    else:
        console.print("[green]No suspicious signals triggered.[/green]\n")

    # Recommendation
    rec_color = risk_colors.get(risk_level, "white")
    console.print(
        Panel(
            score_result["recommendation"],
            title="Recommendation",
            border_style=rec_color,
        )
    )


def _score_to_level(score: float) -> str:
    """Convert numeric score to risk level."""
    if score < 0.25:
        return "LOW"
    elif score < 0.50:
        return "MEDIUM"
    elif score < 0.75:
        return "HIGH"
    return "CRITICAL"


def _plain_report(url: str, score_result: Dict, analysis_results: Dict) -> None:
    """Plain text fallback report when Rich is not available."""
    overall = score_result["overall_score"]
    risk_level = score_result["risk_level"]

    print("=" * 60)
    print("AI SCAM SITE DETECTOR")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Risk Level: {risk_level} ({overall:.1%})")
    print("\nCategory Scores:")
    for cat, score in score_result["category_scores"].items():
        print(f"  {cat.title()}: {score:.3f}")

    triggered = score_result.get("triggered_signals", [])
    if triggered:
        print("\nTriggered Signals:")
        for sig in triggered:
            print(f"  [{sig.category}] {sig.signal_name}: {sig.detail}")

    print(f"\nRecommendation: {score_result['recommendation']}")
    print("=" * 60)


def export_json(url: str, score_result: Dict, analysis_results: Dict) -> str:
    """Export analysis results as JSON string.

    Args:
        url: The analyzed URL.
        score_result: Output from scorer.calculate_risk_score().
        analysis_results: Dict of per-category analysis results.

    Returns:
        JSON string representation of results.
    """
    # Convert dataclasses to dicts for serialization
    triggered = [
        {
            "signal_name": s.signal_name,
            "category": s.category,
            "triggered": s.triggered,
            "confidence": s.confidence,
            "detail": s.detail,
        }
        for s in score_result.get("triggered_signals", [])
    ]

    output = {
        "url": url,
        "overall_score": score_result["overall_score"],
        "risk_level": score_result["risk_level"],
        "recommendation": score_result["recommendation"],
        "category_scores": score_result["category_scores"],
        "triggered_signals": triggered,
        "total_signals_checked": score_result.get("total_signals_checked", 0),
        "category_details": {
            cat: {
                "score": data.get("score", 0),
                "signals": data.get("signals", []),
                "stats": data.get("stats", {}),
            }
            for cat, data in analysis_results.items()
        },
    }

    return json.dumps(output, indent=2, default=str)
