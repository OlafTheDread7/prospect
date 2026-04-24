"""Node 7: draft

Second LLM call. Produces the personalized opening line — the line that
actually gets pasted into the customer's sequencer. This is where the
LoRA fine-tune will live in the future: trained on customer-labeled
openers that drove replies.
"""
from __future__ import annotations

import logging

from pydantic import BaseModel

from ..llm import get_llm
from ..schemas import AgentState, FinalBrief

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You write B2B outbound opening lines.

Rules (non-negotiable):
- 2-3 sentences, under 55 words total.
- Reference ONE concrete signal from the brief, by name.
- End with a soft, specific call to action ('worth 15 minutes next week?').
- No flattery. No 'I hope this finds you well'. No buzzwords.
- Second person. Present tense. Plain English.

Output the JSON { "opener": "..." } only."""


class Opener(BaseModel):
    opener: str


def draft_node(state: AgentState) -> AgentState:
    scored = state.scored_brief
    if not scored:
        state.errors.append("draft: missing scored_brief")
        return state

    signals_str = "\n".join(f"- [{s.kind}] {s.text}" for s in scored.top_signals)
    buyer = scored.buyers[0] if scored.buyers else None
    buyer_str = f"{buyer.name} ({buyer.role})" if buyer else "the likely buyer"

    user_prompt = (
        f"Company: {state.account.company_name or state.account.domain}\n"
        f"Likely buyer: {buyer_str}\n"
        f"Pain hypothesis: {scored.pain}\n"
        f"Top signals:\n{signals_str}\n\n"
        "Write the opener."
    )

    llm = get_llm(escalation=False)
    try:
        o = llm.chat_json(SYSTEM_PROMPT, user_prompt, Opener)  # type: ignore[arg-type]
        opener_text = o.opener  # type: ignore[attr-defined]
    except Exception as e:
        state.errors.append(f"draft: {e}")
        log.exception("draft failed")
        opener_text = _fallback_opener(scored, buyer)

    state.final_brief = FinalBrief(
        **scored.model_dump(),
        opener=opener_text,
        model_version=state.model_version or llm.model,
    )
    log.info("draft complete, opener=%r", opener_text[:80])
    return state


def _fallback_opener(scored, buyer) -> str:
    sig = scored.top_signals[0].text if scored.top_signals else "the recent public changes"
    name = buyer.name.split()[0] if buyer and buyer.name else "there"
    return (
        f"{name} — noticed {sig.lower()} at your side recently. "
        f"Most teams hit a visibility gap in weeks 3-6 after that kind of move; "
        f"we help peers stay ahead of it. Worth 15 minutes next week?"
    )
