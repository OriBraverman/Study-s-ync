# Study[S]ync

Token-efficient multi-agent system for BIU students returning from reserve duty, aligned with the plan in `PLANNING.md`.

## Current Status

- **Repository structure** has been reorganized into three main agents.
- **Scraper** (`src/scraper`): Active BIU syllabus scraping pipeline — handled by another team member.
- **Agents** (`src/agents`): Three main agents implemented.
  1. **Planner Agent** (`src/agents/planner/`) — analyzes missed topics, retrieves material, and generates a day-by-day recovery plan.
  2. **Visualizer Agent** (`src/agents/visualizer/`) — generates interactive React simulations for complex topics (based on `VisoAgent`).
  3. **Tester Agent** (`src/agents/tester/`) — generates practice tests, quizzes, and code-tracing questions.
- **Orchestration** (`src/orchestration`): LangGraph pipeline for the Planner Agent's internal flow.
- **Retrieval** (`src/retrieval`): ChromaDB vector store with syllabus + mock CS drive ingestion.
- **API** (`src/api`): FastAPI backend with endpoints for all 3 agents.
- **UI** (`src/ui`): Streamlit frontend (temporary — another team member is building the main website).
- **Schemas** (`src/schemas`): Pydantic v2 contracts for strict typed communication between agents.
- Legacy/experimental code lives in `experiments/`.

## Project Goal

Study[S]ync will:

1. Receive absence window and course list (from the website).
2. Identify missed topics from official syllabus data.
3. Retrieve the most relevant course materials.
4. Generate a prioritized recovery bootcamp plan with citations.
5. Generate interactive **React visualizations** for complex algorithmic topics.
6. Generate **practice tests** so students can verify their understanding.

## Repository Structure

```text
Study[S]ync/
├── PLANNING.md
├── README.md
├── requirements.txt
├── data/
│  ├── README.md
│  ├── chroma_db/           # ChromaDB persistent store (gitignored)
│  ├── mock_cs_drive/       # Mock course material text files
│  ├── outcasts/            # Scraping logs for failed courses
│  ├── raw/
│  │  └── syllabuses.json   # Scraped BIU syllabi
│  └── processed/
├── src/
│  ├── __init__.py
│  ├── README.md
│  ├── scraper/             # BIU syllabus scraper (another team member)
│  │  ├── __init__.py
│  │  ├── README.md
│  │  ├── syllabus_scraper.py
│  │  ├── batch_scrape_syllabuses.py
│  │  ├── inspect_biu_home.py
│  │  ├── outcast_processor.py
│  │  └── last_biu_home.html
│  ├── agents/              # Three main agents
│  │  ├── __init__.py
│  │  ├── README.md
│  │  ├── planner/          # Planner Agent — creates the study plan
│  │  │  ├── __init__.py
│  │  │  ├── README.md
│  │  │  └── agent.py       # Unified planner interface
│  │  ├── visualizer/       # Visualizer Agent — React simulations
│  │  │  ├── __init__.py
│  │  │  ├── README.md
│  │  │  └── agent.py
│  │  ├── tester/           # Tester Agent — practice tests
│  │  │  ├── __init__.py
│  │  │  ├── README.md
│  │  │  └── agent.py
│  │  ├── analyzer.py       # Core module (used by Planner)
│  │  ├── pruning_router.py # Core module (used by Planner)
│  │  ├── retriever.py       # Core module (used by Planner)
│  │  └── planner.py        # Core module (used by Planner)
│  ├── retrieval/           # Vector store & ingestion
│  │  ├── __init__.py
│  │  ├── README.md
│  │  ├── vector_store.py
│  │  └── ingest.py
│  ├── orchestration/       # LangGraph pipeline
│  │  ├── __init__.py
│  │  ├── README.md
│  │  └── graph.py
│  ├── api/                 # FastAPI backend
│  │  ├── __init__.py
│  │  ├── README.md
│  │  └── main.py
│  ├── schemas/             # Pydantic data contracts
│  │  ├── __init__.py
│  │  ├── README.md
│  │  └── models.py
│  └── ui/                  # Streamlit frontend (temporary)
│     ├── __init__.py
│     ├── README.md
│     └── app.py
└── experiments/
   ├── README.md
   ├── legacy_scraper/
   │  └── README.md
   └── legacy_artifacts/
      ├── README.md
      └── src_data_snapshot/
         └── README.md
```

## Three-Agent Architecture

Study[S]ync is built around three specialized agents:

```text
┌─────────────────┐
│  Website UI     │  (another team member)
│  (React/Next.js)│
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────────────────────────────────┐
│           FastAPI Backend                   │
│  (src/api/main.py)                          │
└────────┬──────────────────┬─────────────────┘
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌─────────────────┐
│  Planner Agent  │  │  Visualizer     │
│  (src/agents/    │  │  Agent          │
│   planner/)      │  │  (src/agents/   │
│                  │  │   visualizer/)  │
│  Internal flow:  │  │                 │
│  Analyzer ->     │  │  Generates      │
│  Pruner ->       │  │  interactive    │
│  Retriever ->    │  │  React          │
│  Planner         │  │  components     │
└────────┬────────┘  └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Tester Agent   │
│  (src/agents/   │
│   tester/)      │
│                 │
│  Generates      │
│  practice tests │
│  per topic      │
└─────────────────┘
```

