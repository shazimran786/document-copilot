# Document Copilot — implementation checklist

Work through these phases in order. Each phase unlocks the next.

**Backend or frontend first?** Start with **shared foundation** (Supabase, env, Python 3.12), then **backend data + retrieval** — that is the product (grounded, cited answers). Build the **frontend shell in parallel** once the backend has auth and a stub chat endpoint; wire the real RAG path only after ingestion and retrieval work.

**North star:** 5 senior analysts use it for a week and report ≥3 hours saved per analyst per week ([client brief](client-brief.md)).

Reference: [architecture.md](architecture.md) · [client-brief.md](client-brief.md)

---

## Phase 0 — Local machine & accounts

- [x] Install Python **3.12+** (`uv python install 3.12` or python.org installer)
- [x] Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [x] Install Node **20+** and enable **pnpm** (`corepack enable`)
- [x] Create [OpenAI API key](https://platform.openai.com/api-keys)
- [x] Create Supabase project ([guide](guides/supabase-setup.md))
- [x] Copy env templates: `backend/.env.example` → `backend/.env`, `frontend/.env.example` → `frontend/.env`
- [x] Fill Supabase URL, anon key, service role key, and direct `DATABASE_URL` in `backend/.env`
- [x] Fill `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE_URL` in `frontend/.env`

---

## Phase 1 — Backend scaffold & database

The schema is the contract between ingestion, retrieval, chat, and the UI. Get it right before building features on top.

- [x] `cd backend && uv sync` and add dependencies per [backend-setup.md](guides/backend-setup.md)
- [x] Create `app/main.py` (FastAPI + CORS + health check `GET /health`)
- [x] Create `app/config.py` (all env vars; fail fast on missing required values)
- [x] Init Alembic: `uv run alembic init alembic`, wire `env.py` to SQLAlchemy metadata + `settings.DATABASE_URL`
- [x] Add SQLAlchemy models: `users`, `source_documents`, `document_chunks`, `chat_threads`, `chat_messages`, `message_citations`
- [x] Generate and **review** initial migration — add explicit ops for:
  - [x] `create extension if not exists vector`
  - [x] `vector(1536)` embedding column
  - [x] generated `tsvector` on chunks
  - [x] HNSW index (vectors) and GIN index (full-text)
  - [x] RLS policies (users see only their own chats)
- [x] `uv run alembic upgrade head` against Supabase
- [x] Verify tables in Supabase dashboard (read-only check — schema source of truth is Alembic)

---

## Phase 2 — Corpus download & ingestion

No retrieval without indexed filings. Run this before the real chat agent.

- [ ] Edit `data/download.py`: set `USER_AGENT` to your email (SEC requirement)
- [ ] `uv run data/download.py` — confirm 10-Ks for AAPL, MSFT, NVDA, AMZN, GOOGL land in `data/downloads/`
- [ ] Build ingestion pipeline (`backend/ingest/`):
  - [ ] Parse downloaded HTML → normalized Markdown per filing
  - [ ] Extract metadata: ticker, company, filing type, fiscal year, accession number, source URL
  - [ ] Chunk text with stable chunk IDs and page/section metadata
  - [ ] Embed chunks with configured OpenAI embedding model
  - [ ] Upsert `source_documents` + `document_chunks` (text, embedding, `tsvector`) into Supabase
- [ ] Spot-check: query a few chunks in Supabase; confirm metadata and text look correct
- [ ] Add backend unit tests for chunking and metadata extraction

---

## Phase 3 — Retrieval (hybrid search)

Trust starts here: the LLM only sees what retrieval returns.

- [ ] `app/retrieval/queries.py` — pgvector semantic search over `document_chunks`
- [ ] `app/retrieval/queries.py` — Postgres full-text search over `search_vector`
- [ ] `app/retrieval/fusion.py` — Reciprocal Rank Fusion in Python
- [ ] `app/retrieval/retriever.py` — fuse, fetch passages + neighboring context + document metadata
- [ ] Manual smoke test: fixed queries (e.g. "AWS operating margin", "NVIDIA data center demand") return sensible chunks
- [ ] Unit tests for fusion ranking and passage assembly

---

## Phase 4 — LLM agent, grounding & chat API

Backend owns the full turn: retrieve → generate → validate citations → persist → stream.

- [ ] `app/auth/dependencies.py` — verify Supabase JWT on every protected route
- [ ] `app/database/supabase.py` — user-scoped and service-role clients
- [ ] `app/database/chats.py` + `documents.py` — typed read/write helpers
- [ ] `app/assistant/` — PydanticAI agent with `DocumentAgentDeps`, `GroundedAnswer`, `instructions.md`
- [ ] Agent tools (bounded): `search_filings`, `read_chunk`, `read_surrounding_chunks`
- [ ] `app/grounding/validator.py` — every citation maps to a retrieved passage; fail closed on violation
- [ ] `app/chat/orchestrator.py` — one turn end-to-end
- [ ] `app/chat/streaming.py` — AI SDK-compatible streaming events
- [ ] API routes:
  - [ ] `GET/POST /chat/threads` — list and create threads (user-scoped)
  - [ ] `GET /chat/threads/{id}/messages` — message history
  - [ ] `POST /chat/stream` — streaming assistant response
- [ ] Persist user message, assistant message, and citations after successful run
- [ ] Unit tests: citation validation, grounding enforcement, message conversion
- [ ] Run example analyst questions from [client-brief.md](client-brief.md) via API or script; confirm cited answers or honest "not enough evidence"

---

## Phase 5 — Frontend scaffold & auth

Thin browser: session, chat UI, stream display. No OpenAI or service-role keys in the client.

- [ ] Scaffold Vite + React + TS per [frontend-setup.md](guides/frontend-setup.md)
- [ ] Tailwind + shadcn/ui base layout
- [ ] `src/lib/env.ts`, `src/lib/supabase.ts`, `src/lib/http.ts`, `src/lib/api.ts`
- [ ] Email sign-in / sign-up pages (Supabase Auth)
- [ ] Protected routes — redirect unauthenticated users to login
- [ ] App shell: sidebar (thread list), main chat area, sign-out

---

## Phase 6 — Chat UI & citations

This is what analysts touch daily. Polish here drives pilot adoption.

- [ ] Thread list: load from backend, create new thread, switch threads
- [ ] Chat page with Vercel AI SDK `useChat` → `POST /chat/stream` with Supabase bearer token
- [ ] Message list: user vs assistant styling, streaming indicator, error states
- [ ] Citation UI: filing name, company, date, page/section per claim
- [ ] Source passage panel: expandable excerpt so analyst can verify in one click
- [ ] Empty state and "insufficient evidence" messaging (matches trust contract)
- [ ] Manual pass: sign in → ask → see streamed answer → click citation → read passage

---

## Phase 7 — Pilot readiness

- [ ] CORS: `ALLOWED_ORIGINS` includes local frontend URL
- [ ] Structured logging on backend (`structlog`) for auth, retrieval, and LLM failures
- [ ] Run full example-question set from client brief; note gaps and fix retrieval or prompts
- [ ] Confirm bot refuses to infer beyond filings (e.g. generative-AI margin question #10)
- [ ] Confirm no hallucinated citations under deliberate stress questions
- [ ] README "Running locally" section: exact commands for backend + frontend + ingest
- [ ] Short internal runbook for re-ingesting new filings

---

## Phase 8 — Deploy (Railway)

- [ ] Railway: backend service (`uvicorn app.main:app`)
- [ ] Railway: frontend service (Vite static build)
- [ ] Production env vars on both services (Supabase, OpenAI, `ALLOWED_ORIGINS`, API base URL)
- [ ] Run Alembic migrations against production Supabase
- [ ] Run ingestion against production DB
- [ ] Smoke test deployed app: auth → chat → citation → passage
- [ ] Invite 5 senior analysts for one-week pilot

---

## Definition of done (customer)

From [client-brief.md](client-brief.md) — tick when true in production:

- [ ] Analysts sign in with Driftwood email (email auth)
- [ ] Plain-English questions over the curated 10-K corpus (2021–2025 sample companies)
- [ ] Every factual claim has a citation (filing + page/section)
- [ ] Underlying passage visible for one-click verification
- [ ] Bot says "not in corpus" instead of inventing facts
- [ ] Users see their own past conversations
- [ ] No trading recommendations or external data sources
- [ ] Pilot group reports ≥3 hours saved per analyst per week → firm-wide rollout

---

## Suggested weekly focus (if building solo)


| Week | Focus                                                        |
| ---- | ------------------------------------------------------------ |
| 1    | Phase 0–1: Supabase, backend scaffold, schema migrated       |
| 2    | Phase 2–3: Download corpus, ingest, hybrid retrieval working |
| 3    | Phase 4: Auth + streaming chat API with grounded agent       |
| 4    | Phase 5–6: Frontend auth + chat + citations                  |
| 5    | Phase 7–8: Hardening, example-question QA, deploy, pilot     |


Adjust pace as needed; **do not skip ingestion/retrieval before wiring the real agent.**