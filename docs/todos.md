# Document Copilot — implementation checklist

Work through these phases in order. Each phase unlocks the next.

**Backend or frontend first?** Start with **shared foundation** (Supabase, env, Python 3.12), then **backend schema** (Phase 1). Next, **auth shell** (Phase 2), then a **stubbed chat vertical slice** (Phase 3) so analysts can click through threads and messages before corpus work. Build **ingestion → retrieval → real agent** in Phases 4–6; polish citations and ship in Phases 7–9.

**North star:** 5 senior analysts use it for a week and report ≥3 hours saved per analyst per week ([client brief](client-brief.md)).

Reference: [architecture.md](architecture.md) · [client-brief.md](client-brief.md)

---

## Progress snapshot (2026-06-08)

- **Branch:** Local `development` — Phases 4–6 complete (uncommitted). **Do not** blind `git pull` vs `origin/development` (remote still has the reverted full RAG stack).
- **Phase 0–4:** Complete — toolchain, Supabase, schema, auth shell, stubbed chat, corpus download, Docling conversion, full ingest to Supabase.
- **Phase 5:** Complete — hybrid retrieval (pgvector + full-text + RRF fusion).
- **Phase 6:** Complete — PydanticAI agent, grounding validator, real `POST /chat/stream`. **Next:** Phase 7 citations UI.
- **Tests:** `uv run pytest -v` — 45 passing (grounding, assistant, chat, retrieval, ingest, API).
- **Plans:** [phase-one](../implementation-plan/phase-one-implementation-plan.md) · [phase-two](../implementation-plan/phase-two-implementation-plan.md) · [phase-three](../implementation-plan/phase-three-implementation-plan.md) · [phase-four](../implementation-plan/phase-four-implementation-plan.md) · [phase-five](../implementation-plan/phase-five-implementation-plan.md) · [phase-five-testing](../implementation-plan/phase-five-testing-plan.md) · [phase-six](../implementation-plan/phase-six-implementation-plan.md) · [phase-six-testing](../implementation-plan/phase-six-testing-plan.md)
- **Issues logs:** [INGESTION_ISSUES.md](../backend/ingest/INGESTION_ISSUES.md) (Phase 4) · [phase-six-implementation-issues.md](../implementation-plan/phase-six-implementation-issues.md) (Phase 6)
- **Corpus (Supabase):** 25 `source_documents`, 7,470 `document_chunks`, 100% embedded.
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

**Plan:** [phase-one-implementation-plan.md](../implementation-plan/phase-one-implementation-plan.md)

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

**Plan:** [phase-two-implementation-plan.md](../implementation-plan/phase-two-implementation-plan.md)

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

**Plan:** [phase-three-implementation-plan.md](../implementation-plan/phase-three-implementation-plan.md)

**Backend (stubbed chat API)**

- [x] `app/database/chats.py` — typed read/write helpers for threads and messages (user-scoped via Supabase client)
- [x] `app/chat/schemas.py`, `app/chat/messages.py`, `app/chat/streaming.py`, `app/api/chat.py` — wire models, AI SDK message helpers, stub SSE, routes
- [x] `GET/POST /chat/threads` — list and create threads
- [x] `GET /chat/threads/{id}/messages` — message history for a thread
- [x] `POST /chat/stream` — AI SDK-compatible streaming events with a **fixed stub reply** (no OpenAI, no retrieval); persist user message + stub assistant message after stream completes
- [x] Unit tests: thread ownership, message ordering, stub stream event shape (`uv run pytest` — 18 passing)

**Frontend (wired chat UI)**

- [x] Replace Phase 2 home diagnostic with chat-first layout (or demote diagnostics to dev-only)
- [x] Thread list: load from backend, create new thread, switch threads
- [x] Chat composer + message list (user vs assistant styling, streaming indicator, error states)
- [x] Vercel AI SDK `useChat` → `POST /chat/stream` with Supabase bearer token
- [x] Empty states: no threads yet, no messages in thread

**Manual pass**

- [x] Sign in → create thread → send question → see stubbed streamed reply → refresh → history persists → sign out

---

## Phase 4 — Corpus download & ingestion

No retrieval without indexed filings. **Complete 2026-06-08.**

**Plan:** [phase-four-implementation-plan.md](../implementation-plan/phase-four-implementation-plan.md) · **Issues log:** [backend/ingest/INGESTION_ISSUES.md](../backend/ingest/INGESTION_ISSUES.md) · **Markdown QA:** [data/markdown-testing-strategy.md](../data/markdown-testing-strategy.md)

**Download (SEC EDGAR)**

- [x] Edit `data/download.py`: set `USER_AGENT` to your email (SEC requirement)
- [x] `uv run data/download.py` — 10-Ks for AAPL, MSFT, NVDA, AMZN, GOOGL in `data/downloads/`
- [x] Verify `data/downloads/manifest.json` — accession numbers, source URLs, local paths

**HTML → Markdown (Docling)**

- [x] `data/convert_to_markdown.py` — Docling batch convert; output mirrors `downloads/` under `data/markdown/`
- [x] `docling==2.96.1` in backend dev deps; `.gitignore` for `/data/markdown/*`
- [x] Converted 25 HTML filings → 25 Markdown files (`markdown/2021/` … `markdown/2025/`)
- [ ] Re-run after new downloads: `cd backend && uv run python ../data/convert_to_markdown.py`

**Ingestion pipeline (`backend/ingest/`)**

