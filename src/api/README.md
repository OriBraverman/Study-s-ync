# API Module

This folder contains the FastAPI backend.

## Implemented Responsibilities

- `main.py` exposes endpoints for all three agents:
  - `GET /health` — liveness check and mock-mode flag.
  - `GET /courses` — list of courses available in the syllabus database.
  - `POST /generate_bootcamp` — runs the **Planner Agent** pipeline and returns `BootcampPlanSchema` + pruning stats.
  - `POST /generate_visualizer` — runs the **Visualizer Agent** and returns React code + HTML wrapper.
  - `POST /generate_test` — runs the **Tester Agent** and returns practice questions.
- CORS middleware enabled for local frontend development.
- Defaults to mock LLM mode so the API works without an OpenAI key.

## Run

```powershell
uvicorn src.api.main:app --reload --port 8000
```

## Suggested Future Files

- `routes/bootcamp.py` — bootcamp-specific routes.
- `routes/visualizer.py` — visualizer-specific routes.
- `routes/tester.py` — tester-specific routes.
- `dependencies/` — shared dependency injection.
- `config.py` — centralized settings.
