"""Domain analysis for scam detection."""

import re
from urllib.parse import urlparse
from typing import Dict
from datetime import datetime, timezone

SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".buzz", ".click", ".info", ".site", ".online",
    ".store", ".shop", ".club", ".space", ".fun", ".icu", ".monster",
    ".rest", ".hair", ".beauty", ".quest", ".sbs",
}

TRUSTED_TLDS = {".gov", ".edu", ".mil"}


def analyze_domain(url: str) -> Dict:
    """Analyze a domain for scam indicators.

    Args:
        url: The URL or domain to analyze.

    Returns:
        Dict with domain metadata, score, and signals.
    """
    parsed = urlparse(url if "://" in url else f"https://{url}")
    domain = parsed.netloc or parsed.path.split("/")[0]

    # Strip port if present
    if ":" in domain:
        domain = domain.split(":")[0]

    signals = []

    # Check TLD
    tld = "." + domain.split(".")[-1].lower() if "." in domain else ""

    if tld in SUSPICIOUS_TLDS:
        signals.append({
            "name": "suspicious_tld",
            "triggered": True,
            "confidence": 0.5,
            "detail": f"Domain uses suspicious TLD: {tld}",
        })
    elif tld in TRUSTED_TLDS:
        signals.append({
            "name": "trusted_tld",
            "triggered": False,
            "confidence": 0.0,
            "detail": f"Domain uses trusted TLD: {tld}",
        })

    # Check domain length (very long = suspicious)
    domain_parts = domain.split(".")
    domain_name = domain_parts[0] if len(domain_parts) > 0 else domain
    if len(domain_name) > 20:
        signals.append({
            "name": "long_domain_name",
            "triggered": True,
            "confidence": 0.3,
            "detail": f"Unusually long domain name: {len(domain_name)} chars",
        })

    # Check for numbers in domain (often spammy)
    if re.search(r"\d{3,}", domain_name):
        signals.append({
            "name": "numbers_in_domain",
            "triggered": True,
            "confidence": 0.3,
            "detail": "Domain contains number sequences",
        })

    # Check for hyphens (multiple hyphens = suspicious)
    if domain_name.count("-") >= 2:
        signals.append({
            "name": "multiple_hyphens",
            "triggered": True,
            "confidence": 0.4,
            "detail": f"Domain has {domain_name.count('-')} hyphens",
        })

    # Check for keyword stuffing in domain
    spam_keywords = re.compile(
        r"(free|cheap|best|top|deal|discount|review|buy|sale|win|prize|cash|bonus)",
        re.I,
    )
    keyword_matches = spam_keywords.findall(domain_name)
    if len(keyword_matches) >= 2:
        signals.append({
            "name": "keyword_stuffed_domain",
            "triggered": True,
            "confidence": 0.4,
            "detail": f"Domain contains {len(keyword_matches)} promotional keywords",
        })

    # WHOIS check (optional)
    domain_age_days = None
    whois_privacy = False
    try:
        import whois
        w = whois.whois(domain)
        if w.creation_date:
            created = w.creation_date
            if isinstance(created, list):
                created = created[0]
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            domain_age_days = (datetime.now(timezone.utc) - created).days
            if domain_age_days < 90:
                signals.append({
                    "name": "very_new_domain",
                    "triggered": True,
                    "confidence": 0.7,
                    "detail": f"Domain is only {domain_age_days} days old",
                })
            elif domain_age_days < 365:
                signals.append({
                    "name": "new_domain",
                    "triggered": True,
                    "confidence": 0.3,
                    "detail": f"Domain is less than 1 year old ({domain_age_days} days)",
                })

        # Check for privacy protection
        emails = w.emails or []
        if isinstance(emails, str):
            emails = [emails]
        privacy_markers = ["privacy", "protect", "proxy", "whoisguard", "domainprivacy"]
        if any(m in str(e).lower() for e in emails for m in privacy_markers):
            whois_privacy = True
            signals.append({
                "name": "whois_privacy_protected",
                "triggered": True,
                "confidence": 0.2,
                "detail": "Domain uses WHOIS privacy protection",
            })

    except Exception:
        pass  # WHOIS not available or failed

    triggered = [s for s in signals if s.get("triggered")]
    score = (
        sum(s["confidence"] for s in triggered) / max(len(signals), 1)
        if triggered
        else 0.05
    )

    return {
        "domain": domain,
        "tld": tld,
        "domain_age_days": domain_age_days,
        "whois_privacy": whois_privacy,
        "score": round(score, 3),
        "signals": signals,
    }
