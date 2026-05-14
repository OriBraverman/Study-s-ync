# Source Code Layout

This folder contains the codebase for the Study[S]ync system.

## Current State

- `scraper/`: BIU syllabus scraping pipeline — baseline for data collection (another team member handles data).
- `agents/`: Three main agents:
  - `planner/` — Planner Agent: analyzes missed topics, retrieves material, creates study plan.
  - `visualizer/` — Visualizer Agent: generates interactive React simulations.
  - `tester/` — Tester Agent: generates practice tests and quizzes.
  - Core modules (`analyzer.py`, `pruning_router.py`, `retriever.py`, `planner.py`) used internally by the Planner Agent.
- `retrieval/`: ChromaDB vector store and ingestion pipeline for syllabuses + mock CS drive documents.
- `orchestration/`: LangGraph flow for the Planner Agent's internal pipeline.
- `api/`: FastAPI backend serving endpoints for all 3 agents.
- `schemas/`: Pydantic v2 contracts between all components.
- `ui/`: Streamlit frontend (temporary — another team member is building the main website).

Each subfolder has its own README with details and next steps.
