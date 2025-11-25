"""Web page scraping and content extraction."""

import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPER_AVAILABLE = True
except ImportError:
    SCRAPER_AVAILABLE = False

from .config import REQUEST_TIMEOUT, REQUEST_HEADERS


def fetch_page(url: str) -> Dict:
    """Fetch a web page and return its content and metadata.

    Args:
        url: The URL to fetch.

    Returns:
        Dict with keys: url, title, meta_description, text, links, images,
        html, author_info, error (if any).
    """
    if not SCRAPER_AVAILABLE:
        return {"error": "requests and beautifulsoup4 are required for scraping"}

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    result = {
        "url": url,
        "title": "",
        "meta_description": "",
        "text": "",
        "links": [],
        "images": [],
        "html": "",
        "author_info": {},
        "error": None,
    }

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers=REQUEST_HEADERS,
            allow_redirects=True,
        )
        response.raise_for_status()
        result["html"] = response.text
        result["final_url"] = response.url

        soup = BeautifulSoup(response.text, "html.parser")

        # Title
        title_tag = soup.find("title")
        if title_tag:
            result["title"] = title_tag.get_text(strip=True)

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            result["meta_description"] = meta_desc.get("content", "")

        # Main text content
        result["text"] = _extract_text(soup)

        # Links
        result["links"] = _extract_links(soup, url)

        # Images
        result["images"] = _extract_images(soup, url)

        # Author info
        result["author_info"] = _extract_author_info(soup)

    except requests.exceptions.ConnectionError:
        result["error"] = f"Could not connect to {url}"
    except requests.exceptions.Timeout:
        result["error"] = f"Request timed out for {url}"
    except requests.exceptions.HTTPError as e:
        result["error"] = f"HTTP error: {e}"
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"

    return result


def _extract_text(soup: "BeautifulSoup") -> str:
    """Extract clean text from HTML, removing scripts and styles."""
    # Remove unwanted tags
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        tag.decompose()

    # Try to find main content area first
    main_content = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id=re.compile(r"content|main|body", re.I))
        or soup.find(class_=re.compile(r"content|main|body|post", re.I))
    )

    if main_content:
        text = main_content.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # Clean up excessive whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n\n".join(lines)


def _extract_links(soup: "BeautifulSoup", base_url: str) -> List[Dict]:
    """Extract all links from the page."""
    links = []
    seen = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        full_url = urljoin(base_url, href)
        if full_url not in seen:
            seen.add(full_url)
            links.append({
                "url": full_url,
                "text": a_tag.get_text(strip=True)[:100],
                "rel": a_tag.get("rel", []),
            })

    return links[:200]  # Cap at 200 links


def _extract_images(soup: "BeautifulSoup", base_url: str) -> List[Dict]:
    """Extract image information from the page."""
    images = []

    for img in soup.find_all("img", src=True):
        src = img.get("src", "").strip()
        if not src:
            continue

        full_src = urljoin(base_url, src)
        images.append({
            "src": full_src,
            "alt": img.get("alt", ""),
            "class": " ".join(img.get("class", [])),
        })

    return images[:100]


def _extract_author_info(soup: "BeautifulSoup") -> Dict:
    """Extract author-related information from the page."""
    author_info = {
        "names": [],
        "bios": [],
        "image_urls": [],
    }

    # Look for author bylines
    author_patterns = [
        {"class": re.compile(r"author|byline|writer", re.I)},
        {"rel": "author"},
        {"itemprop": "author"},
    ]

    for pattern in author_patterns:
        for tag in soup.find_all(True, pattern):
            text = tag.get_text(strip=True)
            if text and len(text) > 2:
                author_info["names"].append(text[:100])

    # Look for bio sections
    bio_patterns = [
        {"class": re.compile(r"bio|about-author|author-bio|author-description", re.I)},
        {"id": re.compile(r"bio|author-bio|about-author", re.I)},
    ]

    for pattern in bio_patterns:
        for tag in soup.find_all(True, pattern):
            text = tag.get_text(strip=True)
            if text and len(text) > 10:
                author_info["bios"].append(text[:500])

    # Look for author images
    for img in soup.find_all("img", class_=re.compile(r"author|avatar|profile", re.I)):
        src = img.get("src", "")
        if src:
            author_info["image_urls"].append(src)

    return author_info
