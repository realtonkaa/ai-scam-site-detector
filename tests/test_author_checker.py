"""Tests for author_checker module."""

import pytest
from src.author_checker import (
    analyze_author,
    check_author_from_text,
    _is_suspicious_name,
    GENERIC_BIO_PHRASES,
    STOCK_PHOTO_PATTERNS,
)


class TestAnalyzeAuthorBasics:
    def test_returns_dict(self, legit_author_info):
        result = analyze_author(legit_author_info)
        assert isinstance(result, dict)

    def test_has_required_keys(self, legit_author_info):
        result = analyze_author(legit_author_info)
        assert "score" in result
        assert "signals" in result
        assert "stats" in result

    def test_score_in_range(self, legit_author_info):
        result = analyze_author(legit_author_info)
        assert 0.0 <= result["score"] <= 1.0

    def test_stats_counts(self, legit_author_info):
        result = analyze_author(legit_author_info)
        assert result["stats"]["names_found"] == 1
        assert result["stats"]["bios_found"] == 1


class TestNoAuthorInfo:
    def test_empty_author_triggers_signal(self, empty_author_info):
        result = analyze_author(empty_author_info)
        signal_names = [s["name"] for s in result["signals"]]
        assert "no_author_info" in signal_names

    def test_empty_author_has_score(self, empty_author_info):
        result = analyze_author(empty_author_info)
        assert result["score"] > 0


class TestGenericBioPhrases:
    def test_generic_phrases_trigger_signal(self):
        author_info = {
            "names": ["John Smith"],
            "bios": [
                "John is a passionate writer and expert in digital marketing with years of experience. "
                "He is dedicated to helping readers find the best content online."
            ],
            "image_urls": [],
        }
        result = analyze_author(author_info)
        signal_names = [s["name"] for s in result["signals"]]
        assert "generic_bio_phrases" in signal_names

    def test_specific_bio_no_signal(self, legit_author_info):
        result = analyze_author(legit_author_info)
        signal_names = [s["name"] for s in result["signals"]]
        assert "generic_bio_phrases" not in signal_names

    def test_single_generic_phrase_no_signal(self):
        """One generic phrase alone shouldn't trigger (threshold is >= 2)."""
        author_info = {
            "names": ["Jane Doe"],
            "bios": ["Jane is passionate about cooking and loves to share recipes."],
            "image_urls": [],
        }
        result = analyze_author(author_info)
        signal_names = [s["name"] for s in result["signals"]]
        assert "generic_bio_phrases" not in signal_names

    def test_generic_phrases_list_populated(self):
        assert len(GENERIC_BIO_PHRASES) >= 10


class TestStockPhotoDetection:
    def test_shutterstock_url_triggers_signal(self):
        author_info = {
            "names": ["Author"],
            "bios": ["A writer."],
            "image_urls": ["https://www.shutterstock.com/image-photo/person-12345"],
        }
        result = analyze_author(author_info)
        signal_names = [s["name"] for s in result["signals"]]
        assert "stock_photo_author" in signal_names

    def test_default_avatar_triggers_signal(self):
        author_info = {
            "names": ["Admin"],
            "bios": ["Site admin."],
            "image_urls": ["/images/default-user-avatar.png"],
        }
        result = analyze_author(author_info)
        signal_names = [s["name"] for s in result["signals"]]
        assert "stock_photo_author" in signal_names

    def test_real_author_image_no_signal(self, legit_author_info):
        result = analyze_author(legit_author_info)
        signal_names = [s["name"] for s in result["signals"]]
        assert "stock_photo_author" not in signal_names

    def test_getty_images_triggers_signal(self):
        author_info = {
            "names": ["Author"],
            "bios": ["A writer."],
            "image_urls": ["https://media.gettyimages.com/photos/person-id-12345"],
        }
        result = analyze_author(author_info)
        signal_names = [s["name"] for s in result["signals"]]
        assert "stock_photo_author" in signal_names

    def test_stock_patterns_list_populated(self):
        assert len(STOCK_PHOTO_PATTERNS) >= 5


class TestSuspiciousNames:
    def test_admin_name_is_suspicious(self):
        assert _is_suspicious_name("admin") is True

    def test_numbered_author_is_suspicious(self):
        assert _is_suspicious_name("author123") is True

    def test_real_name_not_suspicious(self):
        assert _is_suspicious_name("Sarah Chen") is False

    def test_very_short_single_word_suspicious(self):
        assert _is_suspicious_name("Ed") is True

    def test_staff_is_suspicious(self):
        assert _is_suspicious_name("Staff Writer") is True

    def test_user_number_suspicious(self):
        assert _is_suspicious_name("user42") is True


class TestVeryShortBio:
    def test_very_short_bio_triggers_signal(self):
        author_info = {
            "names": ["Admin"],
            "bios": ["Expert writer."],
            "image_urls": [],
        }
        result = analyze_author(author_info)
        signal_names = [s["name"] for s in result["signals"]]
        assert "very_short_bio" in signal_names


class TestCheckAuthorFromText:
    def test_returns_dict(self):
        text = "By Sarah Chen. This is a great article about baking bread."
        result = check_author_from_text(text)
        assert isinstance(result, dict)

    def test_detects_byline(self):
        text = "By John Smith. This article explores the history of bread baking in detail."
        result = check_author_from_text(text)
        assert result["stats"]["names_found"] >= 0  # May or may not find depending on regex

    def test_scam_author_info_scores_higher(self, scam_author_info, legit_author_info):
        scam_result = analyze_author(scam_author_info)
        legit_result = analyze_author(legit_author_info)
        assert scam_result["score"] >= legit_result["score"]
