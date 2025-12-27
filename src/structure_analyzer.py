"""Page structure analysis for detecting scam site patterns."""

import re
from typing import Dict, List

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# Class name patterns common in cookie-cutter templates
TEMPLATE_CLASS_PATTERNS = [
    r"wp-block",
    r"elementor",
    r"divi",
    r"thrive",
    r"beaver-builder",
    r"vc_row",
    r"fusion-",
    r"et_pb_",
    r"fl-builder",
]

# Patterns indicating real contact information
CONTACT_PATTERNS = {
    "phone": re.compile(
        r"(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
    ),
    "address": re.compile(
        r"\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Ct)",
        re.I,
    ),
    "email": re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    ),
}

# Known social media domains
SOCIAL_MEDIA_DOMAINS = [
    "facebook.com", "twitter.com", "x.com", "instagram.com",
    "linkedin.com", "youtube.com", "tiktok.com", "pinterest.com",
]


def analyze_structure(html: str, url: str = "") -> Dict:
    """Analyze HTML structure for scam site patterns.

    Args:
        html: Raw HTML content of the page.
        url: The source URL (used for context).

    Returns:
        Dict with score, signals, and structural metadata.
    """
    if not html or len(html) < 100:
        return {"score": 0.1, "signals": [], "error": "HTML too short to analyze"}

    if not BS4_AVAILABLE:
        return {"score": 0.1, "signals": [], "error": "beautifulsoup4 not available"}

    soup = BeautifulSoup(html, "html.parser")
    signals = []
    metadata = {}

    # 1. Missing or generic About page link
    about_signal = _check_about_page(soup)
    if about_signal:
        signals.append(about_signal)

    # 2. Contact information analysis
    contact_signal, contact_meta = _check_contact_info(soup, html)
    metadata["contact"] = contact_meta
    if contact_signal:
        signals.append(contact_signal)

    # 3. Cookie-cutter template detection
    template_signal, template_meta = _check_template_patterns(soup)
    metadata["template"] = template_meta
    if template_signal:
        signals.append(template_signal)

    # 4. Excessive CTA / pop-up detection
    cta_signal, cta_meta = _check_excessive_ctas(soup)
    metadata["cta_count"] = cta_meta
    if cta_signal:
        signals.append(cta_signal)

    # 5. Social media links
    social_signal, social_meta = _check_social_links(soup)
    metadata["social_links"] = social_meta
    if social_signal:
        signals.append(social_signal)

    # 6. Missing privacy policy / terms
    policy_signal = _check_legal_pages(soup)
    if policy_signal:
        signals.append(policy_signal)

    # Calculate score
    triggered = [s for s in signals if s.get("triggered")]
    if triggered:
        structure_score = sum(s["confidence"] for s in triggered) / len(signals)
    else:
        structure_score = 0.05

    return {
        "score": round(structure_score, 3),
        "signals": signals,
        "metadata": metadata,
    }


def _check_about_page(soup: "BeautifulSoup") -> Dict:
    """Check for presence and quality of About page link."""
    links = soup.find_all("a", href=True)
    about_links = [
        a for a in links
        if re.search(r"\babout\b", a.get_text(strip=True), re.I)
        or re.search(r"\babout\b", a.get("href", ""), re.I)
    ]

    if not about_links:
        return {
            "name": "missing_about_page",
            "triggered": True,
            "confidence": 0.4,
            "detail": "No 'About' page link found on this site",
        }
    return None


def _check_contact_info(soup: "BeautifulSoup", html: str) -> tuple:
    """Check for real contact information vs generic contact forms only."""
    text = soup.get_text()
    contact_meta = {
        "has_phone": bool(CONTACT_PATTERNS["phone"].search(text)),
        "has_address": bool(CONTACT_PATTERNS["address"].search(text)),
        "has_email": bool(CONTACT_PATTERNS["email"].search(text)),
        "has_contact_form": bool(
            soup.find("form")
            and any(
                re.search(r"contact|message|inquiry", str(f), re.I)
                for f in soup.find_all("form")
            )
        ),
    }

    real_contact_count = sum([
        contact_meta["has_phone"],
        contact_meta["has_address"],
        contact_meta["has_email"],
    ])

    if real_contact_count == 0 and contact_meta["has_contact_form"]:
        return {
            "name": "no_real_contact_info",
            "triggered": True,
            "confidence": 0.5,
            "detail": "Only a contact form found, no phone/address/email",
        }, contact_meta
    elif real_contact_count == 0:
        return {
            "name": "no_contact_info",
            "triggered": True,
            "confidence": 0.6,
            "detail": "No contact information found on this page",
        }, contact_meta

    return None, contact_meta


def _check_template_patterns(soup: "BeautifulSoup") -> tuple:
    """Detect cookie-cutter page builder templates."""
    all_classes = []
    for tag in soup.find_all(class_=True):
        all_classes.extend(tag.get("class", []))

    class_string = " ".join(all_classes).lower()
    matched_templates = []

    for pattern in TEMPLATE_CLASS_PATTERNS:
        if re.search(pattern, class_string):
            matched_templates.append(pattern.strip(r"^").strip("-"))

    template_meta = {"detected_builders": matched_templates}

    if len(matched_templates) >= 1:
        # Not necessarily scammy, but worth noting
        return None, template_meta  # Don't flag page builders alone

    return None, template_meta


def _check_excessive_ctas(soup: "BeautifulSoup") -> tuple:
    """Detect excessive calls-to-action and pop-up patterns."""
    cta_keywords = re.compile(
        r"buy now|sign up|subscribe|get started|click here|limited|"
        r"act now|don't miss|free trial|order now|claim|exclusive",
        re.I,
    )

    buttons = soup.find_all(["button", "a"])
    cta_count = sum(1 for b in buttons if cta_keywords.search(b.get_text()))

    # Check for overlay/modal patterns
    overlay_patterns = soup.find_all(
        class_=re.compile(r"popup|modal|overlay|lightbox", re.I)
    )

    total_cta = cta_count + len(overlay_patterns)

    if total_cta > 8:
        return {
            "name": "excessive_cta",
            "triggered": True,
            "confidence": min(0.6, total_cta * 0.05),
            "detail": f"Found {total_cta} aggressive CTAs/pop-ups",
        }, total_cta

    return None, total_cta


def _check_social_links(soup: "BeautifulSoup") -> tuple:
    """Check for social media presence."""
    links = soup.find_all("a", href=True)
    social_found = []

    for link in links:
        href = link.get("href", "").lower()
        for domain in SOCIAL_MEDIA_DOMAINS:
            if domain in href:
                social_found.append(domain)
                break

    social_meta = list(set(social_found))

    if not social_found:
        return {
            "name": "no_social_media",
            "triggered": True,
            "confidence": 0.3,
            "detail": "No social media links found",
        }, social_meta

    return None, social_meta


def _check_legal_pages(soup: "BeautifulSoup") -> Dict:
    """Check for privacy policy and terms of service links."""
    links = soup.find_all("a", href=True)
    link_texts = [a.get_text(strip=True).lower() for a in links]
    link_hrefs = [a.get("href", "").lower() for a in links]

    has_privacy = any(
        "privacy" in t or "privacy" in h
        for t, h in zip(link_texts, link_hrefs)
    )
    has_terms = any(
        "terms" in t or "terms" in h
        for t, h in zip(link_texts, link_hrefs)
    )

    if not has_privacy and not has_terms:
        return {
            "name": "missing_legal_pages",
            "triggered": True,
            "confidence": 0.4,
            "detail": "No privacy policy or terms of service links found",
        }

    return None
