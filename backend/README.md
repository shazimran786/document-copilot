# Backend

FastAPI service for Document Copilot. See [../docs/guides/backend-setup.md](../docs/guides/backend-setup.md) for full setup.

## First time

```bash
cd backend
cp .env.example .env   # fill in Supabase, DATABASE_URL (direct), OpenAI
uv sync
```

`DATABASE_URL` must use Supabase's **direct** connection (`db.<ref>.supabase.co`), not the pooler.

## Run the API

```bash
cd backend
uv run uvicorn app.main:app --reload
```

Or:

```bash
uv run python app/main.py
```

- API: http://localhost:8000
- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs

## Config

All env vars live in `.env` and load through `app.config.settings`. The app fails on startup if required values are missing or invalid.

## Migrations

Schema is managed by Alembic. The initial migration lives at
`alembic/versions/ab03722082e4_initial_schema.py`.

**Before applying** (from `backend/`):

1. Confirm `DATABASE_URL` in `.env` uses the **direct** Supabase host (`db.<ref>.supabase.co`), not the pooler.
2. Review the migration file — it creates tables, `vector` extension, `search_vector` tsvector, HNSW/GIN indexes, RLS policies, and the sign-up trigger.
3. Optional dry-run: `uv run alembic upgrade head --sql` prints SQL without executing it.

**Apply to Supabase** (when ready):

```bash
uv run alembic upgrade head
```

**Verify** in the Supabase dashboard → Table Editor: `users`, `source_documents`, `document_chunks`, `chat_threads`, `chat_messages`, `message_citations`.

## Lint & test

```bash
uv run ruff check .
uv run pytest
```
