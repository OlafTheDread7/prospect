"""The agent graph orchestrator.

Keeps things simple: a linear DAG. If/when we need conditional edges
(e.g. escalation to Llama 70B), promote to LangGraph without changing
the node signatures.
"""
from __future__ import annotations

import logging
import time

from .nodes import (
    crawl_node,
    draft_node,
    enrich_node,
    ingest_node,
    score_node,
    signal_scan_node,
    synthesize_node,
)
from .schemas import AgentState

log = logging.getLogger(__name__)

NODE_ORDER = [
    ("ingest", ingest_node),
    ("crawl", crawl_node),
    ("enrich", enrich_node),
    ("signal_scan", signal_scan_node),
    ("synthesize", synthesize_node),
    ("score", score_node),
    ("draft", draft_node),
]


def run_graph(state: AgentState) -> AgentState:
    """Run all 7 nodes in sequence. Errors are captured on state.errors."""
    for name, fn in NODE_ORDER:
        t0 = time.perf_counter()
        try:
            state = fn(state)
        except Exception as e:
            state.errors.append(f"{name}: {e}")
            log.exception("node %s crashed", name)
        dt = (time.perf_counter() - t0) * 1000
        log.info("node %s completed in %.0fms (errors=%d)", name, dt, len(state.errors))
    return state
