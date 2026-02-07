# PRD: Voice Agent for Autonomous Devtool Demo Scheduling (Repo-Aware)

## 1. Product Overview

### Product Name (Working)
**StackScout** / **DemoPilot** / **RepoMatch AI**

### Summary
A voice AI agent that analyzes a startup’s GitHub repository, identifies scalability and engineering gaps, recommends better-fit devtools/startups, and autonomously schedules demos with the highest-fit vendors.

The product solves the problem of “vibe-coded” early stacks that are hard to scale by turning tool discovery + vendor outreach into an automated workflow.

---

## 2. Problem Statement

Startups often build fast with incomplete architectural planning (“vibe coding”), leading to:
- messy infrastructure
- scalability bottlenecks
- missing observability/security/testing
- hard rewrites during pivots

When teams realize they need better tools, they waste time:
- searching for relevant startups/tools
- evaluating vendors manually
- scheduling demos back-and-forth

This slows down execution during the exact moment they need speed.

---

## 3. Goal & Vision

### Vision
Make scaling and refactoring easier by automatically matching a codebase to the best modern tools and scheduling vendor demos without human effort.

### Primary Goal (Hackathon Track Fit)
Deliver an **autonomous voice agent** that can reach out to startups/tools and schedule demo appointments based on repo-derived needs.

### Secondary Goal
Provide a credible recommendation + scoring engine that explains why each tool is suitable.

---

## 4. Target Users

### Primary User
- Founders / CTOs / engineers at early-stage startups
- teams evaluating infrastructure/devtools upgrades

### Secondary User
- Devtool vendors who want qualified inbound demo bookings

---

## 5. Core Use Case (“Killer Loop”)

**GitHub repo → tool recommendations → voice agent outreach → demo scheduling → recap + follow-ups**

1. User inputs a GitHub repo URL  
2. System scans repo and generates a “Stack Fingerprint”  
3. System outputs a ranked list of tool startups with suitability ratings  
4. User selects top tools and says:  
   “Schedule demos with the top 2 next week afternoons”  
5. Voice agent contacts vendors (or simulated call flow), confirms times, schedules demo  
6. System sends recap: tool scores, meeting times, next-step checklist  

---

## 6. Product Requirements (MVP)

### 6.1 Repo Ingestion & Analysis
**Requirement:** System must ingest a GitHub repo and infer tech stack + gaps.

**Inputs**
- GitHub repo URL

**Outputs**
- Tech stack summary (language, framework, infra hints)
- Detected missing components (observability, CI/CD, caching, testing, auth, etc.)
- “Scalability risk flags” (e.g. monolith, no tests, no logging)

**Success Criteria**
- Produces a structured JSON fingerprint usable by the recommendation engine.

---

### 6.2 Tool Discovery & Product Database
**Requirement:** System must fetch and store candidate tools/startups.

**Sources**
- YC Directory
- a16z directory
- Product Hunt
- GitHub trending / OSS “awesome lists”
- X hashtags (optional)
- Perplexity-style search queries (optional)

**Stored Fields**
- tool name
- category (observability, DB, auth, infra, testing, etc.)
- URL + demo booking link
- tags + integration keywords
- last updated timestamp
- maturity signals (funding/news/docs presence)

**Success Criteria**
- At least 50–200 tools in the database for demo credibility.

---

### 6.3 Recommendation + Rating Engine
**Requirement:** System must output ranked tool recommendations with explainable scoring.

#### Suitability Score (0–10)
Weighted scoring rubric:

- **Repo Fit (0–3):** compatibility with stack/framework
- **Scalability Upgrade (0–3):** solves repo-detected bottlenecks
- **Migration Cost (0–2):** effort/risk to adopt
- **Maturity & Safety (0–2):** docs, adoption, pricing, compliance/security

#### Demo Priority Score (0–10)
Used for scheduling urgency:
- ROI clarity
- time-to-value
- low integration friction
- solves urgent repo issue

