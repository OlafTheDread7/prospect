"""LLM client.

Production: an OpenAI-compatible HTTP endpoint (vLLM on RunPod Serverless).
Mock: an in-process implementation that produces plausible structured output
so the graph can run end-to-end without any external API.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import config

log = logging.getLogger(__name__)


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def chat_json(self, system: str, user: str, schema: type[BaseModel]) -> BaseModel:
        """Structured output. Returns an instance of `schema`.

        Works across vLLM (guided_json), Together, OpenRouter, and OpenAI.
        Strategy:
          1. Tell the model in the system prompt what JSON it must produce.
          2. Use response_format=json_object for generic JSON mode.
          3. Also pass guided_json — vLLM enforces the schema; other backends ignore it.
          4. Parse, validate with Pydantic, retry on failure (tenacity).
        """
        json_schema = schema.model_json_schema()
        system_with_schema = (
            f"{system}\n\n"
            f"You MUST respond with a single JSON object matching this schema:\n"
            f"{json.dumps(json_schema)}\n"
            f"Return ONLY the JSON object, no markdown, no prose."
        )

        payload: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_with_schema},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": 2048,
            "response_format": {"type": "json_object"},
            # vLLM-specific hard schema enforcement; non-vLLM backends ignore this.
            "guided_json": json_schema,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        with httpx.Client(timeout=180.0) as client:
            r = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
        if r.status_code != 200:
            raise LLMError(f"LLM HTTP {r.status_code}: {r.text[:500]}")
        body = r.json()
        content = body["choices"][0]["message"]["content"]
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise LLMError(f"LLM returned non-JSON: {content[:500]}") from e
        return schema.model_validate(data)


# ---------------------------------------------------------------------------
# Mock LLM — produces a deterministic, plausible brief for any input
# ---------------------------------------------------------------------------
class MockLLMClient:
    """Deterministic mock that returns a well-formed object for any schema.

    The point is to let the whole pipeline run without API keys, not to
    produce high-quality synthesis. Swap for LLMClient in production.
    """

    def __init__(self, model: str = "mock-v0") -> None:
        self.model = model

    def chat_json(self, system: str, user: str, schema: type[BaseModel]) -> BaseModel:
        log.info("mock LLM call for schema=%s", schema.__name__)
        # Inspect the context we were given so the mock output references it.
        account_name, pain_hint = _extract_context(user)

        if schema.__name__ == "BriefDraft":
            from .schemas import BriefDraft, Buyer, Signal
            return BriefDraft(
                summary=(
                    f"{account_name} is a mid-market company showing multiple outbound-worthy "
                    f"signals in the last 30 days. A confluence of hiring, tooling migration, "
                    f"and public executive commentary points to an active buying window."
                ),
                pain=(
                    f"Likely operational pain: {pain_hint or 'scaling go-to-market execution'} "
                    f"against a backdrop of recent organizational change. The timing suggests "
                    f"a 60-120 day window where budget and political will are both present."
                ),
                buyers=[
                    Buyer(name="J. Rivera", role="VP Operations",
                          note="Recent public comments on operational scaling pain."),
                    Buyer(name="M. Chen", role="Head of Revenue",
                          note="Likely economic buyer given the current hiring pattern."),
                ],
                top_signals=[
                    Signal(kind="hiring", text="6 ops roles posted in the last 14 days", weight=0.8),
                    Signal(kind="exec_hire", text="New VP of Engineering joined 30 days ago", weight=0.7),
                    Signal(kind="news", text="Announced Q1 cloud migration in press release", weight=0.6),
                ],
            )

        if schema.__name__ == "Opener":
            return schema.model_validate({
                "opener": (
                    f"Saw the recent moves at {account_name} - the hiring pace across ops "
                    f"and the cloud migration announcement usually line up with a rough "
                    f"3-6 week window where exception volume spikes. Worth 15 minutes next week?"
                ),
            })

        # Generic fallback — build an instance with all-default values.
        try:
            return schema()
        except Exception as e:  # pragma: no cover
            raise LLMError(f"MockLLMClient could not construct {schema.__name__}: {e}") from e


def _extract_context(user_prompt: str) -> tuple[str, str]:
    """Pull the company name and any pain hint out of the user prompt."""
    name = "the target company"
    pain = ""
    for line in user_prompt.splitlines():
        low = line.lower().strip()
        if low.startswith("company:"):
            name = line.split(":", 1)[1].strip() or name
        elif low.startswith("icp pain:"):
            pain = line.split(":", 1)[1].strip()
    return name, pain


def get_llm(escalation: bool = False) -> LLMClient | MockLLMClient:
    """Return the configured LLM client (real or mock)."""
    if config.mock_llm:
        return MockLLMClient(model="mock-llama-escalation" if escalation else "mock-qwen-primary")
    if not config.llm_base_url or not config.llm_api_key:
        raise LLMError("LLM_BASE_URL and LLM_API_KEY must be set when MOCK_LLM=false")
    model = config.llm_model_escalation if escalation else config.llm_model_primary
    return LLMClient(config.llm_base_url, config.llm_api_key, model)
