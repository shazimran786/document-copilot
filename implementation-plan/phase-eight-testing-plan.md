# Phase 8 — Pilot readiness testing plan

Validate observability, agent reliability, documentation, and trust behavior before Railway deploy (Phase 9).

Related: [phase-eight-implementation-plan.md](phase-eight-implementation-plan.md) · [analyst-evaluation-question-bank.md](analyst-evaluation-question-bank.md) · [phase-seven-testing-plan.md](phase-seven-testing-plan.md) · [docs/client-brief.md](../docs/client-brief.md)

---

## Pre-flight (before starting Phase 8)

```powershell
cd backend
uv run pytest -v
uv run python scripts/smoke_retrieval.py
uv run python scripts/smoke_agent.py

cd ../frontend
pnpm tsc --noEmit
pnpm lint
```

| Check | Expected |
|-------|----------|
| pytest | 50+ pass |
| smoke scripts | Exit 0 (agent may vary on cited count) |
| frontend static analysis | Clean |

---

## Automated regression (after each Phase 8 change)

```powershell
cd backend && uv run pytest -v
cd ../frontend && pnpm tsc --noEmit && pnpm lint && pnpm build
```

| Suite | Blocks |
|-------|--------|
| Full pytest | Logging refactor breaks imports |
| `pnpm build` | Phase 9 deploy |

---

## Manual test matrix

### MT-P8-1 — Phase 7 sign-off (gate)

From [phase-seven-testing-plan.md](phase-seven-testing-plan.md): MT-1, MT-2, MT-3.

**Blocks Phase 8 done** if citation UI cannot be verified.

---

### MT-P8-2 — Structured logging

| Step | Action | Expected |
|------|--------|----------|
| 1 | Start backend with structlog configured | Console/JSON logs on startup |
| 2 | Send one chat question | Log line with `thread_id`, retrieval/turn timing |
| 3 | Trigger grounding fallback (narrow stress question) | `validation_failed=true` in logs |
| 4 | Force auth failure (expired token) | Auth error logged without stack trace leak to client |

---

### MT-P8-3 — Agent limits & long turns

| Step | Action | Expected |
|------|--------|----------|
| 1 | Ask cross-company question from question bank Cross #1 | Completes **or** clear error banner (not infinite dots) |
| 2 | Wait 60–90s if needed | Progress copy appears after ~10s |
| 3 | Response timer shows elapsed time | Final “Responded in Xs” on assistant bubble |
| 4 | Backend log shows tool/request count or limit event | Observable in structlog |

---

### MT-P8-4 — Trust & refusal (client brief)

| Question | Expected |
|----------|----------|
| Client-brief #10 (generative AI margins) | Blue insufficient-evidence banner; **no** citation chips |
| Stress: “What was Tesla’s AWS margin in 2024?” | Refusal or no relevant citations (not in corpus) |
| Stress: “Cite exact page 42 of AAPL 10-K” | Cites from passage metadata or honest limitation |

Record in `pilot-evaluation-log.md`.

---

### MT-P8-5 — Documentation walkthrough

| Step | Action | Expected |
|------|--------|----------|
| 1 | New machine / clean shell — follow README “Running locally” only | Backend + frontend start |
| 2 | Follow `re-ingest-runbook.md` dry-run | `ingest-corpus --dry-run` succeeds |
| 3 | Open `corpus-vs-openai.md` | Explains OpenAI vs corpus |

---

### MT-P8-6 — Quick smoke question bank

Run these five from [analyst-evaluation-question-bank.md](analyst-evaluation-question-bank.md):

1. AMZN #2 (AWS margin)
2. NVDA #1 (Data Center demand)
3. AAPL #10 (refusal boundary)
4. MSFT #3 (Azure / AI infra)
5. Cross #10 (refusal stress)

| Result | Minimum for Phase 8 pass |
|--------|--------------------------|
| ≥3 cited answers with chips | Yes |
| Both refusal questions correct banner | Yes |
| 0 blank streams (no text, no error) | Yes |

---

## Evaluation log

Use [pilot-evaluation-log.md](pilot-evaluation-log.md) (create when starting Phase 8) to record each run.

---

## Definition of done (Phase 8 testing)

- [ ] MT-P8-1 Phase 7 sign-off pass
- [ ] MT-P8-2 logging verified
- [ ] MT-P8-3 long-turn / limits acceptable
- [ ] MT-P8-4 refusal + stress cases pass
- [ ] MT-P8-5 docs walkthrough pass
- [ ] MT-P8-6 quick smoke ≥3 cited + 2 refusals correct
- [ ] `pnpm build` green
- [ ] `pytest` green

---

## Failure signals

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Blank UI 60s+ then error | `UsageLimitExceeded` | Wire agent limits; simplify cross-company prompts |
| No structlog output | Not wired in `main.py` | Fix logging init |
| README steps fail | Drift from actual commands | Update README |
| build fails TS5101 | Deprecated `baseUrl` | Apply tsconfig fix |
| Refusal shows amber banner | `insufficient_evidence` + citations not stripped | Check orchestrator normalize |
