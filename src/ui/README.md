# UI Module

This folder contains the user-facing interface.

## Implemented Responsibilities

- `app.py` — Streamlit frontend (`src/ui/app.py`).
  - Input form for course selection and absence date range.
  - Demo mode pre-fill for quick testing.
  - Displays generated bootcamp plan with executive summary, day-by-day tasks, study tips, and citations.
  - Pruning dashboard showing original topics, pruned count, token reduction, and removal reasons.
  - Raw JSON debug view.

## Stack

- **Streamlit** for quick delivery and hackathon judging.
- **React/Next.js** planned for richer UX and visualizer iframe embedding in Phase 5.

## Run

```powershell
streamlit run src/ui/app.py --server.port 8501
```

## Notes

- Requires the FastAPI backend to be running at `http://localhost:8000`.
