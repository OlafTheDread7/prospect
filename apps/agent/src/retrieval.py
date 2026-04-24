"""Web retrieval: crawling and search.

Real: Firecrawl + Brave Search API + Playwright fallback.
Mock: deterministic fake pages and search results.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import config
from .schemas import PageBundle

log = logging.getLogger(__name__)


# ---------- Crawl ----------

def crawl_site(domain: str, paths: list[str] | None = None) -> list[PageBundle]:
    """Fetch a small set of key pages from a company website."""
    paths = paths or ["/", "/about", "/pricing", "/careers", "/blog"]
    if config.mock_crawl:
        return _mock_pages(domain, paths)
    return _firecrawl(domain, paths)


def _firecrawl(domain: str, paths: list[str]) -> list[PageBundle]:
    if not config.firecrawl_api_key:
        raise RuntimeError("FIRECRAWL_API_KEY required when MOCK_CRAWL=false")
    out: list[PageBundle] = []
    headers = {"Authorization": f"Bearer {config.firecrawl_api_key}"}
    for p in paths:
        url = f"https://{domain}{p}"
        try:
            with httpx.Client(timeout=30.0) as client:
                r = client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers=headers,
                    json={"url": url, "formats": ["markdown"]},
                )
            if r.status_code == 200:
                body = r.json().get("data", {})
                out.append(PageBundle(
                    url=url,
                    title=body.get("metadata", {}).get("title"),
                    text=body.get("markdown", "")[:8000],
                ))
        except Exception as e:  # pragma: no cover
            log.warning("firecrawl failed on %s: %s", url, e)
    return out


def _mock_pages(domain: str, paths: list[str]) -> list[PageBundle]:
    name = _titleize(domain)
    templates = {
        "/": f"{name} — the platform logistics teams use to stay ahead of exceptions.",
        "/about": f"{name} was founded in 2019. Headquartered in Chicago, 340 employees.",
        "/pricing": f"{name} offers Team, Business, and Enterprise tiers.",
        "/careers": (
            f"Open roles at {name}: VP Logistics Technology, Senior Platform Engineer, "
            "Director of Operations, Customer Success Manager (x3), Solutions Architect."
        ),
        "/blog": f"Latest from the {name} team: Announcing our Q1 cloud migration. Our CEO on the future of route optimization.",
    }
    return [
        PageBundle(url=f"https://{domain}{p}", title=f"{name}{p}", text=templates.get(p, ""))
        for p in paths
    ]


# ---------- Search ----------

def search_news(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Return a list of {title, url, snippet} for news about `query`."""
    if config.mock_search:
        return _mock_news(query, limit)
    return _brave_search(query, limit)


def _brave_search(query: str, limit: int) -> list[dict[str, Any]]:
    if not config.brave_api_key:
        raise RuntimeError("BRAVE_API_KEY required when MOCK_SEARCH=false")
    headers = {"X-Subscription-Token": config.brave_api_key, "Accept": "application/json"}
    params = {"q": query, "count": limit, "freshness": "pm"}  # past month
    with httpx.Client(timeout=20.0) as client:
        r = client.get("https://api.search.brave.com/res/v1/news/search", headers=headers, params=params)
    if r.status_code != 200:
        log.warning("brave search %s: %s", r.status_code, r.text[:200])
        return []
    items = r.json().get("results", [])
    return [
        {"title": it.get("title", ""), "url": it.get("url", ""), "snippet": it.get("description", "")}
        for it in items[:limit]
    ]


def _mock_news(query: str, limit: int) -> list[dict[str, Any]]:
    name = _titleize(query.split()[0]) if query else "Acme"
    return [
        {
            "title": f"{name} announces cloud migration from legacy systems",
            "url": f"https://news.example.com/{name.lower()}-migration",
            "snippet": f"{name} has completed Q1 migration to cloud infrastructure, citing exception-handling as primary driver.",
        },
        {
            "title": f"{name} hires new VP of Engineering",
            "url": f"https://news.example.com/{name.lower()}-vp-eng",
            "snippet": f"{name} welcomes former Acme Logistics CTO as incoming VP of Engineering, effective last month.",
        },
    ][:limit]


def _titleize(text: str) -> str:
    base = text.split(".")[0].replace("-", " ").replace("_", " ")
    return base.title() if base else "Acme"
