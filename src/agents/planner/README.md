# Planner Agent Module

This folder contains the **Planner Agent** (סוכן המתכנן) for Study[S]ync.

## Purpose

The Planner Agent is the core intelligence of the system. Given a student's missed dates and course information, it:

1. **Analyzes** the syllabus to identify missed topics
2. **Prunes** administrative entries, duplicates, and empty topics
3. **Retrieves** relevant study material from the vector store
4. **Generates** a prioritized, day-by-day recovery bootcamp plan with citations

## How it works

The planner agent wraps the existing core modules:
- `src.agents.analyzer` — syllabus analysis
- `src.agents.pruning_router` — topic validation and deduplication
- `src.agents.retriever` — ChromaDB vector search
- `src.agents.planner` — bootcamp plan generation

## Files

- `agent.py` — Unified planner interface that orchestrates the 4 internal steps.

## Integration

The Planner Agent is one of the three main agents in Study[S]ync:
1. **Planner Agent** — creates the study plan (this module)
2. **Visualizer Agent** — generates interactive simulations (`src/agents/visualizer/`)
3. **Tester Agent** — generates tests and quizzes (`src/agents/tester/`)

## Usage

```python
from src.agents.planner.agent import create_study_plan
from src.schemas.models import StudentInputSchema

plan = create_study_plan(StudentInputSchema(
    student_name="Alice",
    course_name="Intro to CS",
    course_num="89-110",
    absence_start=date(2026, 3, 1),
    absence_end=date(2026, 3, 14),
))
```
