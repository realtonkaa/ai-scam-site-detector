# AI Scam Site Detector

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-166%20passing-brightgreen)
![Status](https://img.shields.io/badge/status-active-brightgreen)

Analyze websites for signs of AI-generated content and scam patterns

## Table of Contents

- [Why I Built This](#why-i-built-this)
- [Features](#features)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Sample Analysis Output](#sample-analysis-output)
- [Running Tests](#running-tests)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [Project Structure](#project-structure)
- [References](#references)
- [Built With Claude](#built-with-claude)
- [License](#license)

## Why I Built This

A few months ago I watched a relative share a health article on Facebook. The site looked polished. It had a byline, a photo of the "author", and confident medical claims. The problem was that the whole thing was fabricated. The author didn't exist, the domain was three weeks old, and the article was clearly churned out by an AI tuned to maximize engagement.

Finding this stuff manually takes time and some technical knowledge most people don't have. I wanted a tool that could look at a URL and give a quick, evidence-based risk assessment, something that explains why a site is suspicious, not just whether it is.

This project is my attempt at that. It's not perfect, but it gives you a structured starting point.

## Features

- **URL analysis**: Fetches and analyzes any public webpage
- **Content heuristics**: Detects AI-generated text patterns (uniform sentences, filler phrases, superlative overuse)
- **Domain checking**: Flags suspicious TLDs, new domains, and keyword-stuffed domain names
- **Structure analysis**: Identifies cookie-cutter templates, missing contact info, excessive CTAs
- **Author verification**: Detects generic bios, stock photo authors, and suspicious names
- **Risk scoring**: Weighted combination of all signals into a single risk level
- **CLI tool**: Analyze single URLs or batch-process a list from a file
- **Web UI**: Streamlit interface for non-technical users
- **JSON export**: Machine-readable reports for further processing

## How It Works

The analyzer runs four parallel checks and combines them into a weighted risk score:

### Content Analysis (40% of score)
Examines the text content for patterns common in AI-generated writing:
- Sentence length uniformity: human writing has natural variation; AI text tends to be suspiciously consistent
- Filler phrase density: phrases like "in today's fast-paced world" or "look no further" appear frequently in AI-generated marketing copy
- Superlative overuse: "best", "revolutionary", "unparalleled" etc. per 100 words
- Vocabulary diversity: type-token ratio measures how often the same words are reused
- Paragraph uniformity: AI text often produces paragraphs of near-identical length

### Structure Analysis (20% of score)
Checks the page's HTML structure for scam site patterns:
- Missing or absent "About" page links
- No real contact information (phone, address, email): only a generic contact form
- Excessive calls-to-action or pop-ups
- No social media links
- Missing privacy policy or terms of service

### Domain Analysis (25% of score)
Looks at the domain itself:
- Suspicious TLDs (`.xyz`, `.top`, `.buzz`, `.click`, etc.)
- Very new domain age (under 90 days)
- Multiple hyphens in the domain name
- Long numeric sequences in the domain
- WHOIS privacy protection

### Author Analysis (15% of score)
Checks author credibility:
- Generic bio language ("passionate writer", "expert in", "years of experience")
- Missing author information entirely
- Stock photo URLs for author images
- Suspicious/generic author names (e.g. "Admin", "Staff")

## Quick Start

```bash
git clone https://github.com/realtonkaa/ai-scam-site-detector.git
cd ai-scam-site-detector
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m src.cli https://example-suspicious-site.com
```

## Installation

```bash
git clone https://github.com/realtonkaa/ai-scam-site-detector
cd ai-scam-site-detector
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Analyze a single URL

```bash
python -m src.cli https://example.com
```

### Save results as JSON

```bash
python -m src.cli https://example.com --output report.json
```

### Batch analysis from a file

```bash
python -m src.cli urls.txt --output batch_results.json
```

`urls.txt` should have one URL per line. Lines starting with `#` are ignored.

### Launch the web interface

```bash
streamlit run app/app.py
```

## Sample Analysis Output

```
AI Scam Site Detector
URL: https://suspicious-deals.xyz/make-money-fast

Risk Level: HIGH  (68.3% confidence)

Category Breakdown:
  Content   0.721   HIGH
  Structure 0.580   HIGH
  Domain    0.750   CRITICAL
  Author    0.400   MEDIUM

Triggered Signals:
  [Domain]  Suspicious Tld          50%   Domain uses suspicious TLD: .xyz
  [Domain]  Very New Domain         70%   Domain is only 23 days old
  [Content] Ai Filler Phrases       80%   Found 7 AI-typical phrases
  [Content] High Superlative Density 60%  12 superlatives in 340 words (3.5%)
  [Author]  Generic Bio Phrases     45%   Bio contains 3 generic phrases

Recommendation:
Multiple red flags detected. This site may be AI-generated or a scam.
Avoid sharing personal data.
```

## Running Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Limitations

This tool is a heuristic analyzer, not a definitive classifier. You should know:

- **False positives are possible.** Legitimate marketing sites use many of the same patterns this tool flags. A HIGH score doesn't guarantee a site is a scam.
- **False negatives exist.** Sophisticated scam operations can avoid these heuristics. A LOW score doesn't mean a site is safe.
- **Content analysis requires sufficient text.** Pages with very little text will produce unreliable content scores.
- **Domain age requires WHOIS access.** If the `python-whois` package can't reach the WHOIS server, domain age checking is skipped.
- **AI text detection is an active research area.** The heuristics here are pattern-based, not model-based, so they work best on low-effort AI-generated content.
- **This is not a legal or financial tool.** Don't use it to make high-stakes decisions about whether a site is fraudulent.

## Contributing

Pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

When adding a new detection signal:
1. Add the logic to the appropriate `src/` module
2. Return a signal dict with `name`, `triggered`, `confidence`, and `detail`
3. Write tests in the corresponding `tests/test_*.py` file
4. Run `make test` to verify nothing is broken

## Project Structure

```
ai-scam-site-detector/
  src/
    cli.py                CLI entry point
    scraper.py            Web page fetching and content extraction
    content_analyzer.py   AI text detection heuristics
    structure_analyzer.py Page structure pattern detection
    author_checker.py     Author bio analysis
    domain_checker.py     Domain and TLD analysis
    scorer.py             Combined risk scoring
    report.py             Terminal and JSON output
    config.py             Configuration constants
  app/
    app.py                Streamlit web interface
  tests/
    fixtures/             Sample HTML and text files for testing
    test_*.py             Test modules
```

## References

- World Economic Forum: AI Disinformation Threats 2026 ([WEF](https://www.weforum.org/stories/2026/03/how-cognitive-manipulation-and-ai-will-shape-disinformation-in-2026/))
- Fake Image Detection Market Report ([Market.us](https://market.us/report/fake-image-detection-market/))
- textstat: Text readability statistics ([GitHub](https://github.com/textstat/textstat))
- BeautifulSoup4: HTML parsing ([Documentation](https://www.crummy.com/software/BeautifulSoup/))

## Built With Claude

I built this project with help from [Claude](https://claude.ai) by Anthropic. I used it to work through the scoring logic, reason about edge cases in the text heuristics, and debug the BeautifulSoup parsing code. The design decisions and motivation are mine; Claude helped me think through the implementation more carefully and move faster.

If you find this tool useful and want to build on it, I'd recommend using Claude to help you think through new detection signals. It's particularly good at reasoning about why a heuristic might produce false positives and how to tune thresholds.

## License

MIT License. See [LICENSE](LICENSE) for details.
