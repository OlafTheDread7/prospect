"""Node 6: score

Deterministic, no LLM. Computes a 0-10 priority score as:

    score = round(10 * (0.45 * icp_fit + 0.35 * timing + 0.20 * accessibility))

- icp_fit: how well firmographics match the ICP size_range/industry/geo
- timing:   weighted sum of signal weights, clipped to 0..1
- accessibility: soft bonus for having identified a likely buyer

Returns a ScoredBrief with a score_breakdown dict so we can explain it.
"""
from __future__ import annotations

import logging

from ..schemas import AgentState, ScoredBrief

log = logging.getLogger(__name__)


def score_node(state: AgentState) -> AgentState:
    if not state.brief_draft:
        state.errors.append("score: missing brief_draft")
        return state

    icp_fit = _icp_fit(state)
    timing = _timing(state)
    accessibility = _accessibility(state)

    raw = 0.45 * icp_fit + 0.35 * timing + 0.20 * accessibility
    score = max(0, min(10, round(10 * raw)))

    state.scored_brief = ScoredBrief(
        **state.brief_draft.model_dump(),
        score=score,
        score_breakdown={
            "icp_fit": round(icp_fit, 3),
            "timing": round(timing, 3),
            "accessibility": round(accessibility, 3),
            "formula": "0.45*icp_fit + 0.35*timing + 0.20*accessibility",
        },
    )
    log.info("score=%d (icp=%.2f timing=%.2f access=%.2f)", score, icp_fit, timing, accessibility)
    return state


def _icp_fit(state: AgentState) -> float:
    firmo = state.firmographics
    icp = state.icp
    if not firmo:
        return 0.3  # unknown -> neutral-low

    fit = 0.5
    # size range e.g. "20-200"
    if icp.size_range and firmo.employee_count and "-" in icp.size_range:
        try:
            lo, hi = (int(x) for x in icp.size_range.split("-", 1))
            ec = firmo.employee_count
            if lo <= ec <= hi:
                fit += 0.3
            elif ec < lo * 0.5 or ec > hi * 2:
                fit -= 0.3
        except ValueError:
            pass
    if icp.industry and firmo.industry and icp.industry.lower() in firmo.industry.lower():
        fit += 0.2
    return max(0.0, min(1.0, fit))


def _timing(state: AgentState) -> float:
    if not state.signals:
        return 0.2
    total = sum(s.weight for s in state.signals)
    # normalize: 3 signals at ~0.7 ≈ 1.0
    return max(0.0, min(1.0, total / 2.5))


def _accessibility(state: AgentState) -> float:
    if not state.brief_draft:
        return 0.5
    # If the LLM named at least one buyer with a role, we call it accessible.
    if state.brief_draft.buyers and any(b.role for b in state.brief_draft.buyers):
        return 0.8
    return 0.4
