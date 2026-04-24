# PROSPECT agent

The Python worker that runs the 7-node agent graph.

## The graph

```
ingest  →  crawl  →  enrich  →  signal_scan  →  synthesize  →  score  →  draft
```

Each node is a pure function: `AgentState → AgentState`. Definitions live in `src/nodes/`.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smoke test (no API keys)

```bash
python -m src.smoke_test
```

Runs the whole graph on a fake account using mock LLM / mock crawl / mock search / mock enrichment. Prints the final brief. Use this to sanity-check code changes before plugging in real keys.

## Production worker

```bash
python -m src.worker
```

Requires:
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- `LLM_BASE_URL`, `LLM_API_KEY` (with `MOCK_LLM=false`)
- `FIRECRAWL_API_KEY`, `BRAVE_API_KEY`, `APOLLO_API_KEY`

Polls the `jobs` table for pending rows, runs the graph, writes to `briefs`.

## Layout

```
src/
├── __init__.py
├── config.py           # env loading + MOCK_* flags
├── schemas.py          # Pydantic: AgentState, Brief, Signal, Buyer, …
├── llm.py              # OpenAI-compatible HTTP client + MockLLMClient
├── retrieval.py        # Firecrawl + Brave (mock fallbacks)
├── enrichment.py       # Apollo (mock fallback)
├── graph.py            # the orchestrator
├── nodes/
│   ├── ingest.py
│   ├── crawl.py
│   ├── enrich_node.py
│   ├── signal_scan.py
│   ├── synthesize.py
│   ├── score.py
│   └── draft.py
├── db.py               # Supabase client for the worker
├── worker.py           # polling loop
└── smoke_test.py       # run the graph end-to-end without API keys
```

## Swapping the LLM

Everything LLM-related flows through `get_llm()` in `src/llm.py`. To change models or providers:

1. Point `LLM_BASE_URL` at an OpenAI-compatible endpoint (vLLM, Together, OpenRouter).
2. Set `LLM_MODEL_PRIMARY` / `LLM_MODEL_ESCALATION`.
3. Flip `MOCK_LLM=false`.

The structured-output contract uses `response_format: json_schema`, which vLLM supports via `guided_json` and Together supports natively.
