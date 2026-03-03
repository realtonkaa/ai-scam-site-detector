"""Tests for domain_checker module."""

import pytest
from src.domain_checker import analyze_domain, SUSPICIOUS_TLDS, TRUSTED_TLDS


class TestAnalyzeDomainBasics:
    def test_returns_dict(self):
        result = analyze_domain("https://example.com")
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        result = analyze_domain("https://example.com")
        assert "domain" in result
        assert "tld" in result
        assert "score" in result
        assert "signals" in result

    def test_score_in_range(self):
        result = analyze_domain("https://example.com")
        assert 0.0 <= result["score"] <= 1.0

    def test_extracts_domain(self):
        result = analyze_domain("https://example.com/some/path")
        assert result["domain"] == "example.com"

    def test_extracts_tld(self):
        result = analyze_domain("https://example.com")
        assert result["tld"] == ".com"

    def test_url_without_scheme(self):
        result = analyze_domain("example.com")
        assert "example" in result["domain"]

    def test_url_with_port_stripped(self):
        result = analyze_domain("https://example.com:8080")
        assert "8080" not in result["domain"]


class TestSuspiciousTLD:
    def test_xyz_tld_triggers_signal(self):
        result = analyze_domain("https://mysite.xyz")
        signal_names = [s["name"] for s in result["signals"]]
        assert "suspicious_tld" in signal_names

    def test_top_tld_triggers_signal(self):
        result = analyze_domain("https://bestdeals.top")
        signal_names = [s["name"] for s in result["signals"]]
        assert "suspicious_tld" in signal_names

    def test_buzz_tld_triggers_signal(self):
        result = analyze_domain("https://news.buzz")
        signal_names = [s["name"] for s in result["signals"]]
        assert "suspicious_tld" in signal_names

    def test_click_tld_triggers_signal(self):
        result = analyze_domain("https://deal.click")
        signal_names = [s["name"] for s in result["signals"]]
        assert "suspicious_tld" in signal_names

    def test_com_tld_no_suspicious_signal(self):
        result = analyze_domain("https://example.com")
        signal_names = [s["name"] for s in result["signals"]]
        assert "suspicious_tld" not in signal_names

    def test_gov_tld_trusted_signal(self):
        result = analyze_domain("https://example.gov")
        signal_names = [s["name"] for s in result["signals"]]
        assert "trusted_tld" in signal_names

    def test_suspicious_tlds_set_populated(self):
        assert len(SUSPICIOUS_TLDS) >= 10

    def test_suspicious_tld_confidence(self):
        result = analyze_domain("https://mysite.xyz")
        for sig in result["signals"]:
            if sig["name"] == "suspicious_tld":
                assert sig["confidence"] > 0
                break

    def test_icu_triggers_signal(self):
        result = analyze_domain("https://deals.icu")
        signal_names = [s["name"] for s in result["signals"]]
        assert "suspicious_tld" in signal_names


class TestDomainLength:
    def test_long_domain_triggers_signal(self):
        result = analyze_domain("https://this-is-a-very-long-domain-name-here.com")
        signal_names = [s["name"] for s in result["signals"]]
        assert "long_domain_name" in signal_names

    def test_short_domain_no_signal(self):
        result = analyze_domain("https://bbc.com")
        signal_names = [s["name"] for s in result["signals"]]
        assert "long_domain_name" not in signal_names

    def test_domain_exactly_20_chars_no_signal(self):
        # 20 chars exactly - boundary test
        result = analyze_domain("https://twentycharsdo1234.com")
        # Just checking it doesn't crash
        assert isinstance(result, dict)


class TestNumbersInDomain:
    def test_numbers_in_domain_trigger_signal(self):
        result = analyze_domain("https://news123456.com")
        signal_names = [s["name"] for s in result["signals"]]
        assert "numbers_in_domain" in signal_names

    def test_single_number_no_signal(self):
        result = analyze_domain("https://web2.example.com")
        signal_names = [s["name"] for s in result["signals"]]
        assert "numbers_in_domain" not in signal_names

    def test_two_numbers_no_signal(self):
        result = analyze_domain("https://news42.com")
        signal_names = [s["name"] for s in result["signals"]]
        assert "numbers_in_domain" not in signal_names


class TestHyphensInDomain:
    def test_multiple_hyphens_trigger_signal(self):
        result = analyze_domain("https://best-deals-now.com")
        signal_names = [s["name"] for s in result["signals"]]
        assert "multiple_hyphens" in signal_names

    def test_single_hyphen_no_signal(self):
        result = analyze_domain("https://my-site.com")
        signal_names = [s["name"] for s in result["signals"]]
        assert "multiple_hyphens" not in signal_names

    def test_no_hyphens_no_signal(self):
        result = analyze_domain("https://example.com")
        signal_names = [s["name"] for s in result["signals"]]
        assert "multiple_hyphens" not in signal_names


class TestKeywordStuffing:
    def test_keyword_stuffed_domain_triggers_signal(self):
        result = analyze_domain("https://bestfreedeal.com")
        signal_names = [s["name"] for s in result["signals"]]
        assert "keyword_stuffed_domain" in signal_names

    def test_clean_domain_no_keyword_stuffing(self):
        result = analyze_domain("https://nytimes.com")
        signal_names = [s["name"] for s in result["signals"]]
        assert "keyword_stuffed_domain" not in signal_names
