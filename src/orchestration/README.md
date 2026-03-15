# Orchestration Module (Planned)

This folder will contain the workflow graph and runtime coordination logic.

## Planned Responsibilities

- Define node sequence and guards between agents.
- Inject pruning checks before expensive model calls.
- Control retries, logging, and failure handling.
- Provide run traces for demos/judging.

## Candidate Frameworks

- LangGraph (preferred for strict flow control).
- CrewAI (fallback for faster prototyping).