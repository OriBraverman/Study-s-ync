# Visualizer Agent Module

This folder contains the **Visualizer Agent** (סוכן הסימולציות) for Study[S]ync.

## Purpose

When a bootcamp plan contains a complex algorithmic or architectural topic (e.g., *Pipeline Data Hazards*, *Bubble Sort*, *Graph BFS*), the Visualizer Agent generates a self-contained, interactive **React component** that the student can open in any browser without a build step.

## How it works

1. **Concept Extraction** — identifies the core algorithm/concept from the study task topic.
2. **Component Design** — designs a layout with a visualization area and a control panel.
3. **Code Generation** — produces a React functional component (Hooks, inline styles) that is fully self-contained.
4. **HTML Integration** — wraps the component in an HTML file using React/Babel CDNs so it runs without a build step.

## Files

- `agent.py` — LLM wrapper and prompt engineering.
- `templates/` — HTML wrapper and React boilerplate (to be added).
- `prompts/` — Prompt templates for different visualization categories (sorting, graphs, CPU pipeline, etc.).

## Integration

The Visualizer Agent is one of the three main agents in Study[S]ync:
1. **Planner Agent** — creates the study plan
2. **Visualizer Agent** — generates interactive simulations
3. **Tester Agent** — generates tests and quizzes

It can be called on-demand via the FastAPI endpoint:

```
POST /generate_visualizer
{
  "topic": "Pipeline Data Hazards in MIPS",
  "concept_type": "cpu_pipeline"
}
```

## Status

Active — integrated into the agent suite.
