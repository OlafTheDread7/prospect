"""The worker loop.

Polls the `jobs` table for pending rows, claims one, runs the agent graph,
writes the brief, marks the job complete.

Run:
    python -m src.worker
"""
from __future__ import annotations

import logging
import signal
import time

from .config import config
from .db import (
    claim_next_job,
    complete_job,
    fetch_account,
    fetch_icp,
    get_client,
    write_brief,
)
from .graph import run_graph
from .schemas import AgentState, CanonicalAccount, ICP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("prospect.worker")

_running = True


def _stop(*_):
    global _running
    _running = False
    log.info("shutting down after current job")


signal.signal(signal.SIGINT, _stop)
signal.signal(signal.SIGTERM, _stop)


def process_one(client) -> bool:
    """Process exactly one job. Returns True if work was done."""
    job = claim_next_job(client)
    if not job:
        return False

    log.info("claimed job %s (attempt %d)", job["id"], job["attempts"])
    try:
        account = fetch_account(client, job["account_id"])
        if not account:
            complete_job(client, job["id"], error="account not found")
            return True

        icp_row = fetch_icp(client, account.get("icp_id"))
        icp = ICP(
            name=(icp_row or {}).get("name", "default"),
            industry=(icp_row or {}).get("industry"),
            size_range=(icp_row or {}).get("size_range"),
            geo=(icp_row or {}).get("geo"),
            pain=(icp_row or {}).get("pain"),
            timing_cues=(icp_row or {}).get("timing_cues"),
        )

        state = AgentState(
            account=CanonicalAccount(
                domain=account.get("domain", ""),
                company_name=account.get("company_name"),
                raw_input=account.get("raw_input") or {},
            ),
            icp=icp,
        )
        state = run_graph(state)

        if state.final_brief:
            write_brief(
                client,
                user_id=job["user_id"],
                job_id=job["id"],
                account_id=job["account_id"],
                final_brief=state.final_brief.model_dump(),
            )
            complete_job(client, job["id"])
            log.info("job %s completed, score=%d", job["id"], state.final_brief.score)
        else:
            err = "; ".join(state.errors) or "no brief produced"
            complete_job(client, job["id"], error=err)
            log.warning("job %s failed: %s", job["id"], err)
    except Exception as e:
        log.exception("job %s crashed", job["id"])
        complete_job(client, job["id"], error=str(e)[:500])
    return True


def main() -> None:
    client = get_client()
    log.info("worker started, polling every %ds", config.worker_poll_interval)
    while _running:
        try:
            did_work = process_one(client)
        except Exception:
            log.exception("worker loop error")
            did_work = False
        if not did_work:
            time.sleep(config.worker_poll_interval)
    log.info("worker stopped")


if __name__ == "__main__":
    main()
