"""Node 2: crawl

Fetches a small, fixed set of key pages (home, about, pricing, careers, blog).
Writes results into state.pages.
"""
from __future__ import annotations

import logging

from ..retrieval import crawl_site
from ..schemas import AgentState

log = logging.getLogger(__name__)


def crawl_node(state: AgentState) -> AgentState:
    domain = state.account.domain
    if not domain:
        state.errors.append("crawl: no domain")
        return state
    try:
        state.pages = crawl_site(domain)
        log.info("crawl fetched %d pages for %s", len(state.pages), domain)
    except Exception as e:
        state.errors.append(f"crawl: {e}")
        log.exception("crawl failed for %s", domain)
    return state
