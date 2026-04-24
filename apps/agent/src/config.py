"""Centralized configuration. Reads from environment.

Every external integration has a MOCK_* flag that lets the agent
run end-to-end with zero API keys. Flip the flags to false when you
plug in the real services.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file).
_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_ROOT / ".env")


def _bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Config:
    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # LLM (vLLM OpenAI-compatible endpoint)
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model_primary: str = os.getenv("LLM_MODEL_PRIMARY", "qwen2.5-32b-instruct")
    llm_model_escalation: str = os.getenv("LLM_MODEL_ESCALATION", "llama-3.3-70b-instruct")

    # Retrieval
    firecrawl_api_key: str = os.getenv("FIRECRAWL_API_KEY", "")
    brave_api_key: str = os.getenv("BRAVE_API_KEY", "")
    apollo_api_key: str = os.getenv("APOLLO_API_KEY", "")

    # Feature flags
    mock_llm: bool = _bool("MOCK_LLM", True)
    mock_crawl: bool = _bool("MOCK_CRAWL", True)
    mock_enrich: bool = _bool("MOCK_ENRICH", True)
    mock_search: bool = _bool("MOCK_SEARCH", True)

    # Worker
    worker_poll_interval: int = int(os.getenv("WORKER_POLL_INTERVAL", "5"))


config = Config()
