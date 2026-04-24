"""Pydantic schemas for the agent state.

Every node in the graph takes an AgentState and returns an AgentState.
State is JSON-serializable so any run can be checkpointed and resumed.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


SignalKind = Literal[
    "hiring",
    "funding",
    "news",
    "product_launch",
    "exec_hire",
    "tech_migration",
    "github",
    "exec_post",
    "partnership",
    "layoff",
    "expansion",
    "other",
]


class ICP(BaseModel):
    """The customer's Ideal Customer Profile."""
    name: str
    industry: Optional[str] = None
    size_range: Optional[str] = None
    geo: Optional[str] = None
    pain: Optional[str] = None
    timing_cues: Optional[str] = None


class CanonicalAccount(BaseModel):
    """Normalized target company."""
    domain: str
    company_name: Optional[str] = None
    raw_input: dict = Field(default_factory=dict)


class PageBundle(BaseModel):
    """One scraped page."""
    url: str
    title: Optional[str] = None
    text: str = ""


class Firmographics(BaseModel):
    """Company attributes from enrichment."""
    employee_count: Optional[int] = None
    revenue_estimate_usd: Optional[int] = None
    industry: Optional[str] = None
    hq_city: Optional[str] = None
    hq_country: Optional[str] = None
    tech_stack: list[str] = Field(default_factory=list)
    funding_stage: Optional[str] = None
    last_funding_amount_usd: Optional[int] = None
    last_funding_date: Optional[str] = None


class Signal(BaseModel):
    """A single timing/pain signal about an account."""
    kind: SignalKind
    text: str
    url: Optional[str] = None
    weight: float = Field(default=0.5, ge=0.0, le=1.0)
    observed_at: Optional[str] = None


class Buyer(BaseModel):
    """A likely buyer at the account."""
    name: str
    role: str
    quote_url: Optional[str] = None
    note: Optional[str] = None


class BriefDraft(BaseModel):
    """The LLM's first pass — pre-scoring, pre-opener."""
    summary: str
    pain: str
    buyers: list[Buyer] = Field(default_factory=list)
    top_signals: list[Signal] = Field(default_factory=list)


class ScoredBrief(BriefDraft):
    """BriefDraft plus a deterministic priority score."""
    score: int = Field(ge=0, le=10)
    score_breakdown: dict = Field(default_factory=dict)


class FinalBrief(ScoredBrief):
    """The full deliverable — what the customer sees."""
    opener: str
    model_version: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentState(BaseModel):
    """Passed between nodes. Mutated in-place by each node."""
    account: CanonicalAccount
    icp: ICP
    pages: list[PageBundle] = Field(default_factory=list)
    firmographics: Optional[Firmographics] = None
    signals: list[Signal] = Field(default_factory=list)
    brief_draft: Optional[BriefDraft] = None
    scored_brief: Optional[ScoredBrief] = None
    final_brief: Optional[FinalBrief] = None
    errors: list[str] = Field(default_factory=list)
    model_version: str = "qwen2.5-32b-v0"
