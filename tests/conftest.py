"""Shared fixtures for test suite."""

import os
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def legit_text():
    """Load legitimate text fixture."""
    with open(os.path.join(FIXTURES_DIR, "legit_text.txt"), encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def scam_text():
    """Load scam/AI-generated text fixture."""
    with open(os.path.join(FIXTURES_DIR, "scam_text.txt"), encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def legit_html():
    """Load legitimate page HTML fixture."""
    with open(os.path.join(FIXTURES_DIR, "legit_page.html"), encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def scam_html():
    """Load scam page HTML fixture."""
    with open(os.path.join(FIXTURES_DIR, "scam_page.html"), encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def legit_author_info():
    """Author info matching the legit page fixture."""
    return {
        "names": ["Sarah Chen"],
        "bios": [
            "Sarah Chen is a gear editor with 12 years of experience covering outdoor equipment. "
            "She has completed the Colorado Trail twice and tested gear in conditions from desert "
            "heat to alpine winter. She lives in Fort Collins, Colorado with her two dogs."
        ],
        "image_urls": ["/images/sarah-chen.jpg"],
    }


@pytest.fixture
def scam_author_info():
    """Author info matching the scam page fixture."""
    return {
        "names": ["Admin"],
        "bios": ["Expert in making money online."],
        "image_urls": ["/images/default-user-avatar.png"],
    }


@pytest.fixture
def empty_author_info():
    """Empty author info."""
    return {"names": [], "bios": [], "image_urls": []}


@pytest.fixture
def minimal_analysis_results():
    """Minimal analysis results dict for scorer testing."""
    return {
        "content": {"score": 0.1, "signals": []},
        "structure": {"score": 0.1, "signals": []},
        "domain": {"score": 0.1, "signals": []},
        "author": {"score": 0.1, "signals": []},
    }