- [x] `models.py` — typed filing metadata + chunk records (internal, not DB models)
- [x] `metadata.py` — manifest → fields; resolve Markdown path (`downloads/` → `markdown/`)
- [x] `chunking.py` — section-aware splits + token-bounded chunks; stable `stable_chunk_id`; `section_label` truncated to 255
- [x] `embeddings.py` — batch OpenAI embeddings (`text-embedding-3-small`, 1536 dims)
- [x] `persist.py` — upsert `source_documents` + replace `document_chunks`; retry + batch size 25
- [x] `run.py` — CLI: `uv run python -m ingest.run` / `uv run ingest-corpus` (idempotent re-run)
- [x] `INGESTION_ISSUES.md` — errors found and fixed during ingest

**Verification & tests**

- [x] Supabase spot-check: 25 documents, 7,470 chunks, embeddings non-null
- [x] Unit tests: metadata + chunking (`tests/corpus_ingest/` — 9 tests)
- [x] Full ingest of corpus completed; re-run is idempotent

**Known ingest fixes (see issues log)**

- [x] MSFT `section_label` varchar(255) overflow → truncate in chunking
- [x] Transient Supabase disconnects → retry + smaller batch inserts
- [x] Windows console Unicode in CLI logs → ASCII output
- [x] `tests/ingest/` package shadowing → renamed to `tests/corpus_ingest/`

---

## Phase 5 — Retrieval (hybrid search)

Trust starts here: the LLM only sees what retrieval returns.

**Plan:** [phase-five-implementation-plan.md](../implementation-plan/phase-five-implementation-plan.md) · **Testing:** [phase-five-testing-plan.md](../implementation-plan/phase-five-testing-plan.md)

- [x] `app/retrieval/queries.py` — pgvector semantic search over `document_chunks`
- [x] `app/retrieval/queries.py` — Postgres full-text search over `search_vector`
- [x] `app/retrieval/fusion.py` — Reciprocal Rank Fusion in Python
- [x] `app/retrieval/retriever.py` — fuse, fetch passages + neighboring context + document metadata
- [x] Manual smoke test: fixed queries (e.g. "AWS operating margin", "NVIDIA data center demand") return sensible chunks
- [x] Unit tests for fusion ranking and passage assembly

---

## Phase 6 — LLM agent, grounding & real chat stream

Replace the Phase 3 stub with the real turn: retrieve → generate → validate citations → persist → stream. **Complete 2026-06-08.**

**Plan:** [phase-six-implementation-plan.md](../implementation-plan/phase-six-implementation-plan.md) · **Testing:** [phase-six-testing-plan.md](../implementation-plan/phase-six-testing-plan.md) · **Issues log:** [phase-six-implementation-issues.md](../implementation-plan/phase-six-implementation-issues.md)

**Assistant & grounding**

- [x] `app/config.py` — `openai_chat_model`, `openai_chat_timeout_seconds`, `agent_max_tool_calls`
- [x] `app/assistant/` — PydanticAI agent with `DocumentAgentDeps`, `GroundedAnswer`, `instructions.md`
- [x] Agent tools (bounded): `search_filings`, `read_chunk`, `read_surrounding_chunks`
- [x] `app/grounding/validator.py` — every citation maps to a retrieved passage; fail closed on violation
- [x] `app/database/documents.py` — chunk lookup helpers for agent tools (`fetch_chunk_by_stable_id`, neighbors)

**Orchestration & API**

- [x] `app/chat/orchestrator.py` — one turn: retrieve → `agent.run()` → validate → word deltas
- [x] `app/chat/streaming.py` — wire real agent into `POST /chat/stream` (same AI SDK event shape as stub)
- [x] `app/api/chat.py` — stub replaced; persist assistant message + `message_citations` on successful grounding
- [x] `app/database/chats.py` — `insert_citations()`; optional `message_id` on `insert_message`
- [x] Grounding failure UX: safe fallback message streamed; no `message_citations` rows (not HTTP 502)

**Verification & tests**

- [x] Unit tests: grounding validator, `GroundedAnswer`/`Citation`, orchestrator mock, citation metadata shape (`tests/grounding/`, `tests/assistant/`, `tests/chat/`)
- [x] API regression: `test_post_stream_returns_ai_sdk_sse` mocks `stream_agent_turn` (no live OpenAI in CI)
- [x] `uv run pytest -v` — 45 tests passing
- [x] `uv run python scripts/smoke_agent.py` — client-brief queries return cited answers or honest refusal
- [x] `phase-six-implementation-issues.md` — errors found and fixed during implementation

**Known Phase 6 notes (see issues log)**

- [x] Structured `GroundedAnswer` incompatible with `stream_text()` → `agent.run()` + post-hoc word deltas
- [x] OpenAI key from `settings` via explicit `OpenAIProvider` (not raw env alone)
- [ ] Optional: wire `openai_chat_timeout_seconds` and `agent_max_tool_calls` into Agent settings
- [ ] Optional: loosen excerpt grounding for table-heavy Docling chunks if fallback rate is too high

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
| 3    | Phase 3: Stubbed chat slice *(complete)*                                |
| 4    | Phase 4: Download corpus, ingest *(complete)* · Phase 5: hybrid retrieval *(complete)* |
| 5    | Phase 6: Real streaming agent + grounding *(complete)*               |
| 6    | Phase 7–9: Citations UI, hardening, deploy, pilot                    |


Adjust pace as needed; **do not wire the real agent until ingestion and retrieval are working** (Phases 4–5 before Phase 6).
