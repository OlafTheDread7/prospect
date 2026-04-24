"""Supabase client for the worker.

Uses the service-role key — this bypasses RLS. Never expose this key to
the browser.
"""
from __future__ import annotations

import logging
from typing import Any

from .config import config

log = logging.getLogger(__name__)


def get_client():  # -> supabase.Client
    """Return a configured Supabase client (lazy import so local dev doesn't need it)."""
    if not config.supabase_url or not config.supabase_service_role_key:
        raise RuntimeError(
            "Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
            "in .env, or run the smoke test (no DB required)."
        )
    from supabase import create_client  # type: ignore
    return create_client(config.supabase_url, config.supabase_service_role_key)


def claim_next_job(client) -> dict[str, Any] | None:
    """Claim the oldest pending job with a simple optimistic update.

    Returns the claimed job row, or None if the queue is empty.
    """
    res = client.table("jobs").select("*").eq("status", "pending").order("created_at").limit(1).execute()
    rows = res.data or []
    if not rows:
        return None
    job = rows[0]
    upd = (
        client.table("jobs")
        .update({"status": "running", "started_at": "now()", "attempts": job["attempts"] + 1})
        .eq("id", job["id"])
        .eq("status", "pending")
        .execute()
    )
    if not upd.data:
        return None  # someone else claimed it
    return upd.data[0]


def fetch_account(client, account_id: str) -> dict[str, Any] | None:
    res = client.table("accounts").select("*").eq("id", account_id).limit(1).execute()
    rows = res.data or []
    return rows[0] if rows else None


def fetch_icp(client, icp_id: str | None) -> dict[str, Any] | None:
    if not icp_id:
        return None
    res = client.table("icps").select("*").eq("id", icp_id).limit(1).execute()
    rows = res.data or []
    return rows[0] if rows else None


def write_brief(client, user_id: str, job_id: str, account_id: str, final_brief: dict) -> None:
    payload = {
        "user_id": user_id,
        "job_id": job_id,
        "account_id": account_id,
        "score": final_brief.get("score"),
        "summary": final_brief.get("summary"),
        "signals": final_brief.get("top_signals", []),
        "pain": final_brief.get("pain"),
        "buyers": final_brief.get("buyers", []),
        "opener": final_brief.get("opener"),
        "evidence": final_brief.get("score_breakdown", {}),
        "model_version": final_brief.get("model_version"),
    }
    client.table("briefs").insert(payload).execute()


def complete_job(client, job_id: str, error: str | None = None) -> None:
    client.table("jobs").update({
        "status": "failed" if error else "completed",
        "error": error,
        "completed_at": "now()",
    }).eq("id", job_id).execute()
