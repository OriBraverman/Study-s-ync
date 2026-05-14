# Tester Agent Module

This folder contains the **Tester Agent** (סוכן הבוחן) for Study[S]ync.

## Purpose

After the Planner Agent creates a study plan, the Tester Agent generates practice questions, quizzes, and mini-exams for each topic. This helps students verify their understanding before moving on.

## How it works

1. **Topic Analysis** — receives a topic from the study plan.
2. **Question Generation** — creates multiple-choice, short-answer, and code-tracing questions.
3. **Answer & Explanation** — every question includes the correct answer and a brief explanation.
4. **Adaptive Difficulty** — adjusts question difficulty based on topic complexity.

## Files

- `agent.py` — Test generation logic with mock and LLM modes.

## Integration

The Tester Agent is one of the three main agents in Study[S]ync:
1. **Planner Agent** — creates the study plan (`src/agents/planner/`)
2. **Visualizer Agent** — generates interactive simulations (`src/agents/visualizer/`)
3. **Tester Agent** — generates tests and quizzes (this module)

## Usage

```python
from src.agents.tester.agent import generate_test

test = generate_test("Recursion", num_questions=3)
for q in test.questions:
    print(q.question_text)
```

## Status

Active — mock mode works out of the box; LLM mode requires `USE_MOCK_LLM=false` + `OPENAI_API_KEY`.
