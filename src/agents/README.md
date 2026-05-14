# Agents Package

This package contains the three main agents of Study[S]ync.

## Main Agents

### 1. Planner Agent (`src/agents/planner/`)
**Role:** Creates the recovery study plan.

Steps:
1. Analyzes the student's missed dates against the course syllabus
2. Prunes administrative/duplicate topics
3. Retrieves relevant study material from the vector store
4. Generates a prioritized, day-by-day bootcamp plan with citations

Entry point: `src.agents.planner.agent.create_study_plan()`

### 2. Visualizer Agent (`src/agents/visualizer/`)
**Role:** Generates interactive React simulations.

For complex algorithmic or architectural topics (e.g., Pipeline Hazards, Bubble Sort, Graph BFS), this agent produces a self-contained React component that students can run in any browser.

Entry point: `src.agents.visualizer.agent.generate_visualizer()`

### 3. Tester Agent (`src/agents/tester/`)
**Role:** Generates practice tests and quizzes.

For each topic in the study plan, this agent creates multiple-choice, short-answer, and code-tracing questions with answers and explanations.

Entry point: `src.agents.tester.agent.generate_test()`

## Core Modules (Legacy Support)

The following modules still live at `src/agents/` root level and are used internally by the Planner Agent:
- `analyzer.py`
- `pruning_router.py`
- `retriever.py`
- `planner.py`

These are considered implementation details. New code should prefer the unified agent interfaces above.
