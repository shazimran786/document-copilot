# Analyst evaluation question bank

Manual test questions for Document Copilot against the curated **10-K corpus** (fiscal years **2021–2025**).

**Companies:** Apple (AAPL) · Amazon (AMZN) · Alphabet (GOOGL) · Microsoft (MSFT) · NVIDIA (NVDA)

**How to use**

1. Sign in → open a thread → paste one question at a time.
2. Check: streamed answer, citation chips, passage panel, response timer, trust banners.
3. Mark each run: **Pass** (cited + verifiable) · **Refusal** (honest “not in corpus”) · **Fail** (wrong, hallucinated, or validation fallback).

**Pass criteria (from [client-brief.md](../docs/client-brief.md))**

- Factual claims have citations you can click and verify.
- Refusals are clear when evidence is weak — no invented facts.
- Multi-year questions cite specific fiscal years from filings.

Related: [phase-seven-testing-plan.md](phase-seven-testing-plan.md) · [client-brief.md](../docs/client-brief.md)

---

## Apple (AAPL)

| # | Question | What you're testing |
|---|----------|---------------------|
| 1 | How did Apple's revenue mix between iPhone, Services, Mac, iPad, and Wearables change from fiscal 2021 through fiscal 2025, and which segment grew fastest in share of total net sales? | Multi-year segment mix · cited figures |
| 2 | What did Apple's latest 10-K say about Services gross margin compared to Products gross margin? | Segment profitability · single-company |
| 3 | How does Apple describe its dependence on single-source or limited-source suppliers and manufacturing partners, and did that language change between 2021 and 2025? | Supply chain risk · trend |
| 4 | What geographic regions does Apple disclose as the largest sources of net sales in its most recent 10-K, and how did China/Hong Kong exposure change year over year? | Geographic revenue |
| 5 | What risk factors did Apple add or emphasize related to AI, machine learning, or competition in its 2024 or 2025 10-K compared to 2021? | Risk-factor delta |
| 6 | What did Apple disclose about R&D spending and what areas of technology investment it highlights in MD&A? | CapEx / R&D narrative |
| 7 | How does Apple describe App Store and Services regulatory risk in Europe and the United States across the available filings? | Regulation · multi-year |
| 8 | What did Apple's filings say about iPhone unit demand trends or upgrade cycles in any year between 2021 and 2025? | Product demand · specific segment |
| 9 | Summarize Apple's disclosed gross margin drivers (product mix, foreign exchange, component costs) from the most recent MD&A section. | MD&A extraction |
| 10 | Did Apple's filings prove that generative AI directly improved Apple's company-wide operating margin in any fiscal year? If not, what evidence exists and what should the bot refuse to claim? | **Refusal / evidence boundary** |

---

## Amazon (AMZN)

| # | Question | What you're testing |
|---|----------|---------------------|
| 1 | For Amazon, compare AWS net sales and operating income to North America and International segments from 2021 through 2025. In which years did AWS operating margin exceed North America? | Cross-segment comparison · multi-year |
| 2 | What did Amazon's latest 10-K say about AWS operating margin trends and the main drivers management cites? | AWS margin narrative |
| 3 | How does Amazon describe fulfillment network capacity, labor costs, and logistics efficiency in recent filings? | Operations · MD&A |
| 4 | What did Amazon disclose about advertising services revenue growth and its role in the North America segment? | Emerging revenue line |
| 5 | What risk factors does Amazon highlight for AI services, cloud competition, and antitrust scrutiny, and how did that wording evolve from 2021 to 2025? | Risk · AI/regulation |
| 6 | What geographic net sales breakdown does Amazon report, and which international markets showed the weakest or strongest growth? | Geographic mix |
| 7 | What did Amazon say about capital expenditures and infrastructure investment related to AWS and fulfillment in 2024–2025? | CapEx narrative |
| 8 | How does Amazon describe third-party seller services and take rates or marketplace mix in segment discussion? | Marketplace economics |
| 9 | What did Amazon's filings disclose about customer concentration or reliance on a small number of enterprise AWS customers? | Concentration risk |
| 10 | According to Amazon's 10-Ks only, did AWS alone fund operating losses in International in every year from 2021 to 2025? Cite the years where evidence supports or contradicts that. | Analytical · must cite |

---

## Alphabet (GOOGL)

| # | Question | What you're testing |
|---|----------|---------------------|
| 1 | How did Google Search, YouTube ads, Google Network, Google Cloud, and Other Bets revenue trends differ across Alphabet's 2021–2025 10-Ks? | Multi-segment revenue trend |
| 2 | What did Alphabet's latest filing say about Google Cloud operating loss or path to profitability? | Cloud segment · margin |
| 3 | How does Alphabet describe AI investments, Gemini, and integration of AI into Search and advertising products in recent risk factors or MD&A? | AI narrative · multi-year |
| 4 | What did Alphabet disclose about regulatory risk related to Search, advertising, app stores, and EU Digital Markets Act? | Regulation |
| 5 | What geographic revenue concentrations does Alphabet report (United States vs rest of world), and how did international growth compare to U.S. growth? | Geographic |
| 6 | What did Alphabet say about headcount reductions, efficiency initiatives, and operating expense discipline from 2022 through 2025? | Cost structure |
| 7 | How does Alphabet describe YouTube's monetization, Shorts, and competition with other video platforms? | Product segment |
| 8 | What capital expenditure and data center investment language does Alphabet use for AI and cloud infrastructure in 2024–2025? | CapEx · AI infra |
| 9 | What risk factors does Alphabet disclose about intellectual property, open-source software, and cybersecurity incidents? | Risk inventory |
| 10 | Do Alphabet's filings provide enough evidence to conclude that AI Search features increased total company operating margin in fiscal 2024? Answer only from the corpus. | **Refusal / evidence boundary** |

