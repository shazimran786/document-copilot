# Phase 4 ingestion — issues found and fixed

Log of errors encountered while building and running the corpus ingest pipeline (`backend/ingest/`). Use this when re-ingesting, upgrading Docling, or onboarding someone to operate the CLI.

Related: [phase-four-implementation-plan.md](../../implementation-plan/phase-four-implementation-plan.md) · [data/markdown-testing-strategy.md](../../data/markdown-testing-strategy.md)

---

## Verified corpus (2026-06-08)

After full ingest:

| Metric | Value |
|--------|------:|
| `source_documents` | 25 (5 tickers × 5 fiscal years) |
| `document_chunks` | 7,470 |
| Chunks with embeddings | 7,470 (100%) |
| Tickers | AAPL, MSFT, NVDA, AMZN, GOOGL |

CLI:

```powershell
cd backend
uv run python -m ingest.run              # full re-ingest (idempotent)
uv run ingest-corpus --dry-run           # chunk counts only
uv run python -m ingest.run --ticker AAPL
```

---

## Issues during ingestion

### 1. `section_label` exceeds `varchar(255)` (blocking)

| | |
|---|---|
| **When** | Full ingest, filing 6/25 — MSFT FY2025 (`0000950170-25-100235`) |
| **Error** | Postgres `22001`: `value too long for type character varying(255)` |
| **Cause** | Docling Markdown for large MSFT 10-Ks includes very long lines matched as section headings (table rows, TOC artifacts). `document_chunks.section_label` is `String(255)`. |
| **Fix** | `chunking.py` — `_normalize_section_label()` truncates to 255 chars (with `...` suffix when trimmed). |
| **Prevention** | Re-run dry-run on MSFT after chunking changes; spot-check longest `section_label` in Supabase. |

---

### 2. Transient Supabase / HTTP disconnects (intermittent)

| | |
|---|---|
| **When** | Full ingest — NVDA FY2023 (`SSLV3_ALERT_BAD_RECORD_MAC`); GOOGL filings (`Server disconnected`) |
| **Error** | Python SSL alert or Supabase client disconnect mid batch insert |
| **Cause** | Large chunk batches (text + 1536-dim embedding vectors) over PostgREST; transient network blips. |
| **Fix** | `persist.py` — `_execute_with_retry()` with exponential backoff (5 attempts); reduced `CHUNK_BATCH_SIZE` from 50 → **25**. |
| **Recovery** | Re-run ingest for failed ticker only: `uv run python -m ingest.run --ticker GOOGL`. Idempotent per accession. |

---

### 3. Windows console encoding on dry-run output (cosmetic → crash)

| | |
|---|---|
| **When** | `ingest.run --dry-run` on Windows PowerShell |
| **Error** | `'charmap' codec can't encode character '\u2192'` |
| **Cause** | Dry-run log used Unicode arrow `→` in print output. |
| **Fix** | `run.py` — use ASCII `->` in all CLI log lines. |

---

### 4. pytest import shadowing `ingest` package (test infra)

| | |
|---|---|
| **When** | First ingest unit test run |
| **Error** | `ModuleNotFoundError: No module named 'ingest.metadata'` |
| **Cause** | Test directory named `tests/ingest/` shadowed the top-level `ingest` package during collection. |
| **Fix** | Moved tests to `tests/corpus_ingest/`. **Do not** create `tests/ingest/` again. |

---

### 5. Dry-run summary counted chunks as embeddings (logic bug)

| | |
|---|---|
| **When** | `--dry-run` completion summary |
| **Symptom** | Report showed hundreds of “embeddings” despite no OpenAI calls |
| **Cause** | `ingest_filing()` returned `(0, len(chunks))` in dry-run; runner added second value to `embeddings_created`. |
| **Fix** | Dry-run returns `(0, 0)`; chunk count is log-only. |

---

### 6. Accidental merge of `_content_hash` during section_label fix (dev regression)

| | |
|---|---|
| **When** | Re-run after issue #1 fix |
| **Error** | `name '_content_hash' is not defined` |
| **Cause** | Edit accidentally inlined hash logic into `_normalize_section_label`. |
| **Fix** | Restored standalone `_content_hash()` in `chunking.py`. |

---

## Pre-ingest issues (conversion / setup)

These occurred before or outside the Supabase write path but blocked Phase 4 progress.

### 7. Docling via root `uv run` + inline script deps

| | |
|---|---|
| **Error** | `transformers` / FileNotFoundError in isolated script env |
| **Fix** | Run conversion from backend venv: `cd backend && uv run python ../data/convert_to_markdown.py` (`docling==2.96.1` in dev deps). Do not use PEP 723 inline deps on `convert_to_markdown.py`. |

### 8. PowerShell `&&` command chaining

| | |
|---|---|
| **Error** | Parser error on `cd backend && uv run ...` |
| **Fix** | Use `;` in PowerShell: `cd backend; uv run python -m ingest.run` |

---

## Operational notes

| Topic | Recommendation |
|-------|----------------|
| **Idempotent re-run** | Safe to re-run full ingest; documents upsert by `accession_number`, chunks replaced per document. |
| **Partial failure** | Resume with `--ticker TICKER`; completed tickers are overwritten cleanly. |
| **Large filings** | MSFT and GOOGL produce the most chunks (~270–410 per filing); expect longer runs and higher disconnect risk without retry. |
| **OpenAI cost** | ~7,500 embedding calls (batched 64 per request) for full corpus. |
| **Skip embeddings** | `--skip-embeddings` writes chunks without vectors (debug persist only; not valid for Phase 5). |
| **Documents only** | `--documents-only` loads `source_documents` without chunks (useful for smoke test). |

---

## Failure signals (quick reference)

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `varchar(255)` on insert | Long `section_label` | Confirm truncation in `chunking.py`; re-ingest |
| `Server disconnected` / SSL alert | Transient PostgREST / network | Retry ticker ingest; confirm retry logic in `persist.py` |
| Missing `.md` | Conversion not run | `uv run python ../data/convert_to_markdown.py` |
| OpenAI `401` | Bad `OPENAI_API_KEY` | Fix `backend/.env` |
| Empty chunk count | All sections below 50-token floor | Inspect Markdown; adjust `MIN_CHUNK_TOKENS` if needed |
| Duplicate accession rows | Should not happen | Upsert is by `accession_number`; investigate manual DB edits |

---

## Files changed for fixes

| File | Change |
|------|--------|
| `ingest/chunking.py` | `_normalize_section_label()`, max 255 chars |
| `ingest/persist.py` | Retry wrapper, batch size 25 |
| `ingest/run.py` | ASCII logs, dry-run summary fix |
| `tests/corpus_ingest/` | Renamed from `tests/ingest/` |
| `pyproject.toml` | `ingest` package + `ingest-corpus` script entry |
