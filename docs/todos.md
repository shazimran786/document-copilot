# Document Copilot — implementation checklist

Work through these phases in order. Each phase unlocks the next.

**Backend or frontend first?** Start with **shared foundation** (Supabase, env, Python 3.12), then **backend schema** (Phase 1). Next, **auth shell** (Phase 2), then a **stubbed chat vertical slice** (Phase 3) so analysts can click through threads and messages before corpus work. Build **ingestion → retrieval → real agent** in Phases 4–6; polish citations and ship in Phases 7–9.

**North star:** 5 senior analysts use it for a week and report ≥3 hours saved per analyst per week ([client brief](client-brief.md)).

Reference: [architecture.md](architecture.md) · [client-brief.md](client-brief.md)

---

## Progress snapshot (2026-06-07)

- **Branch:** Local `development` @ `7cebbb4` — Phase 2 only. **Ahead 2 / behind 14** vs `origin/development` (remote still has the reverted full RAG stack). Do **not** `git pull` without a merge plan; use `git push --force-with-lease` only if you intend to replace remote with Phase 2.
- **Phase 0–2:** Complete — toolchain, Supabase, schema, auth shell, manual pass verified (dashboard user → sign in → `/health` + `/me` OK → sign out). Public sign-up disabled; create users via **Authentication → Users → Add user** (auto-confirm for dev).
- **Next phase:** Phase 3 — stubbed chat vertical slice (threads, messages, fake streamed reply).
- **Windows note:** `corepack enable` needs Administrator — use `npm install -g pnpm` instead.

---

## Phase 0 — Local machine & accounts

- [x] Install Python **3.12+** (`uv python install 3.12` or python.org installer)
- [x] Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [x] Install Node **20+** and **pnpm** (`corepack enable`, or `npm install -g pnpm` on Windows without admin)
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

## Phase 2 — Frontend scaffold & backend configuration

Thin browser shell plus backend auth wiring. No OpenAI or service-role keys in the client.

**Backend configuration**

- [x] `app/auth/dependencies.py` — verify Supabase JWT on every protected route (`get_current_user`, `get_user_scoped_supabase`; test via `GET /me`)
- [x] `app/database/supabase.py` — user-scoped and service-role clients
- [x] CORS: `ALLOWED_ORIGINS` includes local frontend URL (`app/main.py` + `app/config.py`; default `http://localhost:5173`)

**Frontend scaffold**

- [x] Scaffold Vite + React + TS per [frontend-setup.md](guides/frontend-setup.md)
- [x] Install frontend dependencies (`pnpm install`; `react-router-dom`, `@supabase/supabase-js`, `tailwindcss`, `@tailwindcss/vite`)
- [x] Tailwind + shadcn/ui base layout (`pnpm dlx shadcn@latest init`; wire `@tailwindcss/vite` in `vite.config.ts`)
- [x] `src/lib/env.ts`, `src/lib/supabase.ts`, `src/lib/http.ts`, `src/lib/api.ts`
- [x] Email sign-in / sign-up pages (Supabase Auth; `/login`, `/signup`, `AuthLayout` tab bar)
- [x] Protected routes — redirect unauthenticated users to login
- [x] App shell: sidebar (thread list placeholder), main chat area, sign-out
- [x] Manual pass: create user in Supabase dashboard (sign-up disabled) → sign in → home page shows **OK** for `GET /health` and `GET /me` → sign out
  ```powershell
  # Terminal 1: cd backend && uv run uvicorn app.main:app --reload
  # Terminal 2: cd frontend && pnpm dev
  # Browser: http://localhost:5173/login — user created via Supabase → Authentication → Users → Add user
  ```

---

## Phase 3 — Chat shell (vertical slice, stubbed)

End-to-end chat UX with **no retrieval or LLM** — proves threads, persistence, streaming transport, and UI before corpus work.

**Backend (stubbed chat API)**

- [ ] `app/database/chats.py` — typed read/write helpers for threads and messages (user-scoped via Supabase client)
- [ ] `GET/POST /chat/threads` — list and create threads
- [ ] `GET /chat/threads/{id}/messages` — message history for a thread
- [ ] `POST /chat/stream` — AI SDK-compatible streaming events with a **fixed stub reply** (no OpenAI, no retrieval); persist user message + stub assistant message after stream completes
- [ ] Unit tests: thread ownership, message ordering, stub stream event shape

