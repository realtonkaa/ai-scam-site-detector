"""Configuration and constants for the AI Scam Site Detector."""

# Request settings
REQUEST_TIMEOUT = 15  # seconds
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Scoring thresholds
RISK_THRESHOLDS = {
    "LOW": 0.25,
    "MEDIUM": 0.50,
    "HIGH": 0.75,
}

# Category weights for combined scoring
CATEGORY_WEIGHTS = {
    "content": 0.40,
    "structure": 0.20,
    "domain": 0.25,
    "author": 0.15,
}

# Minimum text length for content analysis
MIN_TEXT_LENGTH = 50

# WHOIS cache duration in seconds
WHOIS_CACHE_TTL = 3600
