# Phase 6 agent & chat stream — issues found and fixed

Log of errors encountered while implementing the PydanticAI agent, grounding validator, and real `POST /chat/stream` pipeline. Use this when debugging agent runs, smoke tests, or pytest collection failures.

Related: [phase-six-implementation-plan.md](phase-six-implementation-plan.md) · [phase-five-implementation-plan.md](phase-five-implementation-plan.md) (retrieval) · [backend/scripts/smoke_agent.py](../backend/scripts/smoke_agent.py)

---

## Verified state (after Phase 6 implementation)

| Check | Result |
|-------|--------|
| `uv run pytest -v` | 45 tests passing |
| `uv run python scripts/smoke_agent.py` | Exit 0 (with live `.env` + Supabase + OpenAI) |
| `POST /chat/stream` | Real agent (no stub); same AI SDK SSE event shape |
| Citation persistence | `message_citations` + `message_json.metadata.citations` on successful grounded turns |

Smoke commands:

```powershell
cd backend
uv run pytest tests/grounding tests/assistant tests/chat -v
uv run python scripts/smoke_agent.py
```

---

## Issues fixed during implementation

### 1. pytest collection crash — Agent import without credentials (blocking)

| | |
|---|---|
| **When** | First `uv run pytest` after adding `app/assistant/agent.py` |
| **Error** | `openai.OpenAIError: Missing credentials` during `from app.main import app` → import chain loads `document_agent` at module level |
| **Cause** | `Agent("openai:gpt-4o-mini", ...)` resolves the OpenAI provider immediately and expects `OPENAI_API_KEY` in the process environment. Tests do not always load `backend/.env` before imports. |
| **Fix** | `agent.py` — pass `defer_model_check=True` to `Agent(...)` so model/provider validation is deferred until the first `run()`. |
| **Files** | `backend/app/assistant/agent.py` |

---

### 2. Runtime smoke failure — API key in `.env` but not passed to PydanticAI (blocking)

| | |
|---|---|
| **When** | `uv run python scripts/smoke_agent.py` after fixing issue #1 |
| **Error** | Same `Missing credentials` at `document_agent.run_stream()` / `run()` time |
| **Cause** | PydanticAI’s default OpenAI provider reads `OPENAI_API_KEY` from the OS environment. `pydantic-settings` loads `openai_api_key` from `backend/.env` into `settings`, but does not export it to `os.environ` automatically. |
| **Fix** | Construct the agent with an explicit provider: `OpenAIChatModel(settings.openai_chat_model, provider=OpenAIProvider(api_key=settings.openai_api_key))`. |
| **Files** | `backend/app/assistant/agent.py` |

---

### 3. `stream_text()` incompatible with structured `GroundedAnswer` output (blocking)

| | |
|---|---|
| **When** | Smoke agent after wiring `orchestrator.stream_turn()` with `agent.run_stream()` + `result.stream_text(delta=True)` |
| **Error** | `pydantic_ai.exceptions.UserError: stream_text() can only be used with text responses` |
| **Cause** | Phase 6 plan assumed live token streaming via `run_stream` while `output_type=GroundedAnswer`. PydanticAI only allows `stream_text()` when the final output is plain text, not a Pydantic model. |
| **Fix** | `orchestrator.py` — use `await document_agent.run(prompt, deps=deps)`, then simulate SSE word deltas with `split_text_deltas(grounded_answer.answer)` before validation. SSE shape unchanged; generation completes before deltas emit. |
| **Files** | `backend/app/chat/orchestrator.py` |
| **Plan deviation** | Step 9–10 described `run_stream` + live `stream_text`. Implementation uses `run()` + post-hoc delta chunking until PydanticAI supports streaming structured fields or we split text/structured into two steps. |

---

### 4. `read_surrounding_chunks` tool used DB session after close (latent bug)

| | |
|---|---|
| **When** | Code review of `read_surrounding_chunks` in `agent.py` |
| **Error** | Would raise session/connection errors when the agent calls the tool |
| **Cause** | `chunk_row_to_source_passage(session, neighbor_row)` was called after the `with ctx.deps.session_factory() as session:` block exited. |
| **Fix** | Keep center chunk load, neighbor fetch, and all `chunk_row_to_source_passage` calls inside the same `with session` block. |
| **Files** | `backend/app/assistant/agent.py` |

---

### 5. Circular import risk — `streaming` ↔ `orchestrator` (design)

| | |
|---|---|
| **When** | Moving `split_text_deltas` import into `orchestrator.py` from `streaming.py` |
| **Risk** | `streaming.py` imports `stream_turn` from `orchestrator.py`; importing `split_text_deltas` from `streaming` in `orchestrator` would create a cycle. |
| **Fix** | Move `split_text_deltas()` to `app/chat/messages.py`; both `streaming.py` and `orchestrator.py` import from there. |
| **Files** | `backend/app/chat/messages.py`, `backend/app/chat/streaming.py`, `backend/app/chat/orchestrator.py` |

---

### 6. `HTTPException` inside `StreamingResponse` generator (incorrect pattern)

| | |
|---|---|
| **When** | Initial `post_chat_stream` error handling |
| **Issue** | Raising `HTTPException(status_code=502)` inside the async SSE generator does not set the HTTP response status — the client may already have received `200` with `text/event-stream`. |
| **Fix** | Log and re-raise unexpected exceptions from the generator; rely on outer route-level handling for pre-stream failures (auth, 404 thread, 422 payload). |
| **Files** | `backend/app/api/chat.py` |

