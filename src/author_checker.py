"""Fake author bio detection."""

import re
from typing import Dict, List

# Phrases commonly found in generic/AI-generated author bios
GENERIC_BIO_PHRASES = [
    "passionate writer",
    "passionate about",
    "expert in",
    "years of experience",
    "seasoned professional",
    "dedicated to helping",
    "loves to write",
    "writes about",
    "content creator",
    "freelance writer",
    "digital nomad",
    "thought leader",
    "industry expert",
    "specialist in",
    "enthusiast",
    "committed to providing",
    "strives to",
    "aims to",
    "helping readers",
    "bringing you the latest",
]

# Stock photo URL patterns (common stock sites and generic CDN patterns)
STOCK_PHOTO_PATTERNS = [
    re.compile(r"shutterstock\.com", re.I),
    re.compile(r"gettyimages\.com", re.I),
    re.compile(r"istockphoto\.com", re.I),
    re.compile(r"depositphotos\.com", re.I),
    re.compile(r"dreamstime\.com", re.I),
    re.compile(r"123rf\.com", re.I),
    re.compile(r"alamy\.com", re.I),
    re.compile(r"unsplash\.com", re.I),
    re.compile(r"pexels\.com", re.I),
    re.compile(r"/stock[-_]?photo", re.I),
    re.compile(r"placeholder.*avatar", re.I),
    re.compile(r"avatar.*placeholder", re.I),
    re.compile(r"generic[-_]?avatar", re.I),
    re.compile(r"default[-_]?(user|avatar|profile)", re.I),
    re.compile(r"gravatar\.com/avatar/[0-9a-f]+$", re.I),  # default gravatar
    re.compile(r"ui-avatars\.com", re.I),
]

# Patterns that suggest a name was auto-generated
SUSPICIOUS_NAME_PATTERNS = [
    re.compile(r"^[A-Z][a-z]+ [A-Z][a-z]+$"),  # Very generic "Firstname Lastname"
    re.compile(r"admin|editor|staff|team|author\d+|user\d+", re.I),
    re.compile(r"^\w+$"),  # Single word "username" style
]


def analyze_author(author_info: Dict) -> Dict:
    """Analyze author information for signs of fake/AI-generated identities.

    Args:
        author_info: Dict with 'names', 'bios', and 'image_urls' keys.

    Returns:
        Dict with score, signals, and analysis details.
    """
    signals = []

    names = author_info.get("names", [])
    bios = author_info.get("bios", [])
    image_urls = author_info.get("image_urls", [])

    # 1. No author information at all
    if not names and not bios:
        signals.append({
            "name": "no_author_info",
            "triggered": True,
            "confidence": 0.4,
            "detail": "No author information found on the page",
        })
    else:
        # 2. Generic bio phrases
        bio_text = " ".join(bios).lower()
        if bio_text:
            found_generic = [p for p in GENERIC_BIO_PHRASES if p in bio_text]
            if len(found_generic) >= 2:
                signals.append({
                    "name": "generic_bio_phrases",
                    "triggered": True,
                    "confidence": min(0.7, len(found_generic) * 0.15),
                    "detail": f"Bio contains {len(found_generic)} generic phrases: {found_generic[:3]}",
                })

        # 3. Suspicious author name patterns
        for name in names[:5]:  # Check first 5 names
            clean_name = name.strip()
            if _is_suspicious_name(clean_name):
                signals.append({
                    "name": "suspicious_author_name",
                    "triggered": True,
                    "confidence": 0.4,
                    "detail": f"Author name appears generic or auto-generated: '{clean_name}'",
                })
                break

    # 4. Stock photo detection
    if image_urls:
        stock_found = []
        for url in image_urls:
            for pattern in STOCK_PHOTO_PATTERNS:
                if pattern.search(url):
                    stock_found.append(url)
                    break

        if stock_found:
            signals.append({
                "name": "stock_photo_author",
                "triggered": True,
                "confidence": 0.6,
                "detail": f"Author image appears to be a stock photo: {stock_found[0][:60]}",
            })

    # 5. Bio length check (very short bios often fake)
    if bios:
        avg_bio_len = sum(len(b.split()) for b in bios) / len(bios)
        if avg_bio_len < 10:
            signals.append({
                "name": "very_short_bio",
                "triggered": True,
                "confidence": 0.3,
                "detail": f"Author bio is very short ({avg_bio_len:.0f} words average)",
            })

    triggered = [s for s in signals if s.get("triggered")]
    if triggered:
        score = sum(s["confidence"] for s in triggered) / max(len(signals), 1)
    else:
        score = 0.05

    return {
        "score": round(score, 3),
        "signals": signals,
        "stats": {
            "names_found": len(names),
            "bios_found": len(bios),
            "images_found": len(image_urls),
        },
    }


def _is_suspicious_name(name: str) -> bool:
    """Check if an author name looks suspicious."""
    # Check for explicit admin-type names
    if re.search(r"admin|editor|staff|author\d+|user\d+", name, re.I):
        return True

    # Check for very short names (likely usernames)
    parts = name.split()
    if len(parts) == 1 and len(name) < 4:
        return True

    return False


def check_author_from_text(text: str) -> Dict:
    """Check for author-related patterns directly in page text.

    Useful when structured author_info is not available.

    Args:
        text: Plain text content of the page.

    Returns:
        Dict with author analysis results.
    """
    author_info = {
        "names": [],
        "bios": [],
        "image_urls": [],
    }

    # Look for "By [Name]" patterns
    by_patterns = re.findall(r"[Bb]y\s+([A-Z][a-z]+ [A-Z][a-z]+)", text)
    author_info["names"].extend(by_patterns)

    # Look for bio-like paragraphs
    bio_keywords = re.compile(
        r"(passionate|expert|experience|writer|specialist|enthusiast)", re.I
    )
    paragraphs = text.split("\n\n")
    for para in paragraphs:
        if bio_keywords.search(para) and len(para.split()) < 80:
            author_info["bios"].append(para.strip())

    return analyze_author(author_info)
