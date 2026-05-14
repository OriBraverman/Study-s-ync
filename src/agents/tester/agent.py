"""
Study[S]ync Tester Agent

Generates quizzes, tests, and practice exams for a given study topic.
Helps students verify their understanding of missed material.
"""
import os
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv

from src.schemas.models import (
    QuestionSchema,
    TestSchema,
)

load_dotenv()


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are an Expert Computer Science Educator & Exam Writer.
Your mission is to create high-quality practice questions for university
computer science topics.

Rules:
- Generate multiple-choice, short-answer, and code-tracing questions.
- Each question must test a specific concept (not just trivia).
- Provide the correct answer and a brief explanation.
- Adjust difficulty based on the topic complexity.
- Output valid JSON only — no markdown fences, no extra text.

Output JSON Structure:
{
  "questions": [
    {
      "question_type": "multiple_choice|short_answer|code_tracing",
      "question_text": "string",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "string",
      "explanation": "string",
      "difficulty": "easy|medium|hard",
      "topic": "string"
    }
  ]
}
"""

# ---------------------------------------------------------------------------
# Mock data for default mode
# ---------------------------------------------------------------------------

MOCK_QUESTIONS = {
    "loops": [
        QuestionSchema(
            question_type="multiple_choice",
            question_text="What is the output of the following Python loop?\nfor i in range(3):\n    print(i)",
            options=["A. 1 2 3", "B. 0 1 2", "C. 0 1 2 3", "D. Error"],
            correct_answer="B. 0 1 2",
            explanation="range(3) generates 0, 1, 2. The loop prints each value.",
            difficulty="easy",
            topic="Loops",
        ),
        QuestionSchema(
            question_type="code_tracing",
            question_text="Trace this loop:\narr = [3, 1, 4]\nfor i in range(len(arr)):\n    arr[i] = arr[i] * 2\nWhat is arr after the loop?",
            options=["A. [3, 1, 4]", "B. [6, 2, 8]", "C. [3, 2, 4]", "D. Error"],
            correct_answer="B. [6, 2, 8]",
            explanation="Each element is multiplied by 2: 3*2=6, 1*2=2, 4*2=8.",
            difficulty="easy",
            topic="Loops",
        ),
    ],
    "recursion": [
        QuestionSchema(
            question_type="short_answer",
            question_text="What is the base case in a recursive factorial function?",
            options=[],
            correct_answer="n <= 1 (or n == 0, returning 1)",
            explanation="The base case stops the recursion. For factorial, it's when n reaches 0 or 1.",
            difficulty="medium",
            topic="Recursion",
        ),
        QuestionSchema(
            question_type="code_tracing",
            question_text="What is the result of fib(4) where fib(n) = fib(n-1) + fib(n-2) with base cases fib(0)=0, fib(1)=1?",
            options=["A. 2", "B. 3", "C. 5", "D. 8"],
            correct_answer="B. 3",
            explanation="fib(4) = fib(3) + fib(2) = (fib(2)+fib(1)) + (fib(1)+fib(0)) = (1+1) + (1+0) = 3.",
            difficulty="medium",
            topic="Recursion",
        ),
    ],
    "sorting": [
        QuestionSchema(
            question_type="multiple_choice",
            question_text="What is the worst-case time complexity of Bubble Sort?",
            options=["A. O(n)", "B. O(n log n)", "C. O(n²)", "D. O(2ⁿ)"],
            correct_answer="C. O(n²)",
            explanation="Bubble Sort compares and swaps adjacent elements repeatedly, leading to O(n²) in the worst case.",
            difficulty="easy",
            topic="Sorting",
        ),
    ],
    "graphs": [
        QuestionSchema(
            question_type="multiple_choice",
            question_text="Which data structure is typically used in Breadth-First Search (BFS)?",
            options=["A. Stack", "B. Queue", "C. Heap", "D. Priority Queue"],
            correct_answer="B. Queue",
            explanation="BFS explores nodes level by level, using a queue to track the frontier.",
            difficulty="easy",
            topic="Graphs",
        ),
    ],
}


def _topic_to_key(topic: str) -> str:
    """Map a topic string to a mock question bank key."""
    t = topic.lower()
    if any(k in t for k in ["loop", "לולאה", "iteration"]):
        return "loops"
    if any(k in t for k in ["recursion", "רקורסיה", "recursive"]):
        return "recursion"
    if any(k in t for k in ["sort", "מיון", "bubble", "merge", "quick"]):
        return "sorting"
    if any(k in t for k in ["graph", "גרף", "bfs", "dfs"]):
        return "graphs"
    return "loops"  # default fallback


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

def generate_test(
    topic: str,
    num_questions: int = 3,
    difficulty: Optional[str] = None,
    api_key: Optional[str] = None,
) -> TestSchema:
    """
    Generate a practice test for the given topic.

    Args:
        topic: The study task topic (e.g., "Loops", "Recursion", "Sorting").
        num_questions: Number of questions to generate.
        difficulty: Optional difficulty filter ("easy", "medium", "hard").
        api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.

    Returns:
        TestSchema containing the list of questions.
    """
    use_mock = os.getenv("USE_MOCK_LLM", "true").lower() == "true"

    if use_mock:
        key = _topic_to_key(topic)
        questions = MOCK_QUESTIONS.get(key, MOCK_QUESTIONS["loops"])[:num_questions]
        return TestSchema(
            topic=topic,
            questions=questions,
            total_questions=len(questions),
            estimated_minutes=len(questions) * 5,
            generated_at=datetime.utcnow().isoformat() + "Z",
        )

    key = api_key or os.getenv("OPENAI_API_KEY", "")
    if not key:
        return generate_test(topic, num_questions, difficulty)  # fallback to mock

    try:
        from openai import OpenAI
    except ImportError:
        return generate_test(topic, num_questions, difficulty)  # fallback to mock

    client = OpenAI(api_key=key)

    user_prompt = f"""
Generate {num_questions} practice questions for the topic: {topic}.
Difficulty preference: {difficulty or "mixed"}.
Output only valid JSON matching the specified structure.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
        if raw.endswith("```"):
            raw = "\n".join(raw.split("\n")[:-1])

        import json
        data = json.loads(raw)
        questions = []
        for q in data.get("questions", []):
            questions.append(
                QuestionSchema(
                    question_type=q.get("question_type", "multiple_choice"),
                    question_text=q.get("question_text", ""),
                    options=q.get("options", []),
                    correct_answer=q.get("correct_answer", ""),
                    explanation=q.get("explanation", ""),
                    difficulty=q.get("difficulty", "medium"),
                    topic=topic,
                )
            )
        return TestSchema(
            topic=topic,
            questions=questions,
            total_questions=len(questions),
            estimated_minutes=len(questions) * 5,
            generated_at=datetime.utcnow().isoformat() + "Z",
        )
    except Exception:
        return generate_test(topic, num_questions, difficulty)  # fallback to mock


if __name__ == "__main__":
    test = generate_test("Recursion and base cases", num_questions=2)
    print(f"Generated test for: {test.topic}")
    for q in test.questions:
        print(f"\n[{q.difficulty.upper()}] {q.question_type}: {q.question_text}")
        if q.options:
            for opt in q.options:
                print(f"  {opt}")
        print(f"Answer: {q.correct_answer}")
        print(f"Explanation: {q.explanation}")
