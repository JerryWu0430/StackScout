# StackScout

AI-powered devtool recommendation engine. Analyzes GitHub repos to identify tech gaps and recommends best-fit tools with voice-driven demo scheduling.

## Features

- **Repo Analysis** - LLM-powered fingerprinting of tech stack, gaps, risks, complexity
- **Tool Recommendations** - Hybrid vector similarity + rules scoring engine
- **Voice Agent** - ElevenLabs conversational AI for analysis narration & demo scheduling
- **Email Drafts** - LLM-generated vendor outreach with batch sending
- **CallPilot** - Phone-based demo booking via Twilio
- **Tool Discovery** - Auto-sync from Product Hunt, YC, GitHub Trending

## Tech Stack

**Frontend:** React 19, TypeScript, Vite, TanStack Query, Tailwind, shadcn, Framer Motion, ElevenLabs SDK, Three.js

**Backend:** FastAPI, Python, LiteLLM/OpenAI, Supabase (PostgreSQL + pgvector), ElevenLabs, Twilio, Google Calendar, Resend, APScheduler

## Project Structure

```
├── frontend/
│   ├── src/
│   │   ├── pages/          # Home, AnalysisPage, BookingForm, CallStatus
│   │   ├── components/     # VoiceAgent, ToolCard, StackCard, GapCard, etc.
│   │   ├── hooks/          # useAnalysisVoice, useEmailDrafts
│   │   └── types/          # TypeScript definitions
│   └── vite.config.ts      # API proxy config
│
├── backend/
│   ├── routers/            # repos, tools, voice, booking, discovery, email_drafts
│   ├── services/
│   │   ├── analyzer.py     # LLM repo fingerprinting
│   │   ├── recommender.py  # Vector similarity scoring
│   │   ├── github.py       # GitHub API client
│   │   ├── elevenlabs.py   # Voice API wrapper
│   │   ├── discovery/      # Product Hunt, YC, GitHub trending scrapers
│   │   └── ...
│   └── db/                 # Supabase client, migrations
│
└── scripts/                # setup.sh, dev.sh, cleanup.sh
```

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # configure env vars
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`, proxies `/api/*` to backend.

## Environment Variables

```env
# Database
SUPABASE_URL=
SUPABASE_KEY=

# LLM
OPENAI_API_KEY=              # or use LiteLLM
LITELLM_BASE_URL=
LITELLM_API_KEY=
LITELLM_MODEL=gpt-4o

# GitHub
GITHUB_TOKEN=

# Voice
ELEVENLABS_API_KEY=
ELEVENLABS_AGENT_ID=

# Calendar
GOOGLE_API_KEY=
GOOGLE_CALENDAR_CREDENTIALS=

# Phone (CallPilot)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Email
RESEND_API_KEY=
RESEND_FROM_EMAIL=

# Discovery (optional)
PRODUCT_HUNT_TOKEN=
DISCOVERY_SYNC_ENABLED=true
DISCOVERY_SYNC_HOUR=3
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/repos/analyze` | Analyze GitHub repo |
| GET | `/api/repos/{id}` | Get repo fingerprint |
| GET | `/api/repos/{id}/recommendations` | Get tool recommendations |
| GET | `/api/tools` | List all tools |
| POST | `/api/discovery/sync` | Trigger tool discovery |
| POST | `/api/voice/start` | Start voice conversation |
| POST | `/api/email-drafts` | Generate email draft |
| POST | `/api/booking/start` | Start demo call |

API docs: `http://localhost:8000/docs`

## Data Flow

```
GitHub URL → Fetch Files → LLM Fingerprint → Store in Supabase
                                    ↓
              Display Stack/Gaps/Risks ← GET /repos/{id}
                                    ↓
              Vector Embeddings → Similarity Score → Ranked Tools
                                    ↓
                     Voice Agent / Email / CallPilot
```

## Recommendation Scoring

- **Repo Fit** (0-3): Tech stack compatibility
- **Scalability** (0-3): Solves identified gaps
- **Migration Cost** (0-2): Adoption effort
- **Maturity** (0-2): Docs, funding, compliance
- **Demo Priority** (0-5): Urgency for scheduling

## Architecture

- **Async** - FastAPI + httpx for concurrent GitHub/LLM calls
- **LLM Analysis** - GPT-4o for nuanced code understanding
- **Vector Search** - pgvector for semantic tool matching
- **Voice AI** - ElevenLabs conversational (analysis + scheduling modes)
- **Background Jobs** - APScheduler for daily tool discovery sync
