"""Node 1: ingest

Input: raw account (domain/URL/name in any shape).
Output: CanonicalAccount with a normalized root domain.
"""
from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

import tldextract

from ..schemas import AgentState, CanonicalAccount

log = logging.getLogger(__name__)


def ingest_node(state: AgentState) -> AgentState:
    raw = state.account.raw_input or {}
    candidate = (
        state.account.domain
        or raw.get("domain")
        or raw.get("url")
        or raw.get("website")
        or ""
    )
    domain = _normalize_domain(candidate)
    if not domain:
        state.errors.append("ingest: could not derive a domain from input")
        return state

    name = state.account.company_name or raw.get("name") or _domain_to_name(domain)
    state.account = CanonicalAccount(domain=domain, company_name=name, raw_input=raw)
    log.info("ingest normalized domain=%s name=%s", domain, name)
    return state


def _normalize_domain(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    if "://" not in s:
        s = "https://" + s
    try:
        netloc = urlparse(s).netloc or s
    except Exception:
        netloc = s
    ext = tldextract.extract(netloc)
    if not ext.domain or not ext.suffix:
        return ""
    return f"{ext.domain}.{ext.suffix}".lower()


def _domain_to_name(domain: str) -> str:
    base = domain.split(".")[0]
    base = re.sub(r"[-_]+", " ", base)
    return base.title()
