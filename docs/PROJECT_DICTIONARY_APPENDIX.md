# Project Dictionary / Glossary Appendix

This appendix is a quick-reference guide for **developers, analysts, architects, testers, and stakeholders** working on Document Copilot. It explains terminology, concepts, architecture, and naming conventions used across the repository — in code, configuration, documentation, database objects, and operational workflows.

Terms are grouped by category. Where a term has a **project-specific meaning** different from its general industry meaning, that distinction is called out in the definition.

---

## Table of contents

1. [Project & business](#1-project--business)
2. [Architecture & system boundaries](#2-architecture--system-boundaries)
3. [Frontend (React SPA)](#3-frontend-react-spa)
4. [Backend (FastAPI service)](#4-backend-fastapi-service)
5. [API routes & streaming contract](#5-api-routes--streaming-contract)
6. [Database & persistence](#6-database--persistence)
7. [Retrieval & search](#7-retrieval--search)
8. [LLM agent, grounding & trust](#8-llm-agent-grounding--trust)
9. [Ingestion pipeline](#9-ingestion-pipeline)
10. [Security & authentication](#10-security--authentication)
11. [Configuration & environment](#11-configuration--environment)
12. [DevOps, deployment & tooling](#12-devops-deployment--tooling)
13. [Testing](#13-testing)
14. [Data corpus & SEC domain](#14-data-corpus--sec-domain)
15. [Implementation phases & process](#15-implementation-phases--process)
16. [Acronyms & abbreviations](#16-acronyms--abbreviations)

---

## 1. Project & business

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| Document Copilot | Product / feature | The internal AI chatbot that lets Driftwood analysts ask plain-English questions about SEC filings and receive sourced, citable answers. | `README.md`, `docs/client-brief.md`, `backend/app/assistant/instructions.md`, UI copy | Central product name; all architecture serves this experience. |
| Driftwood Capital | Business / client | Fictional independent investment research firm (~40 analysts) that sells equity research to institutional clients. The project's primary user persona. | `docs/client-brief.md`, `backend/app/assistant/instructions.md` | Drives trust requirements, corpus scope, and out-of-scope rules (no stock picks). |
| Analyst | Business role | Driftwood employee who covers ~15 US public companies, reads SEC filings, and produces research reports. Primary end user of Document Copilot. | `docs/client-brief.md`, `docs/architecture.md` | UX, citation design, and answer style target analyst workflows. |
| Portfolio Manager (PM) | Business role | Institutional client who consumes Driftwood research; has limited time to read raw filings. | `docs/client-brief.md`, `backend/app/assistant/instructions.md` | Answers are written to be concise enough for PM review. |
| Source-document intake | Business process | The repetitive work of opening filings, scanning sections (risk factors, MD&A, segments), and extracting passages before original analysis. Document Copilot automates this. | `docs/client-brief.md`, `backend/app/assistant/instructions.md` | Defines the product problem and success metric (hours saved). |
| Condensation | Business concept | Turning thousands of pages of filings into actionable, verifiable summaries. Driftwood's core value proposition. | `docs/client-brief.md` | Explains why cited brevity matters more than exhaustive prose. |
| Trust contract | Product policy | Hard rules: never invent facts, always cite, show underlying passages, fail clearly when evidence is missing. A wrong confident answer is worse than no answer. | `docs/architecture.md`, `backend/app/assistant/instructions.md`, `TrustStatusBanner` | Governs agent instructions, grounding validator, and UI trust banners. |
| Pilot group | Business milestone | Five senior analysts who trial the product for one week; success unlocks firm-wide rollout. | `docs/client-brief.md`, `docs/todos.md`, `implementation-plan/pilot-evaluation-log.md` | Phase 8–9 gate and definition of done. |
| Definition of done (customer) | Business acceptance | Pilot saves ≥3 hours per analyst per week; cited answers; honest refusals; no trading advice. | `docs/client-brief.md`, `docs/todos.md` | North-star acceptance criteria for the entire build. |
| North star | Process | The customer definition of done above — used to prioritize phases and avoid scope creep. | `docs/todos.md` | Keeps implementation aligned with client value. |
| Curated corpus | Data / business | The controlled set of SEC filings indexed for retrieval — not the open internet. Sample: 10-Ks for AAPL, AMZN, GOOGL, MSFT, NVDA, fiscal years 2021–2025. | `docs/client-brief.md`, `backend/app/assistant/instructions.md` | Bounds what the bot can answer; out-of-corpus questions must be refused. |
| Out of scope | Product constraint | Explicitly excluded: trading recommendations, external news/data, multi-tenant SaaS, billing, mobile app, SSO. | `docs/client-brief.md`, `docs/architecture.md` | Prevents feature drift during build and pilot. |
| Hallucination | AI risk | Model invents facts or citations not supported by retrieved text. Treated as a product-killing failure. | `docs/client-brief.md`, grounding tests | Motivates retrieval-first design and citation validation. |
| Refusal | Product behavior | Honest answer when corpus evidence is insufficient (`insufficient_evidence: true`, empty citations). | `GroundedAnswer`, `TrustStatusBanner`, analyst question bank | Preferred over guessing; evaluated in pilot testing. |

---

## 2. Architecture & system boundaries

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| Thin browser | Architecture principle | Frontend renders UI and streams responses only; no retrieval, OpenAI, or privileged DB writes in the browser. | `docs/architecture.md`, `frontend/AGENTS.md` | Security and single source of truth for trust logic. |
| Authoritative backend | Architecture principle | FastAPI owns retrieval, LLM execution, grounding, citation checks, and durable persistence. | `docs/architecture.md` | All privileged credentials and trust enforcement live server-side. |
| Live chat path | Data flow | User question → auth → retrieval → agent → stream → persist citations. Serves analysts in real time. | `docs/architecture.md` (mermaid diagram) | Primary runtime path for the product. |
| Ingestion path | Data flow | Offline: download → convert → chunk → embed → Supabase. Prepares corpus before chat. | `docs/architecture.md`, `backend/ingest/` | Separate from chat; must complete before retrieval works. |
| Vertical slice | Implementation pattern | End-to-end feature through all layers (e.g. stubbed chat in Phase 3) before deepening individual components. | `docs/todos.md`, Phase 3 plan | De-risks integration early. |
| Stateless backend | Deployment | Railway FastAPI service holds no local document or chat state; durability is in Supabase. | `docs/architecture.md` | Simplifies scaling and redeploys. |
| Hybrid retrieval | Architecture pattern | Semantic (pgvector) + lexical (full-text) search run separately, fused in Python with RRF. | `backend/app/retrieval/`, `AGENTS.md` | Core search design; not a single-score DB query. |
| RAG (Retrieval-Augmented Generation) | Architecture pattern | LLM answers are conditioned on retrieved passages, not model training data alone. | `docs/architecture.md`, Phase 6 notes | Industry term for this project's core chat architecture. |
| AI SDK streaming contract | Integration pattern | Vercel AI SDK UI message stream format (`text-delta`, `finish`, header `x-vercel-ai-ui-message-stream: v1`) over SSE. | `backend/app/chat/streaming.py`, `frontend/src/components/chat/ChatPanel.tsx` | Keeps frontend `useChat` compatible with FastAPI. |
| Service-level architecture | Documentation | Two Railway services (frontend + backend) plus hosted Supabase and OpenAI. | `docs/architecture.md` | Deployment and responsibility map. |
| Non-goals | Architecture guardrail | Rejected patterns: Next.js/SSR, browser OpenAI calls, separate vector DB, multi-tenant, market data feeds. | `docs/architecture.md` | Prevents stack debates during implementation. |

---

## 3. Frontend (React SPA)

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| SPA (Single Page Application) | Frontend architecture | Vite + React client-side app with React Router; no server-side rendering. **Not Next.js.** | `frontend/AGENTS.md`, `docs/architecture.md` | Locked stack choice; affects routing and API integration. |
| Vite | Build tool | Frontend dev server and production bundler (`pnpm dev`, `pnpm build`). Default dev URL: `http://localhost:5173`. | `frontend/vite.config.ts`, `frontend/package.json` | Local dev entry point. |
| React Router | Routing library | Client-side routes: `/login`, `/signup`, `/chat`, `/chat/:threadId`. | `frontend/src/App.tsx` | Navigation and protected-route gating. |
| `@/*` import alias | Naming convention | TypeScript path alias for `src/*` (e.g. `@/lib/api`). | `frontend/tsconfig.json`, all `src/` imports | Consistent import style across components. |
| shadcn/ui | UI framework | Copy-in UI primitives under `components/ui/`; added via `pnpm dlx shadcn@latest add`. | `frontend/AGENTS.md`, `components/ui/` | Standard component source; don't hand-roll primitives. |
| Tailwind CSS | Styling | Utility-first CSS; global tokens in `src/index.css`. No CSS modules. | `frontend/AGENTS.md`, components | All component styling convention. |
| `src/lib/env.ts` | Configuration module | Single source of truth for `VITE_*` env vars; fails fast if missing. | `frontend/src/lib/env.ts` | Never read `import.meta.env` in components. |
| `src/lib/supabase.ts` | Auth client | Browser Supabase client + `getAccessToken()` for API calls. | `frontend/src/lib/supabase.ts` | Session management for email auth. |
| `src/lib/http.ts` | HTTP utility | Thin `fetch` wrapper: base URL, bearer token, `ApiError` with status/body. | `frontend/src/lib/http.ts` | No axios; distinguishes HTTP vs network errors. |
| `src/lib/api.ts` | API client | Product-level calls: `getCurrentUser`, `listThreads`, `createThread`, `getThreadMessages`. | `frontend/src/lib/api.ts` | Components use this instead of raw fetch paths. |
| `ApiError` | Frontend type | Typed HTTP failure from `apiFetch`; includes `status` and response `body`. | `frontend/src/lib/http.ts`, `ChatPage.tsx` | User-facing error handling and retry logic. |
| `useChat` | React hook | Vercel AI SDK hook managing message state, streaming status, and send. | `frontend/src/components/chat/ChatPanel.tsx` | Core chat UX primitive. |
| `DefaultChatTransport` | AI SDK class | Configures stream endpoint, auth headers, and request body shape for `useChat`. | `ChatPanel.tsx` | Bridges SPA to `POST /chat/stream`. |
| `ChatPanel` | UI component | Thread-scoped chat: composer, message list, streaming, response-time tracking. | `frontend/src/components/chat/ChatPanel.tsx` | Main interactive chat surface. |
| `ChatPage` | Page component | Route handler for `/chat/:threadId`; hydrates messages from backend. | `frontend/src/pages/ChatPage.tsx` | Loads history before `useChat` initializes. |
| `AppShell` | Layout component | Sidebar (thread list) + main content outlet for authenticated app. | `frontend/src/components/AppShell.tsx` | Primary logged-in layout. |
| `ThreadList` / `ThreadListItem` | UI components | Sidebar list of user's chat threads from `GET /chat/threads`. | `frontend/src/components/chat/ThreadList.tsx` | Thread navigation. |
| `MessageList` / `MessageBubble` | UI components | Renders user and assistant messages in a thread. | `frontend/src/components/chat/` | Chat transcript display. |
| `AssistantMessageBubble` | UI component | Assistant-specific bubble: citations, trust banner, response time, passage panel. | `frontend/src/components/chat/AssistantMessageBubble.tsx` | Where trust UX lives for answers. |
| `CitationChip` / `CitationChipList` | UI components | Clickable citation badges per claim (ticker, filing, section). | `frontend/src/components/chat/CitationChip.tsx` | One-click verification entry point. |
| `SourcePassagePanel` | UI component | Expandable panel showing verbatim excerpt and filing metadata for a citation. | `frontend/src/components/chat/SourcePassagePanel.tsx` | Implements "verify in one click" requirement. |
| `TrustStatusBanner` | UI component | Shows insufficient-evidence or validation-failed messaging. | `frontend/src/components/chat/TrustStatusBanner.tsx` | Surfaces trust contract outcomes in UI. |
| `StreamingIndicator` | UI component | Animated indicator during agent response; shows elapsed time. | `frontend/src/components/chat/StreamingIndicator.tsx` | Feedback during long turns. |
| `ResponseTimeLabel` | UI component | Session-only label of how long an assistant reply took (not persisted). | `frontend/src/components/chat/ResponseTimeLabel.tsx` | Pilot observability for analyst feedback. |
| `ProtectedRoute` | Auth wrapper | Redirects unauthenticated users to `/login`. | `frontend/src/components/ProtectedRoute.tsx` | Route guard for app shell. |
| `PublicRoute` | Auth wrapper | Redirects authenticated users away from login/signup. | `frontend/src/components/PublicRoute.tsx` | Prevents logged-in users on auth pages. |
| `useThreads` | React hook | Loads and manages thread list state for sidebar. | `frontend/src/hooks/useThreads.ts` | Thread CRUD from backend API. |
| `useSession` | React hook | Tracks Supabase auth session for the SPA. | `frontend/src/hooks/useSession.ts` | Drives auth-dependent rendering. |
| `ChatMessage` | TypeScript type | `UIMessage` extended with optional `metadata` (citations, flags). | `frontend/src/lib/chat-types.ts` | Typed bridge between AI SDK and citation UI. |
| `CitationMetadata` | TypeScript type | Frontend shape for one citation: chunk IDs, excerpt, ticker, fiscal year, section, source URL. | `frontend/src/lib/chat-types.ts`, `src/lib/citations.ts` | Powers citation chips and passage panel. |
| `AssistantMessageMetadata` | TypeScript type | `citations`, `insufficientEvidence`, `validationFailed` on assistant messages. | `frontend/src/lib/chat-types.ts` | Trust state after stream + hydration. |
| Hydration (frontend) | Data flow | After stream completes, `ChatPage` refetches messages to load full citation metadata from DB. | `ChatPage.tsx` (`hydrationKey`, `onStreamComplete`) | Stream may not carry full passage text; DB is source of truth. |
| `DevHealthPage` | Dev-only page | `/dev/health` — checks `GET /health` and `GET /me` (dev builds only). | `frontend/src/pages/DevHealthPage.tsx` | Phase 2 diagnostic; not in production routes. |
| `pnpm` | Package manager | **Only** allowed frontend package manager; lockfile `pnpm-lock.yaml`. | `frontend/AGENTS.md`, `frontend/.npmrc` | Enforced dependency policy. |
| Minimum release age | Security policy | pnpm refuses packages published &lt;7 days ago (`minimum-release-age=10080`). | `frontend/.npmrc` | Supply-chain protection. |

---

## 4. Backend (FastAPI service)

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| FastAPI | Web framework | Python async API framework; entrypoint `app/main.py`, routers under `app/api/`. | `backend/app/main.py`, `AGENTS.md` | All HTTP endpoints and DI live here. |
| Uvicorn | ASGI server | Production/dev server for FastAPI (`uv run uvicorn app.main:app`). | `backend/pyproject.toml`, `docs/todos.md` | Railway backend process command. |
| `app/main.py` | Module | FastAPI app: CORS, health, `/me`, chat router mount. | `backend/app/main.py` | Application entrypoint. |
| `app/config.py` | Settings module | Pydantic `Settings` — single source of truth for all backend env vars. | `backend/app/config.py` | Fail-fast config; no `os.getenv` elsewhere. |
| `settings` | Singleton | Module-level `Settings()` instance imported across backend. | `backend/app/config.py` | Retrieval tuning, OpenAI models, Supabase URLs. |
| `app/api/chat.py` | API router | Chat threads, messages, streaming endpoint. | `backend/app/api/chat.py` | Primary product API surface. |
| `app/auth/dependencies.py` | Auth module | `get_bearer_token`, `get_current_user`, `get_user_scoped_supabase`. | `backend/app/auth/dependencies.py` | JWT verification on every protected route. |
| `CurrentUser` | Dataclass | Authenticated user: `id`, `email`, `access_token`. | `backend/app/auth/dependencies.py` | Request-scoped identity for chat and RLS-scoped client. |
| `app/database/supabase.py` | DB client factory | `create_user_scoped_client`, `get_service_role_client`. | `backend/app/database/supabase.py` | Separates browser-safe vs privileged DB access. |
| `app/database/chats.py` | Persistence helpers | Thread/message CRUD, citation inserts, sequence numbers. | `backend/app/database/chats.py` | Chat durability via Supabase client. |
| `app/database/documents.py` | Document helpers | Chunk/document fetch for agent tools and assembly. | `backend/app/database/documents.py` | Bridge between SQLAlchemy rows and `SourcePassage`. |
| `app/database/engine.py` | SQLAlchemy engine | Direct Postgres connection for retrieval queries and Alembic. | `backend/app/database/engine.py` | Session-scoped raw SQL for hybrid search. |
| `session_scope` | Context manager | SQLAlchemy session lifecycle for retrieval and agent tools. | `backend/app/database/engine.py` | Used by `DocumentRetriever` and agent `read_*` tools. |
| `app/chat/orchestrator.py` | Turn orchestration | One chat turn: retrieve → `agent.run()` → validate → yield deltas/`TurnResult`. | `backend/app/chat/orchestrator.py` | End-to-end turn lifecycle owner. |
| `TurnResult` | Dataclass | Final turn output: `GroundedAnswer`, passages map, message IDs, `validation_failed`. | `backend/app/chat/orchestrator.py` | Passed to streaming persistence callback. |
| `app/chat/streaming.py` | Streaming layer | SSE event formatting, `stream_agent_turn`, AI SDK event types. | `backend/app/chat/streaming.py` | Wire format for frontend `useChat`. |
| `app/chat/messages.py` | Message conversion | AI SDK ↔ internal types; citation UI metadata builders. | `backend/app/chat/messages.py` | Shapes persisted `message_json` for frontend. |
| `app/chat/schemas.py` | API models | `ThreadResponse`, `MessageResponse`, `ChatStreamRequest`, etc. | `backend/app/chat/schemas.py` | Pydantic validation at HTTP boundary. |
| `app/assistant/agent.py` | LLM agent | PydanticAI `document_agent` with tools and `GroundedAnswer` output. | `backend/app/assistant/agent.py` | Typed LLM boundary. |
| `document_agent` | Agent instance | Configured PydanticAI `Agent` using `gpt-4o-mini` (default) and `instructions.md`. | `backend/app/assistant/agent.py` | Invoked per chat turn. |
| `DocumentAgentDeps` | Agent dependencies | Per-turn deps: user/thread IDs, retriever, session factory, `retrieved_passages` registry. | `backend/app/assistant/deps.py` | Explicit DI; tracks allowed citation pool. |
| `app/assistant/instructions.md` | System prompt | Product contract for the agent: corpus scope, tools, citation rules, prohibitions. | `backend/app/assistant/instructions.md` | "The prompt is the product" per backend AGENTS.md. |
| `app/assistant/outputs.py` | Output models | `GroundedAnswer`, `Citation` Pydantic models. | `backend/app/assistant/outputs.py` | Structured agent response schema. |
| `app/grounding/validator.py` | Trust enforcement | `GroundingValidator` — citations must map to retrieved passages with grounded excerpts. | `backend/app/grounding/validator.py` | Fail-closed before persisting bad citations. |
| `GroundingValidationError` | Exception | Raised when answer violates grounding contract. | `backend/app/grounding/validator.py` | Triggers safe fallback UX, not HTTP 502. |
| `app/retrieval/retriever.py` | Retrieval façade | `DocumentRetriever.search()` — full hybrid pipeline. | `backend/app/retrieval/retriever.py` | Injected into chat stream and agent tools. |
| `ingest/` package | Offline pipeline | Markdown → chunk → embed → Supabase (not in request path). | `backend/ingest/` | Populates tables retrieval searches. |
| `structlog` | Logging library | Declared dependency; structured logging planned for Phase 8. | `backend/pyproject.toml`, `docs/todos.md` | Future observability for pilot. |
| `uv` | Python tooling | Dependency and project manager for backend (`uv sync`, `uv run`). | `backend/pyproject.toml`, `AGENTS.md` | Replaces pip/poetry for this repo. |
| `ChatPersistenceError` | Exception | Supabase write/read failure in chat helpers. | `backend/app/database/chats.py` | Mapped to HTTP 502 in chat routes. |

---

## 5. API routes & streaming contract

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| `GET /health` | API route | Liveness check returning `{"status": "ok"}`. No auth. | `backend/app/main.py`, `frontend/src/lib/api.ts` | Deploy and dev diagnostics. |
| `GET /me` | API route | Returns authenticated user `id` and `email`. Requires bearer token. | `backend/app/main.py` | Verifies auth wiring end-to-end. |
| `GET /chat/threads` | API route | Lists current user's chat threads. | `backend/app/api/chat.py` | Sidebar thread list. |
| `POST /chat/threads` | API route | Creates a new thread; optional `title` in body. | `backend/app/api/chat.py` | "New chat" action. |
| `GET /chat/threads/{id}/messages` | API route | Returns message history as AI SDK-compatible UI messages. | `backend/app/api/chat.py` | Thread hydration on page load. |
| `POST /chat/stream` | API route | Main chat endpoint: SSE stream of assistant response; persists user + assistant messages. | `backend/app/api/chat.py`, `ChatPanel.tsx` | Core product interaction. |
| `ChatStreamRequest` | Request body | `{ threadId, messages }` — AI SDK message list at API boundary. | `backend/app/chat/schemas.py` | Wire contract for streaming. |
| SSE (Server-Sent Events) | Protocol | `text/event-stream` response; `data: {...}\n\n` frames. | `backend/app/chat/streaming.py` | Incremental answer delivery to browser. |
| `text-delta` | Stream event type | AI SDK event carrying incremental answer text. | `backend/app/chat/streaming.py` | Powers typing/streaming UX. |
| `[DONE]` | Stream sentinel | Final SSE data line signaling stream end. | `backend/app/chat/streaming.py` | Client knows stream completed. |
| `x-vercel-ai-ui-message-stream` | HTTP header | Version header (`v1`) identifying AI SDK UI stream format. | `backend/app/chat/streaming.py` | Client library compatibility marker. |
| Word deltas | Streaming technique | Full answer split into word chunks post-`agent.run()` (not token-level LLM streaming). | `backend/app/chat/orchestrator.py`, `split_text_deltas` | Known Phase 8 gap: long wait before first delta. |
| `on_complete` callback | Persistence hook | Called after stream finishes to persist assistant message + citations. | `backend/app/api/chat.py`, `stream_agent_turn` | Durability happens after successful turn. |
| HTTP 401 | Error class | Missing/invalid/expired Supabase JWT. | `docs/architecture.md`, `get_current_user` | Auth failure before any LLM cost. |
| HTTP 403 | Error class | Authenticated user accessing another user's thread (RLS + route checks). | `docs/architecture.md` | Multi-user isolation. |
| HTTP 404 | Error class | Thread not found. | `backend/app/api/chat.py` | Invalid `threadId` in stream request. |
| HTTP 422 | Error class | Invalid request payload (e.g. no user message in stream body). | `backend/app/api/chat.py` | Input validation at boundary. |
| HTTP 502 | Error class | Upstream Supabase persistence failure. | `backend/app/api/chat.py` | Distinguishes infra errors from grounding failures. |
| CORS | Security / HTTP | Cross-Origin Resource Sharing; `ALLOWED_ORIGINS` in backend config. | `backend/app/main.py`, `app/config.py` | Local dev: frontend port 5173 → backend 8000. |

---

## 6. Database & persistence

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| Supabase Postgres | Database | Hosted PostgreSQL for users, chats, documents, chunks, vectors, citations. | `README.md`, all `app/database/` | Single durable store for product state and retrieval. |
| SQLAlchemy | ORM | Python models in `app/database/models/`; metadata for Alembic autogenerate. | `backend/app/database/models/` | Schema source of truth alongside migrations. |
| Alembic | Migration tool | Versioned schema changes in `backend/alembic/versions/`. | `backend/alembic/`, `AGENTS.md` | Never edit production schema via Supabase dashboard alone. |
| `users` | Table | App user profile keyed by Supabase `auth.users.id`; email and timestamps. | `backend/alembic/versions/ab03722082e4_initial_schema.py` | Links auth identity to chat ownership. |
| `source_documents` | Table | One row per SEC filing: ticker, company, fiscal year, accession, URL, full `markdown_content`. | Migration, `ingest/persist.py` | Parent record for chunks; stores normalized filing text. |
| `document_chunks` | Table | Retrieval units: text, embedding, metadata, `stable_chunk_id`, section labels. | Migration, retrieval queries | Core search index for hybrid retrieval. |
| `chat_threads` | Table | Conversation metadata: `user_id`, `title`, timestamps. | Migration, `app/database/chats.py` | User-scoped conversation container. |
| `chat_messages` | Table | Ordered messages: `role`, `content_text`, `message_json`, `sequence_number`. | Migration, `app/database/chats.py` | Chat history + AI SDK-compatible JSON. |
| `message_citations` | Table | Normalized citations: `chunk_id`, `claim_index`, `excerpt`, `citation_metadata`. | Migration, `insert_citations` | Durable citation records for UI hydration. |
| `message_role` | Postgres enum | `user` or `assistant`. | Alembic migration | Typed message roles in DB. |
| `stable_chunk_id` | Identifier | Human-stable chunk key: `{accession_number}:{chunk_index}` (e.g. `0001018724-22-000005:60`). Survives chunk UUID regeneration on re-ingest. | `ingest/chunking.py`, citations, RRF fusion | Cross-ingest identity for citations and fusion. |
| `chunk_id` | Identifier | UUID primary key of `document_chunks`; authoritative citation key per turn. | `Citation` model, grounding validator | Must match a passage retrieved in the same turn. |
| `accession_number` | SEC metadata | SEC EDGAR unique filing identifier; unique constraint on `source_documents`. | `source_documents` table, manifest | Idempotent document upsert key. |
| `embedding` | Column | `vector(1536)` on `document_chunks` for semantic search. | Alembic migration, ingest | Requires OpenAI embeddings at ingest time. |
| `search_vector` | Column | Generated `tsvector` from `chunk_text` (English); not set by ingest. | Alembic `alter table ... generated always as` | Powers full-text channel automatically. |
| `chunk_metadata` | JSONB column | Per-chunk metadata: ticker, fiscal year, char offsets, `content_hash`, etc. | `document_chunks` | Filters and citation display context. |
| `message_json` | JSONB column | AI SDK-compatible message payload including citation metadata for assistants. | `chat_messages` | Frontend hydration source after stream. |
| pgvector | Postgres extension | Vector similarity search extension (`create extension vector`). | Alembic migration | Enables semantic retrieval in-database. |
| HNSW index | Database index | `document_chunks_embedding_hnsw_idx` — approximate nearest-neighbor vector search. | Alembic migration | Fast semantic search at scale. |
| GIN index | Database index | On `search_vector` and `chunk_metadata` for full-text and JSON queries. | Alembic migration | Lexical search performance. |
| RLS (Row Level Security) | Security / DB | Postgres policies restricting rows by `auth.uid()`. | Alembic migration policies | Users see only their chats; authenticated read on corpus. |
| `handle_new_user` | DB trigger | Inserts into `public.users` when Supabase `auth.users` row created. | Alembic migration | Syncs auth users to app `users` table. |
| Direct connection URL | Config | `DATABASE_URL` must use `db.<ref>.supabase.co`, **not** transaction pooler. | `backend/app/config.py` | Required for migrations, extensions, and indexes. |
| Transaction pooler | Supabase feature | Pooled Postgres URL (`pooler.supabase.com`) — rejected for `DATABASE_URL`. | `backend/app/config.py` validator | Pooler breaks session-level migration operations. |
| Service-role key | Credential | Supabase secret key for backend privileged writes (ingest, some persistence). | `SUPABASE_SERVICE_ROLE_KEY`, `get_service_role_client` | Never exposed to frontend. |
| Anon key | Credential | Public Supabase key safe for browser with RLS. | `VITE_SUPABASE_ANON_KEY`, `SUPABASE_ANON_KEY` | Frontend auth only. |

---

## 7. Retrieval & search

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| `DocumentRetriever` | Service class | Orchestrates embed → dual search → RRF → assembly. | `backend/app/retrieval/retriever.py` | Single entry point for chat and agent tools. |
| `RetrievalQuery` | Model | Input: `text` + optional `RetrievalFilters`. | `backend/app/retrieval/schemas.py` | Standard retrieval request shape. |
| `RetrievalFilters` | Model | Optional `tickers`, `fiscal_years`, `filing_types` filters. | `schemas.py`, `search_filings` tool | Scoped search for comparisons. |
| Semantic search | Retrieval channel | pgvector cosine distance on `document_chunks.embedding`. | `backend/app/retrieval/queries.py` | Finds conceptually similar passages. |
| Full-text search | Retrieval channel | Postgres `ts_rank_cd` + `websearch_to_tsquery` on `search_vector`. | `backend/app/retrieval/queries.py` | Finds keyword matches (e.g. exact segment names). |
| `RetrievalChannel` | Enum | `semantic` or `fulltext` — tags which channel produced a hit. | `backend/app/retrieval/schemas.py` | Observability and passage assembly. |
| `ChunkHit` | Model | Single ranked result from one channel: id, rank, score, channel. | `backend/app/retrieval/schemas.py` | Input to RRF fusion. |
| RRF (Reciprocal Rank Fusion) | Algorithm | Merges ranked lists: `score += 1/(k + rank)`; default `k=60`. | `backend/app/retrieval/fusion.py` | Combines semantic + lexical without score normalization. |
| `FusedChunkHit` | Model | Post-RRF chunk with `fused_score` and per-channel ranks. | `backend/app/retrieval/fusion.py` | Top-K selection before assembly. |
| `assemble_passages` | Function | Hydrates fused hits into full `SourcePassage` objects with neighbors. | `backend/app/retrieval/assembly.py` | LLM sees text + metadata, not just IDs. |
| `SourcePassage` | Model | Full retrieval unit: chunk text, document summary, neighbors, fused score, channels. | `backend/app/retrieval/schemas.py` | Passed to agent as seed context and citation pool. |
| `DocumentSummary` | Model | Lightweight filing metadata attached to each passage. | `backend/app/retrieval/schemas.py` | Citation chips and tool responses. |
| `NeighborChunk` | Model | Adjacent chunk within same filing (`before` / `after` position). | `backend/app/retrieval/schemas.py` | Extra context for tables and cut-off paragraphs. |
| `neighbor_window` | Config | How many adjacent chunks to include (default `1`). | `backend/app/config.py` | Balances context size vs. prompt size. |
| Seed passages | Agent concept | Passages retrieved **before** agent runs, injected into user prompt. | `backend/app/assistant/agent.py`, `instructions.md` | Starting evidence pool for the turn. |
| `embed_query` | Function | Embeds user question via same model as ingest (`text-embedding-3-small`). | `backend/app/retrieval/embed.py` | Query/corpus vector alignment. |
| `retrieval_semantic_top_k` | Config | Max semantic hits before fusion (default 50). | `backend/app/config.py` | Retrieval breadth tuning. |
| `retrieval_fusion_top_k` | Config | Max fused hits kept (default 10). | `backend/app/config.py` | Limits prompt size and agent context. |
| `smoke_retrieval.py` | Script | Manual script to test retrieval against live corpus. | `backend/scripts/smoke_retrieval.py` | Phase 5 verification. |

---

## 8. LLM agent, grounding & trust

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| PydanticAI | Framework | Typed Python agent framework for LLM orchestration with tools and structured outputs. | `backend/app/assistant/agent.py`, `pyproject.toml` | Replaces ad hoc prompt calls. |
| OpenAI | LLM provider | Chat model (`gpt-4o-mini`) and embeddings (`text-embedding-3-small`). | `app/config.py`, `ingest/embeddings.py` | External AI API; corpus remains in Supabase. |
| `GroundedAnswer` | Output schema | Agent output: `answer`, `citations`, `insufficient_evidence`. | `backend/app/assistant/outputs.py` | Structured contract enforced by PydanticAI. |
| `Citation` | Output schema | One claim link: `chunk_id`, `stable_chunk_id`, `claim_index`, `excerpt`. | `outputs.py`, `message_citations` table | Every factual claim must map to evidence. |
| `claim_index` | Citation field | Zero-based index of the factual claim in `answer` text. | `instructions.md`, `Citation` model | Links prose claims to citation chips in UI. |
| `insufficient_evidence` | Output flag | `true` when corpus cannot support an answer; citations must be empty. | `GroundedAnswer`, `TrustStatusBanner` | Honest refusal path. |
| `search_filings` | Agent tool | Re-runs hybrid retrieval with optional ticker/year filters. | `backend/app/assistant/agent.py` | Agent can broaden/narrow evidence mid-turn. |
| `read_chunk` | Agent tool | Fetches full text for one `stable_chunk_id`. | `backend/app/assistant/agent.py` | Handles truncated previews in seed/tool results. |
| `read_surrounding_chunks` | Agent tool | Fetches target chunk plus neighbors in same filing. | `backend/app/assistant/agent.py` | Fixes cut-off tables and paragraph context. |
| Retrieved passages registry | Runtime state | `DocumentAgentDeps.retrieved_passages` — all passages allowed for citation this turn. | `backend/app/assistant/deps.py`, agent tools | Grounding validator's allowlist. |
| `GroundingValidator` | Service class | Validates citations against retrieved passages and excerpt grounding. | `backend/app/grounding/validator.py` | Architecture-level trust enforcement. |
| Excerpt grounding | Validation rule | Citation `excerpt` must appear (normalized) in passage `chunk_text`. | `backend/app/grounding/validator.py` | Prevents paraphrased or fabricated quotes. |
| Validation fallback | UX path | On grounding failure, stream safe message with `validation_failed: true`; no citations persisted. | `orchestrator.py`, `GROUNDING_FALLBACK_MESSAGE` | Fail closed without HTTP error to user. |
| `_normalize_agent_answer` | Helper | Drops citations when model incorrectly sets `insufficient_evidence` with citations. | `backend/app/chat/orchestrator.py` | Fixes common model mistakes pre-validation. |
| `agent_max_tool_calls` | Config | Max tool invocations per turn (default 5; wiring pending Phase 8). | `backend/app/config.py` | Cost and latency guardrail. |
| `openai_chat_model` | Config | Default `gpt-4o-mini` for document agent. | `backend/app/config.py` | Chat model selection. |
| `instructions.md` | Prompt template | System prompt defining role, corpus, tools, output contract, prohibitions. | `backend/app/assistant/instructions.md` | Product behavior specification for the LLM. |
| `smoke_agent.py` | Script | Manual end-to-end agent smoke tests against client-brief questions. | `backend/scripts/smoke_agent.py` | Phase 6 trust verification. |
| Prohibited content | Policy | No stock recommendations, invented metadata, or uncited factual claims. | `instructions.md` | Regulatory and client trust requirements. |

---

## 9. Ingestion pipeline

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| Ingestion | Process | Offline pipeline: manifest → Markdown → chunks → embeddings → Supabase. | `backend/ingest/`, `docs/architecture.md` | Without ingest, retrieval returns nothing. |
| `ingest-corpus` | CLI script | Console entry point: `uv run ingest-corpus` → `ingest.run:main`. | `backend/pyproject.toml` | Operator command for full corpus load. |
| `manifest.json` | Data file | Index of downloaded filings: accession, URLs, local paths, dates. | `data/downloads/manifest.json`, `ingest/metadata.py` | Drives which filings to ingest. |
| `DocumentMetadata` | Ingest model | In-memory filing record before chunking (ticker, accession, markdown content, etc.). | `backend/ingest/models.py` | Bridge from manifest to DB upsert. |
| `ChunkRecord` | Ingest model | In-memory chunk before persist; embedding attached after `embed_texts`. | `backend/ingest/models.py` | Unit written to `document_chunks`. |
| `chunk_markdown` | Function | Splits filing Markdown into section-aware, token-bounded chunks. | `backend/ingest/chunking.py` | Defines chunk boundaries for retrieval quality. |
| `MAX_CHUNK_TOKENS` | Chunking constant | 800 tokens max per chunk (estimated as `len/4`). | `backend/ingest/chunking.py` | Retrieval granularity vs. context size. |
| `OVERLAP_TOKENS` | Chunking constant | 100-token overlap when splitting long sections. | `backend/ingest/chunking.py` | Reduces lost context at chunk boundaries. |
| `MIN_CHUNK_TOKENS` | Chunking constant | Chunks below 50 tokens are discarded. | `backend/ingest/chunking.py` | Filters noise fragments. |
| `SECTION_HEADING_RE` | Regex | Detects Markdown `#` headings or SEC `Item N.` headings for section splits. | `backend/ingest/chunking.py` | Section-aware chunking for analyst-relevant labels. |
| `embed_texts` | Function | Batch OpenAI embedding with retries; shared with query embedding. | `backend/ingest/embeddings.py`, `retrieval/embed.py` | Same model for corpus and queries. |
| `upsert_document` | Persist function | Insert/update `source_documents` by `accession_number`. | `backend/ingest/persist.py` | Idempotent document writes. |
| `replace_document_chunks` | Persist function | Delete all chunks for document, batch-insert new rows. | `backend/ingest/persist.py` | Full chunk refresh on re-ingest. |
| Idempotent ingest | Operational property | Re-running ingest for same accession overwrites document and replaces chunks safely. | `backend/ingest/README.md` | Safe re-runs after conversion fixes. |
| `--dry-run` | CLI flag | Chunk only; no Supabase or OpenAI calls. | `backend/ingest/run.py` | Preview chunk counts cheaply. |
| `--documents-only` | CLI flag | Upsert documents without chunks/embeddings. | `backend/ingest/run.py` | Partial pipeline debugging. |
| `--skip-embeddings` | CLI flag | Write chunks without vectors. | `backend/ingest/run.py` | Debug persist; semantic search won't find these chunks. |
| Docling | Library | HTML→Markdown converter (`docling==2.96.1`, dev dependency). | `data/convert_to_markdown.py` | SEC HTML filing normalization step. |
| `convert_to_markdown.py` | Script | Batch converts `data/downloads/` HTML to `data/markdown/`. | `data/convert_to_markdown.py` | Prerequisite before ingest. |
| `download.py` | Script | Fetches sample 10-Ks from SEC EDGAR into `data/downloads/`. | `data/download.py` | Corpus acquisition; requires `USER_AGENT` email. |
| `INGESTION_ISSUES.md` | Operations log | Documented ingest failures and fixes (MSFT section labels, batch size, etc.). | `backend/ingest/INGESTION_ISSUES.md` | Institutional knowledge for re-ingest. |
| Verified corpus snapshot | Metric | 25 documents, 7,470 chunks, 100% embedded (5 tickers × 5 years). | `backend/ingest/README.md`, `docs/todos.md` | Baseline for retrieval and pilot tests. |

---

## 10. Security & authentication

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| Supabase Auth | Auth service | Email-only sign-in; issues JWT access tokens for API calls. | `frontend/src/lib/supabase.ts`, `app/auth/` | Identity source for the whole app. |
| JWT (JSON Web Token) | Security token | Supabase access token sent as `Authorization: Bearer <token>`. | `http.ts`, `get_current_user` | Request credential verified on every protected route. |
| Bearer token | HTTP auth scheme | `Authorization: Bearer` header injected by `apiFetch`. | `frontend/src/lib/http.ts`, FastAPI `HTTPBearer` | Standard auth transport to backend. |
| User-scoped Supabase client | Client pattern | Supabase client created with user's JWT; RLS enforces row access. | `create_user_scoped_client` | Chat reads/writes respect ownership. |
| `get_current_user` | FastAPI dependency | Verifies JWT via `client.auth.get_user()`; returns `CurrentUser`. | `backend/app/auth/dependencies.py` | Auth gate before retrieval/LLM. |
| Email-only auth | Product constraint | No Google SSO or other providers. | `frontend/AGENTS.md`, `docs/guides/supabase-setup.md` | Matches Driftwood internal login requirement. |
| `authenticated` role | Postgres role | Supabase RLS policies target `to authenticated`. | Alembic RLS policies | DB-level access control for anon-key clients. |
| `auth.uid()` | Postgres function | Current Supabase user UUID in RLS policy expressions. | Alembic migration | Enforces per-user chat isolation. |
| Fail fast (config) | Security principle | App refuses to start if required secrets/URLs missing or invalid. | `app/config.py`, `env.ts` | No silent misconfiguration in production. |

---

## 11. Configuration & environment

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| `VITE_API_BASE_URL` | Frontend env | Backend base URL for `apiFetch` (e.g. `http://localhost:8000`). | `frontend/.env`, `src/lib/env.ts` | SPA → FastAPI routing. |
| `VITE_SUPABASE_URL` | Frontend env | Supabase project URL for browser client. | `frontend/.env`, `src/lib/env.ts` | Auth and RLS-scoped reads. |
| `VITE_SUPABASE_ANON_KEY` | Frontend env | Public anon key for browser. | `frontend/.env`, `src/lib/env.ts` | Safe to bundle in frontend. |
| `SUPABASE_URL` | Backend env | Same project URL for server Supabase client. | `backend/.env`, `app/config.py` | Server-side Supabase API. |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend env | Secret key bypassing RLS for ingest and privileged writes. | `backend/.env`, `app/config.py` | Backend-only; highest sensitivity. |
| `DATABASE_URL` | Backend env | Direct Postgres connection for SQLAlchemy/Alembic. | `backend/.env`, `app/config.py` | Migrations and retrieval SQL. |
| `OPENAI_API_KEY` | Backend env | OpenAI credentials for embeddings and chat. | `backend/.env`, `app/config.py` | Required for ingest and chat. |
| `ALLOWED_ORIGINS` | Backend env | Comma-separated CORS origins (default `http://localhost:5173`). | `backend/app/config.py` | Production must include deployed frontend URL. |
| `openai_embedding_model` | Setting | Default `text-embedding-3-small`. | `backend/app/config.py` | Must match between ingest and query embed. |
| `openai_embedding_dimensions` | Setting | Default `1536` — matches `vector(1536)` column. | `backend/app/config.py`, Alembic | Dimension mismatch breaks semantic search. |
| `.env.example` | Template | Documented env var templates for backend and frontend. | `backend/.env.example`, `frontend/.env.example` | Onboarding new developers. |
| `settings` module pattern | Convention | One validated settings module per service; no scattered `getenv`. | `AGENTS.md`, `config.py`, `env.ts` | Prevents config drift and secret leaks. |

---

## 12. DevOps, deployment & tooling

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| Railway | Hosting platform | Planned deployment: separate frontend (static) and backend (Uvicorn) services. | `README.md`, `docs/architecture.md`, Phase 9 | Target production environment. |
| `uv run alembic upgrade head` | Command | Apply all pending DB migrations. | `backend/AGENTS.md`, setup guides | Schema deploy step. |
| `uv run pytest` | Command | Backend test suite (50 tests as of Phase 7). | `backend/tests/`, `docs/todos.md` | CI/local correctness gate. |
| `pnpm dev` | Command | Start Vite dev server for frontend. | `frontend/package.json` | Local UI development. |
| `pnpm build` | Command | Typecheck + production bundle. | `frontend/package.json` | Railway frontend deploy artifact. |
| `pnpm tsc --noEmit` | Command | TypeScript check without emit (frontend verification). | `frontend/AGENTS.md` | No frontend test runner; types are the guard. |
| `ruff` | Linter | Python linter in backend dev deps. | `backend/pyproject.toml` | Code style enforcement. |
| `pyrightconfig.json` | Config | Root Python type-checking configuration. | `pyrightconfig.json` | Cross-package type analysis. |
| `AGENTS.md` | Documentation | Source of truth for coding agents: stack, layout, policies. | Root, `backend/`, `frontend/` | Onboarding AI and human contributors. |
| `implementation-plan/` | Documentation | Phased build plans, testing plans, issue logs. | `implementation-plan/*.md` | Historical build sequence and decisions. |
| `docs/` | Folder | Specs, briefs, architecture, setup guides, this glossary. | `docs/` | Non-code project knowledge. |
| `data/` | Folder | Corpus scripts, downloads (gitignored), markdown (gitignored). | `data/` | Local SEC sample data pipeline. |
| Gitignored payloads | Policy | Downloaded filings and converted markdown not committed. | `.gitignore`, `README.md` | Keeps repo small; manifest + scripts stay in git. |
| `verify_schema.py` | Script | Validates DB schema expectations against Supabase. | `backend/scripts/verify_schema.py` | Post-migration verification. |

---

## 13. Testing

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| Unit test (backend) | Testing | Fast, mocked tests; default `pytest -m "not integration"`. | `backend/tests/`, `backend/AGENTS.md` | Required coverage: ingest, retrieval, grounding. |
| Integration test | Testing | Live OpenAI/Supabase tests behind `@pytest.mark.integration`. | `backend/AGENTS.md` | Optional; needs real credentials. |
| `tests/corpus_ingest/` | Test package | Chunking and metadata unit tests (renamed from `tests/ingest/` to avoid shadowing). | `backend/tests/corpus_ingest/` | Ingest logic verification. |
| `tests/grounding/` | Test package | Grounding validator contract tests. | `backend/tests/grounding/test_validator.py` | Trust enforcement regression safety. |
| `tests/retrieval/` | Test package | RRF fusion and schema/assembly tests. | `backend/tests/retrieval/` | Hybrid search correctness. |
| `tests/chat/` | Test package | Messages, citations metadata, orchestrator, streaming shape. | `backend/tests/chat/` | Chat API and SSE contract. |
| No frontend tests | Policy | Manual browser verification + `tsc` + `eslint` only. | `frontend/AGENTS.md` | Explicit project choice. |
| Analyst evaluation question bank | Manual QA | Structured questions per ticker for pilot pass/refusal/fail scoring. | `implementation-plan/analyst-evaluation-question-bank.md` | Phase 7–8 trust validation. |
| `pilot-evaluation-log.md` | Manual QA | Template to record pilot analyst runs and outcomes. | `implementation-plan/pilot-evaluation-log.md` | Evidence for definition of done. |
| Pass / Refusal / Fail | QA labels | Manual test outcomes for cited answers, honest gaps, or broken trust. | Analyst question bank | Standardized pilot evaluation. |
| MT-1 / MT-2 | Manual test IDs | Phase 7/8 manual browser pass checklist items. | `docs/todos.md`, phase-eight-testing-plan | Gate before pilot deploy. |
| Mocked LLM in unit tests | Testing pattern | Orchestrator/API tests mock agent; grounding contract tested separately. | `tests/chat/test_orchestrator.py` | Fast CI without OpenAI spend. |

---

## 14. Data corpus & SEC domain

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| SEC | Regulatory body | US Securities and Exchange Commission; publishes EDGAR filings. | `docs/client-brief.md`, `data/download.py` | Source of all corpus documents. |
| EDGAR | Data system | SEC Electronic Data Gathering, Analysis, and Retrieval system. | `data/download.py`, manifest `source` | Public filing download API. |
| 10-K | Filing type | Annual report SEC filing; primary corpus type in sample (10-Q planned in brief scope). | `docs/client-brief.md`, `download.py` | Dominant document type for analyst intake. |
| 10-Q | Filing type | Quarterly report; in client brief corpus scope but **not** in current sample ingest. | `docs/client-brief.md` | Future corpus expansion. |
| Ticker | Finance symbol | Stock symbol (AAPL, MSFT, NVDA, AMZN, GOOGL in sample). | Tables, filters, UI labels | Primary company filter in retrieval tools. |
| CIK | SEC identifier | Central Index Key — numeric company ID for EDGAR API (e.g. AAPL `0000320193`). | `data/download.py` `COMPANY_CIKS` | Download script company lookup. |
| Fiscal year | Time dimension | Company's reporting year (2021–2025 in sample corpus). | `source_documents.fiscal_year`, agent filters | Multi-year analyst questions. |
| Accession number | Filing ID | SEC unique filing identifier; used in `stable_chunk_id` prefix. | `source_documents`, manifest | Stable document identity across downloads. |
| MD&A | Report section | Management's Discussion and Analysis — common analyst focus area. | `docs/client-brief.md`, example questions | Typical retrieval target for narratives. |
| Risk factors | Report section | Item 1A risk disclosures; tracked for wording changes over years. | Client brief example questions | Trend/comparison questions in pilot bank. |
| AWS | Business segment | Amazon Web Services — frequent comparison segment in AMZN questions. | Analyst question bank | Realistic retrieval stress test. |
| S&P 500 | Index scope | Client brief long-term corpus target; sample uses five mega-cap names. | `docs/client-brief.md` | Corpus expansion north star. |
| `USER_AGENT` | SEC requirement | Download script must identify requester with contact email per SEC fair access policy. | `data/download.py` | Required for legal EDGAR access. |
| `manifest.json` fields | Data schema | `accession_number`, `source_url`, `local_path`, `report_date`, `filing_date`, etc. | `data/downloads/manifest.json` | Traceability from DB row to source file. |

---

## 15. Implementation phases & process

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| Phase 0 | Implementation | Local toolchain + accounts (Python, uv, Node, pnpm, Supabase, OpenAI). | `docs/todos.md` | Prerequisites for all work. |
| Phase 1 | Implementation | Backend scaffold + Alembic schema + RLS. | `docs/todos.md`, phase-one plan | DB contract for everything else. |
| Phase 2 | Implementation | Auth shell: JWT verification, frontend login, API client. | `docs/todos.md` | Security foundation. |
| Phase 3 | Implementation | Stubbed chat vertical slice (no real LLM/retrieval). | `docs/todos.md` | Proves threads, SSE, persistence early. |
| Phase 4 | Implementation | Corpus download, Docling conversion, full ingest. | `docs/todos.md` | Indexed filings required before RAG. |
| Phase 5 | Implementation | Hybrid retrieval (pgvector + full-text + RRF). | `docs/todos.md` | Evidence layer for agent. |
| Phase 6 | Implementation | PydanticAI agent, grounding validator, real stream. | `docs/todos.md` | Replaces Phase 3 stub. |
| Phase 7 | Implementation | Citations UI, trust banners, grounding Sprint A fixes. | `docs/todos.md` | Analyst-facing trust UX. |
| Phase 8 | Implementation | Pilot readiness: logging, timeouts, evaluation, docs. | `docs/todos.md` | Gate before Railway deploy. |
| Phase 9 | Implementation | Railway deploy + analyst pilot. | `docs/todos.md` | Production path. |
| Sprint A | Process label | Grounding fixes: validator tolerance, instructions, orchestrator normalization. | `docs/todos.md`, phase-seven-fix.md | Targeted trust hardening batch. |
| Stubbed chat | Implementation state | Phase 3 `POST /chat/stream` returning fixed template without OpenAI. | `backend/app/chat/streaming.py` `STUB_REPLY_TEMPLATE` | Superseded by Phase 6 agent stream. |
| `development` branch | Git workflow | Local integration branch for Phases 4–7 (per todos snapshot). | `docs/todos.md` | Coordination note for contributors. |
| Dependency policy | Engineering rule | Prefer stdlib/small code; justify every new package in commit message. | `AGENTS.md` | Controls bundle size and supply-chain risk. |
| `corpus-vs-openai.md` | Explainer doc | Clarifies corpus (evidence) vs OpenAI (embed + write) roles. | `docs/guides/general-questions/` | Stakeholder FAQ for architecture reviews. |

---

## 16. Acronyms & abbreviations

| Term | Category | Definition | Where Used | Why It Matters |
|------|----------|------------|------------|----------------|
| API | Acronym | Application Programming Interface — HTTP JSON endpoints between SPA and FastAPI. | Throughout | Core integration layer. |
| SPA | Acronym | Single Page Application — the React frontend. | `frontend/AGENTS.md` | Distinguishes from SSR/Next.js. |
| JWT | Acronym | JSON Web Token — Supabase session credential. | Auth docs, `http.ts` | Request authentication mechanism. |
| RLS | Acronym | Row Level Security — Postgres per-row access policies. | Alembic migration, Supabase skill | Multi-user data isolation. |
| RRF | Acronym | Reciprocal Rank Fusion — hybrid search merge algorithm. | `backend/app/retrieval/fusion.py` | Key retrieval term in code and docs. |
| RAG | Acronym | Retrieval-Augmented Generation — LLM answers grounded in retrieved docs. | Architecture docs | Industry label for this app's pattern. |
| SSE | Acronym | Server-Sent Events — one-way HTTP streaming to browser. | `streaming.py` | Chat response transport. |
| ORM | Acronym | Object-Relational Mapping — SQLAlchemy models. | `backend/app/database/models/` | Schema definition approach. |
| CIK | Acronym | Central Index Key (SEC company identifier). | `data/download.py` | EDGAR downloads. |
| SEC | Acronym | Securities and Exchange Commission. | Client brief, data pipeline | Regulatory source of corpus. |
| EDGAR | Acronym | SEC's public filings database/API. | `data/download.py` | Download source. |
| PM | Acronym | Portfolio Manager — institutional consumer of research. | Client brief | Answer audience shorthand. |
| MD&A | Acronym | Management's Discussion and Analysis (10-K section). | Example questions | Common filing section label. |
| CapEx | Acronym | Capital expenditures — frequent comparison topic in filings. | Client brief questions | Typical analyst query theme. |
| FY | Abbreviation | Fiscal year (e.g. FY2024). | Ingest logs, UI labels | Time axis for multi-year questions. |
| HNSW | Acronym | Hierarchical Navigable Small World — vector index algorithm in pgvector. | Alembic migration | Semantic search performance. |
| GIN | Acronym | Generalized Inverted Index — Postgres index type for full-text/JSONB. | Alembic migration | Lexical search performance. |
| JSONB | Acronym | Binary JSON Postgres column type for `message_json`, `chunk_metadata`. | Schema migration | Flexible structured metadata storage. |
| tsvector | Postgres type | Full-text search document representation; generated from `chunk_text`. | `search_vector` column | Lexical retrieval channel. |
| UUID | Identifier format | Universal unique identifier for threads, messages, chunks. | All primary keys | Standard ID type across stack. |
| CORS | Acronym | Cross-Origin Resource Sharing. | `main.py`, config | Browser-to-backend security header policy. |
| ASGI | Acronym | Asynchronous Server Gateway Interface — Python async web server standard (Uvicorn). | Backend stack | FastAPI runtime interface. |
| DI | Pattern | Dependency Injection — FastAPI `Depends()` for retriever, auth, Supabase client. | `api/chat.py` | Testable, request-scoped services. |

---

## Repository folder map (quick reference)

| Path | Responsibility |
|------|----------------|
| `AGENTS.md` | Universal agent/coding rules for the monorepo |
| `README.md` | Project overview, stack table, prerequisites |
| `docs/` | Architecture, client brief, setup guides, todos, this glossary |
| `backend/app/` | FastAPI application: API, auth, chat, assistant, retrieval, grounding, database |
| `backend/ingest/` | Offline corpus ingestion pipeline |
| `backend/alembic/` | Database migrations |
| `backend/tests/` | Backend unit tests (pytest) |
| `backend/scripts/` | Smoke tests and schema verification |
| `frontend/src/` | React SPA: pages, components, lib, hooks |
| `data/` | SEC download script, Markdown conversion, local corpus (payloads gitignored) |
| `implementation-plan/` | Phased plans, testing plans, evaluation logs, issue logs |

---

*Generated from repository scan: source code, migrations, READMEs, architecture docs, client brief, implementation plans, ingest/retrieval READMEs, agent instructions, and configuration files. Update this appendix when introducing new modules, tables, API routes, or product terms.*
