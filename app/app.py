"""Streamlit web interface for AI Scam Site Detector."""

import sys
import os

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

from src.scraper import fetch_page
from src.content_analyzer import analyze_content
from src.structure_analyzer import analyze_structure
from src.author_checker import analyze_author
from src.domain_checker import analyze_domain
from src.scorer import calculate_risk_score
from src.report import export_json

st.set_page_config(
    page_title="AI Scam Site Detector",
    page_icon="magnifying glass",
    layout="wide",
)

RISK_COLORS = {
    "LOW": "#28a745",
    "MEDIUM": "#ffc107",
    "HIGH": "#fd7e14",
    "CRITICAL": "#dc3545",
}

RISK_EMOJI = {
    "LOW": "green circle",
    "MEDIUM": "yellow circle",
    "HIGH": "orange circle",
    "CRITICAL": "red circle",
}


def run_analysis(url: str) -> dict:
    """Run full analysis on URL and return results."""
    page_data = fetch_page(url)

    if page_data.get("error"):
        analysis_results = {
            "content": {"score": 0, "signals": [], "error": page_data["error"]},
            "structure": {"score": 0, "signals": [], "error": page_data["error"]},
            "author": {"score": 0, "signals": []},
            "domain": analyze_domain(url),
        }
    else:
        analysis_results = {
            "content": analyze_content(page_data.get("text", "")),
            "structure": analyze_structure(page_data.get("html", ""), url),
            "author": analyze_author(page_data.get("author_info", {})),
            "domain": analyze_domain(url),
        }

    score_result = calculate_risk_score(analysis_results)
    return score_result, analysis_results, page_data


def main():
    st.title("AI Scam Site Detector")
    st.markdown(
        "Analyze websites for signs of AI-generated content and scam patterns."
    )

    st.divider()

    # URL input
    col1, col2 = st.columns([4, 1])
    with col1:
        url = st.text_input(
            "Enter URL to analyze",
            placeholder="https://example.com",
            label_visibility="visible",
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button("Analyze", type="primary", use_container_width=True)

    if analyze_btn and url:
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        with st.spinner(f"Analyzing {url}..."):
            try:
                score_result, analysis_results, page_data = run_analysis(url)
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                return

        risk_level = score_result["risk_level"]
        overall = score_result["overall_score"]
        color = RISK_COLORS.get(risk_level, "#6c757d")

        # Main risk display
        st.divider()
        st.markdown(f"### Results for `{url}`")

        col_score, col_rec = st.columns([1, 2])
        with col_score:
            st.markdown(
                f"""
                <div style="
                    background-color: {color}22;
                    border: 2px solid {color};
                    border-radius: 12px;
                    padding: 24px;
                    text-align: center;
                ">
                    <div style="font-size: 2.5em; font-weight: bold; color: {color};">
                        {risk_level}
                    </div>
                    <div style="font-size: 1.2em; color: #666;">
                        Score: {overall:.1%}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_rec:
            st.info(score_result["recommendation"])
            if page_data.get("title"):
                st.markdown(f"**Page title:** {page_data['title']}")
            if page_data.get("error"):
                st.warning(f"Note: {page_data['error']}")

        # Category scores
        st.divider()
        st.subheader("Category Breakdown")
        cat_cols = st.columns(4)
        category_labels = {
            "content": "Content Analysis",
            "structure": "Page Structure",
            "domain": "Domain Check",
            "author": "Author Check",
        }

        for i, (cat, label) in enumerate(category_labels.items()):
            cat_score = score_result["category_scores"].get(cat, 0)
            cat_level = _score_to_level(cat_score)
            cat_color = RISK_COLORS.get(cat_level, "#6c757d")
            with cat_cols[i]:
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid {cat_color};
                        border-radius: 8px;
                        padding: 16px;
                        text-align: center;
                    ">
                        <div style="font-weight: bold; font-size: 0.9em;">{label}</div>
                        <div style="font-size: 1.8em; color: {cat_color}; font-weight: bold;">
                            {cat_score:.0%}
                        </div>
                        <div style="color: {cat_color}; font-size: 0.85em;">{cat_level}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Triggered signals table
        triggered = score_result.get("triggered_signals", [])
        if triggered:
            st.divider()
            st.subheader(f"Triggered Signals ({len(triggered)})")

            signal_data = []
            for sig in triggered:
                signal_data.append({
                    "Category": sig.category.title(),
                    "Signal": sig.signal_name.replace("_", " ").title(),
                    "Confidence": f"{sig.confidence:.0%}",
                    "Detail": sig.detail,
                })

            st.table(signal_data)
        else:
            st.success("No suspicious signals were triggered.")

        # JSON export
        st.divider()
        with st.expander("Export JSON Report"):
            json_str = export_json(url, score_result, analysis_results)
            st.code(json_str, language="json")
            st.download_button(
                "Download JSON Report",
                data=json_str,
                file_name="scam_analysis.json",
                mime="application/json",
            )

    elif analyze_btn and not url:
        st.warning("Please enter a URL to analyze.")

    # Footer
    st.divider()
    st.markdown(
        "<div style='text-align: center; color: #999; font-size: 0.8em;'>"
        "AI Scam Site Detector - for educational and defensive use only"
        "</div>",
        unsafe_allow_html=True,
    )


def _score_to_level(score: float) -> str:
    if score < 0.25:
        return "LOW"
    elif score < 0.50:
        return "MEDIUM"
    elif score < 0.75:
        return "HIGH"
    return "CRITICAL"


if __name__ == "__main__":
    main()