### 1. Planner Agent (`src/agents/planner/`)

The core intelligence. It runs an internal LangGraph pipeline:

```
StudentInputSchema
       │
       ▼
   [analyzer]
       │ MissedTopicsSchema
       ▼
 [pruning_router]
       │ PrunedTopicsSchema
       ▼
  [retriever]
       │ List[RetrievedChunk]
       ▼
   [planner]
       │ BootcampPlanSchema
       ▼
   (output)
```

| Internal Node | File | Responsibility |
|---------------|------|--------------|
| **Analyzer** | `src/agents/analyzer.py` | Loads syllabus JSON, estimates missed weeks, returns `MissedTopicsSchema`. |
| **Pruning Router** | `src/agents/pruning_router.py` | Removes empty/admin/duplicate topics; tracks token-reduction stats. |
| **Retriever** | `src/agents/retriever.py` | Queries ChromaDB per topic; returns `RetrievedChunk` with citations. |
| **Planner** | `src/agents/planner.py` | Builds day-by-day `BootcampPlanSchema` (mock or GPT-4o-mini). |

### 2. Visualizer Agent (`src/agents/visualizer/`)

Generates interactive React simulations for complex topics:
- Bubble Sort, Merge Sort visualizations
- Graph BFS/DFS step-by-step
- CPU Pipeline stages (IF, ID, EX, MEM, WB)
- Data hazard detection and forwarding

Output: self-contained `index.html` + `index.jsx` using React CDNs.

### 3. Tester Agent (`src/agents/tester/`)

Generates practice tests per study topic:
- Multiple choice questions
- Short answer questions
- Code tracing exercises
- Difficulty levels: easy, medium, hard

## Active Scraper Pipeline

The active scraping code is in `src/scraper`.

### What it does

1. Opens BIU course portal and handles delayed form availability.
2. Filters by CS department (`המחלקה למדעי המחשב`, with fallback logic).
3. Traverses paginated results and collects unique `89*` course codes.
4. Scrapes syllabus text from dedicated syllabus link or details fallback.
5. Extracts heuristic weekly topics.
6. Merges with existing records and writes deduplicated JSON.

### Output

- Primary output: `data/raw/syllabuses.json`

### Run

```powershell
conda activate agents
pip install -r requirements.txt
python src/scraper/batch_scrape_syllabuses.py
```

Single course test:

```powershell
python src/scraper/syllabus_scraper.py 89-110
```

## Run the system

### Planner Agent (programmatic)

```python
from src.schemas.models import StudentInputSchema
from src.orchestration.graph import run_pipeline

plan = run_pipeline(StudentInputSchema(
    student_name="Ori Ben-David",
    course_name="Intro to CS",
    course_num="89-110",
    absence_start=date(2026, 3, 8),
    absence_end=date(2026, 3, 21),
))
```

### API + UI (all 3 agents)

```powershell
# Terminal 1 — FastAPI backend
uvicorn src.api.main:app --reload --port 8000

# Terminal 2 — Streamlit frontend (temporary)
streamlit run src/ui/app.py --server.port 8501
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness check |
| `/courses` | GET | List available courses |
| `/generate_bootcamp` | POST | Run Planner Agent |
| `/generate_visualizer` | POST | Run Visualizer Agent |
| `/generate_test` | POST | Run Tester Agent |

## Alignment With Planning

`PLANNING.md` describes a phased hackathon MVP. Current implementation status:

| Phase | Planning Item | Status |
|-------|---------------|--------|
| **Phase 1** | Repo setup, mock DB, environment | ✅ Complete |
| **Phase 2** | Website UI (form, dashboard) | 🔹 Another team member |
| **Phase 2** | Simulation component | ✅ Visualizer Agent ready |
| **Phase 3** | AI Teacher / study plan | ✅ Planner Agent ready |
| **Phase 3** | Context injection | ✅ Retrieved chunks injected into planner |
| **Phase 4** | Full flow integration | ✅ LangGraph end-to-end pipeline |
| **Phase 4** | Test generation | ✅ Tester Agent ready |
| **Phase 4** | UI/UX polish | 🔹 In progress (main website by another team member) |

## Notes

- `experiments/legacy_scraper` is preserved for reference and is not part of production flow.
- Raw/processed data are ignored in git by default.
- The pipeline defaults to **mock LLM mode** (`USE_MOCK_LLM=true`) so it works without an OpenAI key. Set `USE_MOCK_LLM=false` and provide `OPENAI_API_KEY` for GPT-4o-mini mode.
