# Corpus vs OpenAI — what each part does

**General question:** All data comes from our SEC filing corpus, so why do we make OpenAI API calls? What role does OpenAI play?

**Short answer:** The **corpus** (Supabase) is the **evidence**. OpenAI is the **search assistant** (embeddings) and **writer** (chat model). It does not store your filings or replace the database.

Related: [architecture.md](../../architecture.md) · [backend/ingest/README.md](../../../backend/ingest/README.md) · [backend/app/retrieval/README.md](../../../backend/app/retrieval/README.md)

---

## Mental model

```
Your corpus (Supabase)  = the library (SEC filing text + vectors)
OpenAI                  = the librarian + writer
```

- **Corpus** — what the filings actually say (chunk text, metadata, embeddings, full-text index).
- **OpenAI** — how you find the right passages and turn them into a readable, cited answer for analysts.

---

## Two kinds of OpenAI API calls

### 1. Embeddings API (`text-embedding-3-small`)

**Purpose:** Convert text into a numeric vector so similar meaning sits close together in vector space.

| When | Code | What happens |
|------|------|----------------|
| **Ingest (offline)** | `backend/ingest/embeddings.py` | Every filing chunk is embedded once and stored in `document_chunks.embedding`. |
| **Every chat question** | `backend/app/retrieval/embed.py` | Your question is embedded and compared to stored chunk vectors. |

**Why:** Semantic search. A question like “AWS operating margin” may not share exact words with the filing, but embeddings can still surface relevant chunks.

**Note:** Full-text keyword search uses Postgres `search_vector` — **no OpenAI** for that channel.

Default settings (`backend/app/config.py`):

- Model: `text-embedding-3-small`
- Dimensions: `1536`

---

### 2. Chat API (`gpt-4o-mini` via PydanticAI)

**Purpose:** Read retrieved passages, reason over them, optionally call tools, and return a structured `GroundedAnswer` (prose + citations).

| When | Code | What happens |
|------|------|----------------|
| **Every chat question** | `backend/app/assistant/agent.py` | Agent generates the analyst-facing answer. |

The agent may trigger **additional** work (and more OpenAI round-trips) via tools:

| Tool | Effect |
|------|--------|
| `search_filings` | Runs retrieval again (embedding + Supabase) |
| `read_chunk` | Fetches one chunk from Supabase |
| `read_surrounding_chunks` | Fetches neighbor chunks from Supabase |

**Why:** The corpus is thousands of raw chunks. OpenAI:

- Synthesizes across passages (e.g. compare five companies)
- Writes clear prose for analysts
- Produces citations (`chunk_id`, excerpt, etc.)
- Can set `insufficient_evidence` when the corpus does not support an answer

Retrieval alone cannot do that — it only returns text snippets.

---

## End-to-end flow for one question

```
You type a question
        │
        ▼
┌───────────────────────────────────────┐
│  OPENAI #1 — Embeddings API           │  Embed your question
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  SUPABASE — Hybrid retrieval          │  pgvector + full-text (no OpenAI)
│  Top filing passages                  │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  OPENAI #2+ — Chat API (agent)        │  Answer + citations; tools optional
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  Grounding validator (Python)         │  No OpenAI — checks citation rules
└───────────────────────────────────────┘
        │
        ▼
   Streamed answer in the UI
```

---

## What does *not* use OpenAI

| Component | Source |
|-----------|--------|
| Filing text | Corpus — `document_chunks.chunk_text` |
| Full-text search | Postgres `tsvector` on `search_vector` |
| Citation rows | Supabase `message_citations` |
| Chat history | Supabase `chat_messages` |
| Grounding validation | `backend/app/grounding/validator.py` |
| User login | Supabase Auth |

---

## Caching and repeat questions

| Action | New OpenAI calls? |
|--------|-------------------|
| Ask a question (first time) | **Yes** — embedding + chat (+ tools if used) |
| Ask the **same** question again | **Yes** — full pipeline runs again; no answer cache |
| Reload / reopen a thread | **No** — UI loads stored messages from Supabase only |

Ingest embeddings are computed **once per chunk** (until re-ingest). Query embeddings and chat runs happen **on every send**.

---

## Cost pattern (rough)

| Activity | OpenAI usage |
|----------|----------------|
| Full corpus ingest (~7,500 chunks) | Many embedding batches (one-time per ingest) |
| Each analyst question | 1 embedding call + 1 or more chat calls |
| Browsing old threads | None |

---

## One-line summary

**Corpus = evidence. OpenAI = find relevant evidence (embeddings) and write a grounded, cited answer (chat).**

Without OpenAI you would still have filings in the database, but you would lose semantic search quality and natural-language answers with citations — the core product value for Driftwood analysts.
