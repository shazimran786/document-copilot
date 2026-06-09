# Phase 7 — Citations UI testing plan

Validate that analysts can **see, click, and verify** citations in the browser before Phase 8 hardening and Phase 9 deploy.

Related: [phase-seven-implementation-plan.md](phase-seven-implementation-plan.md) · [phase-six-testing-plan.md](phase-six-testing-plan.md) · [docs/client-brief.md](../docs/client-brief.md)

---

## Testing strategy

Phase 7 is **frontend-heavy**. Per [frontend/AGENTS.md](../frontend/AGENTS.md):

- **No** Vitest, Playwright, or Cypress
- **Yes** `pnpm tsc --noEmit`, `pnpm lint`, manual browser passes
- **Yes** backend unit tests for extended citation metadata shape

Layer tests so backend contracts are locked before UI work, then verify the full analyst flow manually.

---

## Pre-flight (before starting Phase 7 UI)

Confirm Phase 6 handoff criteria from [phase-six-testing-plan.md](phase-six-testing-plan.md):

```powershell
cd backend
uv run pytest -v
uv run python scripts/smoke_retrieval.py
uv run python scripts/smoke_agent.py
```

| Check | Expected |
|-------|----------|
| `pytest` | All tests pass (45+) |
| `smoke_retrieval.py` | Exit 0 |
| `smoke_agent.py` | Exit 0; AMZN query has `citations >= 1`; refusal query has `insufficient_evidence=True` |

**Blocks Phase 7 UI if:** smoke agent fails or `GET /chat/threads/{id}/messages` returns assistant messages without `metadata.citations` on grounded turns.

---

## Automated checks (CI-safe)

### Backend — citation metadata contract

**File:** `backend/tests/chat/test_messages_citations.py`

Add cases after implementing Step 1:

| Test | Assert |
|------|--------|
| `test_ui_metadata_includes_passage_text` | `metadata.citations[0]["passageText"]` equals chunk text |
| `test_ui_metadata_insufficient_evidence_flag` | `metadata.insufficientEvidence is True` when set |
| `test_ui_metadata_validation_failed_flag` | `metadata.validationFailed is True` on grounding fallback message |
| `test_insufficient_evidence_has_empty_citations` | `citations == []` when `insufficientEvidence` |

Run:

```powershell
cd backend
uv run pytest tests/chat/test_messages_citations.py -v
```

### Frontend — static analysis

```powershell
cd frontend
pnpm tsc --noEmit
pnpm lint
pnpm build
```

| Check | Expected |
|-------|----------|
| `tsc` | No type errors on `CitationMetadata` / `AssistantMessageMetadata` |
| `lint` | Clean |
| `build` | Production bundle succeeds |

---

## Manual test matrix

**Environment:** Both services running with live `.env`:

```powershell
# Terminal 1
cd backend && uv run uvicorn app.main:app --reload

# Terminal 2
cd frontend && pnpm dev
```

Browser: http://localhost:5173 — signed in as test user.

### MT-1 — Grounded answer with citations

| Step | Action | Expected |
|------|--------|----------|
| 1 | New thread | Empty state shows real-corpus prompt (no “stub” copy) |
| 2 | Ask: `For Amazon, what did the filing say about AWS operating margin?` | Answer streams token-by-token |
| 3 | Wait for stream to finish | Citation chips appear **without** page refresh |
| 4 | Inspect first chip | Shows Amazon / 10-K / fiscal year / section label |
| 5 | Click chip | Passage panel opens |
| 6 | Read panel | Excerpt matches grounded quote; full passage text visible; SEC link works |
| 7 | Refresh browser | Same citations and panel content from `GET .../messages` |

**Pass:** Chips visible, panel shows excerpt + passage, SEC link opens.

### MT-2 — Insufficient evidence (client-brief Q10)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Ask: `Do the filings prove that generative AI improved margins for any company?` | Stream completes |
| 2 | Inspect message | Amber/info “not in corpus” / insufficient evidence banner |
| 3 | Inspect message | **No** citation chips |
| 4 | Refresh | Banner persists; still no chips |

**Pass:** Honest refusal is visually distinct; no fabricated citations.

### MT-3 — Multi-citation answer

