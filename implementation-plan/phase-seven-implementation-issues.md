# Phase 7 — testing results & issues log

**Tested:** 2026-06-09  
Related: [phase-seven-testing-plan.md](phase-seven-testing-plan.md) · [phase-seven-implementation-plan.md](phase-seven-implementation-plan.md) · [phase-six-implementation-issues.md](phase-six-implementation-issues.md)

---

## Executive summary

| Layer | Result | Notes |
|-------|--------|-------|
| Backend unit tests | **PASS** | 47/47 (`uv run pytest -v`) |
| Frontend `tsc --noEmit` | **PASS** | |
| Frontend `eslint` | **PASS** | |
| Frontend `pnpm build` | **FAIL** | Pre-existing TS5101 `baseUrl` deprecation in `tsconfig.app.json` |
| `smoke_retrieval.py` | **PASS** | All 5 queries return passages |
| `smoke_agent.py` | **EXIT 0** | 2/3 client-brief queries **failed grounding** — no citations persisted |
| Browser manual (MT-1–MT-6) | **NOT RUN** | Requires interactive session; blocked on grounding failures for cited-answer path |

**Bottom line:** Phase 7 UI code is in place, but **citation chips will not appear** for common analyst questions until Phase 6 grounding issues (#1, #2 below) are fixed. Refusal path (Q10) works end-to-end.

---

## Automated test results

### Backend — `uv run pytest -v`

```
47 passed in 0.57s
```

New Phase 7 metadata tests pass:

- `passageText` in UI citation metadata
- `insufficientEvidence` / `validationFailed` flags

### Frontend

| Command | Result |
|---------|--------|
| `pnpm tsc --noEmit` | Pass |
| `pnpm lint` | Pass |
| `pnpm build` | Fail — `TS5101: Option 'baseUrl' is deprecated` |

### Live smoke — `smoke_retrieval.py`

Exit **0**. Hybrid retrieval healthy (semantic + fulltext + fusion).

### Live smoke — `smoke_agent.py`

Exit **0** (script counts failures per query, not process exit on validation).

| Query | `validation_failed` | `insufficient_evidence` | `citations` | UI expectation |
|-------|--------------------:|------------------------:|------------:|----------------|
| AMZN / AWS operating margin | **True** | True | 0 | Amber “could not verify citations” banner; **no chips** |
| NVDA / Data Center demand | **True** | True | 0 | Same |
| Generative AI improved margins (Q10) | False | **True** | 0 | Blue “not in corpus” banner; **no chips** ✓ |

**Grounding errors (from logs):**

1. `Citation stable_chunk_id '0001018724-22-000005' does not match passage '0001018724-22-000005:60'.`
2. `Citation excerpt for 0001045810-23-000017:10 is not grounded in the passage text.`

---

## Issues found

### 1. `stable_chunk_id` mismatch — agent cites accession only (blocking MT-1)

| | |
|---|---|
| **Severity** | P0 — blocks cited answers |
| **When** | Smoke Q1: Amazon / AWS operating margin |
| **Symptom** | `validation_failed=True`; fallback message; no `metadata.citations` in UI |
| **Cause** | Model returned `stable_chunk_id` = accession number only; ingest format is `{accession}:{chunk_index}` (e.g. `0001018724-22-000005:60`). Validator strict string equality fails. |
| **Files** | `app/grounding/validator.py`, `app/assistant/instructions.md`, `app/assistant/agent.py` |

### 2. Excerpt not substring of `chunk_text` — table-heavy Docling chunks (blocking MT-3)

| | |
|---|---|
| **Severity** | P0 — blocks cited answers |
| **When** | Smoke Q2: NVIDIA Data Center demand |
| **Symptom** | `validation_failed=True`; excerpt grounding failure |
| **Cause** | Whitespace-normalized `excerpt` not found in `chunk_text` — common with pipe tables, merged cells, paraphrased quotes. Documented in phase-six-issues §A. |
| **Files** | `app/grounding/validator.py`, optionally `app/assistant/instructions.md` |

### 3. Post-stream hydration has no error handling (UI robustness)

| | |
|---|---|
| **Severity** | P1 |
| **When** | `getThreadMessages` fails after stream completes |
| **Symptom** | Unhandled promise rejection; citations never appear until manual refresh |
| **Cause** | `handleStreamComplete()` in `ChatPage.tsx` has no try/catch |
| **Files** | `frontend/src/pages/ChatPage.tsx` |

### 4. Full `ChatPanel` remount on hydration (UX)

| | |
|---|---|
| **Severity** | P2 |
| **When** | Stream finishes; `hydrationKey` increments |
| **Symptom** | Possible scroll jump, composer focus loss, brief flicker |
| **Cause** | `key={threadId}-${hydrationKey}` forces remount instead of merging metadata in place |
| **Files** | `frontend/src/pages/ChatPage.tsx`, `frontend/src/components/chat/ChatPanel.tsx` |

### 5. Production build broken (tooling)

| | |
|---|---|
| **Severity** | P2 — blocks Phase 9 deploy |
| **When** | `pnpm build` |
| **Symptom** | `tsc -b` fails on deprecated `baseUrl` |
| **Files** | `frontend/tsconfig.app.json` |

### 6. Manual browser pass not completed

| | |
|---|---|
| **Severity** | P1 — Phase 7 DoD |
| **When** | MT-1–MT-6 in [phase-seven-testing-plan.md](phase-seven-testing-plan.md) |
| **Status** | Unchecked in `docs/todos.md` |
| **Blocker** | Issues #1–#2 prevent successful MT-1/MT-3 until fixed |

---

## Fix plan (recommended order)

### Sprint A — Restore cited answers (P0, backend)

**Goal:** `smoke_agent.py` Q1 and Q2 return `validation_failed=False` with `citations >= 1`.

#### A1. Auto-correct `stable_chunk_id` when `chunk_id` is valid

In `GroundingValidator.validate()` (or a pre-validate normalizer in `orchestrator.py`):

- If `citation.chunk_id` exists in `allowed_passages`, **overwrite** `citation.stable_chunk_id` with `passage.stable_chunk_id` before comparison, OR skip stable_id check when chunk_id matches.
- Rationale: `chunk_id` is the authoritative FK; stable_id is a display anchor.

**Test:** New unit test in `tests/grounding/test_validator.py` — mismatched stable_id but valid chunk_id passes after normalization.

#### A2. Loosen excerpt grounding for table markdown

In `validator.py` `_normalize_text()` or a dedicated `_excerpt_is_grounded()`:

1. Strip `|` pipe characters and collapse whitespace (Docling tables).
2. If strict substring still fails, try matching on first 40 chars of excerpt.
3. Optional: allow match in neighbor chunk text if center chunk is table-only.

**Test:** `test_validator_accepts_excerpt_with_table_pipe_normalization`

#### A3. Strengthen agent instructions (low risk, additive)

In `instructions.md`:

```
- stable_chunk_id must be copied exactly from passages (format: accession_number:chunk_index, e.g. 0001018724-22-000005:60). Never use the accession number alone.
- excerpt must be a verbatim substring from the passage text (copy-paste, do not paraphrase).
```

**Verify:** Re-run `uv run python scripts/smoke_agent.py` — target 2/3 cited, 1/3 refusal.

---

### Sprint B — UI hardening (P1, frontend)

#### B1. Error handling in `handleStreamComplete`

```typescript
try {
  await refetchThreads()
  const freshMessages = await getThreadMessages(threadId)
  setInitialMessages(freshMessages)
  setHydrationKey((k) => k + 1)
} catch {
  // surface toast/banner: "Answer saved but sources could not load — refresh"
}
```

#### B2. Prefer metadata merge over remount (optional)

If `@ai-sdk/react` `useChat` exposes `setMessages`, merge last assistant message metadata instead of bumping `hydrationKey`. Reduces flicker.

---

### Sprint C — Tooling & DoD (P2)

#### C1. Fix `pnpm build`

Add to `frontend/tsconfig.app.json`:

```json
"ignoreDeprecations": "6.0"
```

Or migrate off deprecated `baseUrl` per TS 6 guidance.

#### C2. Complete manual pass

After Sprint A, run MT-1 → MT-3 → MT-2 in browser; tick Phase 7 manual item in `docs/todos.md`.

#### C3. Add smoke assertion (optional)

Extend `smoke_agent.py` to exit 1 if cited queries return `validation_failed=True` (stricter CI gate).

---

## What already works (no fix needed)

- Citation metadata shape (`passageText`, flags) — unit tested
- Refusal path (Q10): `insufficientEvidence` without `validationFailed`
- `TrustStatusBanner` priority: validation failed shown before insufficient evidence
- `SourcePassagePanel` fallback when `passageText` missing (uses `excerpt`)
- Post-stream refetch architecture (persist completes before SSE `finish`)

---

## Verification checklist (after fixes)

```powershell
cd backend
uv run pytest tests/grounding/ -v
uv run python scripts/smoke_agent.py   # expect citations on Q1 or Q2

cd ../frontend
pnpm tsc --noEmit
pnpm build                              # after C1
pnpm dev                                # manual MT-1, MT-2, MT-3
```

| Check | Expected |
|-------|----------|
| AMZN margin query | Citation chips + passage panel |
| NVDA demand query | Citation chips or honest limitation (not validation fallback) |
| Q10 refusal | Blue banner only |
| Page refresh | Citations persist |