**Frontend (wired chat UI)**

- [ ] Replace Phase 2 home diagnostic with chat-first layout (or demote diagnostics to dev-only)
- [ ] Thread list: load from backend, create new thread, switch threads
- [ ] Chat composer + message list (user vs assistant styling, streaming indicator, error states)
- [ ] Vercel AI SDK `useChat` → `POST /chat/stream` with Supabase bearer token
- [ ] Empty states: no threads yet, no messages in thread

**Manual pass**

- [ ] Sign in → create thread → send question → see stubbed streamed reply → refresh → history persists → sign out

---

## Phase 4 — Corpus download & ingestion

No retrieval without indexed filings. Run after the chat shell so UI iteration can continue in parallel once ingest scripts exist.

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

## Phase 5 — Retrieval (hybrid search)

Trust starts here: the LLM only sees what retrieval returns.

- [ ] `app/retrieval/queries.py` — pgvector semantic search over `document_chunks`
- [ ] `app/retrieval/queries.py` — Postgres full-text search over `search_vector`
- [ ] `app/retrieval/fusion.py` — Reciprocal Rank Fusion in Python
- [ ] `app/retrieval/retriever.py` — fuse, fetch passages + neighboring context + document metadata
- [ ] Manual smoke test: fixed queries (e.g. "AWS operating margin", "NVIDIA data center demand") return sensible chunks
- [ ] Unit tests for fusion ranking and passage assembly

---

## Phase 6 — LLM agent, grounding & real chat stream

Replace the Phase 3 stub with the real turn: retrieve → generate → validate citations → persist → stream.

- [ ] `app/database/documents.py` — typed read helpers for corpus metadata
- [ ] `app/assistant/` — PydanticAI agent with `DocumentAgentDeps`, `GroundedAnswer`, `instructions.md`
- [ ] Agent tools (bounded): `search_filings`, `read_chunk`, `read_surrounding_chunks`
- [ ] `app/grounding/validator.py` — every citation maps to a retrieved passage; fail closed on violation
- [ ] `app/chat/orchestrator.py` — one turn end-to-end
- [ ] `app/chat/streaming.py` — wire real agent into existing `POST /chat/stream` (same AI SDK event shape as stub)
- [ ] Persist assistant message and `message_citations` after successful run
- [ ] Unit tests: citation validation, grounding enforcement, message conversion
- [ ] Run example analyst questions from [client-brief.md](client-brief.md) via API or script; confirm cited answers or honest "not enough evidence"

---

## Phase 7 — Citations UI & analyst polish

This is what analysts touch daily once answers are real. Polish here drives pilot adoption.

- [ ] Citation UI: filing name, company, date, page/section per claim
- [ ] Source passage panel: expandable excerpt so analyst can verify in one click
- [ ] "Insufficient evidence" / "not in corpus" messaging (matches trust contract)
- [ ] Manual pass: sign in → ask real question → see streamed cited answer → click citation → read passage

---

## Phase 8 — Pilot readiness

- [ ] Structured logging on backend (`structlog`) for auth, retrieval, and LLM failures
- [ ] Run full example-question set from client brief; note gaps and fix retrieval or prompts
- [ ] Confirm bot refuses to infer beyond filings (e.g. generative-AI margin question #10)
- [ ] Confirm no hallucinated citations under deliberate stress questions
- [ ] README "Running locally" section: exact commands for backend + frontend + ingest
- [ ] Short internal runbook for re-ingesting new filings

---

## Phase 9 — Deploy (Railway)

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


| Week | Focus                                                                 |
| ---- | --------------------------------------------------------------------- |
| 1    | Phase 0–1: Supabase, backend scaffold, schema migrated              |
| 2    | Phase 2: Auth shell end-to-end *(complete)*                           |
| 3    | Phase 3: Stubbed chat vertical slice (threads, stream, UI wired)      |
| 4    | Phase 4–5: Download corpus, ingest, hybrid retrieval working          |
| 5    | Phase 6: Real streaming agent + grounding (swap out stub)             |
| 6    | Phase 7–9: Citations UI, hardening, deploy, pilot                    |


Adjust pace as needed; **do not wire the real agent until ingestion and retrieval are working** (Phases 4–5 before Phase 6).