**Output Format**
- Top 5–10 tools
- tool description
- Suitability Score + Demo Priority Score
- key pros/cons
- integration complexity estimate

**Success Criteria**
- Each recommendation includes a rationale and a score breakdown.

---

### 6.4 Voice Agent Scheduling System (Core Track Feature)
**Requirement:** Voice agent must autonomously schedule demos with vendors.

**Voice Agent Capabilities**
- Ask qualifying questions:
  - pricing tier
  - SOC2/security readiness
  - integration complexity
  - onboarding timeline
  - support level
- Propose meeting times based on user availability
- Confirm timezone + meeting duration
- Book meeting (calendar invite or via booking link)
- Send recap summary to user

**Voice Tech**
- ElevenLabs voice API (TTS + conversational voice UX if supported)

**Success Criteria**
- A full end-to-end scheduling flow can be demoed live or convincingly simulated.

---

### 6.5 Summary + Follow-up Output
**Requirement:** System must produce a post-scheduling summary.

**Includes**
- scheduled demo times
- tool ratings
- key questions asked + vendor answers
- recommended adoption plan checklist

**Success Criteria**
- User receives a structured “next actions” briefing.

---

## 7. Key Features (Nice-to-Have)

### 7.1 Audio CTO Briefing (ElevenLabs “Wow Feature”)
Generate a 2-minute voice briefing:
- top 3 tools
- why they fit
- tradeoffs
- migration risk

### 7.2 Migration Roadmap Generator
A step-by-step plan:
- what to refactor first
- what tests to add
- rollout plan (staging → prod)
- rollback strategy

### 7.3 Vendor CRM Pipeline View
A dashboard view:
- contacted
- awaiting response
- scheduled
- completed demo
- shortlisted

---

## 8. Non-Functional Requirements

### Speed
- Repo scan must complete in < 2 minutes for demo repos

### Explainability
- Every score must include a breakdown

### Reliability
- Voice scheduling flow must not fail silently  
  Fallback: email scheduling template if booking fails

### Safety
- Do not auto-send emails/calls without user approval (for hackathon demo)

---

## 9. Out of Scope (Hackathon)
- Full production-grade vendor crawling system
- Fully autonomous negotiation across multiple calendars
- Deep runtime profiling of code
- Real-time security compliance validation

---

## 10. User Journey (MVP Flow)

1. User enters GitHub repo  
2. System shows stack fingerprint + risk flags  
3. System outputs Top 5 tools with:
   - Suitability Score
   - Demo Priority Score
   - reason + tradeoffs
4. User clicks “Schedule demos”  
5. Voice agent confirms availability  
6. Voice agent contacts vendors + schedules demos  
7. User receives summary + audio briefing  

---

## 11. MVP Success Metrics (Hackathon-Appropriate)

- **Recommendation Accuracy Proxy:** recommendations appear plausible + stack-aligned
- **Scheduling Completion Rate:** at least 1 demo booking successfully completed or convincingly simulated
- **Latency:** end-to-end flow demo completes in < 5 minutes
- **User Delight:** audio briefing feels “magical” and useful

---

## 12. Suggested Tech Stack (Implementation Recommendation)

### Frontend
- Next.js + Tailwind

### Backend
- Node.js / Python API service

### Repo Analysis
- GitHub API + Semgrep + dependency parsers

### Database
- Postgres + pgvector

### Ranking
- Hybrid rules + embeddings

### Voice Scheduling
- ElevenLabs voice API
- Calendar integration (Google Calendar / Cal.com / Calendly)

### Orchestration
- lightweight agent workflow engine (LangGraph / custom)

---

## 13. Demo Script (What Judges Will See)

- Paste GitHub repo  
- System identifies: “No observability, weak CI, no caching layer”  
- Recommends 5 startups/tools with scores  
- User says: “Schedule demos with top 2 next week afternoons”  
- Voice agent calls/simulates call, confirms meeting times  
- System outputs booked demo schedule + sends voice CTO briefing recap  
