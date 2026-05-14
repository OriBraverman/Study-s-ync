# UI Module

This folder contains the user-facing interface.

## Main Frontend (HTML/JS)

The primary UI is a Hebrew RTL web app built by a team member:
- `static/index.html` — Tailwind CSS frontend with date picker, lecture browser, content viewer, and AI tutor chat.
- Served directly by FastAPI at `GET /`.

## How it works

1. Student selects a date range.
2. Frontend fetches lectures from `/get_missed_class_all`.
3. Matching lectures are displayed grouped by course.
4. Clicking a lecture shows its content + an AI-generated opening question.
5. Student can chat with the AI tutor via `/chat`.

## Streamlit (Legacy / Dev)

`app.py` is a temporary Streamlit frontend used during early development.
It can still be run for debugging the Planner Agent directly:

```powershell
streamlit run src/ui/app.py --server.port 8501
```

## Run the main UI

The HTML UI is served automatically by the FastAPI backend:

```powershell
uvicorn src.api.main:app --reload --port 8000
# Then open http://localhost:8000 in your browser
```