| Step | Action | Expected |
|------|--------|----------|
| 1 | Ask: `How did NVIDIA describe Data Center demand drivers?` | Answer with 1+ citations |
| 2 | Click each chip | Panel updates to correct filing / excerpt |
| 3 | Compare `claimIndex` order | Chips numbered consistently |

**Pass:** Multiple chips work; panel switches correctly.

### MT-4 — Grounding validation fallback (if reproducible)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Ask a narrow question that sometimes triggers excerpt mismatch | May get fallback message |
| 2 | If fallback appears | “Could not verify citations” styling (`validationFailed`) |
| 3 | Inspect | No citation chips; no `message_citations` in DB |

**Pass:** Fallback distinguishable from insufficient evidence.

*Note:* This case is intermittent. If hard to reproduce, verify via backend test `validationFailed` flag and skip live repro.

### MT-5 — Thread history

| Step | Action | Expected |
|------|--------|----------|
| 1 | Complete MT-1 and MT-2 in same thread | Mixed grounded + refusal messages |
| 2 | Switch to another thread and back | Citations render correctly |
| 3 | Sign out → sign in → reopen thread | History intact with citations |

**Pass:** Persistence across navigation and sessions.

### MT-6 — Accessibility spot-check

| Step | Action | Expected |
|------|--------|----------|
| 1 | Tab to citation chips | Focus ring visible |
| 2 | Enter on focused chip | Panel opens |
| 3 | Escape | Panel closes |

**Pass:** Keyboard-only citation verify is possible.

---

## API verification (devtools / curl)

Useful when UI looks wrong — confirm backend payload first.

```powershell
# After a grounded turn, inspect persisted message_json
# Supabase Table Editor → chat_messages → message_json column
```

| Field path | Grounded success | Insufficient evidence | Validation failed |
|------------|------------------|----------------------|-------------------|
| `metadata.citations` | Non-empty array | `[]` or absent | absent / `[]` |
| `metadata.citations[0].passageText` | Full chunk text | — | — |
| `metadata.insufficientEvidence` | `false` | `true` | `true` (fallback) |
| `metadata.validationFailed` | `false` | `false` | `true` |
| `message_citations` rows | 1+ per citation | 0 | 0 |

Or via API:

```powershell
# Bearer token from browser session
curl -H "Authorization: Bearer <token>" http://localhost:8000/chat/threads/<thread-id>/messages
```

---

## Regression checks (must stay green)

After Phase 7 changes:

```powershell
cd backend
uv run pytest -v
uv run python scripts/smoke_agent.py

cd ../frontend
pnpm tsc --noEmit && pnpm lint && pnpm build
```

| Suite | Why |
|-------|-----|
| Full `pytest` | Metadata changes must not break chat API tests |
| `smoke_agent.py` | Agent + grounding unchanged in behavior |
| Frontend build | No broken imports from new components |

---

## Definition of done (Phase 7 testing)

- [ ] `test_messages_citations.py` extended and passing
- [ ] `pnpm tsc --noEmit` + `pnpm lint` + `pnpm build` pass
- [ ] MT-1 grounded citation flow passes
- [ ] MT-2 insufficient evidence flow passes
- [ ] MT-3 multi-citation panel switching passes
- [ ] MT-5 thread history / refresh passes
- [ ] API spot-check: `metadata.citations` + `passageText` on success path
- [ ] `docs/todos.md` Phase 7 items ticked

---

## Failure signals (quick reference)

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Answer streams but no chips after finish | Post-stream refetch not wired | Fix `ChatPanel.onFinish` hydration |
| Chips on refresh only | Same as above | Merge metadata after `getThreadMessages` |
| Panel shows excerpt only | `passageText` not in metadata | Implement backend Step 1 |
| Refusal shows chips | `insufficientEvidence` not set | Backend metadata flag + UI guard |
| All messages show refusal banner | Parser treats missing metadata as refusal | Fix `getAssistantMetadata()` defaults |
| `tsc` errors on `metadata` | `UIMessage` type too narrow | Extend `ChatMessage` type alias |

---

## Suggested test order

| When | What |
|------|------|
| Before UI work | Pre-flight smoke + pytest |
| After backend Step 1 | `test_messages_citations.py` |
| After each UI component | `tsc` + visual check with loaded history |
| After stream hydration | MT-1 without refresh |
| Before marking Phase 7 done | Full MT-1 → MT-3 → MT-2 → MT-5 + regression suite |
