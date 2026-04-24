"""Node 5: synthesize

The LLM reads:
  - scraped pages
  - firmographics
  - signals
  - the customer's ICP
and produces a BriefDraft (summary, pain, buyers, top_signals).

This is the single highest-leverage node in the graph — the prompt and
the structured-output schema are the product. Tune carefully.
"""
from __future__ import annotations

import json
import logging

from ..llm import get_llm
from ..schemas import AgentState, BriefDraft

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an elite B2B sales researcher.

You produce compact, specific, evidence-backed account briefs. You NEVER
invent facts. When in doubt, hedge. Every claim in your brief must be
traceable to a signal, a firmographic field, or a crawled page. If the
evidence is too thin for a confident claim, say so plainly.

Output strictly in the provided JSON schema. Do not include markdown."""


def synthesize_node(state: AgentState) -> AgentState:
    user_prompt = _build_user_prompt(state)
    llm = get_llm(escalation=False)
    try:
        draft = llm.chat_json(SYSTEM_PROMPT, user_prompt, BriefDraft)
        state.brief_draft = draft  # type: ignore[assignment]
        state.model_version = llm.model
        log.info("synthesize produced draft with %d buyers, %d signals",
                 len(draft.buyers), len(draft.top_signals))
    except Exception as e:
        state.errors.append(f"synthesize: {e}")
        log.exception("synthesize failed")
    return state


def _build_user_prompt(state: AgentState) -> str:
    pages_blob = "\n\n".join(
        f"URL: {p.url}\nTITLE: {p.title or ''}\nTEXT:\n{p.text[:2000]}"
        for p in state.pages
    )
    firmo = state.firmographics.model_dump() if state.firmographics else {}
    signals = [s.model_dump() for s in state.signals]
    icp = state.icp.model_dump()

    return (
        f"Company: {state.account.company_name or state.account.domain}\n"
        f"Domain: {state.account.domain}\n"
        f"ICP industry: {icp.get('industry') or ''}\n"
        f"ICP size range: {icp.get('size_range') or ''}\n"
        f"ICP pain: {icp.get('pain') or ''}\n"
        f"ICP timing cues: {icp.get('timing_cues') or ''}\n\n"
        f"FIRMOGRAPHICS:\n{json.dumps(firmo, default=str)}\n\n"
        f"SIGNALS:\n{json.dumps(signals, default=str)}\n\n"
        f"PAGES:\n{pages_blob}\n\n"
        "Task: produce a BriefDraft. The summary is 2-3 sentences. "
        "The pain is 2 sentences grounded in the ICP pain + observed signals. "
        "Buyers: the 1-2 most likely economic buyers, with role. "
        "top_signals: up to 3 signals from the input list, chosen for outbound relevance."
    )
