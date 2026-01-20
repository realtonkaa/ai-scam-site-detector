"""Tests for content_analyzer module."""

import pytest
from src.content_analyzer import (
    analyze_content,
    AI_FILLER_PHRASES,
    SUPERLATIVES,
    _split_into_chunks,
)


class TestAnalyzeContentBasics:
    def test_returns_dict(self):
        result = analyze_content("This is some sample text with enough words to analyze properly here.")
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        result = analyze_content("This is some sample text with enough words to analyze properly here.")
        assert "score" in result
        assert "signals" in result
        assert "stats" in result

    def test_score_is_float(self):
        result = analyze_content("This is some sample text with enough words to analyze properly here.")
        assert isinstance(result["score"], float)

    def test_score_in_range(self):
        result = analyze_content("This is some sample text with enough words to analyze properly here.")
        assert 0.0 <= result["score"] <= 1.0

    def test_short_text_returns_error(self):
        result = analyze_content("Too short")
        assert "error" in result

    def test_empty_text_returns_error(self):
        result = analyze_content("")
        assert "error" in result

    def test_none_like_empty(self):
        result = analyze_content("")
        assert result["score"] == 0

    def test_signals_is_list(self):
        result = analyze_content("This is some sample text with enough words to analyze properly here.")
        assert isinstance(result["signals"], list)


class TestSuperlativeDensity:
    def test_high_superlative_density_triggers_signal(self):
        text = (
            "This is the best and most amazing and most incredible product. "
            "It is truly outstanding and exceptional and remarkable. "
            "The most extraordinary and unparalleled solution. "
            "World-class premium ultimate extraordinary results."
        )
        result = analyze_content(text)
        signal_names = [s["name"] for s in result["signals"]]
        assert "high_superlative_density" in signal_names

    def test_low_superlative_density_no_signal(self):
        text = (
            "The bread was good. I ate it for lunch on a Tuesday. "
            "The crust was crispy and the inside was soft. "
            "I bought it from the bakery on the corner of Main Street. "
            "It cost about four dollars and was worth it."
        )
        result = analyze_content(text)
        signal_names = [s["name"] for s in result["signals"]]
        assert "high_superlative_density" not in signal_names

    def test_superlative_stats_recorded(self):
        text = "best amazing incredible revolutionary groundbreaking " * 10
        result = analyze_content(text)
        assert result["stats"]["superlative_density"] > 0


class TestFillerPhrases:
    def test_multiple_filler_phrases_trigger_signal(self):
        text = (
            "In today's fast-paced world you need to look no further. "
            "Whether you're a beginner or an expert, it's important to note "
            "that our cutting-edge game-changer will revolutionize your workflow. "
            "At the end of the day, this seamless solution will empower you. "
            "Leverage our robust comprehensive guide to unlock the power today."
        )
        result = analyze_content(text)
        signal_names = [s["name"] for s in result["signals"]]
        assert "ai_filler_phrases" in signal_names

    def test_no_filler_phrases_no_signal(self):
        text = (
            "The cat sat on the mat. It was a grey cat with white paws. "
            "The mat was red. The cat fell asleep after lunch. "
            "A dog walked by outside but the cat did not notice. "
            "The window was open and a breeze came in from the north."
        )
        result = analyze_content(text)
        signal_names = [s["name"] for s in result["signals"]]
        assert "ai_filler_phrases" not in signal_names

    def test_filler_count_in_stats(self):
        text = (
            "In today's fast-paced world you need to look no further. "
            "Whether you're a beginner this seamless game-changer will "
            "revolutionize your leverage-based streamline workflow. "
            "Empower yourself with our robust cutting-edge comprehensive guide."
        )
        result = analyze_content(text)
        assert result["stats"]["filler_phrases_found"] >= 0

    def test_filler_phrase_list_not_empty(self):
        assert len(AI_FILLER_PHRASES) > 10


