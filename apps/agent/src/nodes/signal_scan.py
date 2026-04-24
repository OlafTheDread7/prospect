"""Node 4: signal_scan

Scans public sources for timing / pain signals:
- news about the company
- hiring patterns (careers page parsed in crawl)
- executive posts (public LinkedIn — user-provided export only)
- product / funding events

Produces a list of Signal entries, each with a weight 0..1.
"""
from __future__ import annotations

import logging
import re

from ..retrieval import search_news
from ..schemas import AgentState, Signal

log = logging.getLogger(__name__)

_ROLE_PATTERNS = [
    (re.compile(r"\b(vp|vice president)\b", re.I), "exec_hire", 0.75),
    (re.compile(r"\b(head of|director)\b", re.I), "exec_hire", 0.6),
    (re.compile(r"\b(engineer|developer|architect|sre)\b", re.I), "hiring", 0.55),
    (re.compile(r"\b(operations|ops|logistics)\b", re.I), "hiring", 0.55),
    (re.compile(r"\b(sales|customer success|cs manager)\b", re.I), "hiring", 0.5),
]

_NEWS_KEYWORDS = [
    (re.compile(r"\b(cloud|saas) migration\b", re.I), "tech_migration", 0.7),
    (re.compile(r"\b(raises|funding|series [a-e])\b", re.I), "funding", 0.75),
    (re.compile(r"\b(launches|announces|unveils)\b", re.I), "product_launch", 0.55),
    (re.compile(r"\b(layoffs|layoff|cut \d+% of)\b", re.I), "layoff", 0.4),
    (re.compile(r"\b(expands|opens office|acquires)\b", re.I), "expansion", 0.55),
    (re.compile(r"\b(joins|appoints|hires) .{0,30}(cto|ceo|vp)\b", re.I), "exec_hire", 0.7),
]


def signal_scan_node(state: AgentState) -> AgentState:
    signals: list[Signal] = []

    # --- Hiring signals from the /careers page (already crawled) ---
    careers = next((p for p in state.pages if p.url.endswith("/careers")), None)
    if careers and careers.text:
        role_counts: dict[str, int] = {}
        for line in careers.text.splitlines():
            for pat, kind, weight in _ROLE_PATTERNS:
                if pat.search(line):
                    key = f"{kind}:{pat.pattern}"
                    role_counts[key] = role_counts.get(key, 0) + 1
        for key, count in role_counts.items():
            kind = key.split(":", 1)[0]
            signals.append(Signal(
                kind=kind,
                text=f"{count} matching role(s) posted on careers page",
                url=careers.url,
                weight=min(0.4 + 0.1 * count, 0.9),
            ))

    # --- News signals ---
    query = f"{state.account.company_name or state.account.domain}"
    try:
        results = search_news(query, limit=5)
    except Exception as e:
        state.errors.append(f"signal_scan search: {e}")
        results = []

    for r in results:
        blob = f"{r.get('title','')} {r.get('snippet','')}"
        matched = False
        for pat, kind, weight in _NEWS_KEYWORDS:
            if pat.search(blob):
                signals.append(Signal(
                    kind=kind,
                    text=r.get("title", "")[:200],
                    url=r.get("url"),
                    weight=weight,
                ))
                matched = True
                break
        if not matched:
            signals.append(Signal(
                kind="news",
                text=r.get("title", "")[:200],
                url=r.get("url"),
                weight=0.3,
            ))

    # Dedup + cap
    seen = set()
    deduped: list[Signal] = []
    for s in sorted(signals, key=lambda s: -s.weight):
        key = (s.kind, s.text[:80])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(s)
        if len(deduped) >= 8:
            break

    state.signals = deduped
    log.info("signal_scan produced %d signals", len(deduped))
    return state
