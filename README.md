# PROSPECT

A self-hosted B2B account intelligence agent. Upload a list of target companies, get one-page sales briefs with personalized opening lines — all powered by open-weights LLMs (Qwen 2.5 32B, Llama 3.3 70B) running on infrastructure you control.

No OpenAI. No Anthropic. No third-party LLM in the critical path.

## What's in this repo

```
.
├── docs/                     # Business plan, investor one-pager, tech spec, execution checklist, pilot call script
├── apps/
│   ├── agent/                # Python worker: the 7-node agent graph
│   └── web/                  # Next.js frontend: upload + briefs dashboard
├── infra/
│   └── supabase/
│       └── schema.sql        # Postgres schema (accounts, briefs, jobs, feedback, icps)
├── .env.example              # Copy to .env and fill in
└── README.md
```

## The agent in one picture

```
User uploads CSV → Next.js writes `accounts` + `jobs` rows in Supabase
                                          │
                                          ▼
                         Python worker polls `jobs` (status=pending)
                                          │
      ┌───────────────────────────────────┼───────────────────────────────────┐
      ▼                                   ▼                                   ▼
   ingest  →  crawl  →  enrich  →  signal_scan  →  synthesize  →  score  →  draft
                                                        │                      │
                                                        ▼                      ▼
                                                vLLM HTTP endpoint      (writes `briefs` row)
                                                (Qwen 2.5 / Llama 3.3
                                                 on RunPod Serverless)
```

## Quick start

### 1. Supabase
1. Create a new Supabase project at https://supabase.com.
2. Open the SQL editor and paste `infra/supabase/schema.sql`. Run it.
3. Grab the project URL and anon + service-role keys from Settings → API.

### 2. Environment
```bash
cp .env.example .env
# Edit .env with your Supabase keys + (optional) RunPod + Firecrawl + Brave keys
```

Everything except Supabase is **optional** for local development — the agent has mock providers that let you run it end-to-end without any API keys.

### 3. Run the agent (mock mode — zero API keys needed)
```bash
cd apps/agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.smoke_test
```

This runs the full agent graph on a fake account with mock LLM + mock search. Output: a complete brief printed to stdout. Use this to verify the graph before you plug in real APIs.

### 4. Run the worker against Supabase
```bash
cd apps/agent
python -m src.worker
```
The worker polls the `jobs` table every 5 seconds. Upload accounts via the frontend (or insert rows by hand) and watch briefs appear in the `briefs` table.

### 5. Run the frontend
```bash
cd apps/web
npm install
npm run dev
```
Open http://localhost:3000. Sign up with any email (magic-link auth via Supabase).

## The deployment model (when you're ready to charge)

| Component      | Where it runs                              | Cost at 10 customers |
| -------------- | ------------------------------------------ | -------------------- |
| Web frontend   | Vercel                                     | $0–$20/mo            |
| Agent worker   | Fly.io (tiny VM)                           | $10/mo               |
| LLM inference  | RunPod Serverless (Qwen 32B + Llama 70B)   | ~$400/mo             |
| Postgres + Auth| Supabase Pro                               | $25/mo               |
| Crawl + Search | Firecrawl + Brave                          | ~$60/mo              |
| Enrichment     | Apollo low tier                            | ~$99/mo              |
| **Total**      |                                            | **~$614/mo**         |

Revenue at 10 Pro-plan customers: $4,990/mo. **Gross margin: 87%.** See `docs/technical_spec.docx` for the full breakdown.

## Before you ship to paying customers

- [ ] Replace `apps/agent/src/llm.py`'s mock client with the real RunPod vLLM endpoint
- [ ] Set `FIRECRAWL_API_KEY` and `BRAVE_API_KEY` — remove mock retrieval
- [ ] Set `APOLLO_API_KEY` — remove mock enrichment
- [ ] Enable Supabase Row-Level Security using the policies in `schema.sql`
- [ ] Wire Stripe checkout in `apps/web` (stubbed route exists at `/api/billing/checkout`)
- [ ] Run the smoke test on 50 real accounts and human-review every brief before the customer sees it

## The docs

- `docs/PROSPECT_business_plan.docx` — the full plan (market, GTM, 12-month financials, risks)
- `docs/investor_one_pager.docx` — the one-pager for angel/advisor conversations
- `docs/technical_spec.docx` — architecture, data model, model serving, eval plan
- `docs/execution_checklist.docx` — 12 weeks, one page each, build/sell/kill per week
- `docs/pilot_call_script.docx` — exact script for the first 3 pilot calls

## License

Proprietary. All rights reserved.
