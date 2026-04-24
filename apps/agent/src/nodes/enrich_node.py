"""Node 3: enrich

Pulls firmographics (employee count, revenue, industry, stack, funding) via Apollo.
"""
from __future__ import annotations

import logging

from ..enrichment import enrich_domain
from ..schemas import AgentState

log = logging.getLogger(__name__)


def enrich_node(state: AgentState) -> AgentState:
    try:
        state.firmographics = enrich_domain(state.account.domain)
        log.info("enrich: %s -> %s employees, industry=%s",
                 state.account.domain,
                 state.firmographics.employee_count,
                 state.firmographics.industry)
    except Exception as e:
        state.errors.append(f"enrich: {e}")
        log.exception("enrich failed")
    return state
