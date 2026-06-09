# Pilot evaluation log

Record manual question runs during Phase 8 validation. Use questions from [analyst-evaluation-question-bank.md](analyst-evaluation-question-bank.md) and [client-brief.md](../docs/client-brief.md).

**Legend:** Pass = cited + verifiable · Refusal = honest not-in-corpus · Fail = wrong, hallucinated, blank, or validation fallback on easy question

---

## Quick smoke (minimum before Phase 9)

| Date | Question ID | Response time | Citations | Result | Notes |
|------|-------------|---------------|-----------|--------|-------|
| | AMZN #2 | | | | |
| | NVDA #1 | | | | |
| | AAPL #10 | | | | |
| | MSFT #3 | | | | |
| | Cross #10 | | | | |

---

## Client-brief full set

| Date | Q# | Topic | Citations | Result | Notes |
|------|-----|-------|-----------|--------|-------|
| | 1 | AAPL revenue mix | | | |
| | 2 | AMZN AWS vs segments | | | |
| | 3 | NVDA Data Center | | | |
| | 4 | MSFT Azure / AI | | | |
| | 5 | GOOGL segment trends | | | |
| | 6 | Risk-factor deltas (5 co) | | | |
| | 7 | AAPL + NVDA suppliers | | | |
| | 8 | CapEx comparison | | | |
| | 9 | Geographic exposure | | | |
| | 10 | Gen-AI margins refusal | | | |

---

## Stress / negative tests

| Date | Question | Expected | Actual | Pass? |
|------|----------|----------|--------|-------|
| | Tesla AWS margin 2024 | Refusal / not in corpus | | |
| | Invent a citation for fake chunk | No persisted citation | | |
| | Identical question twice | Two answers (no cache); both complete | | |

---

## Summary (fill after evaluation)

| Metric | Value |
|--------|-------|
| Total questions run | |
| Pass (cited) | |
| Refusal (correct) | |
| Fail | |
| Avg response time (cited answers) | |
| Blockers for pilot | |