---

### 7. Citation metadata shape — UI vs database (data contract)

| | |
|---|---|
| **When** | Persisting `message_citations` and `message_json` together |
| **Issue** | Phase 7 UI expects camelCase in `message_json.metadata.citations`; Postgres `citation_metadata` JSONB should use stable snake_case keys per schema conventions. |
| **Fix** | Split helpers: `build_citation_ui_metadata()` (camelCase) and `build_citation_db_metadata()` (snake_case). |
| **Files** | `backend/app/chat/messages.py`, `backend/app/api/chat.py` |

---

### 8. Assistant message UUID vs wire `messageId` for citation FK (blocking)

| | |
|---|---|
| **When** | Designing `insert_citations(message_id, ...)` |
| **Issue** | Stub used `new_message_id()` → `msg_<hex>` only in `message_json`. `message_citations.message_id` FK requires the real `chat_messages.id` UUID. |
| **Fix** | `TurnResult.message_uuid` assigned before stream; `insert_message(..., message_id=turn_result.message_uuid)`; wire `messageId` in SSE stays human-readable string. |
| **Files** | `backend/app/database/chats.py`, `backend/app/chat/orchestrator.py`, `backend/app/api/chat.py` |

---

### 9. API route tests still targeted stub stream (test update)

| | |
|---|---|
| **When** | `uv run pytest` after replacing stub with `stream_agent_turn` |
| **Issue** | `test_post_stream_returns_ai_sdk_sse` would call live retriever + OpenAI without mocks. |
| **Fix** | Monkeypatch `stream_agent_turn`, `insert_citations`; extend `fake_insert_message` to accept optional `message_id`. |
| **Files** | `backend/tests/api/test_chat_routes.py` |

---

### 10. Orchestrator unit test — word delta assertion (test fix)

| | |
|---|---|
| **When** | `tests/chat/test_orchestrator.py` after switching to `split_text_deltas` |
| **Issue** | Test expected `["AWS ", "margin expanded."]` but `split_text_deltas` emits per-word tokens: `["AWS", " operating", " margin", " expanded."]`. |
| **Fix** | Assert `"".join(deltas) == grounded.answer` instead of matching individual delta strings. |
| **Files** | `backend/tests/chat/test_orchestrator.py` |

---

### 11. Minor lint — unused imports (cleanup)

| | |
|---|---|
| **When** | `uv run ruff check` during Phase 6 |
| **Fix** | Removed unused imports in `agent.py` (`UUID`, `NeighborChunk`) introduced during tool scaffolding. |
| **Files** | `backend/app/assistant/agent.py` |

---

## Known runtime behaviors (not bugs — operational notes)

### A. Grounding validation fallback on LLM excerpt mismatch

| | |
|---|---|
| **When** | Smoke query: *"How did NVIDIA describe Data Center demand drivers?"* |
| **Symptom** | `validation_failed=True`; user sees `GROUNDING_FALLBACK_MESSAGE`; no `message_citations` rows |
| **Cause** | Model returned citations whose `excerpt` is not a whitespace-normalized substring of `chunk_text` (common with table-heavy Docling chunks, paraphrased quotes, or ellipsis). |
| **Mitigation** | Fail-closed by design per Phase 6 plan. Tune prompts, relax validator (fuzzy match), or improve chunk text quality in a later phase. |
| **Files** | `backend/app/grounding/validator.py`, `backend/app/chat/orchestrator.py` |

### B. Config settings added but not all wired yet

| Setting | Status |
|---------|--------|
| `openai_chat_model` | Wired via `OpenAIChatModel` |
| `openai_chat_timeout_seconds` | In `config.py` / `.env.example`; not yet passed to `model_settings` on Agent |
| `agent_max_tool_calls` | In `config.py` / `.env.example`; not yet enforced on Agent tool loop |

Track as follow-up if turns hang or tool loops run too long.

---

## Failure signals during manual / smoke testing

| Symptom | Likely cause | Check |
|---------|--------------|-------|
| pytest fails on `import app.main` | OpenAI provider init at import | `defer_model_check=True` present in `agent.py` |
| Smoke: Missing credentials | `.env` not loaded or key not passed to provider | `settings.openai_api_key` + `OpenAIProvider(api_key=...)` |
| Smoke: `stream_text()` UserError | Structured output + `stream_text` | Should use `agent.run()` in `orchestrator.py` |
| Chat stream 200 but empty assistant | Agent exception mid-generator | Backend logs: `Agent chat stream failed` |
| Answer streams but no citations in DB | Grounding validation failed | `validation_failed=True` in logs; check excerpt grounding |
| `502` on thread/message insert | Supabase RLS or FK | User exists in `public.users`; `message_id` UUID matches insert |

---

## Definition of done (issues log)

- [x] Import-time OpenAI credentials crash documented and fixed
- [x] Runtime API key wiring from `settings` documented and fixed
- [x] Structured-output streaming limitation documented and workaround recorded
- [x] Tool session-scope bug fixed
- [x] Test and persistence contract fixes recorded
- [ ] Optional: wire `openai_chat_timeout_seconds` and `agent_max_tool_calls` into Agent `model_settings` / usage limits
- [ ] Optional: soften excerpt grounding for table-heavy chunks if fallback rate is too high in pilot