---

## Microsoft (MSFT)

| # | Question | What you're testing |
|---|----------|---------------------|
| 1 | How did Microsoft describe Azure revenue growth, AI services attach, and cloud demand drivers across 2021–2025 10-Ks? | Cloud · multi-year |
| 2 | What did Microsoft's latest 10-K say about Intelligent Cloud operating income and margin compared to Productivity and Business Processes and More Personal Computing? | Segment margins |
| 3 | What language does Microsoft use about AI infrastructure capacity constraints, datacenter buildout, and power availability in recent filings? | AI infra constraints |
| 4 | How does Microsoft describe GitHub, Copilot, and generative AI monetization in MD&A or risk factors? | AI product narrative |
| 5 | What did Microsoft disclose about Activision Blizzard acquisition impacts on revenue, amortization, and gaming segment results? | M&A · gaming |
| 6 | What geographic revenue mix does Microsoft report, and which regions drove the fastest constant-currency growth in the latest year? | Geographic |
| 7 | What risk factors did Microsoft add or expand related to export controls, geopolitical conflict, and cybersecurity between 2021 and 2025? | Risk delta |
| 8 | What did Microsoft say about capital expenditures and lease commitments for cloud and AI infrastructure in 2024–2025? | CapEx |
| 9 | How does Microsoft describe competition from Amazon AWS and Google Cloud in its 10-K risk factors? | Competitive landscape |
| 10 | According to Microsoft's filings alone, did Copilot rollouts measurably improve Office 365 gross margin in any disclosed fiscal year? Cite or refuse. | **Refusal / evidence boundary** |

---

## NVIDIA (NVDA)

| # | Question | What you're testing |
|---|----------|---------------------|
| 1 | How did NVIDIA describe Data Center revenue growth and demand drivers (AI training, inference, hyperscale customers) from fiscal 2021 through fiscal 2025? | Flagship segment · multi-year |
| 2 | What did NVIDIA's latest 10-K say about Gaming segment revenue trends and the impact of crypto mining demand in prior years? | Segment contrast |
| 3 | How does NVIDIA describe customer concentration among hyperscalers and large cloud providers, and did concentration language intensify over time? | Customer concentration |
| 4 | What supply chain, CoWoS packaging, and foundry capacity constraints does NVIDIA disclose in recent filings? | Supply constraints |
| 5 | What export controls, China restrictions, and geopolitical risk language appears in NVIDIA's 2023–2025 10-Ks compared to 2021? | Export controls · trend |
| 6 | What did NVIDIA disclose about gross margin drivers, product mix shift toward Data Center, and inventory provisions in the most recent year? | Margin · inventory |
| 7 | How does NVIDIA describe competition from AMD, custom ASICs, and internal cloud silicon in risk factors? | Competition |
| 8 | What geographic revenue split does NVIDIA report, and how did Taiwan or China-related exposure change? | Geographic |
| 9 | What did NVIDIA say about automotive, Omniverse, and software/licensing revenue as a share of the business? | Secondary segments |
| 10 | Do NVIDIA's filings prove that generative AI improved NVIDIA's company-wide gross margin in every year from 2021 to 2025? Answer only from evidence in the corpus. | **Refusal / evidence boundary** |

---

## Cross-company questions (bonus — 10 more)

Use these to test comparison, retrieval breadth, and refusal across the full corpus.

| # | Question | What you're testing |
|---|----------|---------------------|
| 1 | Which of the five companies most explicitly tied capital expenditure increases to AI or cloud infrastructure in their latest 10-K? | Cross-company comparison |
| 2 | Compare how Apple, Microsoft, Amazon, Alphabet, and NVIDIA each describe AI-related regulatory risk in their most recent filings. | Thematic comparison |
| 3 | Which companies disclosed the largest year-over-year increase in R&D or technology spending as a percentage of revenue between 2021 and 2025? | Multi-company · figures |
| 4 | How do the five companies differ in how they describe dependence on Taiwan or China in supply chain risk factors? | Supply chain · geo |
| 5 | Which companies added or expanded export control risk language after 2022? | Risk delta · timeline |
| 6 | Rank the five companies by disclosed Data Center or cloud-related revenue importance using only filing language, not external data. | Analytical · cited |
| 7 | What purchase commitments or backlog disclosures do Amazon, Microsoft, Alphabet, and NVIDIA make related to infrastructure? | CapEx comparison |
| 8 | Which company filings discuss customer concentration most explicitly, and what examples do they give? | Risk comparison |
| 9 | For all five companies, what geographic region appears most often as the largest non-U.S. revenue exposure in the latest 10-K? | Geographic scan |
| 10 | Do any of the five companies' 10-Ks prove that generative AI improved operating margin at the consolidated company level? List evidence per company or state none. | **Refusal stress test** |

---

## Suggested test rotation

| Session goal | Sample picks |
|--------------|--------------|
| Quick smoke (15 min) | AMZN #2, NVDA #1, AAPL #10, Cross #10 |
| Citation UI pass | One question from each company #1 or #2 |
| Refusal behavior | Each company #10 + Cross #10 |
| Full pilot rehearsal | All 50 company questions over a week |

---

## Tracking template

Copy per run:

```
Company: ___
Question #: ___
Date: ___
Response time: ___
Citations: ___
Pass / Refusal / Fail: ___
Notes: ___
```

---

## File map

```
implementation-plan/
└── analyst-evaluation-question-bank.md   ← this file (50 per-company + 10 cross-company)
```
