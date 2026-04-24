"""Firmographic enrichment (Apollo real / mock fallback)."""
from __future__ import annotations

import logging

import httpx

from .config import config
from .schemas import Firmographics

log = logging.getLogger(__name__)


def enrich_domain(domain: str) -> Firmographics:
    if config.mock_enrich:
        return _mock_firmographics(domain)
    return _apollo_enrich(domain)


def _apollo_enrich(domain: str) -> Firmographics:
    if not config.apollo_api_key:
        raise RuntimeError("APOLLO_API_KEY required when MOCK_ENRICH=false")
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": config.apollo_api_key,
    }
    params = {"domain": domain}
    with httpx.Client(timeout=20.0) as client:
        r = client.get(
            "https://api.apollo.io/api/v1/organizations/enrich", headers=headers, params=params
        )
    if r.status_code != 200:
        log.warning("apollo enrich failed %s: %s", r.status_code, r.text[:200])
        return Firmographics()
    org = r.json().get("organization", {}) or {}
    return Firmographics(
        employee_count=org.get("estimated_num_employees"),
        revenue_estimate_usd=org.get("estimated_annual_revenue"),
        industry=org.get("industry"),
        hq_city=org.get("city"),
        hq_country=org.get("country"),
        tech_stack=[t.get("name") for t in (org.get("current_technologies") or []) if t.get("name")],
        funding_stage=org.get("latest_funding_stage"),
        last_funding_amount_usd=org.get("latest_funding_round_amount"),
        last_funding_date=org.get("latest_funding_round_date"),
    )


def _mock_firmographics(domain: str) -> Firmographics:
    return Firmographics(
        employee_count=340,
        revenue_estimate_usd=82_000_000,
        industry="Logistics & Supply Chain",
        hq_city="Chicago",
        hq_country="United States",
        tech_stack=["Salesforce", "Snowflake", "HubSpot", "Segment"],
        funding_stage="Series C",
        last_funding_amount_usd=45_000_000,
        last_funding_date="2024-11-15",
    )
