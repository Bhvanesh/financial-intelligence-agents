# Benchmark — Agentic Financial Analyst

Evaluation of the multi-agent pipeline against a fixed golden dataset
derived from the Goldman Sachs Q3 2026 earnings PDF.

---

## Methodology

### Test Document
Goldman Sachs Group, Inc. — Q3 2026 Earnings Report (real PDF)

All expected values were manually verified against the source document
before being added to the golden dataset. No synthetic or fabricated
data was used.

### Evaluation Approach

Each agent is evaluated independently against expected outputs:

```
Extractor     → exact field comparison with float tolerance
Analyst       → computed percentage values vs Python ground truth
Risk Detector → structural checks (count, verification, quality)
Reporter      → verdict correctness (rule-based, deterministic)
```

### Why Structural Checks for Risks

Risk descriptions and evidence text vary between runs — the LLM
phrases them differently each time. Instead of comparing exact text,
the evaluation checks structural properties that should always hold:

```
minimum_count:  at least 2 risks identified
all_verified:   all risks have evidence_verified=True
no_table_rows:  no table row data used as evidence
```

### Float Tolerance

```
Large values (>= 100):  tolerance = 1.0
Small values (< 100):   tolerance = 0.05

Rationale: LLM extraction may round slightly differently
(e.g. 18679.0 vs 18679) — tolerance handles this without
masking genuine extraction errors.
```

### Reproducibility

The Extractor and Reporter are deterministic (temperature=0).
The Analyst uses tool calling — tool results are deterministic,
but LLM text (summary, key_facts) varies between runs.
Only computed values (floats) are evaluated — not LLM text.

---

## Golden Dataset — golden_dataset.json

25 checks across 4 sections derived from Goldman Sachs Q3 2026.

### Metrics (13 checks)

| Field | Expected | Source |
|-------|----------|--------|
| company_name | The Goldman Sachs Group, Inc. | Cover page |
| fiscal_period | Q3 2026 | Cover page |
| revenue_usd_millions | 18679.0 | Income statement |
| revenue_prior_quarter_usd_millions | 20338.0 | Income statement |
| revenue_prior_year_usd_millions | 15184.0 | Income statement |
| operating_income_usd_millions | null | Not reported by Goldman |
| net_income_usd_millions | 5294.0 | Income statement |
| net_income_prior_quarter_usd_millions | 6628.0 | Income statement |
| net_income_prior_year_usd_millions | 4098.0 | Income statement |
| diluted_eps_usd | 17.01 | EPS table |
| diluted_eps_prior_quarter_usd | 20.98 | EPS table |
| diluted_eps_prior_year_usd | 12.25 | EPS table |
| gross_margin_percent | null | Not reported by Goldman (bank) |

**Why operating_income and gross_margin are null:**
Goldman Sachs is a financial institution — it does not report
operating income or gross margin in the traditional sense.
Returning null for these fields is correct, not a failure.

---

### Analysis (8 checks)

All computed values derived from Python math — not LLM output.

| Field | Expected | Formula |
|-------|----------|---------|
| net_margin_percent | 28.34 | 5294 / 18679 × 100 |
| revenue_qoq_pct | -8.16 | (18679 - 20338) / 20338 × 100 |
| revenue_yoy_pct | 23.02 | (18679 - 15184) / 15184 × 100 |
| net_income_qoq_pct | -20.13 | (5294 - 6628) / 6628 × 100 |
| net_income_yoy_pct | 29.18 | (5294 - 4098) / 4098 × 100 |
| eps_qoq_pct | -18.92 | (17.01 - 20.98) / 20.98 × 100 |
| eps_yoy_pct | 38.86 | (17.01 - 12.25) / 12.25 × 100 |
| net_margin_pct | 28.34 | 5294 / 18679 × 100 |

**Why Python math and not LLM output:**
The Analyst LLM calls Python tools (calculate_change, calculate_margin)
for all arithmetic. The computed dict stores Python-calculated floats —
not LLM approximations. These values are deterministic and exactly
comparable.

---

### Risks (3 checks)

| Check | Expected | Rationale |
|-------|----------|-----------|
| minimum_count | >= 2 | Goldman Q3 has multiple material risks |
| all_verified | True | All evidence must match source PDF |
| no_table_rows | True | Evidence must be narrative, not table data |

