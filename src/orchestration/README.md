# Orchestration Module

This folder contains the workflow graph and runtime coordination logic for the **Planner Agent**.

## Implemented Responsibilities

- `graph.py` defines the LangGraph state machine with four internal nodes:
  1. **analyzer** — maps student input to missed topics.
  2. **pruning_router** — validates and deduplicates topics.
  3. **retriever** — queries ChromaDB for relevant content.
  4. **planner** — synthesizes the final bootcamp plan.
- Conditional edges skip retrieval/planning when all topics are pruned.
- Error handling and early-exit logic are built into each node.

## Three-Agent Architecture

The orchestration module currently only handles the **Planner Agent**'s internal flow.
The **Visualizer Agent** and **Tester Agent** are called on-demand via FastAPI endpoints
after the Planner produces a `BootcampPlanSchema`.

Future: optionally integrate Visualizer and Tester as post-planning nodes in the graph.

## Candidate Frameworks

- LangGraph (active — preferred for strict flow control).
- CrewAI (fallback for faster prototyping).
