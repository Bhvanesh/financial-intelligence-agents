# Agentic Financial Analyst

A production-grade multi-agent system that analyzes real earnings PDFs using LangGraph. Four specialized AI agents — Extractor, Analyst, Risk Detector, and Reporter — work in a coordinated graph topology with parallel execution, autonomous tool calling, and evidence verification.

**Live API:** http://15.135.159.228:8000/docs

---

## Architecture

```
POST /analyze (PDF + user prompt)
        ↓
   Supervisor Agent
   (reads prompt → decides route)
        ↓
┌───────────────────────────────────────────────┐
│                  LangGraph                    │
│                                               │
│  full_analysis route:                         │
│  START → parallel_trigger                     │
│            ├──→ Extractor → Analyst ──────┐   │
│            └──→ Risk Detector ────────────┴→  │
│                                    Reporter → END
│                                               │
│  metrics_only:   Extractor → END              │
│  risks_only:     Risk Detector → END          │
│  metrics_and_analysis: Extractor → Analyst → END
│  summary_only:   Extractor → Analyst → Reporter → END
└───────────────────────────────────────────────┘
        ↓
  Dynamic response (only relevant fields returned)
```

---

## Agents

### Extractor
Reads the earnings PDF and extracts structured financial metrics into a validated Pydantic schema — revenue, net income, EPS, and prior-period comparators. Implements a two-pass retry loop: if CORE fields are null after the first extraction, a focused second pass targets only the missing fields, recovering prior-period values without hallucinating. Achieved **13/13 field accuracy** on Goldman Sachs Q3 2026.

### Analyst
A tool-calling agent using LangGraph-native `bind_tools()`. The LLM autonomously decides which calculations to run — QoQ%, YoY%, net margin — and Python executes them deterministically via `calculate_change()` and `calculate_margin()` tools. The LLM never performs arithmetic. All computed values are stored in a `computed` dict and passed forward to the Reporter, ensuring consistent numbers across agents.

### Risk Detector
Identifies risks with verbatim evidence quotes using three-layer verification:
1. Prompt engineering — "narrative sentences only, no table rows"
2. `_is_table_row()` guard — rejects evidence with high digit ratios or multiple dollar amounts
3. `_normalize()` string matching — checks evidence exists verbatim in source PDF

Only `evidence_verified=True` risks reach the output.

### Reporter (Fan-in)
Waits for both Analyst and Risk Detector via a None-guard clause that handles LangGraph's double-trigger fan-in pattern. Synthesizes all agent outputs into an executive report with a `bullish / neutral / bearish` verdict grounded in Python-computed QoQ/YoY values — never recalculated by the LLM.

### Supervisor
Routes user prompts to the correct agent subset using `with_structured_output()`. Five routes: `full_analysis`, `metrics_only`, `risks_only`, `metrics_and_analysis`, `summary_only`.

---

## Evaluation — Goldman Sachs Q3 2026

Tested against a 25-point golden dataset covering all four agent outputs.

```
Section          Checks    Result
─────────────────────────────────────────
Metrics          13/13     PASS — all fields correctly extracted
Analysis          8/8      PASS — all computed values correct
Risks             2/3      PASS — count and verification pass
                           FAIL — one table-row evidence slipped through
Report            1/1      PASS — verdict "neutral" correct
─────────────────────────────────────────
Total            24/25     96%
```

**Key results:**
- 13/13 field extraction accuracy on real Goldman Sachs Q3 2026 PDF
- All detected risks have `evidence_verified=True`
- Verdict: `neutral` — correctly computed from Python QoQ/YoY values
- Zero hallucinated numbers in Analyst output

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register and receive an API key |
| POST | `/analyze` | Upload PDF + prompt → run analysis |
| GET | `/all_analyses` | List all past analyses |
| GET | `/analysis/{id}` | Get full result for one analysis |

### Authentication
All `/analyze` requests require an API key in the header:
```
X-API-Key: sk-your-key-here
```

### Rate Limiting
Redis-based rate limiting per API key — 5 requests per minute. Returns `429 Too Many Requests` when exceeded.

### Dynamic Response
Response fields vary by route — no null fields returned:

```json
// risks_only route
{
  "id": 1,
  "filename": "Goldman-Q3.pdf",
  "route": "risks_only",
  "risks": [
    {
      "category": "credit",
      "description": "Provision for credit losses increased significantly.",
      "evidence": "Provision for credit losses was $368 million for Q3 2026...",
      "evidence_verified": true
    }
  ]
}

// full_analysis route
{
  "id": 2,
  "route": "full_analysis",
  "company_name": "The Goldman Sachs Group, Inc.",
  "fiscal_period": "Q3 2026",
  "metrics": { "revenue_usd_millions": 18679.0, "diluted_eps_usd": 17.01, ... },
  "analysis": { "summary": "...", "computed": { "revenue_qoq_pct": -8.16, ... } },
  "risks": [ { "category": "credit", "evidence_verified": true, ... } ],
  "report": { "verdict": "neutral", "executive_summary": "..." }
}
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Orchestration | LangGraph 1.x, LangChain |
| LLM | OpenAI GPT-4o-mini |
| Structured Output | Pydantic |
| API | FastAPI |
| Database | PostgreSQL (AWS RDS) |
| Rate Limiting | Redis |
| Migrations | Alembic |
| PDF Extraction | pypdf |
| Observability | LangSmith tracing, structured logging |
| Testing | pytest (9 tests) |
| CI/CD | GitHub Actions → AWS ECR |
| Deployment | AWS EC2, Docker |

---

## Project Structure

```
earnings-analyzer/
├── main.py              # FastAPI app — endpoints, auth, rate limiting
├── graph.py             # LangGraph StateGraph — nodes and conditional edges
├── state.py             # AnalyzerState TypedDict
├── supervisor.py        # Supervisor agent — prompt routing
├── extractor.py         # Extractor agent — structured metric extraction
├── analyst.py           # Analyst agent — tool-calling, computed values
├── risk_detector.py     # Risk Detector — 3-layer evidence verification
├── reporter.py          # Reporter — fan-in, verdict synthesis
├── pdf_loader.py        # PDF text extraction with page numbers
├── api_key_manager.py   # API key generation, validation, Redis rate limiting
├── database.py          # SQLAlchemy engine and session
├── models.py            # SQLAlchemy models — APIKey, Analysis
├── schemas.py           # Pydantic schemas — requests and responses
├── check_golden.py      # Golden set evaluation harness
├── golden_dataset.json  # 25-point ground truth for Goldman Q3 2026
├── migrations/          # Alembic migration files
├── tests/               # pytest test suite (9 tests)
├── Dockerfile           # Docker build config
└── .github/workflows/   # GitHub Actions CI/CD
```

---

## Running Locally

```bash
# Clone
git clone https://github.com/Bhvanesh/financial-intelligence-agents.git
cd financial-intelligence-agents

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your keys

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload
```

---

## Running Tests

```bash
pytest tests/ -v
```

```
tests/test_api.py::test_register_success              PASSED
tests/test_api.py::test_register_missing_owner_name   PASSED
tests/test_api.py::test_register_owner_name_too_short PASSED
tests/test_api.py::test_list_analyses_empty           PASSED
tests/test_api.py::test_get_analysis_not_found        PASSED
tests/test_api.py::test_analyze_no_file               PASSED
tests/test_api.py::test_analyze_wrong_file_type       PASSED
tests/test_api.py::test_analyze_empty_prompt          PASSED
tests/test_api.py::test_analyze_prompt_too_long       PASSED

9 passed
```

---

## Running Golden Set Evaluation

```bash
python check_golden.py samples/Goldman-Q3.pdf golden_dataset.json
```

---

## Deployment

Deployed on AWS EC2 with Docker. CI/CD via GitHub Actions:

```
git push → GitHub Actions → pytest (9 tests)
         → docker build → push to AWS ECR
         → EC2 pulls latest image → restarts container
```

Infrastructure:
- **Compute:** AWS EC2 t2.micro
- **Database:** AWS RDS PostgreSQL
- **Container Registry:** AWS ECR
- **Rate Limiting:** Redis on EC2
- **Observability:** LangSmith

---

## Key Engineering Decisions

**Tool calling over LLM arithmetic:** The Analyst LLM calls Python tools for all calculations. Numbers in the output are deterministic — not approximated by the model.

**Fan-out/fan-in with guard clause:** The Reporter handles LangGraph's double-trigger behavior with a None-guard, ensuring it only runs when both upstream agents have completed.

**Evidence verification over prompt-only:** Risk evidence is checked against source text using `_normalize()` string matching — not just instructed in the prompt. Table rows are rejected programmatically via `_is_table_row()`.

**Extractor retry loop:** A focused second pass recovers missed prior-period fields without hallucinating. Run 1 extracts broadly; Run 2 targets only null CORE fields.

**Dynamic response schema:** `_build_response()` returns only fields relevant to the route — no null fields exposed to the API consumer.

---

## Known Limitations

- `full_analysis` runs Extractor and Risk Detector in parallel via `parallel_trigger` node, but Analyst must wait for Extractor — sequential dependency within the parallel branch.
- One table-row evidence slipped through risk verification in golden evaluation (96% score, not 100%).
