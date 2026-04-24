"""Smoke test — runs the whole agent graph on a mock account.

Zero API keys required. Use this to verify the code runs before you
plug in real Supabase / RunPod / Firecrawl / Apollo credentials.

    python -m src.smoke_test
"""
from __future__ import annotations

import json
import logging
import sys

from .graph import run_graph
from .schemas import AgentState, CanonicalAccount, ICP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stderr,
)


def main() -> int:
    state = AgentState(
        account=CanonicalAccount(
            domain="northwindlogistics.com",
            company_name="Northwind Logistics",
            raw_input={"source": "smoke_test"},
        ),
        icp=ICP(
            name="Mid-market logistics",
            industry="Logistics",
            size_range="100-500",
            geo="North America",
            pain="visibility gaps during TMS migrations",
            timing_cues="cloud migration announced, VP Logistics Tech hired",
        ),
    )

    state = run_graph(state)

    print("\n" + "=" * 70)
    print("PROSPECT smoke test")
    print("=" * 70)
    if state.errors:
        print("\nErrors:")
        for e in state.errors:
            print(" -", e)

    fb = state.final_brief
    if not fb:
        print("\nNo final brief produced. Check logs above.")
        return 1

    print(f"\nAccount: {state.account.company_name} ({state.account.domain})")
    print(f"Score:   {fb.score}/10  (breakdown: {fb.score_breakdown})")
    print(f"\nSummary:\n  {fb.summary}")
    print(f"\nPain:\n  {fb.pain}")
    print("\nBuyers:")
    for b in fb.buyers:
        print(f"  - {b.name} ({b.role}){' — ' + b.note if b.note else ''}")
    print("\nTop signals:")
    for s in fb.top_signals:
        print(f"  - [{s.kind}] {s.text} (weight {s.weight:.2f})")
    print(f"\nOpener:\n  {fb.opener}")
    print(f"\nModel version: {fb.model_version}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
