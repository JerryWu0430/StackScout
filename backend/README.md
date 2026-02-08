# StackScout Backend

FastAPI backend for StackScout - AI-powered dev tool recommendations.

## Quick Start

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Setup env
cp .env.example .env
# Edit .env with your keys (minimum: SUPABASE_*, OPENAI_API_KEY or LITELLM_*, GITHUB_TOKEN)

# 3. Run migrations
# Execute backend/db/migrations/*.sql in Supabase SQL Editor

# 4. Seed tools (one-time)
python scripts/seed_tools.py

# 5. Start server
uvicorn main:app --reload
```

API docs at http://localhost:8000/docs

## Core Features

| Feature | Endpoint | Description |
|---------|----------|-------------|
| Repo Analysis | `POST /api/repos/analyze` | Analyze GitHub repo, extract tech stack |
| Recommendations | `GET /api/repos/{id}/recommendations` | Get tool recommendations for repo |
| Tools | `GET /api/tools` | List all tools |
| Discovery | `POST /api/discovery/sync` | Trigger tool discovery from external sources |

## Discovery System

Auto-discovers new dev tools from:
- **Product Hunt** - daily launches (needs `PRODUCT_HUNT_TOKEN`)
- **YC Companies** - startup directory (no auth)
- **GitHub Trending** - popular repos (uses `GITHUB_TOKEN`)

### Enable Auto-Sync

```env
DISCOVERY_SYNC_ENABLED=true
DISCOVERY_SYNC_HOUR=3  # UTC hour (0-23)
```

### Manual Sync

```bash
# Dry run (fetch only, no DB writes)
curl -X POST "http://localhost:8000/api/discovery/sync?dry_run=true"

# Full sync
curl -X POST "http://localhost:8000/api/discovery/sync"

# Blocking (wait for result)
curl -X POST "http://localhost:8000/api/discovery/sync/blocking"
```

### Test Individual Sources

```bash
python scripts/test_discovery.py yc      # YC companies
python scripts/test_discovery.py gh      # GitHub trending
python scripts/test_discovery.py ph      # Product Hunt (needs token)
python scripts/test_discovery.py all     # All sources
```

## Project Structure

```
backend/
├── main.py                 # FastAPI app entry
├── routers/                # API endpoints
│   ├── repos.py            # Repo analysis
│   ├── tools.py            # Tool listing
│   └── discovery.py        # Discovery sync
├── services/
│   ├── analyzer.py         # LLM repo analysis
│   ├── recommender.py      # Vector similarity recommendations
│   ├── embeddings.py       # OpenAI embeddings
│   └── discovery/          # Tool discovery module
│       ├── product_hunt.py
│       ├── yc_companies.py
│       ├── github_trending.py
│       └── sync.py         # Orchestrator + scheduler
├── db/
│   ├── supabase.py         # DB client
│   └── migrations/         # SQL migrations
├── data/
│   └── tools_seed.json     # Initial tools data
└── scripts/
    ├── seed_tools.py       # Seed DB with tools
    └── test_discovery.py   # Test discovery sources
```

## Environment Variables

See `.env.example` for full list. Minimum required:

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon/service key |
| `OPENAI_API_KEY` | Yes* | OpenAI API key |
| `LITELLM_BASE_URL` | Yes* | LiteLLM proxy URL (alternative to OpenAI) |
| `GITHUB_TOKEN` | Yes | GitHub PAT for repo analysis |
| `PRODUCT_HUNT_TOKEN` | No | Product Hunt API token |

*Either OpenAI or LiteLLM required

## DB Migrations

Run in order in Supabase SQL Editor:

1. `001_callpilot_schema.sql` - CallPilot tables
2. `002_discovery_columns.sql` - Discovery source columns
