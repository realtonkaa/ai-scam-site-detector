"""CLI entry point for AI Scam Site Detector."""

import argparse
import sys
import os
from typing import List

from .scraper import fetch_page
from .content_analyzer import analyze_content
from .structure_analyzer import analyze_structure
from .author_checker import analyze_author
from .domain_checker import analyze_domain
from .scorer import calculate_risk_score
from .report import format_report, export_json


def analyze_url(url: str) -> dict:
    """Run full analysis on a single URL.

    Args:
        url: The URL to analyze.

    Returns:
        Dict with 'score_result' and 'analysis_results'.
    """
    url = url.strip()
    if not url:
        return {"error": "Empty URL"}

    # Fetch page content
    page_data = fetch_page(url)

    if page_data.get("error"):
        # Still try domain analysis even if page fetch failed
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

    return {
        "url": url,
        "score_result": score_result,
        "analysis_results": analysis_results,
        "page_data": page_data,
    }


def analyze_batch(urls: List[str]) -> List[dict]:
    """Analyze multiple URLs.

    Args:
        urls: List of URLs to analyze.

    Returns:
        List of analysis result dicts.
    """
    results = []
    for i, url in enumerate(urls, 1):
        url = url.strip()
        if not url or url.startswith("#"):
            continue
        print(f"[{i}/{len(urls)}] Analyzing {url}...")
        result = analyze_url(url)
        results.append(result)
    return results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze URLs/websites for AI-generated spam and scam patterns",
        prog="ai-scam-detector",
    )
    parser.add_argument(
        "target",
        help="URL to analyze, or path to a text file containing one URL per line",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Save JSON report to this file path",
        default=None,
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress terminal output (useful with --output)",
    )

    args = parser.parse_args()
    target = args.target

    # Determine if target is a file or URL
    if os.path.isfile(target):
        with open(target, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        if not urls:
            print("No valid URLs found in file.", file=sys.stderr)
            sys.exit(1)

        results = analyze_batch(urls)

        if not args.quiet:
            for result in results:
                if "error" in result:
                    print(f"Error analyzing {result.get('url', '?')}: {result['error']}")
                    continue
                format_report(
                    result["url"],
                    result["score_result"],
                    result["analysis_results"],
                )

        if args.output:
            # Export all results as JSON array
            import json
            all_json = []
            for result in results:
                if "score_result" in result:
                    json_data = export_json(
                        result["url"],
                        result["score_result"],
                        result["analysis_results"],
                    )
                    all_json.append(json.loads(json_data))
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(all_json, f, indent=2, default=str)
            print(f"\nJSON report saved to: {args.output}")

    else:
        # Single URL
        result = analyze_url(target)

        if not args.quiet:
            if "error" in result and "score_result" not in result:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)
            format_report(
                result["url"],
                result["score_result"],
                result["analysis_results"],
            )

        if args.output:
            json_output = export_json(
                result["url"],
                result["score_result"],
                result["analysis_results"],
            )
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_output)
            print(f"\nJSON report saved to: {args.output}")

        # Exit with error code if HIGH or CRITICAL
        risk = result.get("score_result", {}).get("risk_level", "LOW")
        if risk in ("HIGH", "CRITICAL"):
            sys.exit(2)


if __name__ == "__main__":
    main()