class TestSentenceUniformity:
    def test_uniform_sentences_trigger_signal(self):
        # Very uniform: all sentences are about 8-10 words
        text = (
            "The product is really good and you should buy it. "
            "Our service is great and helps you every single day. "
            "We offer support that is fast and truly reliable always. "
            "The results you get are always amazing and very consistent. "
            "Customers love our product and recommend it to their friends."
        )
        result = analyze_content(text)
        signal_names = [s["name"] for s in result["signals"]]
        assert "uniform_sentence_length" in signal_names

    def test_varied_sentences_no_signal(self):
        text = (
            "Hi. "
            "The bread was baked slowly in a wood-fired oven for three hours until it achieved a deep golden crust. "
            "Good. "
            "She walked to the store on a cold Tuesday morning in November, bundled up against the sharp wind that had been blowing since dawn. "
            "OK. "
            "That worked."
        )
        result = analyze_content(text)
        signal_names = [s["name"] for s in result["signals"]]
        assert "uniform_sentence_length" not in signal_names


class TestVocabularyDiversity:
    def test_low_diversity_triggers_signal(self):
        # Repeat the same small set of words
        text = "good product good service good quality good value good price " * 15
        result = analyze_content(text)
        signal_names = [s["name"] for s in result["signals"]]
        assert "low_vocabulary_diversity" in signal_names

    def test_ttr_in_stats(self):
        text = "The quick brown fox jumps over the lazy dog in the park today."
        result = analyze_content(text)
        assert "ttr" in result["stats"]
        assert 0.0 <= result["stats"]["ttr"] <= 1.0

    def test_rich_vocabulary_no_diversity_signal(self, legit_text):
        result = analyze_content(legit_text)
        signal_names = [s["name"] for s in result["signals"]]
        assert "low_vocabulary_diversity" not in signal_names


class TestParagraphUniformity:
    def test_uniform_paragraphs_trigger_signal(self):
        # Four paragraphs all around 20 words
        para = "This product is absolutely revolutionary and will change your life completely. We guarantee results.\n\n"
        text = para * 5
        result = analyze_content(text)
        signal_names = [s["name"] for s in result["signals"]]
        assert "uniform_paragraphs" in signal_names

    def test_varied_paragraphs_no_signal(self):
        text = (
            "Short.\n\n"
            "This is a longer paragraph with quite a bit more content than the previous one, "
            "explaining something in some detail.\n\n"
            "Medium length paragraph here.\n\n"
            "This paragraph is also quite long and goes into even more depth about the subject matter "
            "than previous paragraphs. It continues for a while with many different words and ideas.\n\n"
            "Tiny.\n\n"
        )
        result = analyze_content(text)
        signal_names = [s["name"] for s in result["signals"]]
        assert "uniform_paragraphs" not in signal_names


class TestFixtureComparison:
    def test_scam_text_scores_higher_than_legit(self, scam_text, legit_text):
        scam_result = analyze_content(scam_text)
        legit_result = analyze_content(legit_text)
        assert scam_result["score"] > legit_result["score"]

    def test_scam_text_has_signals(self, scam_text):
        result = analyze_content(scam_text)
        assert len(result["signals"]) > 0

    def test_legit_text_low_score(self, legit_text):
        result = analyze_content(legit_text)
        assert result["score"] < 0.5

    def test_scam_text_triggers_filler_phrases(self, scam_text):
        result = analyze_content(scam_text)
        signal_names = [s["name"] for s in result["signals"]]
        assert "ai_filler_phrases" in signal_names


class TestHelperFunctions:
    def test_split_into_chunks(self):
        text = " ".join(["word"] * 300)
        chunks = _split_into_chunks(text, chunk_size=100)
        assert len(chunks) >= 2

    def test_split_into_chunks_minimum_size(self):
        text = " ".join(["word"] * 40)
        chunks = _split_into_chunks(text, chunk_size=100)
        assert len(chunks) == 0  # Too short for a full chunk

    def test_superlatives_list_not_empty(self):
        assert len(SUPERLATIVES) >= 10