**Known limitation:**
One table-row evidence slipped through in the evaluation run
(no_table_rows check: FAIL). The _is_table_row() guard caught
most cases but one pattern was not covered. This is reported
honestly rather than adjusted.

---

### Report (1 check)

| Field | Expected | Rationale |
|-------|----------|-----------|
| verdict | neutral | YoY positive, but net income QoQ > 10% decline |

**Verdict logic:**
```
bullish: revenue YoY positive AND net income YoY positive
         AND both QoQ declines < 10%
bearish: revenue YoY negative OR net income YoY negative
neutral: YoY metrics positive but ANY QoQ decline > 10%

Goldman Q3 2026:
→ revenue YoY:    +23.02% (positive)
→ net income YoY: +29.18% (positive)
→ revenue QoQ:    -8.16%  (negative, < 10%)
→ net income QoQ: -20.13% (negative, > 10%) ← triggers neutral
→ verdict: neutral ✅
```

---

## Results

```
============================================================
GOLDEN SET EVALUATION — Goldman Sachs Q3 2026
============================================================

── METRICS ──
  PASS  metrics.company_name
  PASS  metrics.fiscal_period
  PASS  metrics.revenue_usd_millions
  PASS  metrics.revenue_prior_quarter_usd_millions
  PASS  metrics.revenue_prior_year_usd_millions
  PASS  metrics.operating_income_usd_millions
  PASS  metrics.net_income_usd_millions
  PASS  metrics.net_income_prior_quarter_usd_millions
  PASS  metrics.net_income_prior_year_usd_millions
  PASS  metrics.diluted_eps_usd
  PASS  metrics.diluted_eps_prior_quarter_usd
  PASS  metrics.diluted_eps_prior_year_usd
  PASS  metrics.gross_margin_percent

── ANALYSIS ──
  PASS  analysis.net_margin_percent:          28.34
  PASS  analysis.computed.revenue_qoq_pct:    -8.16
  PASS  analysis.computed.revenue_yoy_pct:    23.02
  PASS  analysis.computed.net_income_qoq_pct: -20.13
  PASS  analysis.computed.net_income_yoy_pct: 29.18
  PASS  analysis.computed.eps_qoq_pct:        -18.92
  PASS  analysis.computed.eps_yoy_pct:        38.86
  PASS  analysis.computed.net_margin_pct:     28.34

── RISKS ──
  PASS  risks.minimum_count: actual=4 >= expected=2
  PASS  risks.all_verified:  True
  FAIL  risks.no_table_rows: one table-row evidence slipped through

── REPORT ──
  PASS  report.verdict: neutral

============================================================
RESULT: 24/25 checks passed
SCORE:  96%
============================================================
```

---

## Key Findings

**Extractor (13/13 — 100%):**
The two-pass retry loop successfully recovered all prior-period
values. null fields (operating_income, gross_margin) are correct
for Goldman Sachs as a financial institution — not extraction
failures.

**Analyst (8/8 — 100%):**
All computed percentage changes match Python ground truth exactly.
Tool-calling architecture (bind_tools + while loop) eliminates
LLM arithmetic errors entirely. The LLM writes analysis text using
tool-returned values — it never calculates independently.

**Risk Detector (2/3 — 67% structural checks):**
Minimum count and evidence verification pass. One table-row
evidence slipped through the _is_table_row() guard — the digit
ratio threshold did not catch this specific pattern. Reported
honestly. The prompt-level guard catches most cases; the code
guard adds defense-in-depth.

**Reporter (1/1 — 100%):**
Verdict correctly computed as neutral from Python QoQ/YoY values.
The None-guard fan-in pattern worked correctly — Reporter waited
for both Analyst and Risk Detector before synthesizing.

---

## Running the Evaluation

```bash
python check_golden.py samples/Goldman-Q3.pdf golden_dataset.json
```

---

## Honest Limitations

```
1. Single document evaluation:
   Tested on one real PDF (Goldman Sachs Q3 2026).
   Performance on other companies or formats
   is not yet measured.

2. Table-row slip-through:
   One risk evidence contained table data
   despite the _is_table_row() guard.
   The digit ratio threshold needs tuning
   for edge cases.

3. Sequential dependency in full_analysis:
   Extractor and Risk Detector start in parallel
   via parallel_trigger node, but Analyst must
   wait for Extractor — true parallelism is
   partial, not complete.
```
