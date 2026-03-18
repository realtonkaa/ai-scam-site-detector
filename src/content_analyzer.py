"""Content analysis for detecting AI-generated text."""

import re
import statistics
from typing import Dict, List

try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False

AI_FILLER_PHRASES = [
    "in today's fast-paced", "in today's digital", "look no further",
    "whether you're a", "it's important to note", "it goes without saying",
    "at the end of the day", "in conclusion", "without further ado",
    "game-changer", "revolutionize", "cutting-edge", "state-of-the-art",
    "seamless", "leverage", "empower", "streamline", "robust",
    "comprehensive guide", "ultimate guide", "everything you need to know",
    "dive deep", "deep dive", "unlock the power", "take it to the next level",
    "don't miss out", "sign up today", "limited time offer",
    "transform your", "boost your", "maximize your", "unleash your",
    "in the ever-evolving", "fast-paced world", "digital age",
    "look no further than", "need not look further", "rest assured",
]

SUPERLATIVES = [
    "best", "amazing", "incredible", "revolutionary", "groundbreaking",
    "unparalleled", "exceptional", "outstanding", "remarkable", "extraordinary",
    "unmatched", "world-class", "top-notch", "premium", "ultimate",
    "phenomenal", "spectacular", "fantastic", "superb", "magnificent",
]


def analyze_content(text: str) -> Dict:
    """Analyze text for signs of AI generation.

    Args:
        text: The text content to analyze.

    Returns:
        Dict with score (0.0-1.0), signals list, and stats.
    """
    if not text or len(text) < 50:
        return {"score": 0, "signals": [], "error": "Text too short to analyze"}

    signals = []
    found_fillers: List[str] = []

    # 1. Sentence length uniformity
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    if len(sentences) >= 5:
        lengths = [len(s.split()) for s in sentences]
        std_dev = statistics.stdev(lengths) if len(lengths) > 1 else 0
        mean_len = statistics.mean(lengths)
        cv = std_dev / mean_len if mean_len > 0 else 0
        if cv < 0.3:  # Very uniform
            signals.append({
                "name": "uniform_sentence_length",
                "triggered": True,
                "confidence": min(0.8, (0.3 - cv) * 3),
                "detail": f"Sentence length CV={cv:.2f} (low variation suggests AI)",
            })

    # 2. Superlative density
    word_count = len(text.split())
    superlative_count = sum(
        1 for word in text.lower().split()
        if word.strip(".,!?;:") in SUPERLATIVES
    )
    superlative_density = (superlative_count / word_count * 100) if word_count > 0 else 0
    if superlative_density > 2:
        signals.append({
            "name": "high_superlative_density",
            "triggered": True,
            "confidence": min(0.7, superlative_density / 5),
            "detail": f"{superlative_count} superlatives in {word_count} words ({superlative_density:.1f}%)",
        })

    # 3. Filler phrase detection
    text_lower = text.lower()
    found_fillers = [p for p in AI_FILLER_PHRASES if p in text_lower]
    if len(found_fillers) >= 2:
        signals.append({
            "name": "ai_filler_phrases",
            "triggered": True,
            "confidence": min(0.9, len(found_fillers) * 0.2),
            "detail": f"Found {len(found_fillers)} AI-typical phrases: {found_fillers[:3]}",
        })

    # 4. Vocabulary diversity (type-token ratio)
    words = text.lower().split()
    if len(words) > 50:
        unique_words = set(words)
        ttr = len(unique_words) / len(words)
        if ttr < 0.4:
            signals.append({
                "name": "low_vocabulary_diversity",
                "triggered": True,
                "confidence": min(0.6, (0.4 - ttr) * 3),
                "detail": f"Type-token ratio={ttr:.2f} (low diversity suggests AI)",
            })

    # 5. Paragraph uniformity
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]
    if len(paragraphs) >= 4:
        para_lengths = [len(p.split()) for p in paragraphs]
        para_mean = statistics.mean(para_lengths)
        para_cv = (
            statistics.stdev(para_lengths) / para_mean
            if para_mean > 0 and len(para_lengths) > 1
            else 0
        )
        if para_cv < 0.25:
            signals.append({
                "name": "uniform_paragraphs",
                "triggered": True,
                "confidence": min(0.5, (0.25 - para_cv) * 3),
                "detail": f"Paragraph length CV={para_cv:.2f} (uniform structure)",
            })

    # 6. Readability uniformity (optional, requires textstat)
    if TEXTSTAT_AVAILABLE and len(text) > 200:
        # Split into chunks and check readability variance
        chunks = _split_into_chunks(text, chunk_size=100)
        if len(chunks) >= 3:
            scores = [textstat.flesch_reading_ease(chunk) for chunk in chunks]
            scores = [s for s in scores if -100 < s < 200]  # filter outliers
            if len(scores) >= 3:
                score_std = statistics.stdev(scores)
                if score_std < 5:
                    signals.append({
                        "name": "uniform_readability",
                        "triggered": True,
                        "confidence": min(0.4, (5 - score_std) / 10),
                        "detail": f"Flesch score std dev={score_std:.1f} (suspiciously uniform readability)",
                    })

    # Overall content score
    if signals:
        content_score = sum(s["confidence"] for s in signals) / len(signals)
    else:
        content_score = 0.1  # Low risk if no signals triggered

    return {
        "score": round(content_score, 3),
        "signals": signals,
        "stats": {
            "word_count": word_count,
            "sentence_count": len(sentences),
            "superlative_density": round(superlative_density, 2),
            "filler_phrases_found": len(found_fillers),
            "ttr": round(len(set(text.lower().split())) / max(len(text.split()), 1), 3),
        },
    }


def _split_into_chunks(text: str, chunk_size: int = 100) -> List[str]:
    """Split text into word-count chunks for analysis."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        if len(chunk.split()) >= chunk_size // 2:
            chunks.append(chunk)
    return chunks
