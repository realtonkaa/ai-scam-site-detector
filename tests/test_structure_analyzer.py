"""Tests for structure_analyzer module."""

import pytest
from src.structure_analyzer import (
    analyze_structure,
    _check_about_page,
    _check_contact_info,
    _check_excessive_ctas,
    _check_social_links,
    _check_legal_pages,
)

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

pytestmark = pytest.mark.skipif(not BS4_AVAILABLE, reason="beautifulsoup4 not installed")


def make_soup(html):
    return BeautifulSoup(html, "html.parser")


class TestAnalyzeStructureBasics:
    def test_returns_dict(self, legit_html):
        result = analyze_structure(legit_html)
        assert isinstance(result, dict)

    def test_has_required_keys(self, legit_html):
        result = analyze_structure(legit_html)
        assert "score" in result
        assert "signals" in result
        assert "metadata" in result

    def test_score_in_range(self, legit_html):
        result = analyze_structure(legit_html)
        assert 0.0 <= result["score"] <= 1.0

    def test_empty_html_returns_error(self):
        result = analyze_structure("")
        assert "error" in result

    def test_short_html_returns_error(self):
        result = analyze_structure("<p>hi</p>")
        assert "error" in result


class TestAboutPageDetection:
    def test_missing_about_page_triggers_signal(self):
        html = "<html><body><a href='/home'>Home</a><a href='/contact'>Contact</a></body></html>"
        soup = make_soup(html)
        signal = _check_about_page(soup)
        assert signal is not None
        assert signal["triggered"] is True
        assert signal["name"] == "missing_about_page"

    def test_has_about_page_no_signal(self):
        html = "<html><body><a href='/about'>About Us</a></body></html>"
        soup = make_soup(html)
        signal = _check_about_page(soup)
        assert signal is None

    def test_about_in_href_no_signal(self):
        html = "<html><body><a href='/about-us'>Company</a></body></html>"
        soup = make_soup(html)
        signal = _check_about_page(soup)
        assert signal is None

    def test_legit_page_has_about(self, legit_html):
        result = analyze_structure(legit_html)
        signal_names = [s["name"] for s in result["signals"] if s.get("triggered")]
        assert "missing_about_page" not in signal_names


class TestContactInfoDetection:
    def test_no_contact_info_triggers_signal(self):
        html = "<html><body><p>Welcome to our site. We sell things.</p></body></html>"
        soup = make_soup(html)
        signal, meta = _check_contact_info(soup, html)
        assert signal is not None
        assert signal["triggered"] is True

    def test_phone_number_detected(self):
        html = "<html><body><p>Call us: (303) 555-0142</p></body></html>"
        soup = make_soup(html)
        signal, meta = _check_contact_info(soup, html)
        assert meta["has_phone"] is True

    def test_email_detected(self):
        html = "<html><body><p>Email: hello@example.com</p></body></html>"
        soup = make_soup(html)
        signal, meta = _check_contact_info(soup, html)
        assert meta["has_email"] is True

    def test_address_detected(self):
        html = "<html><body><p>Visit us at 123 Main Street, Denver CO</p></body></html>"
        soup = make_soup(html)
        signal, meta = _check_contact_info(soup, html)
        assert meta["has_address"] is True

    def test_contact_form_only_triggers_signal(self):
        html = (
            '<html><body>'
            '<form id="contact-form"><input type="email"><button>Send</button></form>'
            '</body></html>'
        )
        soup = make_soup(html)
        signal, meta = _check_contact_info(soup, html)
        assert signal is not None
        assert signal["triggered"] is True


class TestCTADetection:
    def test_excessive_ctas_trigger_signal(self, scam_html):
        soup = make_soup(scam_html)
        signal, count = _check_excessive_ctas(soup)
        assert signal is not None
        assert signal["triggered"] is True
        assert signal["name"] == "excessive_cta"

    def test_few_ctas_no_signal(self):
        html = "<html><body><a href='/signup'>Sign up</a><p>Content here.</p></body></html>"
        soup = make_soup(html)
        signal, count = _check_excessive_ctas(soup)
        assert signal is None

    def test_count_returns_number(self):
        html = "<html><body><button>Buy Now</button></body></html>"
        soup = make_soup(html)
        signal, count = _check_excessive_ctas(soup)
        assert isinstance(count, int)


class TestSocialLinksDetection:
    def test_no_social_links_triggers_signal(self):
        html = "<html><body><a href='/about'>About</a></body></html>"
        soup = make_soup(html)
        signal, meta = _check_social_links(soup)
        assert signal is not None
        assert signal["triggered"] is True
        assert signal["name"] == "no_social_media"

    def test_social_links_found_no_signal(self):
        html = (
            "<html><body>"
            "<a href='https://twitter.com/example'>Twitter</a>"
            "<a href='https://facebook.com/example'>Facebook</a>"
            "</body></html>"
        )
        soup = make_soup(html)
        signal, meta = _check_social_links(soup)
        assert signal is None

    def test_social_meta_contains_domain(self):
        html = "<html><body><a href='https://instagram.com/test'>Instagram</a></body></html>"
        soup = make_soup(html)
        signal, meta = _check_social_links(soup)
        assert "instagram.com" in meta

    def test_legit_page_has_social(self, legit_html):
        soup = make_soup(legit_html)
        signal, meta = _check_social_links(soup)
        assert signal is None


class TestLegalPagesDetection:
    def test_no_legal_pages_triggers_signal(self):
        html = "<html><body><a href='/home'>Home</a><a href='/about'>About</a></body></html>"
        soup = make_soup(html)
        signal = _check_legal_pages(soup)
        assert signal is not None
        assert signal["triggered"] is True

    def test_privacy_policy_found_no_signal(self):
        html = (
            "<html><body>"
            "<a href='/privacy-policy'>Privacy Policy</a>"
            "</body></html>"
        )
        soup = make_soup(html)
        signal = _check_legal_pages(soup)
        assert signal is None

    def test_terms_found_no_signal(self):
        html = (
            "<html><body>"
            "<a href='/terms-of-service'>Terms of Service</a>"
            "</body></html>"
        )
        soup = make_soup(html)
        signal = _check_legal_pages(soup)
        assert signal is None

    def test_legit_page_has_legal_links(self, legit_html):
        soup = make_soup(legit_html)
        signal = _check_legal_pages(soup)
        assert signal is None


class TestFixtureComparison:
    def test_scam_page_scores_higher_than_legit(self, legit_html, scam_html):
        legit_result = analyze_structure(legit_html)
        scam_result = analyze_structure(scam_html)
        assert scam_result["score"] > legit_result["score"]

    def test_scam_page_has_more_signals(self, legit_html, scam_html):
        legit_result = analyze_structure(legit_html)
        scam_result = analyze_structure(scam_html)
        legit_triggered = sum(1 for s in legit_result["signals"] if s.get("triggered"))
        scam_triggered = sum(1 for s in scam_result["signals"] if s.get("triggered"))
        assert scam_triggered >= legit_triggered
